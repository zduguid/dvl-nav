<a href="https://github.com/zduguid">
    <img src="README/glider2.png" alt="glider_image" align="right" height="70">
</a>



<!-----------------------------------------------
Most Recent Changes:
- added new class PathfinderUtils to help with water column processing
  (motivation for this was the shear propagation method)
    + TODO need to be weary of recursion limit errors for long dives
    + TODO not currently averaging 


Changes Before Commit: 
- add UTM conversion function to pathfinder class? or keep in notebook?

Future TODOs
- implement SlocumScienceController
- add a "glider" file that has bias parameter information 
- add more constructor methods ("from_csv", "from_frames", "from_directory")
------------------------------------------------>



<!---------------------------------------------------------------------------->
# DVL Navigation

This repository is used for parsing pd0 data from the Pathfinder DVL instrument and then processing data to perform navigation and sensing for the Slocum Glider. The methods used in this repository are designed to work as a real-time process onboard the glider. 

In the context of this repository, an "ensemble" refers to a collection of oceanographic variables that are reported at the same moment in time by the Pathfinder DVL instrument. A series of these ensembles over time are referred to as a "time series". 

There are three Pathfinder object classes implemented in this repository: 
1. `PathfinderDVL` -- superclass of the Pathfinder objects which defines variables that are present in raw pd0 files output Pathfinder objects. The superclass also defines useful constants for parsing and navigation.
1. `PathfinderEnsemble` -- represents a single ensemble of data reported from the Pathfinder DVL at a moment in time. The input to the PathfinderEnsemble is a string of bytes from the DVL instrument. 
1. `PathfinderTimeSeries` -- represents a time series of Pathfinder DVL data. As data is reported from the DVL instrument during the mission, data can be collected in the time series using the `add_ensemble()` method. Alternatively, when working with Pathfinder data offline, an entire pd0 file can be collected into a time series object with the `from_pd0()` class method. 



