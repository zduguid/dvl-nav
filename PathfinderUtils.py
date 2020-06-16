# PathfinderUtils.py
#
# Utility classes and functions for working with Pathfinder DVL data. 
#   2020-06-12  zduguid@mit.edu    implemented PathfinderUtils.py

import numpy as np



class OceanCurrent(object):
    def __init__(self, u=None, v=None, w=None):
        """Represents a 3D OceanCurrent velocity."""
        self.u = u
        self.v = v
        self.w = w
        if not((u==None and v==None and w==None) or \
               (u!=None and v!=None and w!=None)):
            raise ValueError('bad ocean current',u,v,w)
        if not self.is_none():
            self.mag = np.linalg.norm([self.u,self.v,self.w])
        else:
            self.mag = np.NaN

    def __str__(self):
        if self.is_none():
            return 'V[----,----,----]'
        else:
            return 'V[%4d,%4d,%4d]' % (self.u*100, self.v*100, self.w*100)

    def __eq__(self, other):
        return(str(self)==str(other))

    def copy(self):
        return OceanCurrent(self.u, self.v, self.w)

    def is_none(self):
        return(self.u==None and self.v==None and self.w==None)

    def subtract_shear(self, shear):
        """Subtract one OceanCurrent from another OceanCurrent."""
        new_shear_node = self.copy()
        if not new_shear_node.is_none():
            delta_u,delta_v,delta_w = shear.u,shear.v,shear.w
            new_shear_node.u += -delta_u
            new_shear_node.v += -delta_v
            new_shear_node.w += -delta_w
        return new_shear_node

    def add_shear(self, shear):
        """Add two OceanCurrent objects together."""
        new_shear_node = self.copy()
        if not new_shear_node.is_none():
            delta_u,delta_v,delta_w = shear.u,shear.v,shear.w
            new_shear_node.u += delta_u
            new_shear_node.v += delta_v
            new_shear_node.w += delta_w
        return new_shear_node



