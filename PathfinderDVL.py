# PathfinderDVL.py
#
# Superclass for Pathfinder DVL data 
#   2020-05-05  zduguid@mit.edu         initial implementation

import numpy as np

class PathfinderDVL(object):
    def __init__(self):
        """Parent class for Pathfinder DVL data 

        Used to define Pathfinder variables that are constant between
        different Pathfinder DVL objects. 
        """
        # constants for unit conversion 
        self.DAM_TO_M        = 10           #      [dam] -> [m]
        self.DM_TO_M         = 1/10         #       [dm] -> [m]
        self.CM_TO_M         = 1/100        #       [cm] -> [m]
        self.MM_TO_M         = 1/1000       #       [mm] -> [m]
        self.TENTH_TO_DEG    = 1/10         #  [0.1 deg] -> [deg]
        self.HUNDRETH_TO_DEG = 1/100        # [0.01 deg] -> [deg]
        self.COUNT_TO_DB     = 0.61         #    [0,255] -> [dB]
        self.DEG_TO_RAD      = np.pi/180    #      [deg] -> [rad]
        self.RAD_TO_DEG      = 180/np.pi    #      [rad] -> [deg]

        # constants for the Pathfinder instrument 
        #   + set values for num_beams and num_bins for more efficient 
        #     array processing and ensemble storage. 
        self.NUM_BEAMS_EXP = 4       # expected number of DVL beams  
        self.NUM_BINS_EXP  = 40      # expected number of bins (or cells)
        self.BAD_VELOCITY  = -32768  # value that represents invalid velocity 
        self.BAD_BT_RANGE  = 0       # value that represents invalid range
        self.MAX_ENS_NUM   = 65536   # max number of ensembles before rollover

        # mounting bias parameters 
        self.BIAS_PITCH   = 12.5  # [deg]
        self.BIAS_ROLL    =  0.0  # [deg]
        self.BIAS_HEADING =  0.0  # [deg]

        # self.BIAS_PITCH   =  8.0  # [deg]
        # self.BIAS_ROLL    =  0.0  # [deg]
        # self.BIAS_HEADING =  0.0  # [deg]

        # self.BIAS_PITCH   =  8.0  # [deg]
        # self.BIAS_ROLL    =  4.0  # [deg]
        # self.BIAS_HEADING = -3.0  # [deg]
        
        self.JANUS_ANGLE  = 30    # [deg]

        # map from each variable group name to three letter abbreviation 
        self._data_abbreviations = {
            'fixed_leader'      : 'fld', 
            'variable_leader'   : 'vld',
            'derived'           : 'der',
            'velocity'          : 'vel',
            'correlation'       : 'cor',
            'echo_intensity'    : 'ech',
            'percent_good'      : 'per',
            'bottom_track'      : 'btm',
        }

        # variables that can be derived from other ensemble variables 
        #   - for example, this could navigation or odometry variables
        #   - OKAY to add and edit the variables in this list. If variables are
        #     added, make sure to implement the corresponding parsing function
        #     to the 'PathfinderEnsemble.parse_derived_variables()' function
        self._derived = (
            # relative velocities (through water velocities)
            'rel_vel_pressure_u',
            'rel_vel_pressure_v',
            'rel_vel_pressure_w',
            'rel_vel_dvl_u',
            'rel_vel_dvl_v',
            'rel_vel_dvl_w',

            # ocean current velocities (via propagation methods)
            'ocn_vel_u',
            'ocn_vel_v',
            'ocn_vel_w',

            # absolute velocities (over ground velocities)
            'abs_vel_btm_u',
            'abs_vel_btm_v',
            'abs_vel_btm_w',

            # positions
            'delta_x',
            'delta_y',
            'delta_z',
            'delta_t',
            'delta_z_pressure',
            'delta_pitch',
            'rel_pos_x',
            'rel_pos_y',
            'rel_pos_z',
            'rel_pos_x_dvl_dr',
            'rel_pos_y_dvl_dr',
            'rel_pos_z_dvl_dr',
            'origin_x',
            'origin_y',
            
            # miscellaneous
            'angle_of_attack',
            'num_good_vel_bins',

            # seafloor information 
            'bathy_factor_depth',
            'bathy_factor_slope', 
            'bathy_factor_orient',
        )

        # tuple of variables that are automatically reported by Pathfinder
        #   - header variables are used for parsing the rest of the ensemble
        #   - DO NOT edit these variables 
        self._header = (
            ('id',                              'B',    0),
            ('data_source',                     'B',    1),
            ('num_bytes',                       '<H',   2),
            ('spare',                           'B',    4),
            ('num_data_types',                  'B',    5),
        )

        # tuple of variables that are automatically reported by Pathfinder
        #   - "fixed leader" means that values are fixed during mission
        #   - the units of the raw values are shown in comments
        #   - the values are converted to standard metric units after unpacking
        #   - DO NOT edit these variables 
        self._fixed_leader = (
            ('id',                              '<H',    0),
            ('cpu_firmware_version',            'B',     2),
            ('cpu_firmware_revision',           'B',     3),
            ('system_configuration',            '<H',    4),
            ('simulation_flag',                 'B',     6),
            ('lag_length',                      'B',     7),
            ('num_beams',                       'B',     8),
            ('num_bins',                        'B',     9),
            ('pings_per_ensemble',              '<H',   10),
            ('depth_bin_length',                '<H',   12),    # [cm]
            ('blanking_distance ',              '<H',   14),    # [cm]
            ('profiling_mode',                  'B',    16),
            ('low_correlation_threshold',       'B',    17),
            ('num_code_repetitions',            'B',    18),
            ('percent_good_minimum',            'B',    19),
            ('error_velocity_threshold',        '<H',   20),    # [mm/s]
            ('minutes',                         'B',    22),
            ('seconds',                         'B',    23),
            ('hundredths',                      'B',    24),
            ('coordinate_transformation',       'B',    25),
            ('heading_alignment',               '<h',   26),    # [0.01 deg]
            ('heading_bias',                    '<h',   28),    # [0.01 deg]
            ('sensor_source',                   'B',    30),
            ('sensor_available',                'B',    31),
            ('bin0_distance',                   '<H',   32),    # [cm]
            ('transmit_pulse_length',           '<H',   34),    # [cm]
            ('starting_depth_cell',             'B',    36),
            ('ending_depth_cell',               'B',    37),
            ('false_target_threshold',          'B',    38),
            ('transmit_lag_distance',           '<H',   40),    # [cm]
            ('system_bandwidth',                '<H',   50),
            ('system_serial_number',            '<I',   54),
        )

        # down-select most useful variables from fixed leader variable list
        self._fixed_leader_vars_short = (
            'system_configuration',
            'num_beams',
            'num_bins', 
            'pings_per_ensemble',
            'depth_bin_length',
            'blanking_distance',
            'low_correlation_threshold',
            'percent_good_minimum',
            'error_velocity_threshold',
            'coordinate_transformation',
            'heading_alignment',
            'heading_bias',
            'sensor_source',
            'bin0_distance',
            'transmit_pulse_length',
        )

        # tuple of variables that are automatically reported by Pathfinder
        #   - "variable leader" means the values are dynamic during the mission
        #   - the units of the raw values are shown in comments
        #   - the values are converted to standard metric units after unpacking
        #   - DO NOT edit these variables 
        self._variable_leader = (
            ('id',                              '<H',    0),
            ('ensemble_number',                 '<H',    2),
            ('rtc_year',                        'B',     4),
            ('rtc_month',                       'B',     5),
            ('rtc_day',                         'B',     6),
            ('rtc_hour',                        'B',     7),
            ('rtc_minute',                      'B',     8),
            ('rtc_second',                      'B',     9),
            ('rtc_hundredths',                  'B',    10),
            ('ensemble_rollover',               'B',    11),
            ('bit_result',                      '<H',   12),
            ('speed_of_sound',                  '<H',   14),    # [m/s]
            ('depth',                           '<H',   16),    # [dm]
            ('heading',                         '<H',   18),    # [0.01 deg]
            ('pitch',                           '<h',   20),    # [0.01 deg]
            ('roll',                            '<h',   22),    # [0.01 deg]
            ('salinity',                        '<H',   24),    # [ppt]
            ('temperature',                     '<h',   26),    # [0.01 C]
            ('min_ping_wait_minutes',           'B',    28),
            ('min_ping_wait_seconds',           'B',    29),
            ('min_ping_wait_hundredths',        'B',    30),
            ('heading_standard_deviation',      'B',    31),
            ('pitch_standard_deviation',        'B',    32),    # [0.1 deg]
            ('roll_standard_deviation',         'B',    33),    # [0.1 deg]
            ('adc_rounded_voltage',             'B',    35),
            ('pressure',                        '<I',   48),    # [daPa]
            ('pressure_variance',               '<I',   52),    # [daPa]
            ('health_status',                   'B',    66),
            ('leak_a_count',                    '<H',   67),
            ('leak_b_count',                    '<H',   69),
            ('transducer_voltage',              '<H',   71),    # [0.001 Volts]
            ('transducer_current',              '<H',   73),    # [0.001 Amps]
            ('transducer_impedance',            '<H',   75),    # [0.001 Ohms]
        )

        # down-select most useful variables from variable leader variable list
        self._variable_leader_vars_short = (
            'ensemble_number',
            'rtc_year',
            'rtc_month',
            'rtc_day',
            'rtc_hour',
            'rtc_minute',
            'rtc_second',
            'rtc_hundredths',
            'bit_result',
            'speed_of_sound',
            'depth',
            'heading',
            'pitch',
            'roll',
            'salinity',
            'temperature',
            'min_ping_wait_minutes',
            'min_ping_wait_seconds',
            'min_ping_wait_hundredths',
            'heading_standard_deviation',
            'pitch_standard_deviation',
            'roll_standard_deviation',
            'adc_rounded_voltage',
            'pressure',
            'pressure_variance',
        )

        # tuple of variables reported by Pathfinder in bottom-track mode
        #   - the units of the raw values are shown in comments
        #   - the values are converted to standard metric units after unpacking
        #   - DO NOT edit these variables 
        self._bottom_track = (
            ('id',                              '<H',    0),
            ('btm_pings_per_ensemble',              '<H',    2),        
            ('btm_min_correlation_mag',             'B',     6),
            ('btm_min_echo_intensity_amp',          'B',     7),
            ('btm_bottom_track_mode',               'B',     9),
            ('btm_max_error_velocity',              '<H',   10),    # [mm/s]
            ('btm_beam0_range',                     '<H',   16),    # [cm]
            ('btm_beam1_range',                     '<H',   18),    # [cm]
            ('btm_beam2_range',                     '<H',   20),    # [cm]
            ('btm_beam3_range',                     '<H',   22),    # [cm]
            ('btm_beam0_velocity',                  '<h',   24),    # [mm/s]
            ('btm_beam1_velocity',                  '<h',   26),    # [mm/s]
            ('btm_beam2_velocity',                  '<h',   28),    # [mm/s]
            ('btm_beam3_velocity',                  '<h',   30),    # [mm/s]
            ('btm_beam0_correlation',               'B',    32),
            ('btm_beam1_correlation',               'B',    33),
            ('btm_beam2_correlation',               'B',    34),
            ('btm_beam3_correlation',               'B',    35),        
            ('btm_beam0_echo_intensity',            'B',    36),
            ('btm_beam1_echo_intensity',            'B',    37),
            ('btm_beam2_echo_intensity',            'B',    38),
            ('btm_beam3_echo_intensity',            'B',    39),
            ('btm_beam0_percent_good',              'B',    40),
            ('btm_beam1_percent_good',              'B',    41),
            ('btm_beam2_percent_good',              'B',    42),
            ('btm_beam3_percent_good',              'B',    43),
            ('btm_ref_layer_min',                   '<H',   44),    # [dm]
            ('btm_ref_layer_near',                  '<H',   46),    # [dm]
            ('btm_ref_layer_far',                   '<H',   48),    # [dm]
            ('btm_beam0_ref_layer_velocity',        '<h',   50),    # [mm/s]
            ('btm_beam1_ref_layer_velocity',        '<h',   52),    # [mm/s]
            ('btm_beam2_ref_layer_velocity',        '<h',   54),    # [mm/s]
            ('btm_beam3_ref_layer_velocity',        '<h',   56),    # [mm/s]
            ('btm_beam0_ref_layer_correlation',     'B',    58),
            ('btm_beam1_ref_layer_correlation',     'B',    59),
            ('btm_beam2_ref_layer_correlation',     'B',    60),
            ('btm_beam3_ref_layer_correlation',     'B',    61),
            ('btm_beam0_ref_layer_echo_intensity',  'B',    62),
            ('btm_beam1_ref_layer_echo_intensity',  'B',    63),
            ('btm_beam2_ref_layer_echo_intensity',  'B',    64),
            ('btm_beam3_ref_layer_echo_intensity',  'B',    65),
            ('btm_beam0_ref_layer_percent_good',    'B',    66),
            ('btm_beam1_ref_layer_percent_good',    'B',    67),
            ('btm_beam2_ref_layer_percent_good',    'B',    68),
            ('btm_beam3_ref_layer_percent_good',    'B',    69),
            ('btm_max_tracking_depth',              '<H',   70),    # [dm]
            ('btm_beam0_rssi',                      'B',    72),
            ('btm_beam1_rssi',                      'B',    73),
            ('btm_beam2_rssi',                      'B',    74),
            ('btm_beam3_rssi',                      'B',    75),
            ('btm_shallow_water_gain',              'B',    76),
            ('btm_beam0_msb',                       'B',    77),    # [cm]
            ('btm_beam1_msb',                       'B',    78),    # [cm]
            ('btm_beam2_msb',                       'B',    79),    # [cm]
            ('btm_beam3_msb',                       'B',    80),    # [cm]
        )

        # down-select most useful variables from bottom track variable list
        self._bottom_track_vars_short = (
            'btm_pings_per_ensemble',
            'btm_bottom_track_mode',
            'btm_max_error_velocity',
            'btm_beam0_range',
            'btm_beam1_range',
            'btm_beam2_range',
            'btm_beam3_range',
            'btm_beam0_velocity',
            'btm_beam1_velocity',
            'btm_beam2_velocity',
            'btm_beam3_velocity',
            'btm_beam0_rssi',
            'btm_beam1_rssi',
            'btm_beam2_rssi',
            'btm_beam3_rssi',
        )

        # set up water profiling data field variables
        self._velocity_vars       = self.get_profile_var_list('velocity')
        self._correlation_vars    = self.get_profile_var_list('correlation')
        self._echo_intensity_vars = self.get_profile_var_list('echo_intensity')
        self._percent_good_vars   = self.get_profile_var_list('percent_good')

        # set the lengths of the associated variable lists 
        self._fixed_leader_len    = len(self.fixed_leader_vars)
        self._variable_leader_len = len(self.variable_leader_vars)
        self._derived_len         = len(self.derived_vars)
        self._bottom_track_len    = len(self.bottom_track_vars)
        self._velocity_len        = len(self.velocity_vars)
        self._correlation_len     = len(self.correlation_vars)
        self._echo_intensity_len  = len(self.echo_intensity_vars)
        self._percent_good_len    = len(self.percent_good_vars)
        
        # set the variable lists for full and shortened list of variables
        self._label_list          = tuple(['time'])                 + \
                                    self.fixed_leader_vars_short    + \
                                    self.variable_leader_vars_short + \
                                    self.derived_vars               + \
                                    self.velocity_vars              + \
                                    self.bottom_track_vars_short

        self._label_list_long     = tuple(['time'])                 + \
                                    self.fixed_leader_vars          + \
                                    self.variable_leader_vars       + \
                                    self.derived_vars               + \
                                    self.velocity_vars              + \
                                    self.correlation_vars           + \
                                    self.echo_intensity_vars        + \
                                    self.percent_good_vars          + \
                                    self.bottom_track_vars

        self._label_set           = set(self.label_list)
        self._ensemble_size       = len(self.label_list)
        self._data_lookup         = {self.label_list[i]:i \
                                     for i in range(self.ensemble_size)}
        self._label_set_long      = set(self.label_list_long)
        self._ensemble_size_long  = len(self.label_list_long)
        self._data_lookup_long    = {self.label_list_long[i]:i \
                                     for i in range(self.ensemble_size_long)}


    @property
    def data_abbreviations(self):
        return self._data_abbreviations

    @property
    def header_vars(self):
        return self.get_list_without_id(self._header)

    @property
    def fixed_leader_vars(self):
        return self.get_list_without_id(self._fixed_leader)

    @property
    def fixed_leader_vars_short(self):
        return self._fixed_leader_vars_short
    
    @property
    def variable_leader_vars(self):
        return self.get_list_without_id(self._variable_leader)

    @property
    def variable_leader_vars_short(self):
        return self._variable_leader_vars_short
    
    @property
    def derived_vars(self):
        return self._derived

    @property
    def velocity_vars(self):
        return self._velocity_vars
    
    @property
    def correlation_vars(self):
        return self._correlation_vars
    
    @property
    def echo_intensity_vars(self):
        return self._echo_intensity_vars
    
    @property
    def percent_good_vars(self):
        return self._percent_good_vars
    
    @property
    def bottom_track_vars(self):
        return self.get_list_without_id(self._bottom_track)
    
    @property
    def bottom_track_vars_short(self):
        return self._bottom_track_vars_short
    
    @property
    def header_format(self):
        return self._header

    @property
    def fixed_leader_format(self):
        return self._fixed_leader
    
    @property
    def variable_leader_format(self):
        return self._variable_leader

    @property
    def bottom_track_format(self):
        return self._bottom_track

    @property
    def fixed_leader_len(self):
        return self._fixed_leader_len

    @property
    def variable_leader_len(self):
        return self._variable_leader_len

    @property
    def derived_len(self):
        return self._derived_len

    @property
    def velocity_len(self):
        return self._velocity_len

    @property
    def correlation_len(self):
        return self._correlation_len

    @property
    def echo_intensity_len(self):
        return self._echo_intensity_len

    @property
    def percent_good_len(self):
        return self._percent_good_len

    @property
    def bottom_track_len(self):
        return self._bottom_track_len

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
    def label_list_long(self):
        return self._label_list_long
    
    @property
    def label_set_long(self):
        return self._label_set_long

    @property
    def ensemble_size_long(self):
        return self._ensemble_size_long
    
    @property
    def data_lookup_long(self):
        return self._data_lookup_long


    def get_list_without_id(self, var_list):
        # Note that 'id' term is not a variable, just a flag for parsing 
        return tuple(_[0] for _ in var_list[1:])


    def get_profile_var_name(self, var_type, i, j):
        """Returns variable name string for variable type, bin, and beam.

        Args:
            var_type: the variable type string (i.e. 'velocity')
            i: the bin number 
            j: the beam (or field) number
        """
        return "%s_bin%s_beam%s" % (self._data_abbreviations[var_type], i, j)


    def get_profile_var_list(self, var_type):
        """Returns a tuple of variable names for all bin/beam combinations
        """
        return( 
            tuple(
                [self.get_profile_var_name(var_type, i, j) 
                 for i in range(self.NUM_BINS_EXP) 
                 for j in range(self.NUM_BEAMS_EXP)]
            )
        )


    