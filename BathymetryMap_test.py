# BathymetryMap_test.py
#
# Class for parsing and querying bathymetric data  
#   2020-07-10  zduguid@mit.edu         initial implementation


import seaborn as sns 
import numpy as np
import datetime
#import rasterio as rio
import importlib
#should be able to delete
#import earthpy as et
#import earthpy.plot as ep
import scipy
import scipy.signal
import os
import sys
import utm
from PIL import Image
from matplotlib import pyplot as plt 


class BathymetryMap(object):
    def __init__(self, filepath=None, latlon_format=None, crop=None, name=None, 
        xlabel=None, ylabel=None, tick_format=None, num_ticks=None, 
        slope_max=None, depth_max=None, depth_filter=None, meta_dict=None):
        """TODO
        """
        # constants
        self.DEG_TO_RAD = np.pi/180
        self.RAD_TO_DEG = 1/self.DEG_TO_RAD

        # scharr operator for computing gradients: Gx + j*Gy
        self.SCHARR = np.array([[ +3 - 3j,  +10   , +3 + 3j],
                                [    -10j,   0    ,    +10j],
                                [ -3 - 3j,  -10   , -3 + 3j]]) / 32

        # set default values upon initialization 
        self.filepath       = filepath
        self.latlon_format   = latlon_format
        self.crop           = crop
        self.name           = name
        self.xlabel         = xlabel
        self.ylabel         = ylabel
        self.tick_format    = tick_format
        self.num_ticks      = num_ticks
        self.slope_max      = slope_max
        self.depth_max      = depth_max
        self.depth_filter   = depth_filter

        # update values if meta data is specified 
        if meta_dict:
            self.filepath       = meta_dict['filepath']
            self.latlon_format   = meta_dict['latlon_format']
            self.crop           = meta_dict['crop']
            self.name           = meta_dict['name']
            self.xlabel         = meta_dict['xlabel']
            self.ylabel         = meta_dict['ylabel']
            self.tick_format    = meta_dict['tick_format']
            self.num_ticks      = meta_dict['num_ticks']
            self.slope_max      = meta_dict['slope_max']
            self.depth_max      = meta_dict['depth_max']
            self.depth_filter   = meta_dict['depth_filter']


    def parse_bathy_file(self):
        """TODO

        TIF files have helpful meta data encoded in them, such as WGS84 UTM grids:  
        https://www.spatialreference.org/ref/epsg/4326/
        """
        with rio.open(self.filepath) as dem:
            self.meta      = dem.meta
            self.raw_h     = dem.height
            self.raw_w     = dem.width
            self.height    = dem.height 
            self.width     = dem.width
            self.raw       = np.array(dem.read()[0], dtype=float)
            self.bathy     = np.copy(self.raw).astype(np.float64)
            self.nodata    = dem.meta['nodata']
            self.bounds    = dem.bounds
            self.left      = self.bounds.left
            self.right     = self.bounds.right
            self.top       = self.bounds.top
            self.bottom    = self.bounds.bottom
            self.transform = dem.transform
            self.driver    = dem.driver
            self.count     = dem.count
            self.dtype     = self.raw.dtype
            self.crs       = dem.crs
            self.res       = dem.res
            self.x_res     = dem.res[0]
            self.y_res     = dem.res[1]

        # filter out no data values and values above sea level 
        self.bathy[self.bathy>0] = np.NaN
        self.bathy[self.bathy==self.nodata] = np.NaN

        # filter out depth filter
        #   + depth filter actually mutates bathymetry array, whereas the 
        #     'depth_max' and 'slope_max' parameters are only used for 
        #     plotting purposes and do not change the underlying array 
        if self.depth_filter:
            self.bathy[-self.bathy > self.depth_filter] = np.NaN

        # convert latlon format to utm format
        if self.latlon_format:
            self.fix_aspect_ratio()

        # perform crop of bathymetry if specified 
        if self.crop:
            self.fix_crop()

        # # otherwise extract default height, width, and bounds
        # if (not self.latlon_format) and (not self.crop):
        #     self.left   = self.bounds.left
        #     self.right  = self.bounds.right
        #     self.top    = self.bounds.top
        #     self.bottom = self.bounds.bottom
        #     self.width  = self.raw_w
        #     self.height = self.raw_h

        # compute gradient of the depth file 
        grad = scipy.signal.convolve2d(
            self.bathy, 
            self.SCHARR, 
            boundary='symm', 
            mode='same'
        ) / (np.max([self.x_res, self.y_res]))

        # compute slope and orientation from the gradient
        self.slope  = np.arctan(np.absolute(grad))*self.RAD_TO_DEG
        self.orient = np.angle(grad)*self.RAD_TO_DEG
        self.depth  = -np.copy(self.bathy)

        # # get the bounds of the bathymetry file in UTM coordinates 
        # self.utm_left,  self.utm_bottom, _ = \
        #     self.get_utm_coords_from_bathy(self.bottom, self.left)
        # self.utm_right, self.utm_top, _ = \
        #     self.get_utm_coords_from_bathy(self.top,    self.right)

        # # TODO
        # print(self.utm_right - self.utm_left)
        # print(self.width*np.round(self.x_res))
        # print()
        # print(self.utm_top - self.utm_bottom)
        # print(self.height*self.y_res)


    def fix_aspect_ratio(self):
        """TODO
        """
        # compute physical distance spanned by the lat range and lon range
        self.left   = self.bounds.left
        self.right  = self.bounds.right
        self.top    = self.bounds.top
        self.bottom = self.bounds.bottom
        middle_lat  = self.bottom +  (self.top   - self.bottom)/2
        middle_lon  = self.left   +  (self.right - self.left)/2
        _, y1, _, _ = utm.from_latlon(self.bottom, middle_lon)
        _, y2, _, _ = utm.from_latlon(self.top,    middle_lon)
        x1, _, _, _ = utm.from_latlon(middle_lat,  self.left)
        x2, _, _, _ = utm.from_latlon(middle_lat,  self.right)
        range_x     = x2 - x1
        range_y     = y2 - y1

        # get new width and height values 
        self.width = int(np.round(
            (self.raw_h + (range_x/range_y)*self.raw_w) / 
            (range_y/range_x  +  range_x/range_y)
        ))
        self.height = int(np.round(
            (range_y/range_x)*self.width
        ))

        # recompute x and y resolutions 
        self.x_res = range_x/self.width
        self.y_res = range_y/self.height

        # perform array resizing 
        self.bathy = np.array(Image.fromarray(self.bathy).resize(
            (self.width, self.height)
        )).astype(np.float64)


    def convert_to_utm(self):
        """TODO
        """
        pass


    def fix_crop(self):
        """TODO
        """
        # crop values are given by array indices not physical coordinates
        y1, y2, x1, x2 = self.crop
        y1 = max(y1, 0)
        y2 = min(y2, self.bathy.shape[0])
        x1 = max(x1, 0)
        x2 = min(x2, self.bathy.shape[1])

        # crop the bathymetry array
        # TODO
        # print(self.bathy.shape)
        self.bathy = np.copy(self.bathy[y1:y2, x1:x2])

        # extract bounds (units of bathymetry file, [wgs84] or [utm])
        old_left, old_right  = self.left, self.right
        old_top,  old_bottom = self.top,  self.bottom

        # extract original size of array  
        old_width            = self.width 
        old_height           = self.height 

        # TODO
        # print(self.bathy.shape)
        # print(old_width, old_height)
        # print(y1/old_height, y2/old_height)
        range_x              = old_right  - old_left
        range_y              = old_top    - old_bottom

        # compute new width, height, and bounds
        self.width  = x2 - x1
        self.height = y2 - y1 
        self.left   = old_left   + (x1/old_width)  * range_x
        self.right  = old_left   + (x2/old_width)  * range_x
        self.top    = old_bottom + (y2/old_height) * range_y
        self.bottom = old_bottom + (y1/old_height) * range_y

        # TODO
        # print(self.crop)
        # print()
        # print("left:   %0.3f --> %0.3f" % (old_left, self.left))
        # print("right:  %0.3f --> %0.3f" % (old_right, self.right))
        # print("bottom: %0.3f --> %0.3f" % (old_bottom, self.bottom))
        # print("top:    %0.3f --> %0.3f" % (old_top, self.top))
        # print()
        # print(range_y, range_x)
        # print(old_height, old_width )


    @classmethod
    def get_utm_coords_from_glider_lat_lon(cls, m_lat, m_lon): 
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


    def get_ticks(self):
        """TODO
        """
        xticks  = np.arange(
            self.width / self.num_ticks/2, 
            self.width, 
            self.width / self.num_ticks
        )
        yticks  = np.arange(
            self.height /self.num_ticks/2, 
            self.height, 
            self.height /self.num_ticks
        )
        xlabels = [self.tick_format %
                     np.round((self.right-self.left)*
                        (i/self.width) + self.left, 5) 
                     for i in xticks]
        ylabels = [self.tick_format % 
                     np.round((self.bottom-self.top)*
                        (i/self.height) + self.top, 5) 
                     for i in yticks]
        return(xticks, xlabels, yticks, ylabels)


    def set_ticks_and_tick_labels(self, ax):
        """TODO
        """
        xticks, xlabels, yticks, ylabels = self.get_ticks()   
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels)
        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels)

