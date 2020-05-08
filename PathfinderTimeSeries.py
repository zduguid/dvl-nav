# PathfinderTimeSeries.py
#
# Represents a Pathfinder DVL time series of ensemble measurements.
#   2020-01-29  zduguid@mit.edu         initial implementation
#   2020-05-05  zduguid@mit.edu         reorganized code with DVL superclass 

import csv
import numpy as np 
import pandas as pd
import struct
import sys
import time
from datetime import datetime
from PathfinderDVL import PathfinderDVL
from PathfinderEnsemble import PathfinderEnsemble
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
    def from_pd0(cls, filepath, save, verbose=True):
        """Parses DVL Time Series from given pd0 file. 

        Args: 
            filepath: the file location of the pd0 to be parsed, requires that 
                file located at filepath is a valid pd0 file
            save: boolean flag for saving the resulting time-series or not
            verbose: boolean flag for printing file information while parsing
        """
        PRINT_INTERVAL = 200 

        # open the file 
        pd0_file = open(filepath, 'rb').read()
        count = 0
        if verbose:
            print('________________________________________')
            print('- Parsing New File ---------------------')
            print('    input file: %s' % (filepath,))
            parse_start = time.time()

        # initialize the time series object
        name          = filepath.split('/')[-1].split('.')[0]
        time_series   = cls(name)
        prev_ensemble = None

        # parse ensembles until the end of the pd0 file is reached    
        while len(pd0_file) > 0:

            # parse an ensemble from the pd0 file and add it to the time series
            ensemble = PathfinderEnsemble(pd0_file, prev_ensemble)
            time_series.add_ensemble(ensemble)

            # chop off the ensemble we just parsed and added to the time series
            ensemble_len  = ensemble.num_bytes + 2
            pd0_file      = pd0_file[ensemble_len:]
            count        += 1
            prev_ensemble = ensemble

            # print number of ensembles parsed periodically 
            if verbose:
                if (count % PRINT_INTERVAL == 0):
                    print('    # ensembles:  %5d' % (count,))

        # convert to data-frame once all ensembles are collected
        time_series.to_dataframe()
        
        # parsing completed 
        if verbose:
            parse_stop = time.time()
            print('- Parsing Complete ---------------------')
            print('    # ensembles:  %5d'    % (count))
            print('    parsing time:  %f'    % (parse_stop - parse_start))

        # save the file to .csv format
        if save:
            
            # determine how to save the file
            root, _, glider, _ = filepath.rsplit('/',3)
            directory = root + '/' + 'pd0-parsed/' + glider + '/'
            
            # save the file using pandas 
            save_start = time.time()
            time_series.save_as_csv(name=name, directory=directory)
            save_stop  = time.time()
            if verbose:
                print('    saving time:   %f'    % (save_stop - save_start))
                print('    output file:   %s'    % (name+'.CSV'))

        # parse the configurations for diagnostic purposes
        if verbose:
            ensemble.parse_system_configuration()
            ensemble.parse_coordinate_transformation()
     
        return(time_series)


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
            odometry = self.df[['time','rel_pos_x', 'rel_pos_y', 'rel_pos_z']]
            odometry.to_csv(directory+name+'_odometry.CSV')
        else:
            print("WARNING: No data to save.")