class WaterColumn(object):
    def __init__(self,bin_len=2,bin0_dist=2.91,max_depth=1000,start_filter=0,end_filter=0, voc_mag_filter=0.5, voc_delta_mag_filter=0.30):
        """Represents water column currents in an absolute reference frame.

        Uses measurements from Doppler Velocity Log (DVL) to determine water
        column velocities. The shear-based velocity method is used to 
        propagate water column currents forward and backward in time. Assumes
        downward facing DVL

        Args:
            bin_len: length of DVL depth bin.
            bin0_dist: distance from transducer head to middle of first bin.
            max_depth: max depth considered in the water column.
            start_filter: used to filter out the first number of DVL bins from 
                the propagation process.
            end_filter: used to filter out the last number of DVL bins from 
                the propagation process.
        """
        self._BIN_LEN      = bin_len
        self._BIN0_DIST    = bin0_dist
        self._MAX_DEPTH    = max_depth
        self._START_FILTER = start_filter
        self._END_FILTER   = end_filter
        self._WC_BIN_LEN   = int(bin_len)
        self.shear_node_dict = {i : [] for i in 
                               range(0,self.MAX_DEPTH,self.WC_BIN_LEN)}
        self.avg_voc_dict    = {i : OceanCurrent() for i in 
                               range(0,self.MAX_DEPTH,self.WC_BIN_LEN)}

        # tuning parameters for ocean current estimation
        self.voc_mag_filter = voc_mag_filter
        self.voc_delta_mag_filter = voc_delta_mag_filter

    def __str__(self):
        string  = 'Water Column (depth=%0.f) \n' % (self.MAX_DEPTH)
        for z in self.shear_node_dict.keys():
            string += '|z =%3d|' % z 
            for sn in self.shear_node_dict[z]:
                string += ' '
                string += str(sn)
            string += '\n'
        return(string)

    @property
    def BIN_LEN(self):
        return self._BIN_LEN

    @property
    def BIN0_DIST(self):
        return self._BIN0_DIST

    @property
    def MAX_DEPTH(self):
        return self._MAX_DEPTH

    @property
    def START_FILTER(self):
        return self._START_FILTER

    @property
    def END_FILTER(self):
        return self._END_FILTER

    @property
    def WC_BIN_LEN(self):
        return self._WC_BIN_LEN


    def get_z_true(self, parent, bin_num):
        """Get the true depth of the DVL depth bin

        Args: 
            parent: the parent node 
            bin_num: the DVL bin number removed from transducer (parent node)
        """
        DEG_TO_RAD = np.pi/180
        scale = np.cos(parent.pitch*DEG_TO_RAD)*np.cos(parent.roll*DEG_TO_RAD)
        return (parent.z_true + self.BIN0_DIST+bin_num*self.BIN_LEN)*scale 


    def get_wc_bin(self, z_true):
        """Get the depth of the water column cell."""
        return(int(z_true) - int(z_true)%self.WC_BIN_LEN)


    def mag_filter(self, shear_node):
        """Return true iff node meets magnitude reqs on voc and delta"""
        voc = shear_node.voc
        voc_delta = shear_node.voc_delta
        if not np.isnan(voc_delta.mag):
            if voc_delta.mag > self.voc_delta_mag_filter:
                return(False)
        if not np.isnan(voc.mag):
            if voc.mag > self.voc_mag_filter:
                return(False)
        return(True)


    def get_voc_at_depth(self,z):
        """Get the water column currents recorded at a particular depth."""
        z_bin = self.get_wc_bin(z)
        return(self.shear_node_dict[z_bin])


    def compute_averages(self):
        """Computes average water column currents for each depth bin."""
        # iterate over the depth bins 
        voc_u_list = []
        voc_v_list = []
        voc_w_list = []
        z_list     = []
        for z in self.avg_voc_dict.keys():
            count     = 0
            cum_voc_u = 0
            cum_voc_v = 0
            cum_voc_w = 0 
            node_list = self.get_voc_at_depth(z)

            # iterate over the observations at each depth bin
            for shear_node in node_list:
                voc = shear_node.voc
                if not(voc.is_none()):
                    # filter out large values when computing averages
                    if voc.mag < self.voc_mag_filter:
                        count     += 1
                        cum_voc_u += voc.u
                        cum_voc_v += voc.v
                        cum_voc_w += voc.w

            # report averages when data is available
            if count > 0:
                voc_avg = OceanCurrent(
                            cum_voc_u/count, 
                            cum_voc_v/count, 
                            cum_voc_w/count
                            )
                self.avg_voc_dict[z] = voc_avg
                voc_u_list.append(voc_avg.u)
                voc_v_list.append(voc_avg.v)
                voc_w_list.append(voc_avg.w)
                z_list.append(z)
            else:
                voc_u_list.append(np.NaN)
                voc_v_list.append(np.NaN)
                voc_w_list.append(np.NaN)
                z_list.append(z)
        return (np.array(voc_u_list), 
                np.array(voc_v_list), 
                np.array(voc_w_list),
                np.array(z_list))

    def averages_to_str(self):
        """Converts averages to string format after they have been computed."""
        string  = 'Water Column (depth=%0.f) \n' % (self.MAX_DEPTH)
        for z in self.avg_voc_dict.keys():
            string += '|z =%3d| ' % z 
            string += str(self.avg_voc_dict[z])
            string += '\n'
        return(string)


    def add_shear_node(self, z_true, t, shear_list, voc_ref=OceanCurrent(), 
        direction='descending', pitch=0, roll=0):
        """Adds a new DVL observation to the water column object.

        This is the main workhorse method for estimating ocean currents from
        DVL measurements: this function includes forward and backwards velocity
        shear propagations. The code uses a graph structure to maintain a network of observations to perform the propagations efficiently.
        """
        # add shear node for the current observation
        z_bin = self.get_wc_bin(z_true)
        shear_node = ShearNode(
            z_true=z_true, 
            z_bin=z_bin, 
            t=t, 
            water_col=self, 
            shear_list=shear_list, 
            voc=voc_ref,
            voc_ref=voc_ref,
            direction=direction,
            pitch=pitch,
            roll=roll,
        )

        #########################################
        # CASE 1: absolute reference available via bottom track mode
        #   + back propagate if parent node does not have velocity yet
        #   + set bottom track flag, forward propagate shear values
        if (not voc_ref.is_none()):

            # back propagation, starting from bottom track reference
            back_prop_flag = False
            if len(self.shear_node_dict[z_bin]) > 0:
                if (self.shear_node_dict[z_bin][-1].voc.is_none()):
                    back_node   = self.shear_node_dict[z_bin].pop()
                    parent_node = back_node.parent
                    if parent_node != None:
                        back_prop_flag = True
                        parent_voc = voc_ref.add_shear(back_node.voc_delta)
                        self.back_propagation(parent_node, parent_voc)

            # back propagation, starting from  shear list number
            if not back_prop_flag:
                for i in range(len(shear_list)):
                    child_z_true = self.get_z_true(shear_node,i)
                    child_z_bin  = self.get_wc_bin(child_z_true)
                    if len(self.shear_node_dict[child_z_bin]) > 0:
                        node = self.shear_node_dict[child_z_bin][-1]
                        if (node.voc.is_none()):
                            self.shear_node_dict[child_z_bin].pop()
                            parent_node = node.parent
                            if parent_node != None:
                                voc1 = voc_ref.subtract_shear(shear_list[i])
                                voc2 = voc1.subtract_shear(node.voc_delta)
                                self.back_propagation(parent_node,voc2)

            # perform forward propagation from absolute reference
            shear_node.set_btm_track(True)
            self.shear_node_dict[z_bin].append(shear_node)
            self.forward_propagation(shear_node, t, direction, shear_list)

        # otherwise, absolute velocity reference not available via bottom track
        else:


            #####################################
            # CASE 2: no absolute reference, glider is descending 
            #   A) look for previous measurements for forward propagation
            #   B) if no measurements, save shear data for back propagation
            if direction=='descending':


                #################################
                # CASE 2.A: no abs ref, descending, measurement available
                #   + if Voc available, update velocities (forward propagation)
                #   + otherwise, keep track of deltas and wait for absolute
                #     reference to perform back propagation later
                #   + TODO could use averaging here to make more stable?
                #     (could try to use 10 most recent observations? 
                #      downside to this is cannot make parent-child connection)
                if (len(self.shear_node_dict[z_bin]) > 0):

                    # perform forward propagation from parent node
                    parent  = self.shear_node_dict[z_bin][-1]
                    self.forward_propagation(parent, t, direction, shear_list)

                #################################
                # CASE 2.B: no abs ref, descending, no measurement available
                #   + forward propagate deltas in time so that back propagation
                #     can be performed once an absolute reference is made 
                else:
                    self.shear_node_dict[z_bin].append(shear_node)
                    self.forward_propagation(shear_node,t,direction,shear_list)


            #####################################
            # CASE 3: no absolute reference, glider is ascending 
            #   A) look for previous measurements for forward propagation
            #   B) if no measurements, save shear data for back propagation
            else:

                #################################
                # CASE 3.A: no abs ref, ascending, measurement available
                #   + if Voc available, update velocities (forward propagation)
                #   + otherwise, keep track of deltas and wait for absolute
                #     reference to perform back propagation later
                #   + TODO could use averaging here to make more stable?
                #     (could try to use 10 most recent observations? 
                #      downside to this is cannot make parent-child connection)
                found_ref = False
                for i in range(len(shear_list)):
                    child_z_true = self.get_z_true(shear_node, i)
                    child_z_bin  = self.get_wc_bin(child_z_true)

                    # check if children in shear list are in the water column
                    if (len(self.shear_node_dict[child_z_bin]) > 0):
                        
                        # determine what current node voc must be 
                        prev_ref_node = self.shear_node_dict[child_z_bin][-1]
                        prev_ref_voc  = prev_ref_node.voc
                        current_voc   = prev_ref_voc.add_shear(shear_list[i])
                        found_ref     = True 

                        # adjust the current shear node and forward propagate 
                        shear_node.set_voc(current_voc)
                        shear_node.set_parent(prev_ref_node)
                        shear_node.set_voc_delta(shear_list[i])
                        shear_node.set_fwd_prop(True)
                        self.shear_node_dict[z_bin].append(shear_node)
                        self.forward_propagation(shear_node, t, direction,
                            shear_list, child_z_bin)
                        break

                #################################
                # CASE 3.B: no abs ref, ascending, no measurement available
                #   + forward propagate deltas in time so that back propagation
                #     can be performed once an absolute reference is made 
                if not found_ref:
                    self.shear_node_dict[z_bin].append(shear_node)
                    self.forward_propagation(shear_node,t,direction,shear_list)


    def forward_propagation(self, parent, t, direction, shear_list, 
        skip_bin=None):
        """Performs forward propagation given a new DVL observation. 

        Args: 
            parent: the parent node 
            t: time 
            direction: descending or ascending
            shear_list: list of observed shears to propagate forward
        """
        # iterate through shear list to make new child shear nodes
        for i in range(self.START_FILTER, len(shear_list)-self.END_FILTER):

            # find new bin for child node 
            child_z_true = self.get_z_true(parent, i)
            child_z_bin  = self.get_wc_bin(child_z_true)
            child_voc    = parent.voc.subtract_shear(shear_list[i])

            # skip bin if specified (for ascending forward prop, CASE 3.B)
            if skip_bin!=child_z_bin:

                # create new shear node     
                child_shear_node = ShearNode(
                    z_true=child_z_true, 
                    z_bin=child_z_bin, 
                    t=t, 
                    water_col=self,
                    parent=parent,
                    voc=child_voc,
                    voc_delta=shear_list[i],
                    direction=direction,
                )

                # if velocity is forward propagated, mark the flag
                if not child_voc.is_none():
                    child_shear_node.set_fwd_prop(True)

                # only add child nodes with reasonable deltas 
                if  self.mag_filter(child_shear_node):
                    self.shear_node_dict[child_z_bin].append(child_shear_node)


    def back_propagation(self, back_prop_node, voc):
        """Performs back-propagation given a velocity value in absolute frame.
        """
        # update the given node with the given velocity
        back_prop_node.set_voc(voc)
        back_prop_node.set_bck_prop(True)
        self.forward_after_backward_propagation(back_prop_node)

        # check if need to propagate further
        parent = back_prop_node.parent
        if parent != None:
            if parent.voc.is_none():
                parent_voc = voc.add_shear(back_prop_node.voc_delta)
                self.back_propagation(parent, parent_voc)


    def forward_after_backward_propagation(self, back_node):
        """Propagate forward to children nodes after back propagation.
        """
        for child_node in back_node.children:
            if child_node.voc.is_none():
                child_voc = back_node.voc.subtract_shear(child_node.voc_delta)
                child_node.set_voc(child_voc)
                child_node.set_bck_prop(True)



