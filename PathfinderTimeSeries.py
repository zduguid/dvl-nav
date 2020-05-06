# PathfinderTimeSeries.py
#
# Represents a Pathfinder DVL time series of ensemble measurements.
#   2020-01-29  zduguid@mit.edu         initial implementation
#   2020-05-05  zduguid@mit.edu         reorganized code with DVL superclass 

import csv
import struct
import sys
import numpy as np 
import pandas as pd
from datetime import datetime
from PathfinderDVL import PathfinderDVL
from PathfinderChecksumError import PathfinderChecksumError


class PathfinderTimeSeries(PathfinderDVL):
    def __init__(self, name=datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        """Constructor of a Pathfinder DVL time series of ensembles.

        Please note that various Pathfinder DVL settings may vary from 
        ensemble to ensemble. For example, if several mission are combined 
        into the same time-series object, the different missions will have 
        different starting lat/lon positions (or starting UTM positions)

        The time series data is stored in a pandas DataFrame object 
        for easy manipulation and access. That said, to avoid
        appending to a DataFrame (which is slow) the incoming 
        ensembles are collected in a python list and once the 
        to_datraframe function is called the pandas DataFrame is 
        created.

        Args: 
            name: The name of the time-series. For example, name could be the 
                filename of the parsed DVL Pathfinder file. The name attribute 
                is used when saving a parsed time-series to CSV format. 
        """
        # use the parent constructor for defining Micron Sonar variables
        super().__init__()

        # initialize the DataFrame and ensemble list parameters 
        self._name          = name
        self._df            = None
        self._ensemble_list = []


    @property
    def name(self):
        return self._name

    @property
    def ensemble_list(self):
        return self._ensemble_list

    @property
    def df(self):
        return self._df


    @classmethod
    def from_pd0(cls, filepath, save):
        pass


    def add_ensemble(self, ensemble):
        """Adds a DVL Pathfinder ensemble to the growing list of ensembles.

        Args: 
            ensemble: a Micron Sonar ensemble  
        """
        self._ensemble_list.append(ensemble.data_array)


    def to_dataframe(self):
        """Converts the current list of ensembles into a DataFrame.

        Note: calling this function will invoke pd.concat(), which creates a 
        copy of the whole DataFrame in memory. As a result, if this function 
        is called many times, there will be significant slowdown. Instead,
        consider collecting ensembles into the ensemble_list until a suitable 
        number of ensembles have been collected, and then intermittently call 
        the to_dataframe function.
        """
        # convert available ensembles to DataFrame
        if self.ensemble_list:
            ts      = np.array(self.ensemble_list)
            cols    = self.label_list
            t_index = self.data_lookup['time']
            t       = ts[:,t_index]
            index   = pd.DatetimeIndex([datetime.fromtimestamp(v) for v in t])
            new_df  = pd.DataFrame(data=ts, index=index, columns=cols)

            # concatenate new ensembles with existing DataFrame if possible
            if self.df is None:
                self._df = new_df
            else:
                self._df = pd.concat([self.df, new_df])

            # reset the ensemble list once added to the DataFrame
            self._ensemble_list = []
        else:
            print("WARNING: No ensembles to add to DataFrame.")


    def save_as_csv(self, name=None, directory='./'):
        """Saves the DataFrame to csv file. 

        Args:
            name: name used when saving the file.
            directory: string directory to save the DataFrame to.
        """
        # update name if not given
        if name is None:
            name = self.name 

        # add ensembles to the DataFrame if they haven't been added yet
        if self.ensemble_list:
            self.to_dataframe()

        # save DataFrame to csv file
        if self.df is not None:
            self.df.to_csv(directory+name+'.CSV')
        else:
            print("WARNING: No data to save.")

