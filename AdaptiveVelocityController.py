# AdaptiveVelocityController.py
#
# Class for computing energy-optimal propulsion for AUG glider 
#   2020-07-03  zduguid@mit.edu         initial implementation

import numpy as np


class AVC(object):
    def __init__(self):
        """Initialization function to define constants, no inputs are given. 
        """
        # constants for unit conversion
        self.DEG_TO_RAD       = np.pi/180
        self.RAD_TO_DEG       = 1/self.DEG_TO_RAD
        self.HOURS_TO_SECONDS = 60*60
        self.SECONDS_TO_HOURS = 1/self.HOURS_TO_SECONDS

        # constants to define limits of propulsive thruster
        self.V_MIN  = 0.0
        self.V_MAX  = 1.0
        # self.V_RES  = 61 
        self.V_RES  = 121
        self.V_RES  = 500
        self.V_LIST = np.linspace(self.V_MIN, self.V_MAX, self.V_RES)

        # minimum and maximum pitch values in [deg]
        self.MIN_PITCH = 5
        self.MAX_PITCH = 45

        # energy cost for using the ballast pump at bottom inflection
        self.E_PUMP = 2.95 * self.HOURS_TO_SECONDS


    @classmethod
    def get_optimal_vtw_prop(cls, voc_mag=0, voc_delta=0, p_hotel=6.37, 
        pitch=12, z_dive=500, z_climb=0, percent_ballast=1.00):
        """Determine energy-optimal propulsive velocity for the AUG.

        Energy-optimal propulsive velocity is defined by the propulsive 
        velocity that yields the minimum transport cost given the current 
        vehicle and environment state. 
        
        Args:
            voc_mag: ocean current speed [m/s]
            voc_delta: angle of ocean current relative to glider heading [rad]
            p_hotel: hotel load of the vehicle [W]
            pitch: ascent/descent angle of the glider [deg]
            z_dive: dive depth (positive downwards) [m]
            z_climb: climb depth (positive downwards) [m]
            percent_ballast: percentage of ballast volume pumped [%]

        Returns:
            The energy-optimal propulsive velocity for the glider in [m/s]
        """
        AVC     = cls()
        f_list  =  [AVC.get_transport_cost_vtw_prop(vtw_prop,voc_mag,voc_delta,
                        p_hotel, pitch, z_dive, z_climb, percent_ballast) 
                    for vtw_prop in AVC.V_LIST]
        min_idx = np.nanargmin(f_list)
        opt_v   = AVC.V_LIST[min_idx]
        return(opt_v)


    @classmethod
    def get_optimal_vog(cls, voc_mag=0, voc_delta=0, p_hotel=6.37, 
        pitch=12, z_dive=500, z_climb=0, percent_ballast=1.00):
        """Determine the over-ground velocity when AUG using optimal thrust
        
        Returns:
            The energy-optimal over-ground velocity for the glider in [m/s]
        """
        # find the optimal through-water velocity of the AUG
        vog_AVC  = AVC()
        vtw_prop = AVC.get_optimal_vtw_prop(voc_mag, voc_delta, p_hotel, pitch,
            z_dive, z_climb, percent_ballast)

        # find the resulting over-ground speed of the AUG
        vog = vog_AVC.get_vog(vtw_prop, voc_mag, voc_delta, p_hotel, pitch, 
            z_dive, z_climb, percent_ballast)

        return(vog)


    @classmethod
    def get_optimal_depth_band(cls, voc_u_list, voc_v_list, max_depth, heading,
        pitch, p_hotel, voc_interval_len=1, percent_ballast=0.2, verbose=True):
        """Determine the optimal depth band for the AUG.

        Args: 
            voc_u_list: list of eastward ocean currents 
            voc_v_list: list of northward ocean currents 
            max_depth: maximum depth allowed in this region 
            heading: AUG heading [deg]
            pitch: AUG pitch [deg]
            p_hotel: AUG hotel load [W]
            voc_interval_len: distance between ocean current bins [m]
            percent_ballast: [%]

        Returns: 
            tuple (optimal dive-to depth, optimal climb-to depth, optimal 
                transport cost, dive list, climb list, transport cost list)
        """
        # initialize list to keep track of objective for all depth-bands
        dive_list  = []
        climb_list = []
        TC_list    = []
        AVC_depth_band = AVC()
        if verbose: print("> EDBS for Heading: %d" % (heading))

        # iterate through the valid combinations of dive-to and climb-to depths
        for z_dive in range(max_depth):
            if verbose: 
                if z_dive % 10 == 0: print("   dive depth: %d"%z_dive)
            for z_climb in range(z_dive):

                # update lists
                climb_list.append(z_climb)
                dive_list.append(z_dive)
                TC_list.append(AVC_depth_band.get_depth_band_transport_cost(
                    z_dive, 
                    z_climb, 
                    voc_u_list,
                    voc_v_list,
                    p_hotel, 
                    heading, 
                    pitch,
                    voc_interval_len=voc_interval_len,
                    percent_ballast=percent_ballast)
                )

        # extract the optimal depth band 
        idx_min     = np.argmin(TC_list)
        opt_z_dive  = dive_list[idx_min]
        opt_z_climb = climb_list[idx_min]
        opt_TC      = TC_list[idx_min]
        return(opt_z_dive, opt_z_climb, opt_TC, dive_list, climb_list, TC_list)


    def get_transport_cost_vtw_prop(self, vtw_prop, voc_mag, voc_delta, 
        p_hotel, pitch, z_dive, z_climb, percent_ballast):
        """Computes the transport cost given vehicle and environment state.
        
        Args:
            vtw_prop: through-water velocity generated by thruster [m/s]
            voc_mag: ocean current speed [m/s]
            voc_delta: angle of ocean current relative to glider heading [rad]
            p_hotel: hotel load of the vehicle [W]
            pitch: ascent/descent angle of the glider [deg]
            z_dive: dive depth (positive downwards) [m]
            z_climb: climb depth (positive downwards) [m]
            percent_ballast: percentage of ballast volume pumped [%]
        """
        # get the resulting over-ground velocity for this propulsive power
        vog = self.get_vog(vtw_prop, voc_mag, voc_delta, p_hotel, pitch, 
            z_dive, z_climb, percent_ballast)

        # compute the total through-water velocity 
        vtw_buoy  = self.get_vtw_buoy(pitch, percent_ballast)
        vtw_total = vtw_prop + vtw_buoy
        
        # compute energy expended from all sources of power draw
        p_thr   = self.get_thruster_power(vtw_prop)
        p_buoy  = self.get_buoy_power(vtw_total, pitch, z_dive, z_climb)
        p_total = p_thr + p_buoy + p_hotel
        return(p_total/vog)


    def get_vog(self, vtw_prop, voc_mag, voc_delta, p_hotel, pitch, z_dive, 
        z_climb, percent_ballast):
        """Computes the over-ground velocity given all operating conditions
        """
        # determine the long-track and cross-track ocean current components
        voc_para = voc_mag*np.cos(voc_delta)
        voc_perp = np.abs(voc_mag*np.sin(voc_delta))

        # get the through-water velocity contribution from the buoyancy engine
        vtw_buoy  = self.get_vtw_buoy(pitch, percent_ballast)
        vtw_total = vtw_prop + vtw_buoy
        vtw_hor   = vtw_total*np.cos(pitch*self.DEG_TO_RAD) 
        
        # glider cannot overcome cross-track ocean current 
        if vtw_hor < voc_perp:
            return(np.NaN)
        
        # glider cannot overcome adverse parallel currents
        vtw_para = (vtw_hor**2 - voc_perp**2)**0.5
        if vtw_para <= -voc_para:
            return(np.NaN)
        
        # glider can successfully move in intended direction
        #   + compute energy expended from all sources of power draw
        vog = vtw_para + voc_para
        return(vog)


    def get_depth_band_transport_cost(self, z_dive, z_climb, voc_u_list, 
        voc_v_list, p_hotel, heading, pitch, voc_interval_len=1, 
        percent_ballast=0.2):
        """Determine the transport cost of the depth band given vehicle and 
        environment state variables.

        Args: 
            z_dive: dive depth [m]
            z_climb: climb depth [m]
            p_hotel: hotel load [W]
            heading: glider heading in [deg]
            pitch: glider pitch in [deg]
            voc_u_list: list of eastward ocean current velocities [m/s]
            voc_v_list: list of northward ocean current velocities [m/s]
            voc_interval_length: length of depth interval between water column 
                current lists in voc_u_list and voc_v_list (interval length 
                used when performing water column current integration)
            percent_ballast: percentage of ballast volume pumped [%]
        """
        # compute change in energy over change in horizontal distance
        #   + add fixed energy cost of buoyancy pump
        delta_energy   = (self.E_PUMP/2)*percent_ballast
        delta_distance = 0
        
        # integrate water column variables over the depth band
        for z in range(z_climb, z_dive):
            voc_u   = voc_u_list[z]     # [m/s]
            voc_v   = voc_v_list[z]     # [m/s]

            # determine heading offset and components of ocean currents
            voc_heading  = np.arctan2(voc_u, voc_v)
            voc_mag      = np.linalg.norm([voc_u, voc_v])
            voc_delta    = voc_heading - heading*self.DEG_TO_RAD
            voc_para     = voc_mag*np.cos(voc_delta)
            voc_perp     = voc_mag*np.sin(voc_delta)

            # compute through-water velocity from propeller and buoyancy
            vtw_prop = AVC.get_optimal_vtw_prop(
                voc_mag=voc_mag,
                voc_delta=voc_delta,
                p_hotel=p_hotel,
                pitch=pitch,
                z_dive=z_dive,
                z_climb=z_climb,
                percent_ballast=percent_ballast
            )
            vtw_buoy  = self.get_vtw_buoy(pitch, percent_ballast)
            vtw_total = vtw_prop + vtw_buoy
            vtw_ver   = vtw_total*np.sin(pitch*self.DEG_TO_RAD)
            vtw_hor   = vtw_total*np.cos(pitch*self.DEG_TO_RAD)
            vtw_para  = (vtw_hor**2  - voc_perp**2)**0.5
            vog       = (vtw_para + voc_para)

            # computer power draw with optimal propulsive power
            #   + note that ballast pump cost already to energy consumption
            p_thr   = self.get_thruster_power(vtw_prop)
            p_total = p_thr + p_hotel

            # add energy consumption and distance traveled to the summation 
            delta_time      = voc_interval_len/vtw_ver  # [s]
            delta_energy   += p_total*delta_time        # [W*s]
            delta_distance += vog*delta_time            # [m]
            
        # handle case when vehicle cannot travel with this depth band
        if delta_distance == 0: return(np.nan)
        # otherwise return the transport cost for this depth band 
        return(delta_energy/delta_distance)


    def get_prop_power_new_model(self, vtw_prop):
        """Determines propulsive power needed to achieve propulsive speed
        
        New thruster model, based on preliminary data.
        Source: Brian Claus, June 2020.
        """
        vtw_prop = max(min(vtw_prop, self.V_MAX), self.V_MIN)
        c3 =  3.7856
        c2 =  1.9944
        c1 = -0.2221
        c0 =  1.0948
        return(c3*vtw_prop**3 + c2*vtw_prop**2 + c1*vtw_prop + c0)


    def get_prop_power(self, vtw_prop):
        """Determines propulsive power needed to achieve propulsive speed

        Documented in Master Data file of the Slocum Glider manual.
        """
        vtw_prop = max(min(vtw_prop, self.V_MAX), self.V_MIN)
        c1 = 0.450 
        c2 = 0.385
        return((vtw_prop/c1)**(1/c2))


    def get_controller_power(self, prop_power):
        """Determines motor controller loss as a function of input prop power
        """
        c1 = 0.10 
        c0 = 0.32
        return(prop_power*c1 + c0)


    def get_thruster_power(self, vtw_prop):
        """Determine total thruster power as sum of propeller power and 
        controller power
        """
        p_prop = self.get_prop_power(vtw_prop)
        p_controller = self.get_controller_power(p_prop)
        return(p_prop + p_controller)


    def get_buoy_power(self, vtw_total, pitch, z_dive, z_climb):
        """Determine the average power over the course of an inflection cycle
        """
        if pitch == 0:     return(0)
        if vtw_total <= 0: return(np.nan) # TODO
        # if vtw_total <= 0: return(0)
        vtw_vertical = vtw_total*np.sin(pitch*self.DEG_TO_RAD)
        delta_depth_inflection = z_dive - z_climb
        delta_time_inflection  = 2*delta_depth_inflection/vtw_vertical
        return(self.E_PUMP / delta_time_inflection)


    def get_vtw_buoy(self, pitch, percent_ballast):
        """Determine through-water velocity from buoyancy engine.
        """
        if pitch==0: return(0)
        c0 =  0.11332
        c1 =  0.01552
        c2 = -0.00022
        # horizontal through-water velocity with full ballast
        vtw_hor = c0 + c1*pitch + c2*pitch**2
        # vehicle track through-water velocity with full ballast
        vtw_foreward = vtw_hor / np.cos(pitch*self.DEG_TO_RAD)
        # adjust speed for percent of ballast used
        vtw_adjusted = vtw_foreward*(percent_ballast**0.5)
        return(vtw_adjusted)


    @classmethod
    def get_rescaled_voc_lists(cls, original_depth, new_depth, voc_u_list, voc_v_list):
        """Rescales ocean currents from original depth to new depth 

        This function can be used to study a particular water column current 
        profile at different depth scaling. For example, changing the depth 
        of the profile can be used as a diagnostic tool for EDBS algorithm.
        """
        new_voc_u = [voc_u_list[int((original_depth/new_depth)*i)] 
                        for i in range(new_depth)]
        new_voc_v = [voc_v_list[int((original_depth/new_depth)*i)] 
                        for i in range(new_depth)]
        new_voc_z = np.linspace(0,new_depth,new_depth)

        # fill NaN values 
        for i in range(len(new_voc_u)):
            if np.isnan(new_voc_u[i]):
                new_voc_u[i] = new_voc_u[i-1]
                new_voc_v[i] = new_voc_v[i-1]

        return(new_voc_u, new_voc_v, new_voc_z)


