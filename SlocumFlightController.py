# SlocumFlightController.py
#
# Class for parsing .dbd files 
#   2020-05-22  zduguid@mit.edu         initial implementation

import pandas as pd
import numpy as np
import time 
from datetime import datetime
from os import listdir
from os.path import isfile, join


class SlocumFlightController(object):
    def __init__(self, name=datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        """Represents a Slocum Glider flight log. 
        
        Note that only a subset of the variables are extracted. If more 
        variables are desired, simply add them to the label list below.
        """
        self._label_list = [
            # Index Variable
            'time',

            # User Defined Variables   
            'm_filename_hash',
            'm_mission_hash',

            # Dynamics Variables 
            'm_present_time',
            'm_speed',
            'm_pitch',
            'm_roll',
            'm_heading',
            'm_fin',
            'm_depth',
            'm_depth_rate',
            'm_water_depth',
            'm_pressure',
            'm_altitude',
            'm_battery',
            'm_vacuum',
            
            # Controller Variables 
            'c_pitch',
            'c_roll',
            'c_heading',
            'c_fin',

            # GPS Variables
            'm_gps_x_lmc',
            'm_gps_y_lmc',
            'm_gps_fix_x_lmc',
            'm_gps_fix_y_lmc',
            'm_gps_status',
            'm_gps_full_status',

            # LMC Variables 
            'm_x_lmc',
            'm_y_lmc',
            'm_dr_time',
            'm_dr_surf_x_lmc',
            'm_dr_surf_y_lmc',
            'm_ext_x_lmc',
            'm_ext_y_lmc',
            'm_ext_z_lmc',
            'x_lmc_xy_source',
            'c_wpt_x_lmc',
            'c_wpt_y_lmc',

            # Lat/Lon Variables
            'm_lat',
            'm_lon',
            'm_gps_lat',
            'm_gps_lon',
            'c_wpt_lat',
            'c_wpt_lon',

            # Velocity Variables
            'm_water_vx',
            'm_water_vy',
            'm_vx_lmc',
            'm_vy_lmc',

            # Miscellaneous Variables
            'm_appear_to_be_at_surface',
            'm_science_clothesline_lag',
            'sci_m_present_time',
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


    def get_data(self, ensemble, var):
        """Retrieve value of a variable in the ensemble array 
        """
        return ensemble[self.data_lookup[var]]


    def set_data(self, ensemble, var, val):
        """Set variable-value pair in the data ensemble
        """
        ensemble[self.data_lookup[var]] = val
        

    def get_var_unit(self, var_name):
        """Return the units associated with the var name
        """
        return(self.var_units[self.var_dict[var_name]])


    def add_ensemble(self, ensemble):
        """Adds an ensemble to the ensemble list.
        """
        self._ensemble_list.append(ensemble) 


    def get_utm_coords(m_lat, m_lon): 
        """TODO
        """
        SECS_IN_MIN = 60
        MIN_OFFSET = 100
        lat_min  = m_lat % MIN_OFFSET 
        lon_min  = m_lon % MIN_OFFSET 
        lat_dec  = (m_lat - lat_min)/MIN_OFFSET + lat_min/SECS_IN_MIN
        lon_dec  = (m_lon - lon_min)/MIN_OFFSET + lon_min/SECS_IN_MIN
        utm_pos  = utm.from_latlon(lat_dec, lon_dec)
        easting  = round(utm_pos[0],2)
        northing = round(utm_pos[1],2)
        zone     = utm_pos[2]
        return(easting, northing, zone)   


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
            print("  WARNING: No ensembles to add to DataFrame.")
    
    
    @classmethod
    def from_asc(cls, filepath, save, verbose=True, interval=True):
        """Parses DBD (flight controller file) from the Slocum Glider.

        Args: 
            filepath: the file location of the pd0 to be parsed, requires that 
                file located at filepath is a valid pd0 file
            save: boolean flag for saving the resulting time-series or not
            verbose: boolean flag for printing file information while parsing
        """
        PRINT_INTERVAL = 200 
        HEADER_LEN = 14
        TIME_ZONE_OFFSET = 5

        # open the file 
        asc_file = open(filepath, 'rb').read()
        filename = filepath.split('/')[-1]
        count = 0
        if verbose:
            print('________________________________________')
            print('  Parsing Flight Controller ------------')
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
            ts._var_dict  = {_ : ts.var_names.index(_) for _ in ts.label_list if _ in ts.var_names}

            # parse ensembles until the file is empty 
            line = [float(_) for _ in f.readline().split(' ')[:-1]]
            while line:
                count += 1

                # add selected variables to ensemble 
                ensemble = np.zeros(ts.ensemble_size)
                for var in ts.label_list:
                    if var in ts.var_dict:
                        val = line[ts.var_dict[var]]
                        ts.set_data(ensemble, var, val)

                # add user defined variables to ensemble 
                ts.set_data(ensemble, 'm_filename_hash', 
                    hash(header['filename']))

                # filename changes with dive number, not mission 
                #   + important because LMC coordinates reset each mission
                mission = header['filename'].rsplit('-',1)[0]
                ts.set_data(ensemble, 'm_mission_hash', hash(mission))

                # convert time from EDT to UTC
                EDT_time = ts.get_data(ensemble, 'm_present_time')
                UTC_time = datetime.fromtimestamp(EDT_time) + \
                    pd.Timedelta("%d hours" % TIME_ZONE_OFFSET)
                ts.set_data(ensemble, 'time', UTC_time.timestamp())
                ts.add_ensemble(ensemble)

                # print number of ensembles parsed periodically 
                if verbose and interval:
                    if (count % PRINT_INTERVAL == 0):
                        print('    # ensembles:  %5d' % (count,))

                line = [float(_) for _ in f.readline().split(' ')[:-1]]

        # parsing completed 
        ts.to_dataframe()
        if verbose:
            parse_stop = time.time()
            print('  Parsing Complete ---------------------')
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


    @classmethod
    def from_directory(cls, directory, save=None, name=None, verbose=False):
        """Constructor of flight controllers log from directory of .asc files 
        """
        print('>> Parsing folder of ASC Files')
        # acquire a list of all files in the provided directory 
        file_list = [f for f in listdir(directory) if 
                     isfile(join(directory,f)) and f.split('.')[-1] == 'asc']
        frames    = [cls.from_asc(directory+f, save=False, verbose=verbose,
                     interval=False).df for f in file_list]
        ts        = cls()
        ts._df    = pd.concat(frames)
        ts._df.sort_index(inplace=True)
        print('>> Finished Parsing!')
        return ts

