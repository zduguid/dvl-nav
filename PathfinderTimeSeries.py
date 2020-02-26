# PathfinderTimeSeries.py
#
# TODO
#   2020-01-29  zduguid@mit.edu         initial implementation

import struct
import sys
import numpy as np 
import pandas as pd
from PathfinderChecksumError import PathfinderChecksumError
from datetime import datetime


class PathfinderTimeSeries(object):
    def __init__(self, ensemble):
        """TODO write description here  

        Note: assumes all ensembles stored in the same time series object
        occurred during the same deployment. This means that all ensembles 
        in the time series share the same "fixed_leader" variables. As a
        result, upon construction of a new time series object, the fixed leader
        values are extracted from the first ensemble received. The fixed leader
        values of all subsequent ensembles are ignored because they are

        """
        # add fixed leader attributes of the first ensemble to the time series
        #   + attributes that start with an underscore are not transferred
        ensemble_attributes = ensemble.__dict__
        for key in ensemble_attributes.keys():
            if key[0] != '_':
                setattr(self, key, ensemble_attributes[key])

        # initialize the data_arrays
        self._ensemble_list = [ensemble.data_array]


    @property
    def ensemble_list(self):
        return self._ensemble_list


    @property
    def df(self):
        return self._df


    def add_ensemble(self, ensemble):
        """TODO 
        """
        self._ensemble_list.append(ensemble.data_array)


    def to_dataframe(self):
        """TODO
        """
        ts     = np.array(self.ensemble_list)
        cols   = self.label_list
        t      = ts[:,0] # first column of the times series 
        index  = pd.DatetimeIndex([datetime.fromtimestamp(val) for val in t])

        # save to data-frame 
        self._df  = pd.DataFrame(data=ts, index=index, columns=cols)

