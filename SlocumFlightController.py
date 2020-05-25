# SlocumFlightController.py
#
# Class for parsing .dbd files 
#   2020-05-22  zduguid@mit.edu         initial implementation

import pandas as pd
import numpy as np
import time 
from datetime import datetime


class SlocumFlightController(object):
    def __init__(self, name=datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        """Represents a Slocum Glider flight log. 
        
        Note that only a subset of the variables are extracted. If more 
        variables are desired, simply add them to the label list below.
        """
        self._label_list = [
            'm_present_time',
            'm_speed',
            'm_pitch',
            'c_pitch',
            'm_roll',
            'c_roll',
            'm_heading',
            'c_heading',
            'm_fin',
            'c_fin',
            'm_battery',
            'm_vacuum',
            'm_depth',
            'm_pressure',
            'm_altitude',
            'm_water_depth',
            'm_depth_rate_avg_final',
            'm_final_water_vx',
            'm_final_water_vy',
            'm_water_vx',
            'm_water_vy',
            'c_wpt_lat',
            'c_wpt_lon',
            'm_vx_lmc',
            'm_vy_lmc',
            'm_lat',
            'm_lon',
            'm_dr_time',
            'm_ext_x_lmc',
            'm_ext_y_lmc',
            'm_ext_z_lmc',
            'm_dr_surf_x_lmc',
            'm_dr_surf_y_lmc',
            'm_x_lmc',
            'm_y_lmc',
            'x_lmc_xy_source',
            'm_gps_lat',
            'm_gps_lon',
            'm_gps_fix_x_lmc',
            'm_gps_fix_y_lmc',
            'm_gps_x_lmc',
            'm_gps_y_lmc',
            'm_gps_status',
            'm_gps_full_status',
            'm_appear_to_be_at_surface',
            'sci_m_present_time',
            'm_science_clothesline_lag',
            'x_software_ver'
        ]
        self._header        = None
        self._df            = None
        self._label_set     = set(self.label_list)
        self._ensemble_size = len(self.label_list)
        self._data_lookup   = {self.label_list[i]:i 
            for i in range(self.ensemble_size)}
        self._ensemble_list = []


    @property
    def label_list(self):
        return self._label_list

    @property
    def label_set(self):
        return self._label_set
    
    @property
    def ensemble_size(self):
        return self._ensemble_size

    @property
    def data_lookup(self):
        return self._data_lookup

    @property
    def header(self):
        return self._header

    @property
    def df(self):
        return self._df

    @property
    def var_names(self):
        return self._var_names

    @property
    def var_units(self):
        return self._var_units

    @property
    def var_sizes(self):
        return self._var_sizes

    @property
    def var_dict(self):
        return self._var_dict

    @property
    def ensemble_list(self):
        return self._ensemble_list
        

    def get_var_unit(self, var_name):
        """Return the units associated with the var name
        """
        return(self.var_units[self.var_dict[var_name]])


    def add_ensemble(self, ensemble):
        """Adds an ensemble to the ensemble list.
        """
        self._ensemble_list.append(ensemble)    


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
            t_index = self.data_lookup['m_present_time']
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
    
    
    @classmethod
    def from_asc(cls, filepath, save, verbose=True):
        """Parses DBD (flight controller file) from the Slocum Glider.

        Args: 
            filepath: the file location of the pd0 to be parsed, requires that 
                file located at filepath is a valid pd0 file
            save: boolean flag for saving the resulting time-series or not
            verbose: boolean flag for printing file information while parsing
        """
        PRINT_INTERVAL = 200 
        HEADER_LEN = 14

        # open the file 
        asc_file = open(filepath, 'rb').read()
        filename = filepath.split('/')[-1]
        count = 0
        if verbose:
            print('________________________________________')
            print('- Parsing Slocum File (Flight) ---------')
            print('    input file: %s' % (filename,))
            parse_start = time.time()

        # initialize the time series object
        name   = filepath.split('/')[-1].split('.')[0]
        ts     = cls(name)
        header = {}

        # parse the ASC file 
        with open(filepath, 'r') as f:
            # parse the fixed file header in formation 
            for i in range(HEADER_LEN):
                head_line = f.readline().split(': ')
                header[head_line[0]] = head_line[1].split('\n')[0]
            ts._header = header

            # parse the variables names, sizes
            ts._var_names = f.readline().split(' ')[:-1]
            ts._var_units = f.readline().split(' ')[:-1]
            ts._var_sizes = f.readline().split(' ')[:-1]
            ts._var_dict  = {_ : ts.var_names.index(_) for _ in ts.label_list}

            # parse ensembles until the file is empty 
            line   = [float(_) for _ in f.readline().split(' ')[:-1]]
            while line:
                count += 1
                ens = np.array([line[ts.var_dict[_]] for _ in ts.label_list])
                ts.add_ensemble(ens)
                line = [float(_) for _ in f.readline().split(' ')[:-1]]

                # print number of ensembles parsed periodically 
                if verbose:
                    if (count % PRINT_INTERVAL == 0):
                        print('    # ensembles:  %5d' % (count,))

        # parsing completed 
        ts.to_dataframe()
        if verbose:
            parse_stop = time.time()
            print('- Parsing Complete ---------------------')
            print('    # ensembles:  %5d'    % (count))
            print('    parsing time:  %f'    % (parse_stop - parse_start))

        # save the file to .csv format
        if save:
            
            # determine how to save the file
            root, _, glider, _ = filepath.rsplit('/',3)
            directory = root + '/' + 'dbd-parsed/' + glider + '/'
            
            # save the file using pandas 
            save_start = time.time()
            time_series.save_as_csv(name=name, directory=directory)
            save_stop  = time.time()
            if verbose:
                print('    saving time:   %f'    % (save_stop - save_start))
                print('    output file:   %s'    % (name+'.CSV'))
     
        return(ts)

