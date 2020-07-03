# micron_plotter.py
# 
# Plotting utilities for Micron Sonar
#   2020-05-22  zduguid@mit.edu         initial implementation  

import math
import datetime
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.cm as cm
import matplotlib.pyplot as plt


unit_name = {"sentinel" : "Unit 250",
             "unit_770" : "Unit 770" }


###############################################################################
# PLOT PROFILE
###############################################################################
def plot_profile(ts, glider, save_name=None):
    # pitch data
    sns.set(font_scale = 1.5)
    pitch = ts.df['pitch']
    line_plot = pitch.plot(figsize=(15,8), linewidth=3, color='tab:green')

    # depth data
    depth     = -1 * ts.df['depth']
    line_plot = depth.plot(figsize=(15,8), linewidth=3, color='tab:orange')

    # compute altitude estimate from the four vertical range estimates
    # - does not account for pitch and roll of the vehicle 
    h1 = ts.df['btm_beam0_range']
    h2 = ts.df['btm_beam1_range']
    h3 = ts.df['btm_beam2_range']
    h4 = ts.df['btm_beam3_range']
    altitude = depth - ((h1*h2)/(h1 + h2) + (h3*h4)/(h3 + h4))
    altitude.plot(linewidth=3, color='tab:blue', zorder=1)

    # bottom_track slant range data 
    bt_ranges = [
        'btm_beam0_range',
        'btm_beam1_range',
        'btm_beam2_range',
        'btm_beam3_range'
    ]
    bt_colors = ['powderblue','darkturquoise','lightsteelblue','deepskyblue']
    for i in range(len(bt_ranges)):
        bt_range  = depth - ts.df[bt_ranges[i]]
        bt_range.plot(linewidth=1, color=bt_colors[i], zorder=0)

    # plot moments in time where the glider gets dangerously close to bottom 
    window = 5
    danger = 20
    danger = ts.df[(ts.df.btm_beam0_range < danger) & 
                    (ts.df.btm_beam1_range < danger) & 
                    (ts.df.btm_beam2_range < danger) & 
                    (ts.df.btm_beam3_range < danger)]
    for time_stamp in danger.index:
        plt.axvspan(time_stamp, time_stamp + pd.Timedelta(seconds=window), 
            color='tab:red', alpha=0.05)
            
    # plotting labels 
    dt = datetime.datetime.fromtimestamp(ts.df.time[0]).replace(microsecond=0)
    plt.legend(['Pitch [deg]', 'Depth [m]', 'Altitude [m]', 
        'Vertical Ranges [m]'], fontsize='small', loc='lower left',
        framealpha=1)
    plt.suptitle('Deployment Profile', fontweight='bold')
    plt.title('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),))
    plt.ylabel('Depth [m]')
    plt.xlabel('Time')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT ODOMETRY
###############################################################################
def plot_odometry(ts, glider, save_name=None):
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(10,8))
    sns.scatterplot(
        x=ts.df.rel_pos_x,
        y=ts.df.rel_pos_y,
        palette='viridis_r',
        hue=ts.df.depth,
        linewidth=0,
        s=10,
        data=ts.df)
    dt = datetime.datetime.fromtimestamp(ts.df.time[0]).replace(microsecond=0)
    plt.axis('equal')
    plt.suptitle('DVL Odometry', fontweight='bold')
    plt.title('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),))
    plt.xlabel('x position [m]')
    plt.ylabel('y position [m]')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT ODOMETRY (DEAD-RECKONED)
###############################################################################
def plot_m_odometry_dr(ts_flight, glider, save_name=None):
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(10,8))
    sns.scatterplot(
        ts_flight.df.m_gps_fix_x_lmc, 
        ts_flight.df.m_gps_fix_y_lmc, 
        marker='X',
        color='tab:red', 
        s=300
    )
    sns.scatterplot(
        x=ts_flight.df.m_x_lmc,
        y=ts_flight.df.m_y_lmc,
        palette='viridis_r',
        hue=ts_flight.df.m_depth,
        linewidth=0,
        s=10,
        data=ts_flight.df
    )
    dt = datetime.datetime.fromtimestamp(
        ts_flight.df.m_present_time[0]).replace(microsecond=0)
    plt.axis('equal')
    plt.suptitle('Dead Reckoned Trajectory', fontweight='bold')
    plt.title('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),))
    plt.xlabel('x position [m]')
    plt.ylabel('y position [m]')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT ODOMETRY AND DEAD-RECKONED
###############################################################################
def plot_odometry_and_dr_utm(df_all, glider, save_name=None):
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(10,8))
    sns.scatterplot(
        x=df.utm_dr_x,
        y=df.utm_dr_y,
        color='tab:blue',
        label='Dead-Reckoned',
        linewidth=0,
        s=8,
        data=df_all
    )
    sns.scatterplot(
        x=df_all.utm_odo_x,
        y=df_all.utm_odo_y,
        color='tab:orange',
        label='DVL Odometry',
        linewidth=0,
        s=8,
        data=df_all
    )
    sns.scatterplot(
        x=df_all.utm_gps_x, 
        y=df_all.utm_gps_y,
        marker='X',
        color='tab:red', 
        label='GPS Fix',
        s=200,
        data=df_all,
    )
    sns.scatterplot(
        x=df_all.utm_wpt_x, 
        y=df_all.utm_wpt_y,
        marker='o',
        color='tab:green', 
        label='Waypoint Target',
        s=100,
        data=df_all,
    )
    # TODO -- can add marker for when TAN is able to recognize a feature
    lgnd = ax.legend(frameon=True)
    lgnd.legendHandles[0]._sizes = [60]
    lgnd.legendHandles[1]._sizes = [60]
    lgnd.legendHandles[2]._sizes = [200]
    if len(lgnd.legendHandles) == 4:
        lgnd.legendHandles[3]._sizes = [100]
    dt = df.index[0].replace(microsecond=0)
    plt.axis('equal')
    plt.suptitle('DVL Odometry', fontweight='bold')
    plt.title('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),))
    plt.xlabel('x position [m]')
    plt.ylabel('y position [m]')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT ODOMETRY AND DEAD-RECKONED
###############################################################################
def plot_odometry_and_dr(ts_pd0, ts_dbd_all, glider, save_name=None):
    # sub-select a portion of glider flight computer variables
    start_t = datetime.datetime.fromtimestamp(ts_pd0.df.time[0])
    end_t   = datetime.datetime.fromtimestamp(ts_pd0.df.time[-1])
    dur     = end_t - start_t 
    df_dbd  = ts_dbd_all.df[str(start_t):str(end_t)].copy()

    # initialize the plot
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(10,8))
    sns.scatterplot(
        x=df_dbd.m_x_lmc,
        y=df_dbd.m_y_lmc,
        color='tab:blue',
        label='Dead-Reckoned',
        linewidth=0,
        s=8,
        data=df_dbd
    )
    sns.scatterplot(
        x=ts_pd0.df.rel_pos_x,
        y=ts_pd0.df.rel_pos_y,
        color='tab:orange',
        label='DVL Odometry',
        linewidth=0,
        s=8,
        data=ts_pd0.df
    )
    sns.scatterplot(
        x=df_dbd.m_gps_x_lmc, 
        y=df_dbd.m_gps_y_lmc,
        marker='X',
        color='tab:red', 
        label='GPS Fix',
        s=200,
        data=df_dbd,
    )
    # TODO -- can add marker for when TAN is able to recognize a feature
    lgnd = ax.legend(frameon=True)
    lgnd.legendHandles[0]._sizes = [60]
    lgnd.legendHandles[1]._sizes = [60]
    lgnd.legendHandles[2]._sizes = [200]
    if len(lgnd.legendHandles) == 4:
        lgnd.legendHandles[3]._sizes = [100]
    dt = df_dbd.index[0].replace(microsecond=0)
    plt.axis('equal')
    plt.suptitle('DVL Odometry', fontweight='bold')
    plt.title('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),))
    plt.xlabel('x position [m]')
    plt.ylabel('y position [m]')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT PROFILE AND ODOMETRY
###############################################################################
def plot_profile_and_odometry(ts, glider, save_name=None):
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(1,2, figsize=(15,8))

    # profile
    depth = -1 * ts.df['depth']
    line_plot = depth.plot(figsize=(15,8), linewidth=3, color='tab:orange', ax=ax[0])

    # compute altitude estimate from the four vertical range estimates
    # - does not account for pitch and roll of the vehicle 
    h1 = ts.df['btm_beam0_range']
    h2 = ts.df['btm_beam1_range']
    h3 = ts.df['btm_beam2_range']
    h4 = ts.df['btm_beam3_range']
    altitude = depth - ((h1*h2)/(h1 + h2) + (h3*h4)/(h3 + h4))
    altitude.plot(linewidth=3, color='tab:blue', zorder=1, ax=ax[0])

    # bottom_track slant range data 
    bt_ranges = [
        'btm_beam0_range',
        'btm_beam1_range',
        'btm_beam2_range',
        'btm_beam3_range'
    ]
    bt_colors = ['powderblue','darkturquoise','lightsteelblue','deepskyblue']
    for i in range(len(bt_ranges)):
        bt_range  = depth - ts.df[bt_ranges[i]]
        bt_range.plot(linewidth=1, color=bt_colors[i], zorder=0, ax=ax[0])
    ax[0].set_ylabel('depth [m]')
    ax[0].set_xlabel('time')
    ax[0].set_title('Dive Profile')
    ax[0].legend(['Depth [m]', 'Altitude [m]'], fontsize='small', 
        loc='lower left', framealpha=0.5)

    # odometry
    sns.scatterplot(
        x=ts.df.rel_pos_x,
        y=ts.df.rel_pos_y,
        palette='viridis_r',
        hue=ts.df.depth,
        linewidth=0,
        s=10,
        data=ts.df,
        ax=ax[1])
    dt = datetime.datetime.fromtimestamp(ts.df.time[0]).replace(microsecond=0)
    plt.axis('equal')
    plt.suptitle('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),), fontweight='bold')
    plt.title('DVL Odometry')
    plt.xlabel('x position [m]')
    plt.ylabel('y position [m]')
    plt.legend(loc='lower right')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT PROFILE AND ODOMETRY AND DEAD-RECKONED
###############################################################################
def plot_profile_and_odometry_and_dr(ts_pd0,ts_dbd_all, use_wc=True,
    save_name=None):
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(1,2, figsize=(15,8))


    #############################################
    # PLOT PROFILE ##############################
    #############################################
    depth = -1 * ts_pd0.df['depth']
    line_plot = depth.plot(figsize=(15,8), linewidth=3, color='tab:orange', ax=ax[0])

    # compute altitude estimate from the four vertical range estimates
    # - does not account for pitch and roll of the vehicle 
    h1 = ts_pd0.df['btm_beam0_range']
    h2 = ts_pd0.df['btm_beam1_range']
    h3 = ts_pd0.df['btm_beam2_range']
    h4 = ts_pd0.df['btm_beam3_range']
    altitude = depth - ((h1*h2)/(h1 + h2) + (h3*h4)/(h3 + h4))
    altitude.plot(linewidth=3, color='tab:blue', zorder=1, ax=ax[0])

    # bottom_track slant range data 
    bt_ranges = [
        'btm_beam0_range',
        'btm_beam1_range',
        'btm_beam2_range',
        'btm_beam3_range'
    ]
    bt_colors = ['powderblue','darkturquoise','lightsteelblue','deepskyblue']
    for i in range(len(bt_ranges)):
        bt_range  = depth - ts_pd0.df[bt_ranges[i]]
        bt_range.plot(linewidth=1, color=bt_colors[i], zorder=0, ax=ax[0])
    ax[0].set_ylabel('Depth [m]')
    ax[0].set_xlabel('Time')
    ax[0].set_title('Dive Profile')
    ax[0].legend(['Depth [m]', 'Altitude [m]'], loc='best',
        frameon=True, framealpha=0.6, fontsize='small')



    #############################################
    # PLOT ODOMETRY AND DEAD-RECKONED ###########
    #############################################
    # sub-select a portion of glider flight computer variables
    start_t = datetime.datetime.fromtimestamp(ts_pd0.df.time[0])
    end_t   = datetime.datetime.fromtimestamp(ts_pd0.df.time[-1])
    dur     = end_t - start_t 
    df_dbd  = ts_dbd_all.df[str(start_t):str(end_t)].copy()

    # extract start_t position "origin" from the glider flight data 
    for t in range(len(df_dbd)):
        if not np.isnan(df_dbd.m_x_lmc[t]):
            dbd_origin_x = df_dbd.m_x_lmc[t]
            dbd_origin_y = df_dbd.m_y_lmc[t]
            break
    if use_wc:
        sns.scatterplot(
            x=ts_pd0.df.rel_pos_x,
            y=ts_pd0.df.rel_pos_y,
            color='tab:orange',
            label='DVL Odometry',
            linewidth=0,
            s=8,
            data=ts_pd0.df,
            ax=ax[1],
            zorder=2,
        )
    else:
        sns.scatterplot(
            x=ts_pd0.df.rel_pos_x_dvl_dr,
            y=ts_pd0.df.rel_pos_y_dvl_dr,
            color='tab:orange',
            label='DVL Odometry',
            linewidth=0,
            s=8,
            data=ts_pd0.df,
            ax=ax[1],
        )
    sns.scatterplot(
        x=df_dbd.m_x_lmc - dbd_origin_x,
        y=df_dbd.m_y_lmc - dbd_origin_y,
        color='tab:blue',
        label='Dead-Reckoned',
        linewidth=0,
        s=8,
        data=df_dbd,
        ax=ax[1],
        zorder=1,
    )
    sns.scatterplot(
        x=df_dbd.m_gps_x_lmc - dbd_origin_x, 
        y=df_dbd.m_gps_y_lmc - dbd_origin_y,
        marker='X',
        color='tab:red', 
        label='GPS Fix',
        s=200,
        data=df_dbd,
        ax=ax[1],
        zorder=5,
    )

    # TODO -- can add marker for when TAN is able to recognize a feature
    lgnd = ax[1].legend(frameon=True, framealpha=0.6, loc='best', 
        fontsize='small')
    lgnd.legendHandles[0]._sizes = [60]
    lgnd.legendHandles[1]._sizes = [60]
    lgnd.legendHandles[2]._sizes = [200]
    if len(lgnd.legendHandles) == 4:
        lgnd.legendHandles[3]._sizes = [100]
    dt = df_dbd.index[0].replace(microsecond=0)
    plt.axis('equal')
    plt.suptitle('DVL Odometry with Water Column Sensing', fontweight='bold')
    plt.title('Odometry in LMC')
    plt.xlabel('X position [m]')
    plt.ylabel('Y position [m]')
    plt.subplots_adjust(wspace=0.3)
    if save_name: plt.savefig('/Users/zduguid/Desktop/fig/%s' % save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT WATER COLUMN
###############################################################################
def plot_water_column_currents(voc_u_list, voc_v_list, voc_w_list, voc_z_list, 
    save_name=None):
    sns.set(font_scale = 1.5)
    fig = plt.figure(figsize=(15,8))
    max_current = 1.0

    # plot ocean currents in u-v plane
    ax = fig.add_subplot(1, 2, 1, aspect='equal')
    c = np.arctan2(voc_u_list,voc_v_list)
    sns.scatterplot(
        voc_u_list,
        voc_v_list,
        voc_z_list,
        s=50,
        palette='inferno_r',
    )
    plt.title('Water Column, 2D View')
    plt.xlabel('Eastward [m/s]')
    plt.ylabel('Northward [m/s]')
    ax.set_xlim(-max_current,max_current)
    ax.set_ylim(-max_current,max_current)
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(title='Depth [m]', fontsize='small', loc='best',
        framealpha=0.6, handles=handles[:-1], 
        labels=labels[:-1]).get_title().set_fontsize('small')

    # plot 3D quiver plot
    ax = fig.add_subplot(1, 2, 2, projection='3d')

    # voc_u,voc_v,voc_w,voc_z
    u = voc_u_list[pd.notnull(voc_u_list)]
    v = voc_v_list[pd.notnull(voc_u_list)]
    w = voc_w_list[pd.notnull(voc_u_list)]
    z = voc_z_list[pd.notnull(voc_u_list)]
    x = np.zeros(u.shape)
    y = np.zeros(u.shape)

    # convert data to RGB color map for quiver plot 
    c = (np.arctan2(u,v) + np.pi)/(2*np.pi)
    c = np.concatenate((c, np.repeat(c, 2)))
    c = plt.cm.twilight_shifted(c) 

    # generate quiver plot
    ax.quiver(x, y, -z, u, v, w, colors=c,length=1,normalize=False)
    ax.patch.set_facecolor('white')
    ax.w_xaxis.set_pane_color((234/255, 234/255, 242/255, 1.0))
    ax.w_yaxis.set_pane_color((234/255, 234/255, 242/255, 1.0))
    ax.w_zaxis.set_pane_color((234/255, 234/255, 242/255, 1.0))
    ax.set_xlabel('\n\nEastward [m/s]')
    ax.set_ylabel('\n\nNorthward [m/s]')
    ax.set_zlabel('\n\nDepth [m]')
    ax.azim = -110   # [deg]
    ax.elev =   30   # [deg]
    plt.xlim(-max_current,max_current)
    plt.ylim(-max_current,max_current)
    plt.title('Water Column, 3D View')
    plt.suptitle('Water Column Currents', fontweight='bold')
    if save_name: plt.savefig('/Users/zduguid/Desktop/fig/%s' % save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT VELOCITIES (BOTTOM TRACK)
###############################################################################
def plot_velocity_bottom_track(ts, glider, save_name=None):
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(10,8))
    sns.scatterplot(x=ts.df.abs_vel_btm_u,
                    y=ts.df.abs_vel_btm_v,
                    s=30,
                    hue=ts.df.heading,
                    palette='viridis_r',
                    data=ts.df)
    dt = datetime.datetime.fromtimestamp(ts.df.time[0]).replace(microsecond=0)
    plt.axis('equal')
    plt.suptitle('Bottom Track Velocities', fontweight='bold')
    plt.title('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),))
    plt.xlabel('East Velocity [m/s]')
    plt.ylabel('North Velocity [m/s]')
    tick_spacing = np.arange(-1.2,1.4,0.2)
    plt.xticks(tick_spacing)
    plt.yticks(tick_spacing)
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT VELOCITIES (EASTWARD)
###############################################################################
def plot_velocity_eastward(ts, glider, save_name=None):
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(15,8))
    filter_len = 30
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin0_beam0.rolling(filter_len).mean(),
        color='lightblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 0'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin1_beam0.rolling(filter_len).mean(),
        color='deepskyblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 1'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin2_beam0.rolling(filter_len).mean(),
        color='cornflowerblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 2'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin3_beam0.rolling(filter_len).mean(),
        color='royalblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 3'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=ts.df.abs_vel_btm_u.rolling(filter_len).mean(),
        color='tab:orange',
        data=ts.df,
        s=10,
        linewidth=0,
        label='btm'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=ts.df.rel_vel_pressure_u.rolling(filter_len).mean(),
        color='magenta',
        data=ts.df,
        s=10,
        linewidth=0,
        label='$\Delta$z/$\Delta$t'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=ts.df.pitch.rolling(filter_len).median()/100,
        color='red',
        data=ts.df,
        s=10,
        linewidth=0,
        label='pitch'
    )
    dt = datetime.datetime.fromtimestamp(ts.df.time[0]).replace(microsecond=0)
    plt.suptitle('Eastward Component of Velocity', fontweight='bold')
    plt.title('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),))
    plt.xlabel('Time')
    plt.ylabel('Velocity [m/s]')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT VELOCITIES (NORTHWARD) 
###############################################################################
def plot_velocity_northward(ts, glider, save_name=None, roll_size=10,
    plt_pressure=True, plt_pitch=True):
    sns.set(font_scale = 1.5)
    fig, ax = plt.subplots(figsize=(15,8))
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin0_beam1.rolling(roll_size).median(),
        color='lightblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 0'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin1_beam1.rolling(roll_size).median(),
        color='deepskyblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 1'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin2_beam1.rolling(roll_size).median(),
        color='cornflowerblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 2'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin3_beam1.rolling(roll_size).median(),
        color='royalblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 3'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin4_beam1.rolling(roll_size).median(),
        color='blue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 4'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=-ts.df.vel_bin5_beam1.rolling(roll_size).median(),
        color='darkblue',
        data=ts.df,
        s=10,
        linewidth=0,
        label='bin 5'
    )
    sns.scatterplot(
        x=ts.df.time,
        y=ts.df.abs_vel_btm_v.rolling(roll_size).median(),
        color='tab:orange',
        data=ts.df,
        s=10,
        linewidth=0,
        label='btm'
    )
    if plt_pressure:
        sns.scatterplot(
            x=ts.df.time,
            y=ts.df.rel_vel_pressure_v.rolling(roll_size).median(),
            color='magenta',
            data=ts.df,
            s=10,
            linewidth=0,
            label='$\Delta$z/$\Delta$t'
        )
    if plt_pitch:
        sns.scatterplot(
            x=ts.df.time,
            y=ts.df.pitch.rolling(roll_size).median()/100,
            color='tab:green',
            data=ts.df,
            s=10,
            linewidth=0,
            label='pitch'
        )
    dt = datetime.datetime.fromtimestamp(ts.df.time[0]).replace(microsecond=0)
    plt.suptitle('Northward Component of Velocity', fontweight='bold')
    plt.title('%s Kolumbo Volcano %s' % (unit_name[glider], dt.isoformat(),))
    plt.xlabel('Time')
    plt.ylabel('Velocity [m/s]')
    plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')


###############################################################################
# PLOT CORRELATIONS
###############################################################################
def plot_correlations(ts, glider, save_name=None):
    cols = [
        'pitch', 
        'heading', 
        'roll', 
        'depth',
        'temperature',
        'speed_of_sound',
        'abs_vel_btm_u',
        'abs_vel_btm_v',
        'abs_vel_btm_w',
        'rel_vel_dvl_u',
        'rel_vel_dvl_v',
        'rel_vel_dvl_w',
        'rel_vel_pressure_u',
        'rel_vel_pressure_v',
        'rel_vel_pressure_w',
        'rel_pos_x',
        'rel_pos_y',
        'rel_pos_z',
    ]

    df = ts.df[cols]

    # compute correlations 
    corr = df.corr()
    mask = np.zeros_like(corr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True
    mask[np.diag_indices_from(mask)] = False

    # plot heatmap given the correlations 
    fig, (ax) = plt.subplots(1, 1, figsize=(15,8))
    hm = sns.heatmap(
        corr, 
        ax=ax,
        #mask=mask,
        cmap="coolwarm",
        #square=True,
        annot=True, 
        fmt='.2f', 
        #annot_kws={"size": 14},
        linewidths=.05
    )

    # fig.subplots_adjust(top=0.93)
    ax.set_title('DVL Feature Correlations', fontsize=22, fontweight='bold')
    if save_name: plt.savefig(save_name)
    else:         plt.savefig('/Users/zduguid/Desktop/fig/tmp.png')
