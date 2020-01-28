# Ensemble.py
#
# Represents a Doppler Velocity Log ensemble. 
# Adapted from pd0_parser.py, written by Dave Pingal (dpingal@teledyne.com).
#   2018-11-26  dpingal@teledyne.com    implemented pd0_parser.py
#   2020-01-27  zduguid@mit.edu         implemented Ensemble.py

import json
import sys
import struct
import pandas as pd
from   ChecksumError import ChecksumError
from   datetime      import datetime


class Ensemble(object):
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
            ChecksumError if an invalid checksum is found.
        """
        # maps byte id with particular data types and data parsers
        self._data_format_ids = {
            0x0000: ('fixed_leader',    self.parse_fixed_leader),
            0x0080: ('variable_leader', self.parse_variable_leader),
            0x0100: ('velocity',        self.parse_velocity),
            0x0200: ('correlation',     self.parse_water_profiling_data),
            0x0300: ('echo_intensity',  self.parse_water_profiling_data),
            0x0400: ('percent_good',    self.parse_water_profiling_data),
            0x0600: ('bottom_track',    self.parse_bottom_track),
        }
        self._data = self.parse_ensemble(pd0_bytes)


    @property
    def data(self):
        # type: () -> dict
        return(self._data)


    @property
    def data_format_ids(self):
        # type: () -> dict
        return(self._data_format_ids)


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

        Returns:
            Dictionary of Ensemble data. 
        """
        data = {}
        data['header'] = self.parse_header(pd0_bytes)
        self.validate_checksum(pd0_bytes, data['header']['num_bytes'])
        
        # parse each data type 
        for offset in data['header']['address_offsets']:
            header_id = struct.unpack_from('H', pd0_bytes, offset)[0]
            if header_id in self.data_format_ids:
                key       = self.data_format_ids[header_id][0]
                parser    = self.data_format_ids[header_id][1]
                data[key] = parser(pd0_bytes, offset, data)
            else:
                print('Warning: no parser found for header %d' % (header_id,))
        return(data)


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


    def validate_checksum(self, pd0_bytes, offset):
        """Validates the checksum for the ensemble.
        """
        calc_checksum  = sum([c for c in pd0_bytes[:offset]]) & 0xFFFF
        given_checksum = struct.unpack_from('<H', pd0_bytes, offset)[0]
        if calc_checksum != given_checksum:
            raise ChecksumError(calc_checksum, given_checksum)


    def parse_beams(self, pd0_bytes, offset, num_cells, num_beams, var_format):
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

        Returns: 
            List of lists where data[i][j] is the value at the i-th depth bin 
            for the j-th beam.
        """
        data = []
        var_size = struct.calcsize(var_format)

        # parse data for each depth cell 
        for cell in range(0, num_cells):
            cell_start = offset + cell*num_beams*var_size
            cell_data  = []

            # parse data for each beam for a given depth cell 
            for beam in range(0, num_beams):
                beam_start = cell_start + beam*var_size
                beam_data  = struct.unpack_from(var_format, 
                                                pd0_bytes, 
                                                beam_start)[0]
                cell_data.append(beam_data)
            data.append(cell_data)

        return(data)


    def parse_header(self, pd0_bytes):
        """Parses the header portion of the pd0 file. 

        The pd0 header format is defined in the Pathfinder Manual on pg 172.
        The header size is: 6 + [2 * num_data_types] bytes.

        Args:
            pd0_bytes: bytes fro the PD0 file to be parsed as the header.

        Returns:
            Dictionary of header data field names and corresponding values. 

        Raises: 
            ValueError if header id is incorrect.
        """
        header_format = (
            ('id',                              'B',     0),
            ('data_source',                     'B',     1),
            ('num_bytes',                       '<H',    2),
            ('spare',                           'B',     4),
            ('num_data_types',                  'B',     5),
        )
        header_id       = 0x7f
        header_data     = self.unpack_bytes(pd0_bytes, header_format)
        num_data_types  = header_data['num_data_types']
        address_format  = '<H'
        address_size    = 2
        address_start   = 6
        address_end     = address_start + num_data_types*address_size
        address_list    = []

        # check that header has the correct ID
        if (header_data['id']          != header_id or 
            header_data['data_source'] != header_id):
            raise ValueError('Incorrect Header ID \
                \n  received: %s %s \n  expected: %s %s' % 
                (header_data['id'], header_data['data_source'], 
                 header_id,         header_id))

        # parse the address offset for each data type 
        for start in range(address_start, address_end, address_size):
            address = struct.unpack_from(address_format, pd0_bytes, start)[0]
            address_list.append(address)

        header_data['address_offsets'] = address_list
        return(header_data)


    def parse_fixed_leader(self, pd0_bytes, offset, data):
        """Parses the fixed leader data type of the pd0 file.

        The pd0 fixed leader format is in the Pathfinder Manual on pg 174.
        The fixed leader size is: 58 bytes.

        Args:
            pd0_bytes: pd0 bytes to be parsed into the fixed leader data type.
            offset: byte offset to start parsing the fixed leader. 
            data: dictionary object storing ensemble information.
        """
        fixed_leader_format = (
            ('id',                          '<H',    0),
            ('cpu_firmware_version',        'B',     2),
            ('cpu_firmware_revision',       'B',     3),
            ('system_configuration',        '<H',    4),
            ('simulation_flag',             'B',     6),
            ('lag_length',                  'B',     7),
            ('num_beams',                   'B',     8),
            ('num_cells',                   'B',     9),
            ('pings_per_ensemble',          '<H',   10),
            ('depth_cell_length',           '<H',   12),    # [cm]
            ('blank_after_transmit',        '<H',   14),    # [cm]
            ('profiling_mode',              'B',    16),
            ('low_correlation_threshold',   'B',    17),
            ('num_code_repetitions',        'B',    18),
            ('percent_good_minimum',        'B',    19),    # [%]
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
        return(self.unpack_bytes(pd0_bytes, fixed_leader_format, offset))


    def parse_variable_leader(self, pd0_bytes, offset, data):
        """Parses the variable leader data type of the pd0 file.

        The pd0 variable leader format is in the Pathfinder Manual on pg 180.
        The variable leader size is: 77 bytes.

        Args:
            pd0_bytes: pd0 bytes to be parsed into the variable leader type.
            offset: byte offset to start parsing the variable leader 
            data: dictionary object storing ensemble information.
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
            ('temperature',                 '<h',   26),    # [0.01 deg]
            ('min_ping_wait_minutes',       'B',    28),
            ('min_ping_wait_seconds',       'B',    29),
            ('min_ping_wait_hundredths',    'B',    30),
            ('heading_standard_deviation',  'B',    31),
            ('pitch_standard_deviation',    'B',    32),    # [0.1 deg]
            ('roll_standard_deviation',     'B',    33),    # [0.1 deg]
            ('adc_rounded_voltage',         'B',    35),
            ('pressure',                    '<I',   48),    # [daPa]
            ('pressure_variance',           '<I',   52),    # [daPa]
            ('health_status',               'B',    66),
            ('leak_a_count',                '<H',   67),
            ('leak_b_count',                '<H',   69),
            ('transducer_voltage',          '<H',   71),    # [0.001 Volts]
            ('transducer_current',          '<H',   73),    # [0.001 Amps]
            ('transducer_impedance',        '<H',   75),    # [0.001 Ohms]
        )
        rtc_millenium = 2000
        variable_data = self.unpack_bytes(pd0_bytes, variable_leader_format, 
                                          offset)

        # collect all time information into a single datetime object 
        data['timestamp'] = datetime(
            variable_data['rtc_year'] + rtc_millenium,
            variable_data['rtc_month'],
            variable_data['rtc_day'],
            variable_data['rtc_hour'],
            variable_data['rtc_minute'],
            variable_data['rtc_second'],
            variable_data['rtc_hundredths']
        )
        return(variable_data)


    def parse_velocity(self, pd0_bytes, offset, data):
        """Parses the velocity data type of the pd0 file.

        The pd0 velocity format is in the Pathfinder Manual on pg 188.
        The velocity size is: 2 + [2 * num_bins * num_cells] bytes.
        Units of velocity: [mm/s]
        Bad velocity flag: -32768

        Args:
            pd0_bytes: pd0 bytes to be parsed into the velocity type.
            offset: byte offset to start parsing the velocity 
            data: dictionary object storing ensemble information.
        """
        id_byte_length        = 2
        velocity_format       = (('id', '<H', 0),)
        velocity_byte_size    = '<h'
        velocity_data         = self.unpack_bytes(pd0_bytes, velocity_format,
                                                  offset)
        offset               += id_byte_length
        velocity_data['data'] = self.parse_beams(
            pd0_bytes,
            offset,
            data['fixed_leader']['num_cells'],
            data['fixed_leader']['num_beams'],
            velocity_byte_size
        )

        return(velocity_data)


    def parse_water_profiling_data(self, pd0_bytes, offset, data):
        """Parses the water profiling data type of the pd0 file.

        The pd0 water profiling format is in the Pathfinder Manual on pg 190.
        The water profiling size is: 2 + [num_bins * num_cells] bytes.

        Correlation:    [0,255]
        Echo Intensity: [0.61 dB per count]
        Percent Good:   [0, 100]

        Args:
            pd0_bytes: pd0 bytes to be parsed into the water profiling type.
            offset: byte offset to start parsing the water profiling 
            data: dictionary object storing ensemble information.
        """
        id_byte_length         = 2
        profiling_format       = (('id', '<H', 0),)
        profiling_byte_size    = 'B'
        profiling_data         = self.unpack_bytes(pd0_bytes, 
                                                   profiling_format, 
                                                   offset)
        offset                += id_byte_length
        profiling_data['data'] = self.parse_beams(
            pd0_bytes,
            offset,
            data['fixed_leader']['num_cells'],
            data['fixed_leader']['num_beams'],
            profiling_byte_size
        )
        return(profiling_data)


    def parse_bottom_track(self, pd0_bytes, offset, data):
        """Parses the bottom track data type of the pd0 file.

        The pd0 bottom track format is in the Pathfinder Manual on pg 194.
        The bottom track size is: 81 bytes.

        Args:
            pd0_bytes: pd0 bytes to be parsed into the bottom track type.
            offset: byte offset to start parsing the bottom track 
            data: dictionary object storing ensemble information.
        """

        bottom_track_format = (
            ('id',                              '<H',    0),
            ('pings_per_ensemble',              '<H',    2),        
            ('min_correlation_mag',             'B',     6),
            ('min_evaluation_amp',              'B',     7),
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
            ('beam1_evaluation_amp',            'B',    36),
            ('beam2_evaluation_amp',            'B',    37),
            ('beam3_evaluation_amp',            'B',    38),
            ('beam4_evaluation_amp',            'B',    39),
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
            ('beam1_most_significant_byte',     'B',    77),    # [cm]
            ('beam2_most_significant_byte',     'B',    78),    # [cm]
            ('beam3_most_significant_byte',     'B',    79),    # [cm]
            ('beam4_most_significant_byte',     'B',    80),    # [cm]
            )
        return(self.unpack_bytes(pd0_bytes, bottom_track_format, offset))