class ShearNode(object):
    def __init__(self, z_true, z_bin, t, water_col, shear_list=[], parent=None,
        voc=OceanCurrent(), voc_ref=OceanCurrent(), voc_delta=OceanCurrent(),
        direction='descending', pitch=0, roll=0):
        """Represents a velocity shear measured at an instance in time from 
        the DVL. The ShearNode is the main data type that is managed by the 
        WaterColumn class. 

        Args:
            z_true: transducer depth in meters
            z_bin: water column bin in meters
            t: time in seconds
            water_col: water column object that ShearNode is a part of 
            shear_list: the velocity shears recorded by the DVL by comparing
                the dead-reckoned velocity and the DVL bin velocities.
        """
        self.z_true    = z_true
        self.z_bin     = z_bin
        self.t         = t
        self.water_col = water_col 
        self.children  = shear_list
        self.parent    = parent
        self.voc       = voc
        self.voc_ref   = voc_ref
        self.voc_delta = voc_delta
        self.direction = direction
        self.pitch     = pitch
        self.roll      = roll
        self.children  = []
        self.btm_track = False
        self.fwd_prop  = False
        self.bck_prop  = False
        if parent != None:
            parent.add_child(self)
        if not(direction!='descending' or direction!='ascending'):
            raise ValueError('bad direction value: %s' % direction)

    def __str__(self):
        # extract voc ref method used
        if self.btm_track:
            voc_type = 'btm-trck'
        elif self.fwd_prop:
            voc_type = 'fwd-prop'
        elif self.bck_prop:
            voc_type = 'bck-prop'
        else:
            voc_type = 'none'

        # return string for shear node
        return('Shear<z:%3d, t:%4d, %s, %8s>' % 
               (self.z_bin, self.t, str(self.voc), voc_type))

    def has_voc(self):
        """returns true iff ocean velocity is currently specified

        If not yet specified, back propagation will be called later """
        return(not self.voc is None)

    def set_voc(self,val):
        """updates ocean current velocity"""
        self.voc=val.copy()

    def set_voc_delta(self,val):
        """updates ocean current velocity"""
        self.voc_delta=val.copy()

    def set_parent(self,shear_node):
        """updates parent shear node"""
        self.parent=shear_node

    def set_btm_track(self,boolean):
        """updates bottom track flag"""
        self.btm_track = boolean

    def set_fwd_prop(self,boolean):
        """updates forward prop flag"""
        self.fwd_prop = boolean

    def set_bck_prop(self,boolean):
        """updates back prop flag"""
        self.bck_prop = boolean

    def add_child(self,child_node):
        """"""
        self.children.append(child_node)


    
