# PathfinderEnsemble.py
#
# Represents a Doppler Velocity Log ensemble. 
# Adapted from pd0_parser.py, written by Dave Pingal (dpingal@teledyne.com).
#   2018-11-26  dpingal@teledyne.com    implemented pd0_parser.py
#   2020-01-27  zduguid@mit.edu         implemented PathfinderEnsemble.py
#   2020-05-05  zduguid@mit.edu         reorganized code with DVL superclass 

import numpy as np 
import pandas as pd
import struct
import sys
from datetime import datetime
from PathfinderDVL import PathfinderDVL
from PathfinderChecksumError import PathfinderChecksumError


class PathfinderEnsemble(PathfinderDVL):
    def __init__(self, pd0_bytes, prev_ensemble=None, gps_fix=None):
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
            prev_ensemble: previously collected PathfinderEnsemble. The 
                previous ensemble is used for deducing Pathfinder 
            gps_fix: (x,y) GPS location, used to update the position of the  
                relative frame. As a result, every dive (both start of mission
                and every subsequent surfacing) will have a different relative
                frame of reference.

        Returns:
            A new Ensemble that has been parsed from the given pd0 bytes, or 
            None if there was an error while parsing.

        Raises:
            ValueError if header id is incorrect.
            PathfinderChecksumError if an invalid checksum is found.
        """
        # use the parent constructor for defining Pathfinder DVL variables
        super().__init__()

        # initialize Micron Ensemble data array based on number of variables
        self._data_array = np.zeros(self.ensemble_size)

        # store the previous ensemble and GPS fix information
        self._prev_ensemble = prev_ensemble
        self._gps_fix = gps_fix

        # map from byte id to parsing function 
        self._data_id_parsers = {
            0x0000: ('fixed_leader',    self.parse_fixed_leader),
            0x0080: ('variable_leader', self.parse_variable_leader),
            0x0100: ('velocity',        self.parse_water_profiling_data),
            0x0200: ('correlation',     self.parse_water_profiling_data),
            0x0300: ('echo_intensity',  self.parse_water_profiling_data),
            0x0400: ('percent_good',    self.parse_water_profiling_data),
            0x0600: ('bottom_track',    self.parse_bottom_track),
        }

        # parse array given pd0 bytes
        self.parse_ensemble(pd0_bytes)


    @property
    def data_array(self):
        return self._data_array

    @property
    def prev_ensemble(self):
        return self._prev_ensemble

    @property
    def gps_fix(self):
        return self._gps_fix
  
    @property
    def data_id_parsers(self):
        return self._data_id_parsers
    
    @property
    def data_type_offsets(self):
        return self._data_type_offsets

    @property
    def address_offsets(self):
        return self._address_offsets
    
    @property
    def var_byte_sizes(self):
        return self._var_byte_sizes


    def get_data(self, var):
        """Getter method for a give variable in the data array"""
        if (var not in self.label_set):
            raise ValueError("bad variable for: get(%s)" % (var))
        else:
            return self.data_array[self.data_lookup[var]]


    def set_data(self, var, val, attribute=True):
        """Setter method for a variable-value pair to be put in the array"""
        if (var not in self.label_set):
            raise ValueError("bad variable for: set(%s, %s)" % (var, str(val)))
        self._data_array[self.data_lookup[var]] = val 
        if attribute: setattr(self, var, val)    


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
        # constant used for unpacking bytes
        HEADER_ID = 'H' 

        # parse header to confirm header ID and validate checksum
        self.parse_header(pd0_bytes)
        self.validate_checksum(pd0_bytes)

        # parse each data type 
        for address in self.address_offsets:
            header_id = struct.unpack_from(HEADER_ID, pd0_bytes, address)[0]
            if header_id in self.data_id_parsers:
                name      = self.data_id_parsers[header_id][0]
                parser    = self.data_id_parsers[header_id][1]
                data_dict = parser(pd0_bytes, name, address)
            else:
                print('  WARNING: no parser found for header %d' %(header_id,))

        # parse derived variables 
        self.parse_derived_variables()


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
        HEADER_FLAG    = 0x7f    # flag to indicate start of header
        HEADER_BYTES   = 6       # number of bytes before address offsets
        ADDRESS_FORMAT = '<H'    # format string of the header addresses

        # unpack the header bytes from the byte array
        header_dict = self.unpack_bytes(pd0_bytes, self.header_format)

        # check that header has the correct ID
        if (header_dict['id']          != HEADER_FLAG or 
            header_dict['data_source'] != HEADER_FLAG):
            raise ValueError('Incorrect Header ID \
                \n  received: %s %s \n  expected: %s %s' % 
                (header_dict['id'], header_dict['data_source'], 
                 HEADER_FLAG, HEADER_FLAG))

        # if header has correct ID, store the remaining header values 
        self.header_id          = header_dict['id']
        self.header_data_source = header_dict['data_source']
        self.num_data_types     = header_dict['num_data_types']
        self.num_bytes          = header_dict['num_bytes']

        # parse the address offsets given 
        address_size    = struct.calcsize(ADDRESS_FORMAT)
        address_end     = HEADER_BYTES + self.num_data_types*address_size
        address_offsets = []

        # parse the address offset for each data type 
        for start in range(HEADER_BYTES, address_end, address_size):
            address = struct.unpack_from(ADDRESS_FORMAT, pd0_bytes, start)[0]
            address_offsets.append(address)
        self._address_offsets = address_offsets

        # determine the byte sizes of each variable type
        sizes = self.address_offsets.copy()
        sizes.insert(0,0)
        sizes.append(self.num_bytes)
        self._var_byte_sizes = \
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
        fixed_leader = self.unpack_bytes(pd0_bytes,
                                         self.fixed_leader_format,
                                         offset)

        # add relevant fixed leader values to the data array
        for key in fixed_leader:
            if key in self.label_set:
                self.set_data(key, fixed_leader[key])

        # convert relevant fields to standard metric quantities
        self.convert_to_metric('depth_bin_length',        self.CM_TO_M)
        self.convert_to_metric('blanking_distance',       self.CM_TO_M)
        self.convert_to_metric('error_velocity_threshold',self.MM_TO_M)
        self.convert_to_metric('heading_alignment',       self.HUNDRETH_TO_DEG)
        self.convert_to_metric('heading_bias',            self.HUNDRETH_TO_DEG)
        self.convert_to_metric('bin0_distance',           self.CM_TO_M)
        self.convert_to_metric('transmit_pulse_length',   self.CM_TO_M)

        # raise error if received too many bins 
        #   + expect 40 bins exactly 
        #   + this is performed to make array processing more efficient 
        if self.num_bins != self.NUM_BINS_EXP:
            raise ValueError('Too many bins: expected = %s, actual = %s'
                             % (self.NUM_BINS_EXP, self.num_bins))

        # raise error if incorrect number of beams 
        #   + expect exactly four beams for the Pathfinder DVL 
        if self.num_beams != self.NUM_BEAMS_EXP:
            raise ValueError('Incorrect # beams: expected = %s, actual = %s'
                             % (self.NUM_BEAMS_EXP, self.num_beams))

        # compute expected sizes of each data type for diagnostic purposes
        #   + according to the Pathfinder manual pg 171
        #   + compare this against self.var_byte_sizes
        self.var_byte_sizes_expected = [
            6 + 2*self.num_data_types,          # header
            58,                                 # fixed leader
            77,                                 # variable leader
            2+2*self.num_beams*self.num_bins,   # velocity 
            2 + self.num_beams*self.num_bins,   # correlation
            2 + self.num_beams*self.num_bins,   # echo intensity
            2 + self.num_beams*self.num_bins,   # percent good,
            81                                  # bottom track
        ]            


    def parse_variable_leader(self, pd0_bytes, name, offset):
        """Parses the variable leader data type of the pd0 file.

        The pd0 variable leader format is in the Pathfinder Manual on pg 180.
        The variable leader size is: 77 bytes.

        Args:
            pd0_bytes: pd0 bytes to be parsed into the variable leader type.
            name: the name of the data type (name = 'variable_leader')
            offset: byte offset to start parsing the variable leader 
        """
        # assumes data collected in the 2000's (not recorded by DVL)
        RTC_MILLENIUM = 2000 
        variable_leader = self.unpack_bytes(pd0_bytes, 
                                            self.variable_leader_format, 
                                            offset)
        
        # add relevant variable leader values to the data array
        for key in variable_leader:
            if key in self.label_set:
                self.set_data(key, variable_leader[key])

        # compute ensemble number while accounting for ensemble roll over 
        self.set_data('ensemble_number', variable_leader['ensemble_number'] + \
                        self.MAX_ENS_NUM*variable_leader['ensemble_rollover'])

        # convert data to metric values when applicable 
        self.convert_to_metric('depth',                   self.DM_TO_M)
        self.convert_to_metric('heading',                 self.HUNDRETH_TO_DEG)
        self.convert_to_metric('pitch',                   self.HUNDRETH_TO_DEG)
        self.convert_to_metric('roll',                    self.HUNDRETH_TO_DEG)
        self.convert_to_metric('temperature',             self.HUNDRETH_TO_DEG)
        self.convert_to_metric('pitch_standard_deviation',self.TENTH_TO_DEG)
        self.convert_to_metric('roll_standard_deviation', self.TENTH_TO_DEG)
        self.convert_to_metric('pressure',                self.DAM_TO_M)
        self.convert_to_metric('pressure_variance',       self.DAM_TO_M)

        # collect all time information into a single datetime object 
        timestamp = datetime(
            variable_leader['rtc_year'] + RTC_MILLENIUM,
            variable_leader['rtc_month'],
            variable_leader['rtc_day'],
            variable_leader['rtc_hour'],
            variable_leader['rtc_minute'],
            variable_leader['rtc_second'],
            variable_leader['rtc_hundredths']).timestamp()

        # store time information in data array
        self.set_data('time', timestamp)


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
        ID_BYTE_LENGTH   = 2
        if name == 'velocity': profiling_format = '<h'
        else:                  profiling_format = 'B'
        offset  += ID_BYTE_LENGTH
        profile  = self.parse_beams(pd0_bytes, offset, self.num_bins,
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
        # labels for (u,v,w) components of velocity
        label_u = 'btm_beam0_velocity'
        label_v = 'btm_beam1_velocity'
        label_w = 'btm_beam2_velocity'
        bottom_track = self.unpack_bytes(pd0_bytes,
                                         self.bottom_track_format,
                                         offset)

        # add relevant bottom track values to the data array
        for key in bottom_track:
            if key in self.label_set:
                self.set_data(key, bottom_track[key])

        # helper functions for converting velocity values
        def convert_special_to_metric(var, flag, multiplier):
            if self.get_data(var) == flag:  
                self.set_data(var, np.NaN)
            else: 
                self.convert_to_metric(var, multiplier)

        def convert_velocity_to_metric(var):
            convert_special_to_metric(var, self.BAD_VELOCITY, self.MM_TO_M)

        def convert_bt_range_to_metric(var):
            convert_special_to_metric(var, self.BAD_BT_RANGE, self.CM_TO_M)

        # convert relevant fields to standard metric quantities
        convert_velocity_to_metric('btm_beam0_velocity')
        convert_velocity_to_metric('btm_beam1_velocity')
        convert_velocity_to_metric('btm_beam2_velocity')
        convert_velocity_to_metric('btm_beam3_velocity')
        convert_bt_range_to_metric('btm_beam0_range')
        convert_bt_range_to_metric('btm_beam1_range')
        convert_bt_range_to_metric('btm_beam2_range')
        convert_bt_range_to_metric('btm_beam3_range')
        self.convert_to_metric('btm_max_error_velocity', self.MM_TO_M)
        self.convert_to_metric('btm_beam0_rssi',         self.COUNT_TO_DB)
        self.convert_to_metric('btm_beam1_rssi',         self.COUNT_TO_DB)
        self.convert_to_metric('btm_beam2_rssi',         self.COUNT_TO_DB)
        self.convert_to_metric('btm_beam3_rssi',         self.COUNT_TO_DB)

        # fix velocity 
        u0    = self.get_data(label_u)
        v0    = self.get_data(label_v) 
        w0    = self.get_data(label_w)
        u,v,w = self.apply_mounting_bias_rotations((u0,v0,w0))
        self.set_data(label_u, u)
        self.set_data(label_v, v)
        self.set_data(label_w, w)
 

    def parse_derived_variables(self):
        """Computes the derived variables specified in PathfinderDVL.

        Uses information from other variables 
        """
        # check that the DVL is reporting data in earth coordinates
        EARTH_FRAME = 'Earth Coords'
        MIN_PITCH   = 0.001
        EPSILON     = 0.001
        MAX_SPEED   = 1.3 

        coordinate_frame = self.parse_coordinate_transformation(verbose=False)
        if coordinate_frame != EARTH_FRAME:
            raise ValueError('Bad coord frame: expected = %s, actual = %s' % 
                             (EARTH_FRAME, coordinate_frame))

        # assume zero angle of attack
        self.set_data('angle_of_attack', 0)

        # previous ensemble not given
        #   + assume beginning of dive
        if not self.prev_ensemble:
            # set origin to (0,0) if not specified
            if not self.gps_fix:
                self.set_data('origin_x',  0)
                self.set_data('origin_y',  0)
            # otherwise set origin to GPS fix 
            else:
                self.set_data('origin_x',  self.gps_fix[0])
                self.set_data('origin_y',  self.gps_fix[0])
            return

        # extract position information from previous ensemble 
        #   + performs odometry without computation of ocean currents
        #   + odometry with water column currents is not embedded right now
        prev_origin_x  = self.prev_ensemble.get_data('origin_x')
        prev_origin_y  = self.prev_ensemble.get_data('origin_y')
        prev_rel_pos_x = self.prev_ensemble.get_data('rel_pos_x_dvl_dr')
        prev_rel_pos_y = self.prev_ensemble.get_data('rel_pos_y_dvl_dr')
        prev_rel_pos_z = self.prev_ensemble.get_data('rel_pos_z_dvl_dr')
        prev_depth     = self.prev_ensemble.get_data('depth')
        prev_pitch     = self.prev_ensemble.get_data('pitch')
        prev_t         = self.prev_ensemble.get_data('time') 

        # helper function for setting DVL velocity based on bin number
        def set_dvl_rel_velocities(bin_num):
            u_var = self.get_profile_var_name('velocity', bin_num, 0)
            v_var = self.get_profile_var_name('velocity', bin_num, 1)
            w_var = self.get_profile_var_name('velocity', bin_num, 2)
            self.set_data('rel_vel_dvl_u', -self.get_data(u_var))
            self.set_data('rel_vel_dvl_v', -self.get_data(v_var))
            self.set_data('rel_vel_dvl_w',  self.get_data(w_var))

        # helper function for setting bottom track velocities
        def set_btm_abs_velocities():
            self.set_data('abs_vel_btm_u', -self.btm_beam0_velocity)
            self.set_data('abs_vel_btm_v', -self.btm_beam1_velocity)
            self.set_data('abs_vel_btm_w',  self.btm_beam2_velocity)
    
        # helper function to update relative position 
        def update_position(vel_label):
            vel_options = ['rel_vel_dvl','rel_vel_pressure','abs_vel_btm']
            if vel_label not in vel_options:
                raise ValueError('bad velocity source: %s' % (vel_label))
            # update relative position using bottom track velocity 
            delta_z = self.delta_z_pressure
            self.set_data('delta_x',self.delta_t*self.get_data(vel_label+'_u'))
            self.set_data('delta_y',self.delta_t*self.get_data(vel_label+'_v'))
            self.set_data('delta_z',self.delta_t*self.get_data(vel_label+'_w'))
            self.set_data('rel_pos_x_dvl_dr', prev_rel_pos_x + self.delta_x)
            self.set_data('rel_pos_y_dvl_dr', prev_rel_pos_y + self.delta_y)
            self.set_data('rel_pos_z_dvl_dr', prev_rel_pos_z +      delta_z)

        # helper function for assessing if bottom track data is valid
        def valid_bottom_track():
            return(not np.isnan(self.get_data('btm_beam0_velocity')))

        def valid_bin_num(bin_num):
            var_name = self.get_profile_var_name('velocity', bin_num, 0)
            return(not np.isnan(self.get_data(var_name)))

        # compute through water velocity from pressure method
        self.set_data('delta_t',          self.time  - prev_t)
        self.set_data('delta_z_pressure', self.depth - prev_depth)
        self.set_data('delta_pitch',      self.pitch - prev_pitch)

        # computer horizontal velocity in relative frame 
        #   + avoid division by zero
        if (np.abs(self.pitch) > MIN_PITCH) and \
            (np.abs(self.get_data('delta_z_pressure')) > EPSILON):
            
            # through water velocity from change in pressure and compass
            self.set_data('rel_vel_pressure_w', 
                        self.delta_z_pressure/self.delta_t)

            # horizontal velocity depends on pitch value
            rel_vel_h = self.rel_vel_pressure_w / \
                        np.tan(-self.pitch*self.DEG_TO_RAD)

            rel_vel_u = rel_vel_h*np.sin(self.heading*self.DEG_TO_RAD)
            rel_vel_v = rel_vel_h*np.cos(self.heading*self.DEG_TO_RAD)
            self.set_data('rel_vel_pressure_u', rel_vel_u)
            self.set_data('rel_vel_pressure_v', rel_vel_v)

        # set pressure through water velocities to NaN otherwise
        else:
            self.set_data('rel_vel_pressure_u', np.NaN)
            self.set_data('rel_vel_pressure_v', np.NaN)
            self.set_data('rel_vel_pressure_w', np.NaN)

        # select DVL bin for through-water velocity 
        #   + first two bins are less accurate in steady state conditions
        #   + bins further away are more likely to have random outliers
        for i in [2,1,0]:
            if valid_bin_num(i) and self.get_speed(i) < MAX_SPEED:
                set_dvl_rel_velocities(i)
                break           

        # set bottom-track velocities (even if NaN)
        set_btm_abs_velocities()

        # update relative position using bottom track velocity or DVL velocity
        if valid_bottom_track():
            update_position('abs_vel_btm')
        else:
            update_position('rel_vel_dvl')
        
        # update origin and relative position if GPS fix is given
        if self.gps_fix:
            self.set_data('origin_x', self.gps_fix[0])
            self.set_data('origin_y', self.gps_fix[0])
            self.set_data('rel_pos_x_dvl_dr', 0)
            self.set_data('rel_pos_y_dvl_dr', 0)
            self.set_data('rel_pos_z_dvl_dr', 0)
        else:
            self.set_data('origin_x', prev_origin_x)
            self.set_data('origin_y', prev_rel_pos_y)


    def get_speed(self, bin_num):
        """Returns the magnitude of velocity given a bin number

        Args:
            bin_num: the bin number to compute the speed vector
        """
        x,y,z = 0,1,2
        u = self.get_data(self.get_profile_var_name('velocity', bin_num, x))
        v = self.get_data(self.get_profile_var_name('velocity', bin_num, y))
        w = self.get_data(self.get_profile_var_name('velocity', bin_num, z))
        return(np.linalg.norm([u,v,w]))


    def convert_to_metric(self, variable, multiplier, attribute=True):
        """Converts variable to standard metric value using the multiplier"""
        value = self.get_data(variable) 
        self.set_data(variable, value * multiplier, attribute)
        

    def validate_checksum(self, pd0_bytes):
        """Validates the checksum for the ensemble.
        """
        calc_checksum  = sum([c for c in pd0_bytes[:self.num_bytes]]) & 0xFFFF
        given_checksum = struct.unpack_from('<H', pd0_bytes, self.num_bytes)[0]
        if calc_checksum != given_checksum:
            raise PathfinderChecksumError(calc_checksum, given_checksum)


    def apply_mounting_bias_rotations(self, velocity0):
        """Rotates velocity vector to account for mounting bias.

        Assumes that velocity data is in Earth Coordinate frame.

        Args:
            velocity0: (u0,v0,w0) velocity vector recorded by instrument.

        Returns: (u,v,w) velocity vector in desired coordinate frame.
        """
        BIAS_PITCH   =  8  # [deg]
        BIAS_ROLL    = -1  # [deg]
        BIAS_HEADING =  0  # [deg]
        u0,v0,w0     = velocity0
        Velocity_e0  = np.array([[u0],[v0],[w0]])

        # orthogonal transformation matrices 
        def Qx(phi):
            return(np.array([[           1,            0,            0],
                             [           0,  np.cos(phi), -np.sin(phi)],
                             [           0,  np.sin(phi),  np.cos(phi)]]))
        def Qy(phi):
            return(np.array([[ np.cos(phi),            0,  np.sin(phi)],
                             [           0,            1,            0],
                             [-np.sin(phi),            0,  np.cos(phi)]]))
        def Qz(phi):
            return(np.array([[ np.cos(phi), -np.sin(phi),            0],
                             [ np.sin(phi),  np.cos(phi),            0],
                             [           0,            0,            1]]))

        # rotate from Earth Coords <E,N,U> to Ship Coords <S,F,U>
        head = (self.heading-BIAS_HEADING)*self.DEG_TO_RAD
        pitc = BIAS_PITCH*self.DEG_TO_RAD        
        roll = BIAS_ROLL*self.DEG_TO_RAD
        Velocity_s    = np.dot(Qz( head), Velocity_e0)
        Velocity_s_p  = np.dot(Qx( pitc), Velocity_s)
        Velocity_s_pr = np.dot(Qy( roll), Velocity_s_p)
        Velocity_e    = np.dot(Qz(-head), Velocity_s_pr)
        u,v,w         = Velocity_e.flatten()
        return(u,v,w)


    def parse_beams(self, pd0_bytes, offset, num_bins, num_beams, var_format, 
        var_name):
        """Parses beams of DVL data.
        
        Velocity, correlation mag, echo intensity, and percent good data types
        report values per depth cell per beam. For example, with 4 beams
        and 40 depth cell bins, there are 160 velocity values reported 
        (each value being encoded with two bytes, unlike the other fields).

        Args:
            pd0_bytes: pd0 bytes to be parsed into the fixed leader data type.
            offset: byte offset to start parsing the fixed leader. 
            num_bins: number of depth cells on DVL (user setting).
            num_beams: number of beams on the DVL (fixed at 4).
            var_format: Format String for the variable being parsed for each
                beam. For example var_format = 'h' means type short.
            var_name: name of the variable being parsed (i.e. 'velocity')
        """
        # assumes that last beam is an error velocity, meaning velocity is not
        # reported in beam coordinates 
        ERROR_BEAM_NUM = 3
        beam_u = 0
        beam_v = 1
        beam_w = 2
        var_size  = struct.calcsize(var_format)
        velocity0 = []
        num_good_vel_bins_flag = False

        # only parse velocity water profile data to save processing time
        if var_name == 'velocity':

            # parse data for each depth cell 
            for bin_num in range(num_bins):
                bin_start = offset + bin_num*num_beams*var_size

                # parse data for each beam for a given depth cell 
                velocity0  = []
                for beam_num in range(num_beams):
                    beam_start = bin_start + beam_num*var_size
                    data_val   = struct.unpack_from(var_format, 
                                                    pd0_bytes, 
                                                    beam_start)[0]

                    # compute labels and array index 
                    label = self.get_profile_var_name(var_name, 
                                                      bin_num, 
                                                      beam_num)

                    # filter out bad velocity values 
                    if (var_name == 'velocity'):
                        if (data_val == self.BAD_VELOCITY):
                            self.set_data(label, np.NaN)
                            if not num_good_vel_bins_flag:
                                self.set_data('num_good_vel_bins', bin_num)
                                num_good_vel_bins_flag = True
                        elif (beam_num != ERROR_BEAM_NUM):
                            velocity0.append(data_val*self.MM_TO_M)
                        else: 
                            self.set_data(label, data_val*self.MM_TO_M)

                # rotate velocity vector to account for pitch bias
                if velocity0:
                    u,v,w  = self.apply_mounting_bias_rotations(velocity0)
                    xlabel = self.get_profile_var_name(var_name,bin_num,beam_u)
                    ylabel = self.get_profile_var_name(var_name,bin_num,beam_v)
                    zlabel = self.get_profile_var_name(var_name,bin_num,beam_w)
                    self.set_data(xlabel, u)
                    self.set_data(ylabel, v)
                    self.set_data(zlabel, w)


    def parse_system_configuration(self, verbose=True):
        """Parses system configuration setting and prints out result.

        Requires that system_configuration is in base 10 number format.
        """
        # convert base-10 to binary string
        sys_str       = bin(self.system_configuration)[2:][::-1]
        lagging_zeros = 16 - len(sys_str)
        sys_str      += '0'*lagging_zeros

        # separate the sections of the system configuration message
        hz_bin                  = sys_str[0:3]
        beam_pattern_bin        = sys_str[3:4]
        sensor_config_bin       = sys_str[4:6]
        transducer_attached_bin = sys_str[6:7]
        upwards_facing_bin      = sys_str[7:8]
        beam_angle_bin          = sys_str[8:10]
        janus_config_bin        = sys_str[12:16]

        # parse hz setting 
        if   hz_bin == '000': hz_set = '75kHz System'
        elif hz_bin == '100': hz_set = '150kHz System'
        elif hz_bin == '010': hz_set = '300kHz System'
        elif hz_bin == '110': hz_set = '600kHz System'
        elif hz_bin == '001': hz_set = '1200kHz System'
        elif hz_bin == '101': hz_set = '2400kHz System'

        # parse beam configuration
        if   beam_pattern_bin == '0': beam_pattern_set = 'Concave Beam Pattern'
        elif beam_pattern_bin == '1': beam_pattern_set = 'Convex Beam Pattern'

        # parse sensor configuration
        if   sensor_config_bin == '00': sensor_config_set = 'Sensor Config #1'
        elif sensor_config_bin == '10': sensor_config_set = 'Sensor Config #2'
        elif sensor_config_bin == '01': sensor_config_set = 'Sensor Config #3'

        # parse transducer attached 
        if transducer_attached_bin == '0': 
            transducer_attached_set = 'Not Attached'
        elif transducer_attached_bin == '1': 
            transducer_attached_set = 'Attached'

        # parse upward facing  
        if   upwards_facing_bin == '0': upwards_facing_set = 'Down Facing'
        elif upwards_facing_bin == '1': upwards_facing_set = 'Up Facing'

        # parse beam angle
        if   beam_angle_bin == '00': beam_angle_set = '15E Beam Angle'
        elif beam_angle_bin == '10': beam_angle_set = '20E Beam Angle'
        elif beam_angle_bin == '01': beam_angle_set = '30E Beam Angle'
        elif beam_angle_bin == '11': beam_angle_set = 'Other Beam Angle'

        # parse janus config
        if janus_config_bin == '0010': 
            janus_config_set = '4 Beam Janus'
        elif janus_config_bin == '1010': 
            janus_config_set = '5 Beam Janus, 3 Demod'
        elif janus_config_bin == '1111': 
            janus_config_set = '5 Beam Janus, 2 Demod'

        # print out the sensor configuration if requested
        if verbose:
            print('- Sensor Configuration -----------------')
            print('    ' + hz_set)
            print('    ' + beam_pattern_set)
            print('    ' + sensor_config_set)
            print('    ' + transducer_attached_set)
            print('    ' + upwards_facing_set)
            print('    ' + beam_angle_set)
            print('    ' + janus_config_set)


    def parse_coordinate_transformation(self, verbose=True):
        """Parses coordinate transformation setting and prints out result.

        Requires that coordinate_transformation is in base 10 number format.
        """
        # convert base-10 number to binary string 
        ctf_str = bin(self.coordinate_transformation)[2:][::-1]
        lagging_zeros = 8 - len(ctf_str)
        ctf_str += '0'*lagging_zeros

        # separate the sections of the system configuration message
        bin_mapping_bin      = ctf_str[0:1]
        three_beam_used_bin  = ctf_str[1:2]
        tilts_used_bin       = ctf_str[2:3]
        coord_frame_bin      = ctf_str[3:5]

        # parse bin mapping setting 
        if   bin_mapping_bin == '1': bin_mapping_set = 'Bin Mapping Used'
        elif bin_mapping_bin == '0': bin_mapping_set = 'Bin Mapping Not Used'

        # parse three beam solution setting 
        if three_beam_used_bin == '1': 
            three_beam_used_set = '3-Beam Soln Used'
        elif three_beam_used_bin == '0': 
            three_beam_used_set = '3-Beam Soln Not Used'

        # parse tilts setting 
        if   tilts_used_bin == '1': tilts_used_set = 'Tilts Used'
        elif tilts_used_bin == '0': tilts_used_set = 'Tilts Not Used'

        # parse coordinate transformation setting
        if   coord_frame_bin == '00': coord_frame_set = 'Beam Coords'
        elif coord_frame_bin == '10': coord_frame_set = 'Instrument Coords'
        elif coord_frame_bin == '01': coord_frame_set = 'Ship Coords'
        elif coord_frame_bin == '11': coord_frame_set = 'Earth Coords'

        # print out the coordinate transformation if requested 
        if verbose:
            print('- Coordinate Transformation ------------')
            print('    ' + bin_mapping_set)
            print('    ' + three_beam_used_set)
            print('    ' + tilts_used_set)
            print('    ' + coord_frame_set)

        return coord_frame_set

