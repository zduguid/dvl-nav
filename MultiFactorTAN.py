import numpy as np 
import scipy


class BottomTrackPoint(object):
    def __init__(self, time_index, beam_num, ship_x, ship_y, ship_z, aug_x, aug_y, aug_z): 
        """TODO
        Coordinate system:
            (+) x = East 
            (+) y = North 
            (+) z = Downwards
        """
        self.time_index = time_index
        self.beam_num   = beam_num
        self.ship_x  = ship_x
        self.ship_y  = ship_y
        self.ship_z  = ship_z
        self.aug_x   = aug_x
        self.aug_y   = aug_y
        self.aug_z   = aug_z
        self.earth_x = ship_x + aug_x
        self.earth_y = ship_y + aug_y
        self.earth_z = ship_z + aug_z
        
    
    def __str__(self):
        """TODO"""
        def num_to_str(num):
            if   num  < 0 and abs(num) < 10: space = ' '
            elif num  < 0 and abs(num) > 10: space = ''
            elif num >= 0 and abs(num) < 10: space = '  '
            elif num >= 0 and abs(num) > 10: space = ' '
            return("%s%.2f" % (space, num))
        
        return('Beam%d' % self.beam_num   + 
               '<%4d, ' % self.time_index + 
               '%s, %s, %s>' % tuple([num_to_str(num) for num in [self.ship_x, 
                                                                  self.ship_y, 
                                                                  self.ship_z]]))
    @property
    def x(self): 
        return(self.earth_x)
    
    @property
    def y(self): 
        return(self.earth_y)
    
    @property
    def z(self): 
        return(self.earth_z)
    
    @property
    def pose(self):
        return(np.array([[self.x], [self.y], [self.z]]))

    

# collect set of bottom track point
class PointCloud(object):
    def __init__(self, GRID_RESOLUTION):
        """TODO
        
        x and y positions are given in Earth coordinate frame
        """
        # constants 
        self.GRID_RESOLUTION = GRID_RESOLUTION
        # self.GRID_RESOLUTION = 10
        self.MIN_DELTA_T     = 1
        # self.MIN_SPATIAL_RES = 0.5*self.GRID_RESOLUTION
        self.MIN_SPATIAL_RES = 0.5*GRID_RESOLUTION
        # self.MIN_NUM_PINGS   = 24
        self.MIN_NUM_PINGS   = 12        
        # self.MIN_NUM_PINGS   = 8
        # self.MIN_NUM_PINGS   = 6 
        self.MIN_PITCH       = 10
        self.MIN_OFFSET      = 2
        self.RAD_TO_DEG      = 180/np.pi 
        self.DEG_TO_RAD      = 1/self.RAD_TO_DEG
        
        # initialize dynamic attributes
        self.clear()
        
    def __str__(self):
        """TODO"""
        delta_x = self.max_x-self.min_x
        delta_y = self.max_y-self.min_y
        if np.isnan(delta_x): delta_x_str = ' nan'
        else:                 delta_x_str = '%4d' % delta_x
        if np.isnan(delta_y): delta_y_str = ' nan'
        else:                 delta_y_str = '%4d' % delta_y
            
        return('PC< t: %4d,  n: %4d,  x: %s,  y: %s>' % 
               (t, len(self.point_list), delta_x_str, delta_y_str))


    def Qx(self, phi):
        """Orthogonal rotation matrix about x-axis by angle phi
        """
        return(np.array([[           1,            0,            0],
                         [           0,  np.cos(phi), -np.sin(phi)],
                         [           0,  np.sin(phi),  np.cos(phi)]]))


    def Qy(self, phi):
        """Orthogonal rotation matrix about y-axis by angle phi
        """
        return(np.array([[ np.cos(phi),            0,  np.sin(phi)],
                         [           0,            1,            0],
                         [-np.sin(phi),            0,  np.cos(phi)]]))


    def Qz(self, phi):
        """Orthogonal rotation matrix about z-axis by angle phi
        """
        return(np.array([[ np.cos(phi), -np.sin(phi),            0],
                         [ np.sin(phi),  np.cos(phi),            0],
                         [           0,            0,            1]]))
        
        
    def clear(self):
        """Clears all point cloud measurements
        """
        self.point_list = []
        self.first_time = np.nan
        self.last_time  = np.nan
        self.min_x      = np.nan
        self.max_x      = np.nan
        self.min_y      = np.nan
        self.max_y      = np.nan
    
    
    def add_point(self, bt_point):
        """TODO
        """        
        # TODO instead of moving window of measurements, "clear" the point cloud
        # + this is done because previous feature detections may lead to nav correction and then 
        #   the vehicle coordinate system will change 
        # + if a moving window approach is desired, only measurements will have to be updated 
        #   retroactively after the TAN algorithm updates vehicle position 
        
        # clear the point cloud if old measurements have become stale
        if not (np.isnan(self.last_time)):
            if (bt_point.time_index - self.last_time) > self.MIN_DELTA_T:
                self.clear()
        
        # dont include points below minimum offset distance
        if bt_point.ship_z < self.MIN_OFFSET:
            return()
        
        # add the new bottom track point and update the dynamic cloud attributes
        self.point_list.append(bt_point)
        self.first_time = np.nanmin([self.first_time, bt_point.time_index])
        self.last_time  = np.nanmax([self.last_time,  bt_point.time_index])
        self.min_x = np.nanmin([self.min_x, bt_point.x])
        self.max_x = np.nanmax([self.max_x, bt_point.x])
        self.min_y = np.nanmin([self.min_y, bt_point.y])
        self.max_y = np.nanmax([self.max_y, bt_point.y])
        
    
    def get_factors(self):
        """TODO"""
        # return none point cloud doesn't meet spatial extent or size requirements 
        if ((not np.max([self.max_x-self.min_x, self.max_y-self.min_y]) > self.MIN_SPATIAL_RES) or 
            (len(self.point_list) < self.MIN_NUM_PINGS)):
            return(np.nan, np.nan, np.nan)
        
        # fit a plan to point cloud using least squares formulation
        A = np.array([[bt_point.x, bt_point.y, 1] for bt_point in self.point_list])
        b = np.array([bt_point.z for bt_point in self.point_list])
        fit, residual, rnk, s = scipy.linalg.lstsq(A,b)

        # extract coefficients from the least squares formulation
        # fit = [a, b, c] s.t. z = ax + by + c
        a,b,c  = tuple(fit)
        mid_x  = np.mean([bt_point.aug_x for bt_point in self.point_list])
        mid_y  = np.mean([bt_point.aug_y for bt_point in self.point_list])
        bathy_depth  = a*mid_x + b*mid_y + c
        bathy_slope  = np.arctan((a**2 + b**2)**0.5)*self.RAD_TO_DEG
        bathy_orient = np.arctan2(a, b)*self.RAD_TO_DEG
        
        # clear the point cloud and return the factors 
        self.clear()
        return(bathy_depth, bathy_slope, bathy_orient)