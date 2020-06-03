BathyData = {


    ##################################################
    # Kolumbo Data Subset
    ##################################################
    'Kolumbo' : {
        'file'  : "/Users/zduguid/Dropbox (MIT)/MIT-WHOI/Kolumbo cruise 2019/Grids/kolumbo bathymetry.tif",
        'AR'    : True,
        'crop'  : None,
        'title' : 'Kolumbo Volcano, Santorini, Greece',
        'xlabel': 'Longitude [deg]',
        'ylabel': 'Latitude [deg]',
        'ticks' : '%.3f',
        'num_ticks' : 5,
        'slope_max' : None,
        'depth_max' : None
    },


    ##################################################
    # Kolumbo Data Full
    ##################################################
    'Kolumbo_full' : {
        'file'  : "/Users/zduguid/Dropbox (MIT)/MIT-WHOI/Kolumbo cruise 2019/zduguid/Kolumbo _Ios_10m_grid.tif",
        'AR'    : True,
        'crop'  : None,
        'title' : 'Kolumbo Volcano, Santorini, Greece',
        'xlabel': 'Longitude [deg]',
        'ylabel': 'Latitude [deg]',
        'ticks' : '%.3f',
        'num_ticks' : 5,
        'slope_max' : None,
        'depth_max' : None
    },


    ##################################################
    # Buzzards Bay Data
    ##################################################
    'BuzzardsBay' : {
        'file'  : "/Users/zduguid/Dropbox (MIT)/MIT-WHOI/NSF Arctic NNA/Environment-Data/BuzzardsBay-10m/BuzzBay_10m.tif",
        'AR'    : False,
        'crop'  : [1500, 5740, 1500, 6200],
            # crop  = [top, bot, left, right]
            # bathy = bathy_im[top:bot, left:right]
        'title' : 'Buzzards Bay, MA',
        'xlabel': 'UTM Zone 19',
        'ylabel': '',
        'ticks' : '%.2g',
        'slope_max' : 8,
        'depth_max' : 35,
        'num_ticks' : 5,
        'meta'  : {
            'utm_zone' : 19,
            'coordinate_system' : 'North American Datum of 1983 and the North American Vertical Datum of 1988',
            'link' : 'https://www.sciencebase.gov/catalog/item/5a4649b8e4b0d05ee8c05486'
        }
    },


    ##################################################
    # Costa Rica Data Area1
    ##################################################
    'CostaRica_area1' : {
        'file'  : "/Users/zduguid/Dropbox (MIT)/MIT-WHOI/18-Falkor Costa Rica/Bathy for Sentinel survey/Bathy_for_last_Sentinel_missions.tif",
        'AR'    : False,
        'crop'  : None,
            # crop  = [top, bot, left, right]
            # bathy = bathy_im[top:bot, left:right]
        'title' : 'Costa Rica',
        'xlabel': 'UTM Zone 16',
        'ylabel': '',
        'ticks' : '%.4g',
        'slope_max' : None,
        'depth_max' : None,
        'num_ticks' : 3,
        'meta'  : {
            'utm_zone' : '16N',
        }
    },


    ##################################################
    # Costa Rica Data Area3 
    ##################################################
    'CostaRica_area3' : {
        'file'  : "/Users/zduguid/Documents/MIT-WHOI/MERS/Cook/cook/bathymetry/jaco-scar-depths.tif",
        'AR'    : False,
        'crop'  : [75, 550, 600, 1200],
            # crop  = [top, bot, left, right]
            # bathy = bathy_im[top:bot, left:right]
        'title' : 'Costa Rica',
        'xlabel': 'UTM Zone 16',
        'ylabel': '',
        'ticks' : '%.4g',
        'slope_max' : None,
        'depth_max' : 1000,
        'num_ticks' : 3,
        'meta'  : {
            'utm_zone' : '16N',
        }
    },


    ##################################################
    # Costa Rica Data Full
    ##################################################
    'CostaRica_full' : {
        'file'  : "/Users/zduguid/Documents/MIT-WHOI/MERS/Cook/cook/bathymetry/jaco-scar-depths.tif",
        'AR'    : False,
        'crop'  : None,
            # crop  = [top, bot, left, right]
            # bathy = bathy_im[top:bot, left:right]
        'title' : 'Costa Rica',
        'xlabel': 'UTM Zone 16',
        'ylabel': '',
        'ticks' : '%.4g',
        'slope_max' : None,
        'depth_max' : None,
        'num_ticks' : 3,
        'nodata' : 255,
        'meta'  : {
            'utm_zone' : '16N',
        }
    },


    ##################################################
    # Hawaii Data Small
    ##################################################
    'Hawaii_small' : {
        'file'  : "/Users/zduguid/Documents/MIT-WHOI/MERS/Cook/cook/bathymetry/HI-small.tif",
        'AR'    : True,
        'crop'  : None,
            # crop  = [top, bot, left, right]
            # bathy = bathy_im[top:bot, left:right]
        'title' : 'Hawaii',
        'xlabel': 'Lon [deg]',
        'ylabel': 'Lat [deg]',
        'ticks' : '%.4g',
        'slope_max' : None,
        'depth_max' : None,
        'num_ticks' : 3,
        'nodata' : None,
        'meta'  : {
            'utm_zone' : '16N',
        }
    },


    ##################################################
    # Hawaii Data Small
    ##################################################
    'Hawaii_all' : {
        'file'  : "/Users/zduguid/Documents/MIT-WHOI/MERS/Cook/cook/bathymetry/HI-all.tif",
        'AR'    : True,
        'crop'  : None,
            # crop  = [top, bot, left, right]
            # bathy = bathy_im[top:bot, left:right]
        'title' : 'Hawaii',
        'xlabel': 'Lon [deg]',
        'ylabel': 'Lat [deg]',
        'ticks' : '%.4g',
        'slope_max' : None,
        'depth_max' : None,
        'num_ticks' : 3,
        'nodata' : None,
        'meta'  : {
            'utm_zone' : '16N',
        }
    },


    ##################################################
    # Template Data 
    ##################################################
    'template' : {
        'file'  : "path/to/file.tif",
        'AR'    : False,
        'crop'  : None,
            # crop  = [top, bot, left, right]
            # bathy = bathy_im[top:bot, left:right]
        'title' : 'TODO',
        'xlabel': 'TODO',
        'ylabel': 'TODO',
        'ticks' : '%.2g',
        'slope_max' : None,
        'depth_max' : None,
        'num_ticks' : 3,
        'meta'  : None,
    },
    
}