# currently uses the earthpy module 
#ep.plot_bands()
    # def make_surface_plot(self, ax, bathy_array, bathy_variable, bathy_cmap, 
    #     add_xlabel=True, add_ylabel=True):
    #     """TODO
    #     """
    #     sns.set(font_scale = 1.5)
    #     ep.plot_bands(
    #         bathy_array, 
    #         cmap=bathy_cmap,
    #         title=bathy_variable,
    #         ax=ax,
    #         scale=False
    #     )
    #     plt.suptitle(self.name, fontweight='bold')
    #     if add_xlabel:
    #         ax.set_xlabel(self.xlabel)
    #     if add_ylabel:
    #         ax.set_ylabel(self.ylabel)
    #     self.set_ticks_and_tick_labels(ax)


    def plot_depth_map(self, ax=None, add_xlabel=True, add_ylabel=True):
        """TODO
        """
        # create new plot if not already specified
        save_plot = False
        if not ax:
            sns.set(font_scale = 1.5)
            fig, ax = plt.subplots(figsize=(10,10))
            plt.suptitle(self.name, fontweight='bold')
            save_plot = True

        # perform depth filter if specified 
        depth = np.copy(self.depth)
        if self.depth_max:
            depth[depth > self.depth_max] = self.depth_max

        # generate plot
        self.make_surface_plot(ax, depth, "Depth [m]", "viridis_r", 
            add_xlabel, add_ylabel)
        if save_plot:
            plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


    def plot_slope_map(self, ax=None, add_xlabel=True, add_ylabel=True):
        """TODO
        """
        # create new plot if not already specified
        save_plot = False
        if not ax:
            sns.set(font_scale = 1.5)
            fig, ax = plt.subplots(figsize=(10,10))
            plt.suptitle(self.name, fontweight='bold')
            save_plot = True

        # perform slope filter if specified
        slope = np.copy(self.slope)
        if self.slope_max:
            slope[slope > self.slope_max] = self.slope_max

        # generate plot
        self.make_surface_plot(ax, slope, "Slope [deg]", "inferno_r",
            add_xlabel, add_ylabel)
        if save_plot:
            plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


    def plot_orientation_map(self, ax=None, add_xlabel=True, add_ylabel=True):
        """TODO
        """
        # create new plot if not already specified
        save_plot = False
        if not ax:
            sns.set(font_scale = 1.5)
            fig, ax = plt.subplots(figsize=(10,10))
            plt.suptitle(self.name, fontweight='bold')
            save_plot = True

        # generate plot
        self.make_surface_plot(ax, self.orient, "Orientation [deg]", 
            "twilight_shifted", add_xlabel, add_ylabel)
        if save_plot:
            plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


    def plot_three_factors(self):
        """TODO
        """
        sns.set(font_scale = 1.5)
        fig, ax = plt.subplots(2,3, figsize=(15,8), 
            gridspec_kw={'height_ratios': [2, 1]})
        fig.subplots_adjust(hspace=.4)
        fig.subplots_adjust(wspace=.3)
        plt.suptitle(self.name, fontweight='bold')

        # add three-factor plots to the top row
        self.plot_depth_map(      ax[0,0], add_xlabel=True, add_ylabel=True)
        self.plot_slope_map(      ax[0,1], add_xlabel=True, add_ylabel=False)
        self.plot_orientation_map(ax[0,2], add_xlabel=True, add_ylabel=False)

        # plot kernel densities and add labels
        sns.kdeplot(self.depth.flatten(), shade=True, ax=ax[1,0], linewidth=3)
        sns.kdeplot(self.slope.flatten(), shade=True, ax=ax[1,1], linewidth=3)
        sns.kdeplot(self.orient.flatten(),shade=True, ax=ax[1,2], linewidth=3)
        ax[1,0].set_ylabel('Kernel Density')
        ax[1,0].set_xlabel('Depth [m]')
        ax[1,1].set_xlabel('Slope [deg]')
        ax[1,2].set_xlabel('Orientation [deg]')
        plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


    def plot_depth_contours(self, ax=None):
        """TODO
        """
        if not ax:
            sns.set(font_scale = 1.5)
            fig, ax = plt.subplots(figsize=(10,10))
        interval     = 50
        max_depth    = np.nanmax(self.depth)
        min_depth    = np.nanmin(self.depth)
        max_interval = max_depth - max_depth%interval + interval
        min_interval = min_depth - min_depth%interval
        num_interval = (max_interval - min_interval) / interval + 1
        levels = np.linspace(min_interval, max_interval, num_interval)
        widths = [2 for _ in levels]
        styles = ['solid' for _ in widths]
        colors = plt.cm.Purples(np.array(levels)/(1.50*np.max(levels)))
        cp1 = ax.contourf(
            self.depth,
            levels=levels, 
            linestyles=styles, 
            colors=colors,
        )
        cbar = fig.colorbar(cp1, ax=ax)
        cbar.ax.set_ylabel('Depth [m]')
        plt.gca().invert_yaxis()
        self.set_ticks_and_tick_labels(ax)
        plt.axis('equal')
        plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')