<!---------------------------------------------------------------------------->
## Table of Contents 
- [PathfinderTimeSeries Class Overview](#pathfindertimeseries-class-overview)
- [Data Field Information](#data-field-information)
  - [Fixed Leader Fields](#fixed-leader-fields)
  - [Variable Leader Fields](#variable-leader-fields)
  - [Derived Fields](#derived-fields)
  - [Water Profiling Fields](#water-profiling-fields)
  - [Bottom Track Fields](#bottom-track-fields)
- [Slocum Glider Data Fields](#slocum-glider-data-fields)
- [Kolumbo Data Set Overview](#kolumbo-data-set-overview)
- [Miscellaneous Notes](#miscellaneous-notes)



<!---------------------------------------------------------------------------->
## PathfinderTimeSeries Class Overview 
<!---------------------------------------------->
### How to parse a raw pd0 file

`time_series = PathfinderTimeSeries.from_pd0('/path/to/pd0/file.pd0')`

This function will open a raw pd0 file and parse it into a PathfinderTimeSeries object. A PathfinderTimeseries object will contain all of the fields mentioned in the [data field information](#data-field-information) section below. By default, the `from_pd0` function prints out some helpful diagnostic information about the pd0 file. If this behavior is not desired, include the argument `verbose=False` to the function call. An example of the diagnostic information is shown below.
```
________________________________________
- Parsing New File ---------------------
    input file: /path/to/pd0/file/01820002.pd0
    # ensembles:    200
    # ensembles:    400
    # ensembles:    600
    # ensembles:    800
    # ensembles:   1000
    # ensembles:   1200
    # ensembles:   1400
    # ensembles:   1600
    # ensembles:   1800
    # ensembles:   2000
    # ensembles:   2200
    # ensembles:   2400
- Parsing Complete ---------------------
    # ensembles:   2410
    parsing time:  5.284270
- Sensor Configuration -----------------
    600kHz System
    Convex Beam Pattern
    Sensor Config #1
    Attached
    Down Facing
    30E Beam Angle
    4 Beam Janus
- Coordinate Transformation ------------
    Bin Mapping Used
    3-Beam Soln Used
    Tilts Used
    Earth Coords
```


<!---------------------------------------------->
### How to access a data field from a PathfinderTimeSeries

After parsing a pd0 file into a time series, you can easily access time series data via querying the pandas DataFrame attribute: 

`pitch = time_series.df.pitch` or 
`pitch = time_series.df['pitch']`

The two snippets above will access the time series pitch data from the DataFrame and store that data in the new `pitch` variable.



<!---------------------------------------------->
### How to add a new data field to PathfinderTimeSeries 

Add the desired variable name to the derived variables tuple in the PathfinderDVL superclass, and then implement the corresponding parsing method to the `parse_derived_variables()` function in the PathfinderEnsemble class.



<!---------------------------------------------------------------------------->
## Data Field Information  
<!---------------------------------------------->
### Fixed Leader Fields 
| Variable Name         | Units | Description                                 |
| ---                   | :---: | ---                                         |
| `system_configuration`|       | Several settings are described here. To parse the information, the numerical value must be converted to binary and then each bit must be decoded. The operating frequency and beam configuration parameters are described here. |
| `num_beams`           |       | Number of beams used to calculate velocity data. The minimum number required to back-out velocity is 3 beams. If four beams are used, the problem becomes over-constrained and the instrument reports an error velocity. |
| `num_bins`            |       | Number of depth bins [0, 255].              |
| `pings_per_ensemble`  |       | Number of pings averaged together in each ensemble. |
| `depth_bin_length`    | [m]   | Length of each depth bin.                   |
| `blanking_distance`   | [m]   | Blanking distance used by Pathfinder to allow ringing effect to recover before processing received data |
| `low_correlation_threshold` | | The minimum threshold of correlation that water-profile data can have to be considered good data |
| `percent_good_minimum`      | | Contains the minimum percentage of water-profiling pings in an ensemble that must be considered good to output velocity data. |
| `error_velocity_threshold`  | [mm/s] | Contains the threshold value used to flag water-current data as good or bad. |
| `coordinate_transformation` | | Several settings are described here. To parse the information, the numerical value must be converted to binary and then each bit must be decoded. Most importantly, the coordinate frame for instrument data is reported here. The coordinate frame is one of: beam coordinates, instrument coordinates, ship coordinates, or Earth coordinates. |
| `heading_alignment`   | [deg] | Contains a correction factor for physical heading misalignment. |
| `heading_bias`        | [deg] | Contains a correction factor for electrical/magnetic heading bias. |
| `sensor_source`       |       | Several settings are described here. To parse the information, the numerical value must be converted to binary and then each bit must be decoded. This field explains were environmental sensor data is coming from. | 
| `bin0_distance`       | [m]   | This field contains the distance to the middle of the first depth bin. This distance is a function of depth bin length, the profiling mode, the blank after transmit distance, and speed of sound. | 
| `transmit_pulse_length` | [m] | Contains the length of the transmit pulse. | 



<!---------------------------------------------->
#### Coordinate Transformation

The meaning of the four coordinate systems are described in the table below. Note that the "beam" coordinates is the most low-level as it does not include any additional processing from the raw values collected, while the "Earth" coordinates contain the most additional processing: the Earth frame account for pitch, roll, and heading alignment of the vehicle when reporting velocity values. 

| Coord Sys | Vel 1     | Vel 2     | Vel 3     | Vel 4     |
| ---       | ---       | ---       | ---       | ---       |
| Beam      | Towards Beam1 | Towards Beam2 | Towards Beam3 | Towards Beam4   |
| Instrument| Beam1-to-Beam2| Beam4-to-Beam3| To Transducer | Error Velocity  |
| Ship      | Port-to-Starboard | Aft-to-Forward| To Surface| Error Velocity  |
| Earth     | To East           | To West   | To Surface    | Error Velocity  |



<!---------------------------------------------->
### Variable Leader Fields 
| Variable Name         | Units | Description                                 |
| ---                   | :---: | ---                                         |
| `time`                | [UTC] | Gives the time at which the ensemble was collected by the Pathfinder DVL. For convenience, the time field is used as the index in the PathfinderTimeSeries DataFrame to make slicing by time-windows easy. |
| `ensemble_number`     |       | Ensemble number for the given data file.    |
| `bit_result`          |       |  Several settings are described here. To parse the information, the numerical value must be converted to binary and then each bit must be decoded. This variable reports the results of the built-in Pathfinder tests. |
| `speed_of_sound`      | [m/s] | Manual or calculated speed of sound.        |
| `depth_of_transducer` | [m]   | Depth below water surface (positive down).  |
| `heading`             | [deg] | Heading angle.                              |
| `pitch`               | [deg] | Pitch angle, positive means vehicle is tilted upwards. | 
| `roll`                | [deg] | Roll angle, positive means glider is banking right. |
| `salinity`            | [ppt] | Salinity measured at the transducer head.   |
| `temperature`         | [C]   | Temperature measured at the transducer head.|
| `pressure`            | [Pa]  | Pressure of water relative to 1 atm.        |



<!---------------------------------------------->
### Derived Fields 
| Variable Name         | Units | Description                                 |
| ---                   | :---: | ---                                         |
| `rel_vel_pressure_u`  | [m/s] | X-component (Eastward) of through water velocity, derived by looking at change in pressure over time and heading reading from compass. |
| `rel_vel_pressure_v`  | [m/s] | Y-component (Northward) of through water velocity, derived by looking at change in pressure over time and heading reading from compass. |
| `rel_vel_dvl_u`       | [m/s] | X-component (Eastward) of through water velocity, given by the DVL. | 
| `rel_vel_dvl_v`       | [m/s] | Y-component (Northward) of through water velocity, given by the DVL. | 
| `abs_vel_btm_u`       | [m/s] | X-component (Eastward) of over ground velocity, given by the DVL operating in bottom-track mode. |
| `abs_vel_btm_v`       | [m/s] | X-component (Eastward) of over ground velocity, given by the DVL operating in bottom-track mode. |
| `abs_vel_w`           | [m/s] | Z-component (Vertical) of glider velocity, given by change in pressure over change in time. |
| `delta_x`             | [m]   | Change in x-component of position since last ensemble. |
| `delta_y`             | [m]   | Change in y-component of position since last ensemble. |
| `delta_z`             | [m]   | Change in z-component of position since last ensemble. |
| `delta_t`             | [s]   | Change in time since last ensemble. |
| `rel_pos_x`           | [m]   | X-component of position relative to given origin point (if unspecified, origin is considered the <0,0,0> point). |
| `rel_pos_y`           | [m]   | Y-component of position relative to given origin point (if unspecified, origin is considered the <0,0,0> point). |
| `rel_pos_z`           | [m]   | Z-component of position relative to given origin point (if unspecified, origin is considered the <0,0,0> point). |
| `origin_x`            | [UTM] | X-component of origin point for defining the relative coordinate frame. |
| `origin_y`            | [UTM] | X-component of origin point for defining the relative coordinate frame. |
| `angle_of_attack`     | [deg] | Angle of attack of the glider, currently assumed to be zero for simplicity. |


<!---------------------------------------------->
### Water Profiling Fields 

Note that the interpretation of the water-profiling fields is dependent on the coordinate transformation being used. For example, in Earth coordinates the first beam (`vel_bin#_beam0`) refers to the Eastward velocity component and the second beam (`vel_bin#_beam1`) refers to the Northward velocity component. It is also important to note that the data fields are indexed from zero while the physical beams are indexed from 1. 

| Variable Name         | Units | Description                                 |
| ---                   | :---: | ---                                         |
| `vel_bin#_beam#`      | [m/s] | Velocity.                                   |
| `cor_bin#_beam#`      |       | Linear scale of correlation magnitude (255 = best). |
| `ech_bin#_beam#`      | [dB]  | Echo intensity                              |
| `per_bin#_beam#`      |       | Percent good data quality indicator.        |


<!---------------------------------------------->
### Bottom Track Fields 
| Variable Name               | Units | Description | 
| ---                         | :---: | --- |
| `btm_beam#_range`           | [m]   | Bottom track vertical range (NOT slant range) to the detected bottom, does not take into account the effects of pitch and roll. A value of zero indicates that the bottom was not detected. |
| `btm_beam#_velocity`        | [m/s] | Bottom track velocity, meaning depends on `coordinate_transformation`. |
| `btm_beam#_rssi`            | [dB]  | Receiver Signal Strength Indicator (RSSI) value in the center of the bottom echo for each beam. |
| `btm_pings_per_ensemble`    |       | Number of pings averaged together per ensemble. |
| `btm_bottom_track_mode`     |       | Bottom-tracking mode.  |
| `btm_max_error_velocity`    | [m/s] | Maximum error velocity | 



<!---------------------------------------------------------------------------->
## Slocum Glider Data Fields
The following data fields are extracted from the flight computer of the Slocum Glider. The units and a brief description of each variable is shown in the table below. LMC stands for Local Mission Coordinates.

| Variable Name               | Units | Description | 
| --- | --- | --- |
| `m_present_time`  | [s]   | Time since 1970. |
| `m_speed`         | [m/s] | Horizontal through water speed. |
| `m_pitch`         | [rad] | Pitch of the vehicle, >0 means nose up. |
| `m_roll`          | [rad] | Roll of the vehicle, >0 means port wing up. |
| `m_heading`       | [rad] | Heading of the glider. |
| `m_fin`           | [rad] | Angular position of the tail fin. |
| `m_depth`         | [m]   | Depth of the vehicle. |
| `m_depth_rate`    | [m/s] | Depth rate of the vehicle. |
| `m_water_depth`   | [m]   | Vehicle depth plus altitude of vehicle. |
| `m_pressure`      | [bar] | Pressure measured by the vehicle. |
| `m_altitude`      | [m]   | Height above seafloor. |
| `m_battery`       | [V]   | Average battery voltage. |
| `m_vacuum`        | [inHg]| Internal glider pressure. |
| `c_pitch`         | [rad] | Commanded pitch. |
| `c_roll`          | [rad] | Commanded roll. |
| `c_heading`       | [rad] | Commanded heading. |
| `c_fin`           | [rad] | Commanded fin position, >0 vehicle turns right. |
| `m_gps_x_lmc`     | [m]   | GPS position in LMC. |
| `m_gps_y_lmc`     | [m]   | GPs position in LMC. |
| `m_gps_fix_x_lmc` | [m]   | Location of first GPS position fix in LMC. |
| `m_gps_fix_y_lmc` | [m]   | Location of first GPS position fix in LMC. |
| `m_gps_status`    |       | Updated status of the GPS. |
| `m_x_lmc`         | [m]   | Waypoint location in LMC. |
| `m_y_lmc`         | [m]   | Waypoint location in LMC. |
| `m_dr_time`       | [s]   | Time glider has been underwater since last surface.|
| `m_dr_surf_x_lmc` | [m]   | Dead-reckoned surface location in LMC. |
| `m_dr_surf_y_lmc` | [m]   | Dead-reckoned surface location in LMC. |
| `m_ext_x_lmc`     | [m]   | Vehicle position from external navigation unit. |
| `m_ext_y_lmc`     | [m]   | Vehicle position from external navigation unit. |
| `m_ext_z_lmc`     | [m]   | Vehicle position from external navigation unit. |
| `x_lmc_xy_source` |       | Explains how LMC position was computed. Could be from GPS, dead-reckoned, initiated to zero, or not computed during this cycle.|
| `c_wpt_x_lmc`     | [m]   | Commanded waypoint in LMC coordinates. |
| `c_wpt_y_lmc`     | [m]   | Commanded waypoint in LMC coordinates. |
| `m_lat`           | [deg] | Vehicle position in terms of latitude. |
| `m_lon`           | [deg] | Vehicle position in terms of longitude. |
| `m_gps_lat`       | [deg] | Latitude in DDMM.MMMM format, >0 in the North. |
| `m_gps_lon`       | [deg] | Longitude in DDMM.MMMM format, >0 in the East. |
| `m_water_vx`      | [m/s] | Water speed in LMC. |
| `m_water_vy`      | [m/s] | Water speed in LMC. |
| `m_vx_lmc`        | [m/s] | Horizontal speed over ground, in LMC. |
| `m_vy_lmc`        | [m/s] | Horizontal speed over ground, in LMC. |
| `m_appear_to_be_at_surface` | [bool] | True if glider appears to be at surface. |
| `m_science_clothesline_lag` | [s]    | Time lag between flight computer and science computer. |
| `sci_m_present_time` |        [s]    | Seconds since 1970. |
| `x_software_ver` |                   | Current software version. | 


<!---------------------------------------------------------------------------->
## Kolumbo Data Set Overview

The following data files were collected from the Sentinel glider during the Kolumbo experiments in November 2019.

|Mission # |PD0 File |Start |End |Duration  |# of Dives  |Max Depth |
| ---     | ---     | ---                | ---                | ---  |---|--- |
|Dive 1   |sk211610 |2019-11-21 16:10:24 |2019-11-21 16:28:54 |0.308 |2  |9   |
|Dive 2   |sk211652 |2019-11-21 16:52:53 |2019-11-21 20:35:37 |3.712 |13 |106 |
|Dive 3   |01820002 |2019-11-21 21:17:11 |2019-11-21 23:53:33 |2.606 |11 |103 |
|Dive 4   |sk220034 |2019-11-22 00:34:46 |2019-11-22 01:28:11 |0.890 |4  |95  |
|Dive 5   |01820008 |2019-11-22 01:44:56 |2019-11-22 02:40:35 |0.927 |4  |75  |
|Dive 6   |01820010 |2019-11-22 03:24:02 |2019-11-22 03:46:45 |0.379 |1  |65  |
|Dive 7   |01820013 |2019-11-22 04:03:29 |2019-11-22 04:51:22 |0.798 |4  |66  |
|Dive 8   |sk220500 |2019-11-22 05:00:31 |2019-11-22 06:07:27 |1.115 |5  |57  |
|Dive 9   |sk222256 |2019-11-22 22:56:40 |2019-11-23 01:06:52 |2.170 |13 |52  |
|Dive 10  |sk230107 |2019-11-23 01:07:16 |2019-11-23 01:44:41 |0.623 |2  |52  |
|Dive 11\*|sk230148 |2019-11-23 01:48:05 |2019-11-23 02:43:28 |0.923 |1  |387 |
|Dive 12  |sk230350 |2019-11-23 03:50:37 |2019-11-23 06:41:37 |2.850 |15 |53  |
|Dive 13\*|sk261107 |2019-11-26 11:07:19 |2019-11-26 11:55:24 |0.801 |1  |275 |
|Dive 14  |sk261222 |2019-11-26 12:22:16 |2019-11-26 15:24:27 |3.036 |5  |415 |

\*These dives seems to crash into the seafloor. The DVL file does not include a return to surface.




<!---------------------------------------------------------------------------->
## Miscellaneous Notes
- `python -m cProfile -s tottime simul.py` -- terminal command that runs Python profiler over function and provides extensive information about how many times each sub-method is called and how long each sub-method takes to execute. 
- Whenever possible, numpy or pandas vectorized operations should be used. In order of fastest to slowest: numpy vectorized functions, pandas vectorized functions, lambda functions, pandas built-in loop, python standard loop. Looping over pandas objects should be avoided at all costs.  
  - [Towards Data Science: How to make your pandas loop 71,803 times faster](https://towardsdatascience.com/how-to-make-your-pandas-loop-71-803-times-faster-805030df4f06)
  - [Medium: A Beginner’s Guide to Optimizing Pandas Code for Speed](https://engineering.upside.com/a-beginners-guide-to-optimizing-pandas-code-for-speed-c09ef2c6a4d6)
- the best way to incrementally build a numpy array, without knowing the final array size ahead of time, is to append numpy array rows to a python list and then cast the list into a 2D numpy array at the end. Using the `np.concatenate()` or `numpy.append()` functions are much slower. One downside of casting a python list to a numpy array is that both the list and array will be stored in memory at the same time. 
  - [Stack Overflow: Best way to incrementally build a numpy array](https://stackoverflow.com/questions/30468454/what-is-the-best-way-to-incrementally-build-a-numpy-array)
- Converting from lat/lon to UTM coordinates performed using the [UTM library](https://github.com/Turbo87/utm)
