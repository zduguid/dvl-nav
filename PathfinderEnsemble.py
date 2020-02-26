# PathfinderEnsemble.py
#
# Represents a Doppler Velocity Log ensemble. 
# Adapted from pd0_parser.py, written by Dave Pingal (dpingal@teledyne.com).
#   2018-11-26  dpingal@teledyne.com    implemented pd0_parser.py
#   2020-01-27  zduguid@mit.edu         implemented PathfinderEnsemble.py

import struct
import sys
import numpy as np 
import pandas as pd
from PathfinderChecksumError import PathfinderChecksumError
from datetime import datetime


class PathfinderEnsemble(object):
    def __init__(self, pd0_bytes):
        """Constructor for a Doppler Velocity Log (DVL) Ensemble object. 

        The 'Pathfinder Doppler Velocity Log (DVL) 600 kHz' user manual was 
        consulted while writing this code. Specific pages of the manual are 
        referenced in the doc-strings of relevant functions.

        The Pathfinder always sends the Least Significant Byte (LSB) first.
        This corresponds with little-endian byte ordering. As a result, the 
        less-than symbol (<) is included in the format string so that the 
        struct module can unpack the bytes properly using the function below:

        struct.unpack_from(format-string, buffer, offset=0)
        (https://docs.python.org/3/library/struct.html)

        Args: 
            pd0_bytes: pd0 bytes to be parsed into a DVL ensemble.

        Returns:
            A new Ensemble that has been parsed from the given pd0 bytes, or 
            None if there was an error while parsing.

        Raises:
            ValueError if header id is incorrect.
            PathfinderChecksumError if an invalid checksum is found.
        """
        # maps byte id with particular data types and data parsers
        self._data_id_parsers = {
            0x0000: ('fixed_leader',    self.parse_fixed_leader),
            0x0080: ('variable_leader', self.parse_variable_leader),
            0x0100: ('velocity',        self.parse_water_profiling_data),
            0x0200: ('correlation',     self.parse_water_profiling_data),
            0x0300: ('echo_intensity',  self.parse_water_profiling_data),
            0x0400: ('percent_good',    self.parse_water_profiling_data),
            0x0600: ('bottom_track',    self.parse_bottom_track),
        }

        self._data_short_names = {
            'fixed_leader'      : 'fld', 
            'variable_leader'   : 'vld',
            'velocity'          : 'vel',
            'correlation'       : 'cor',
            'echo_intensity'    : 'ech',
            'percent_good'      : 'per',
            'bottom_track'      : 'btm',
            'derived'           : 'der'
        }

        self.num_beams    = 4       # number of DVL beams is fixed 
        self.bad_velocity = -32768  # value that represents invalid velocity 
        self.bad_bt_range = 0       # value that represents invalid range

        # parse array given pd0 bytes
        self.parse_ensemble(pd0_bytes)


    @property
    def data_array(self):
        return self._data_array

       
    @property
    def data_id_parsers(self):
        return self._data_id_parsers


    @property
    def data_short_names(self):
        return self._data_short_names


    @property
    def data_type_sizes(self):
        return self._data_type_sizes

    
    @property
    def data_type_offsets(self):
        return self._data_type_offsets

    
    @property
    def ensemble_size(self):
        return self._ensemble_size
    

    def parse_ensemble(self, pd0_bytes):
        """Parses an ensemble from pd0 bytes.

        Pseudocode for decoding a pd0 ensemble:
        1. locate the header data via the header id (7F7F).
        2. validate the checksum to confirm a valid ensemble.
        3. locate the number of data types.
        4. locate the offset for each data type.
        5. locate the data type bytes using the offset and data type id.
        6. parse the data type using the Pathfinder byte specification.

        Pseudocode for decoding a sequence in the Pathfinder Manual on pg 241.

        Args:
            pd0_bytes: pd0 bytes to be parsed into a DVL ensemble.
        """
        # parse header to confirm header ID and validate checksum
        self.parse_header(pd0_bytes)
        self.validate_checksum(pd0_bytes)

        # parse each data type 
        for address in self.address_offsets:
            header_format = 'H'
            header_id = struct.unpack_from(header_format,pd0_bytes,address)[0]
            if header_id in self.data_id_parsers:
                name      = self.data_id_parsers[header_id][0]
                parser    = self.data_id_parsers[header_id][1]
                data_dict = parser(pd0_bytes, name, address)
            else:
                print('  WARNING: no parser found for header %d' %(header_id,))


    def unpack_bytes(self, pd0_bytes, format_tuples, offset=0):
        """Unpacks pd0 bytes into data format types.

        Args:
            pd0_bytes: bytes to be parsed into specified data types.
            format_tuples: tuple of variable format tuples,
                where each variable format tuple is of the form:
                (name <string>, format-string <char>, offset <int>).
            offset: byte offset to start reading the pd0 bytes.

        Returns:
            Dictionary representing the parsed data types, where the keys of
            the dictionary are var-name and the values are the parsed values.

        Note: Information table for common Format Strings: 
            format  type                size 
            x       pad-byte 
            c       char                1
            b       signed-char         1
            B       unsigned char       1
            h       short               2
            H       unsigned short      2
            i       int                 4
            I       unsigned int        4
            >i      big-endian int      1
            <i      little-endian int   1
            q       long long           8
            Q       unsigned long long  8 
        (taken from: https://docs.python.org/3/library/struct.html)
        """
        data = {}
        for format_tuple in format_tuples:
            var_name        = format_tuple[0]
            var_format      = format_tuple[1]
            var_size        = struct.calcsize(var_format)
            var_offset      = offset + format_tuple[2]
            data[var_name]  = struct.unpack_from(var_format,
                                                 pd0_bytes,
                                                 var_offset)[0]
        return(data)


    def validate_checksum(self, pd0_bytes):
        """Validates the checksum for the ensemble.
        """
        calc_checksum  = sum([c for c in pd0_bytes[:self.num_bytes]]) & 0xFFFF
        given_checksum = struct.unpack_from('<H', pd0_bytes, self.num_bytes)[0]
        if calc_checksum != given_checksum:
            raise PathfinderChecksumError(calc_checksum, given_checksum)


    def parse_beams(self, pd0_bytes, offset, num_cells, num_beams, var_format, 
        var_name):
        """Parses beams of DVL data.
        
        Velocity, correlation mag, echo intensity, and percent good data types
        report values per depth cell per beam. For example, with 4 beams
        and 40 depth cell bins, there are 160 velocity values reported 
        (each value being encoded with two bytes, unlike the other fields).

        Args:
            pd0_bytes: pd0 bytes to be parsed into the fixed leader data type.
            offset: byte offset to start parsing the fixed leader. 
            num_cells: number of depth cells on DVL (user setting).
            num_beams: number of beams on the DVL (fixed at 4).
            var_format: Format String for the variable being parsed for each
                beam. For example var_format = 'h' means type short.
            var_name: name of the variable being parsed (i.e. 'velocity')
        """
        data     = np.empty([0, num_beams])
        var_size = struct.calcsize(var_format)
        var_sn   = self.data_short_names[var_name]
        count    = 0

        # parse data for each depth cell 
        for cell in range(0, num_cells):
            cell_start = offset + cell*num_beams*var_size

            # parse data for each beam for a given depth cell 
            for beam in range(0, num_beams):
                beam_start = cell_start + beam*var_size
                beam_data  = struct.unpack_from(var_format, 
                                                pd0_bytes, 
                                                beam_start)[0]

                # compute labels and array index 
                label  = var_sn + '_cell%d_beam%d' % (cell+1,beam+1)
                index  = self.data_type_offsets[var_name] + count
                count += 1

                # filter out bad velocities and adjust units if necessary
                if var_name == 'velocity':
                    if beam_data == self.bad_velocity: 
                        value = np.NaN
                    else: 
                        value = beam_data / 1000  # [mm/s] -> [m/s]
                else:
                    value = beam_data             # others keep their units 

                # store information in arrays and dict 
                self.data_array[index]  = value 
                self.data_lookup[label] = index
                self.label_list.append(label)


    def parse_header(self, pd0_bytes):
        """Parses the header portion of the pd0 file. 

        The pd0 header format is defined in the Pathfinder Manual on pg 172.
        The header size is: 6 + [2 * num_data_types] bytes. Stores header 
        information as attributes of the Ensemble class.

        Args:
            pd0_bytes: bytes fro the PD0 file to be parsed as the header.

        Raises: 
            ValueError if header id is incorrect.
        """
        header_format = (
            ('id',              'B',    0),
            ('data_source',     'B',    1),
            ('num_bytes',       '<H',   2),
            ('spare',           'B',    4),
            ('num_data_types',  'B',    5),
        )
        header_flag = 0x7f
        header_dict = self.unpack_bytes(pd0_bytes, header_format)

        # check that header has the correct ID
        if (header_dict['id']          != header_flag or 
            header_dict['data_source'] != header_flag):
            raise ValueError('Incorrect Header ID \
                \n  received: %s %s \n  expected: %s %s' % 
                (header_dict['id'], header_dict['data_source'], 
                 header_flag,       header_flag))

        # if header has correct ID, store the remaining header values 
        self.header_id          = header_dict['id']
        self.header_data_source = header_dict['data_source']
        self.num_data_types     = header_dict['num_data_types']
        self.num_bytes          = header_dict['num_bytes']

        # parse the address offsets given 
        address_start   = 6 # number of header bytes before address offsets
        address_format  = '<H'
        address_size    = struct.calcsize(address_format)
        address_end     = address_start + self.num_data_types*address_size
        address_offsets = []

        # parse the address offset for each data type 
        for start in range(address_start, address_end, address_size):
            address = struct.unpack_from(address_format, pd0_bytes, start)[0]
            address_offsets.append(address)
        self.address_offsets = address_offsets

        # determine the byte sizes of each variable type
        sizes = self.address_offsets.copy()
        sizes.insert(0,0)
        sizes.append(self.num_bytes)
        self.var_byte_sizes = \
            [sizes[i+1] - sizes[i] for i in range(len(sizes)-1)]


    def parse_fixed_leader(self, pd0_bytes, name, offset):
        """Parses the fixed leader data type of the pd0 file.

        The pd0 fixed leader format is in the Pathfinder Manual on pg 174.
        The fixed leader size is: 58 bytes.

        Args:
            pd0_bytes: pd0 bytes to be parsed into the fixed leader data type.
            name: the name of the data type (name = 'fixed_leader')
            offset: byte offset to start parsing the fixed leader. 
        """
        fixed_leader_format = (
            ('id',                          '<H',    0),
            ('cpu_firmware_version',        'B',     2),
            ('cpu_firmware_revision',       'B',     3),
            ('system_configuration',        '<H',    4),
            ('simulation_flag',             'B',     6),
            ('lag_length',                  'B',     7),
            ('num_velocity_beams',          'B',     8),
            ('num_cells',                   'B',     9),
            ('pings_per_ensemble',          '<H',   10),
            ('depth_cell_length',           '<H',   12),    # [cm]
            ('blank_after_transmit',        '<H',   14),    # [cm]
            ('profiling_mode',              'B',    16),
            ('low_correlation_threshold',   'B',    17),
            ('num_code_repetitions',        'B',    18),
            ('percent_good_minimum',        'B',    19),
            ('error_velocity_threshold',    '<H',   20),    # [mm/s]
            ('minutes',                     'B',    22),
            ('seconds',                     'B',    23),
            ('hundredths',                  'B',    24),
            ('coordinate_transformation',   'B',    25),
            ('heading_alignment',           '<h',   26),    # [0.01 deg]
            ('heading_bias',                '<h',   28),    # [0.01 deg]
            ('sensor_source',               'B',    30),
            ('sensor_available',            'B',    31),
            ('bin_1_distance',              '<H',   32),    # [cm]
            ('transmit_pulse_length',       '<H',   34),    # [cm]
            ('starting_depth_cell',         'B',    36),
            ('ending_depth_cell',           'B',    37),
            ('false_target_threshold',      'B',    38),
            ('transmit_lag_distance',       '<H',   40),    # [cm]
            ('system_bandwidth',            '<H',   50),
            ('system_serial_number',        '<I',   54),
        )
        fixed_leader = self.unpack_bytes(pd0_bytes,fixed_leader_format,offset)
        
        # fixed leader values are constant throughout the DVL time-series so 
        # store values as attributes instead of the ensemble
        for key in fixed_leader:
            if key != 'id':
                setattr(self, key, fixed_leader[key])

        # convert units to standard metric values 
        self.depth_cell_length        /= 100  # [cm]       -> [m]
        self.blank_after_transmit     /= 100  # [cm]       -> [m]
        self.error_velocity_threshold /= 1000 # [mm/s]     -> [m/s]
        self.heading_alignment        /= 100  # [0.01 deg] -> [deg]
        self.heading_bias             /= 100  # [0.01 deg] -> [deg]
        self.bin_1_distance           /= 100  # [cm]       -> [m]
        self.transmit_pulse_length    /= 100  # [cm]       -> [m]
        self.transmit_lag_distance    /= 100  # [cm]       -> [m]

        # compute expected sizes of each data type 
        #   + according to the Pathfinder manual pg 171
        #   + compare this against self.var_byte_sizes
        self.var_byte_sizes_expected = [
            6 + 2*self.num_data_types,          # header
            58,                                 # fixed leader
            77,                                 # variable leader
            2+2*self.num_beams*self.num_cells,  # velocity 
            2 + self.num_beams*self.num_cells,  # correlation
            2 + self.num_beams*self.num_cells,  # echo intensity
            2 + self.num_beams*self.num_cells,  # percent good,
            81                                  # bottom track
        ]            

        # compute size of data types 
        #   + variable leader and bottom track types are of fixed size
        beam_size = self.num_beams*self.num_cells
        self._data_type_sizes = (
            ('time',                    1),
          # ('derived',                 X), TODO
            ('variable_leader',        26),
            ('velocity',        beam_size),
            ('correlation',     beam_size),
            ('echo_intensity',  beam_size),
            ('percent_good',    beam_size),
            ('bottom_track',           54)
        )

        # initialize an empty ensemble array 
        self._ensemble_size     = sum([var[1] for var in self.data_type_sizes])
        self._data_type_offsets = {self.data_type_sizes[0][0] : 0}
        self._data_array        = np.empty(self.ensemble_size)
        self.data_lookup        = {}
        self.label_list         = ['time']

        # compute list of array offsets for filling ensemble array
        for i in range(1,len(self.data_type_sizes)):
            name        = self.data_type_sizes[i][0]
            prev_offset = self.data_type_offsets[self.data_type_sizes[i-1][0]]
            prev_size   = self.data_type_sizes[i-1][1]
            self._data_type_offsets[name] = prev_offset + prev_size
        

    def parse_variable_leader(self, pd0_bytes, name, offset):
        """Parses the variable leader data type of the pd0 file.

        The pd0 variable leader format is in the Pathfinder Manual on pg 180.
        The variable leader size is: 77 bytes.

        Args:
            pd0_bytes: pd0 bytes to be parsed into the variable leader type.
            name: the name of the data type (name = 'variable_leader')
            offset: byte offset to start parsing the variable leader 
        """
        variable_leader_format = (
            ('id',                          '<H',    0),
            ('ensemble_number',             '<H',    2),
            ('rtc_year',                    'B',     4),
            ('rtc_month',                   'B',     5),
            ('rtc_day',                     'B',     6),
            ('rtc_hour',                    'B',     7),
            ('rtc_minute',                  'B',     8),
            ('rtc_second',                  'B',     9),
            ('rtc_hundredths',              'B',    10),
            ('ensemble_roll_over',          'B',    11),
            ('bit_result',                  '<H',   12),
            ('speed_of_sound',              '<H',   14),    # [m/s]
            ('depth_of_transducer',         '<H',   16),    # [dm]
            ('heading',                     '<H',   18),    # [0.01 deg]
            ('pitch',                       '<h',   20),    # [0.01 deg]
            ('roll',                        '<h',   22),    # [0.01 deg]
            ('salinity',                    '<H',   24),    # [ppt]
            ('temperature',                 '<h',   26),    # [0.01 C]
            ('min_ping_wait_minutes',       'B',    28),
            ('min_ping_wait_seconds',       'B',    29),
            ('min_ping_wait_hundredths',    'B',    30),
            ('heading_standard_deviation',  'B',    31),
            ('pitch_standard_deviation',    'B',    32),    # [0.1 deg]
            ('roll_standard_deviation',     'B',    33),    # [0.1 deg]
            ('adc_rounded_voltage',         'B',    35),
            ('pressure',                    '<I',   48),    # [daPa]
            ('pressure_variance',           '<I',   52),    # [daPa]
            # # these bytes are currently not being included in the pd0 file, 
            # # see 'self.var_byte_sizes' and 'self.var_byte_sizes_expected'
            # ('health_status',               'B',    66),
            # ('leak_a_count',                '<H',   67),
            # ('leak_b_count',                '<H',   69),
            # ('transducer_voltage',          '<H',   71),    # [0.001 Volts]
            # ('transducer_current',          '<H',   73),    # [0.001 Amps]
            # ('transducer_impedance',        '<H',   75),    # [0.001 Ohms]
        )
        variable_leader = self.unpack_bytes(pd0_bytes, 
                                            variable_leader_format, 
                                            offset)
        
        # store parsed values in the data array 
        for i in range(1,len(variable_leader_format)):

            # compute array index (subtract 1 because we do not include id)
            label       = variable_leader_format[i][0]
            value       = variable_leader[label]
            array_index = i - 1 + self.data_type_offsets[name]

            # store information in arrays and dict 
            self.data_array[array_index]  = value 
            self.data_lookup[label]       = array_index
            self.label_list.append(label)

        # convert units to standard SI units 
        scale_vars = (
            ('depth_of_transducer',         10),    # [dm]      -> [m]
            ('heading',                     100),   # [0.01 deg -> [deg]
            ('pitch',                       100),   # [0.01 deg -> [deg]
            ('roll',                        100),   # [0.01 deg -> [deg]
            ('temperature',                 100),   # [0.01 C]  -> [C]
            ('pitch_standard_deviation',    10),    # [0.1 deg] -> [deg]
            ('roll_standard_deviation',     10),    # [0.1 deg] -> [deg]
            ('pressure',                    0.1),   # [daPa]    -> [Pa]
            ('pressure_variance',           0.1)    # [daPa]    -> [Pa]
        )

        for (var, scale) in scale_vars:
            self.data_array[self.data_lookup[var]] /= scale

        # collect all time information into a single datetime object 
        rtc_millenium = 2000 
        timestamp = datetime(
            variable_leader['rtc_year'] + rtc_millenium,
            variable_leader['rtc_month'],
            variable_leader['rtc_day'],
            variable_leader['rtc_hour'],
            variable_leader['rtc_minute'],
            variable_leader['rtc_second'],
            variable_leader['rtc_hundredths']).timestamp()

        # first slot in the array is reserved for timestamp 
        self.data_array[0] = timestamp


    def parse_water_profiling_data(self, pd0_bytes, name, offset):
        """Parses the water profiling data type of the pd0 file.

        The water profiling format is in the Pathfinder Manual on pg 188 & 190.
        The velocity size is: 2 + [2 * num_beams * num_cells] bytes.
        The other profiling sizes are: 2 + [num_beams * num_cells] bytes.

        Velocity:       [mm/s]
        Correlation:    [0, 255]
        Echo Intensity: [0.61 dB per count]
        Percent Good:   [0, 100]

        Args:
            pd0_bytes: pd0 bytes to be parsed into the water profiling type.
            name: the name of the data type 
            offset: byte offset to start parsing the water profiling 
        """
        id_byte_length   = 2
        if name == 'velocity': profiling_format = '<h'
        else:                  profiling_format = 'B'
        offset  += id_byte_length
        profile  = self.parse_beams(pd0_bytes, offset, self.num_cells,
                                    self.num_beams, profiling_format, name)


    def parse_bottom_track(self, pd0_bytes, name, offset):
        """Parses the bottom track data type of the pd0 file.

        The pd0 bottom track format is in the Pathfinder Manual on pg 194.
        The bottom track size is: 81 bytes.

        Args:
            pd0_bytes: pd0 bytes to be parsed into the bottom track type.
            name: the name of the data type (name = 'bottom_track')
            offset: byte offset to start parsing the bottom track 
        """
        bottom_track_format = (
            ('id',                              '<H',    0),
            ('pings_per_ensemble',              '<H',    2),        
            ('min_correlation_mag',             'B',     6),
            ('min_echo_intensity_amp',          'B',     7),
            ('bottom_track_mode',               'B',     9),
            ('max_error_velocity',              '<H',   10),    # [mm/s]
            ('beam1_range',                     '<H',   16),    # [cm]
            ('beam2_range',                     '<H',   18),    # [cm]
            ('beam3_range',                     '<H',   20),    # [cm]
            ('beam4_range',                     '<H',   22),    # [cm]
            ('beam1_velocity',                  '<h',   24),    # [mm/s]
            ('beam2_velocity',                  '<h',   26),    # [mm/s]
            ('beam3_velocity',                  '<h',   28),    # [mm/s]
            ('beam4_velocity',                  '<h',   30),    # [mm/s]
            ('beam1_correlation',               'B',    32),
            ('beam2_correlation',               'B',    33),
            ('beam3_correlation',               'B',    34),
            ('beam4_correlation',               'B',    35),        
            ('beam1_echo_intensity',            'B',    36),
            ('beam2_echo_intensity',            'B',    37),
            ('beam3_echo_intensity',            'B',    38),
            ('beam4_echo_intensity',            'B',    39),
            ('beam1_percent_good',              'B',    40),
            ('beam2_percent_good',              'B',    41),
            ('beam3_percent_good',              'B',    42),
            ('beam4_percent_good',              'B',    43),
            ('ref_layer_min',                   '<H',   44),    # [dm]
            ('ref_layer_near',                  '<H',   46),    # [dm]
            ('ref_layer_far',                   '<H',   48),    # [dm]
            ('beam1_ref_layer_velocity',        '<h',   50),    # [mm/s]
            ('beam2_ref_layer_velocity',        '<h',   52),    # [mm/s]
            ('beam3_ref_layer_velocity',        '<h',   54),    # [mm/s]
            ('beam4_ref_layer_velocity',        '<h',   56),    # [mm/s]
            ('beam1_ref_layer_correlation',     'B',    58),
            ('beam2_ref_layer_correlation',     'B',    59),
            ('beam3_ref_layer_correlation',     'B',    60),
            ('beam4_ref_layer_correlation',     'B',    61),
            ('beam1_ref_layer_echo_intensity',  'B',    62),
            ('beam2_ref_layer_echo_intensity',  'B',    63),
            ('beam3_ref_layer_echo_intensity',  'B',    64),
            ('beam4_ref_layer_echo_intensity',  'B',    65),
            ('beam1_ref_layer_percent_good',    'B',    66),
            ('beam2_ref_layer_percent_good',    'B',    67),
            ('beam3_ref_layer_percent_good',    'B',    68),
            ('beam4_ref_layer_percent_good',    'B',    69),
            ('max_tracking_depth',              '<H',   70),    # [dm]
            ('beam1_rssi',                      'B',    72),
            ('beam2_rssi',                      'B',    73),
            ('beam3_rssi',                      'B',    74),
            ('beam4_rssi',                      'B',    75),
            ('shallow_water_gain',              'B',    76),
            ('beam1_msb',                       'B',    77),    # [cm]
            ('beam2_msb',                       'B',    78),    # [cm]
            ('beam3_msb',                       'B',    79),    # [cm]
            ('beam4_msb',                       'B',    80),    # [cm]
            )

        bottom_track = self.unpack_bytes(pd0_bytes,bottom_track_format,offset)
        var_sn = self.data_short_names[name]

        # store parsed values in the data array 
        for i in range(1,len(bottom_track_format)):

            # compute array index (subtract 1 because we do not include id)
            label       = bottom_track_format[i][0]
            value       = bottom_track[label]
            array_index = i - 1 + self.data_type_offsets[name]

            # store information in arrays and dict 
            var_fn = var_sn + '_' + label
            self.data_array[array_index]  = value 
            self.data_lookup[var_fn]  = array_index
            self.label_list.append(var_fn)

        # replace bad velocity values with np.NaN
        velocity_vars = [var_sn + '_beam1_velocity', 
                         var_sn + '_beam2_velocity',
                         var_sn + '_beam3_velocity',
                         var_sn + '_beam4_velocity',
                         var_sn + '_beam1_ref_layer_velocity',
                         var_sn + '_beam2_ref_layer_velocity',
                         var_sn + '_beam3_ref_layer_velocity',
                         var_sn + '_beam4_ref_layer_velocity']
                         
        # filter out bad velocity values 
        for var in velocity_vars:
            if self.data_array[self.data_lookup[var]] == self.bad_velocity:
                self.data_array[self.data_lookup[var]] = np.NaN

        # replace bad range values  with np.NaN
        range_vars = [var_sn + '_beam1_range',
                      var_sn + '_beam2_range',
                      var_sn + '_beam3_range',
                      var_sn + '_beam4_range']
        # filter out bad range values 
        for var in range_vars:
            if self.data_array[self.data_lookup[var]] == self.bad_bt_range:
                self.data_array[self.data_lookup[var]] = np.NaN
        
        # convert units to standard SI units 
        scale_vars = (
            (var_sn + '_ref_layer_min',            10),   # [dm]   -> [m]
            (var_sn + '_ref_layer_near',           10),   # [dm]   -> [m]
            (var_sn + '_ref_layer_far',            10),   # [dm]   -> [m]
            (var_sn + '_max_tracking_depth',       10),   # [dm]   -> [m]
            (var_sn + '_beam1_range',              100),  # [cm]   -> [m]
            (var_sn + '_beam2_range',              100),  # [cm]   -> [m]
            (var_sn + '_beam3_range',              100),  # [cm]   -> [m]
            (var_sn + '_beam4_range',              100),  # [cm]   -> [m]
            (var_sn + '_beam1_msb',                100),  # [cm]   -> [m]
            (var_sn + '_beam2_msb',                100),  # [cm]   -> [m]
            (var_sn + '_beam3_msb',                100),  # [cm]   -> [m]
            (var_sn + '_beam4_msb',                100),  # [cm]   -> [m]
            (var_sn + '_beam1_velocity',           1000), # [mm/s] -> [m/s]
            (var_sn + '_beam2_velocity',           1000), # [mm/s] -> [m/s]
            (var_sn + '_beam3_velocity',           1000), # [mm/s] -> [m/s]
            (var_sn + '_beam4_velocity',           1000), # [mm/s] -> [m/s]
            (var_sn + '_max_error_velocity',       1000), # [mm/s] -> [m/s]
            (var_sn + '_beam1_ref_layer_velocity', 1000), # [mm/s] -> [m/s]
            (var_sn + '_beam2_ref_layer_velocity', 1000), # [mm/s] -> [m/s]
            (var_sn + '_beam3_ref_layer_velocity', 1000), # [mm/s] -> [m/s]
            (var_sn + '_beam4_ref_layer_velocity', 1000), # [mm/s] -> [m/s]
        )

        # scale values in the data array accordingly 
        for (var, scale) in scale_vars:
            self.data_array[self.data_lookup[var]] /= scale

