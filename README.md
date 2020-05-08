<a href="https://github.com/zduguid">
    <img src="README/glider2.png" alt="glider_image" align="right" height="70">
</a>


# DVL Navigation
<!---------------------------------------------->

## Table of Contents 
- [Data Field Information](#data-field-information)
  - [Fixed Leader Fields](#fixed-leader-fields)
    - [System Configuration](#system-configuration)
    - [Coordinate Transformation](#coordinate-transformation)
  - [Variable Leader Fields](#variable-leader-fields)
  - [Water Profiling Fields](#water-profilingp-fields)
  - [Bottom Track Fields](#bottom-track-fields)
- [Helpful Commands](#helpful-commands)
- [Miscellaneous Notes](#miscellaneous-notes)
- [List of TODOs](#list-of-todos)


<!-----------------------------------------------
Most Recent Changes:
- implemented basic odometry 
- fixed bug in using DVL velocities incorrectly (0-index issue)


Changes Before Commit: 
- improve documentation

Upcoming Tasks:
- don't worry about 80 char limit of sublime editor -- github has good parsing of table information -- feel free to add more extensive table information.
- finish writing system_configuration table (see pathfinder manual)
- finish writing bottom_track information table (see pathfinder manual)
------------------------------------------------>


<!---------------------------------------------->
## Data Field Information  
### Fixed Leader Fields 
| Variable Name         | Units | Description                                 |
| ---                   | :---: | ---                                         |
| `system_configuration`|       | several settings, see table below           |
| `num_velocity_beams`  |       | number of beams to calculate velocity data  |
| `num_cells`           |       | number of depth cells [0, 255]              |
| `pings_per_ensemble`  |       | number of pings averaged per ensemble       |
| `depth_cell_length`   | [m]   | length of one depth cell                    |
| `coordinate_transformation` | | several settings, 31 = earth reference frame|
| `heading_alignment`   | [deg] | correction factor for physical misalignment |
| `heading_bias`        | [deg] | correction factor for magnetic bias         |
| `sensor_source`       |       | several settings, 130 = all available       |


#### System Configuration

Example: `system_configuration = 16971 = 1101,0010,0100,0010` [bit0,...,bit15]
In bit order, this means: 
- [TODO: write a table here with information from pg162 of pathfinder manual]


#### Coordinate Transformation
| EX-Cmd  | Value | Coord Sys | Vel 1     | Vel 2     | Vel 3     | Vel 4     |
| ---     | ---   | ---       | ---       | ---       | ---       | ---       |
| 00xxx   | 7     | Beam      | to beam1  | to beam2  | to beam3  | to beam4  |
| 01xxx   | 15    | Instrument| bm1-bm2   | bm4-bm3   | to xducer | err vel   |
| 10xxx   | 23    | Ship      | prt-stbd  | aft-fwd   | to surface| err vel   |
| 11xxx   | 31    | Earth     | to East   | to West   | to surface| err vel   |

The remaining three bits, labeled 'x' above, represent three more operation configuration parameters.

| EX-Cmd  | Description                                                       |
| ---     | ---                                                               |
| xx1xx   | Uses Pitch and Roll for computing Ship/Earth transformation       |
| xxx1x   | Allows 3-beam velocity solution if one beam below threshold       |
| xxxx1   | Allows bin-mapping (see manual for more details)                  |

Example: `EX11111 = coordinate_transformation = 31`: earth coordinate transformation, with Pitch and Roll used for computing transformation, 3-beam velocity solution is allowed, and bin-mapping is allowed. Note, for Ship coordinate transformation and Earth coordinate transformation, the "Heading Alignment" and "Heading Bias" parameters must be set properly. 


### Variable Leader Fields 
| Variable Name         | Units | Description                                 |
| ---                   | :---: | ---                                         |
| `speed_of_sound`      | [m/s] | either manual or calculated speed of sound  |
| `depth_of_transducer` | [m]   | positive down, depth below water surface    |
| `heading`             | [deg] | heading angle relative to coordinate frame  |
| `pitch`               | [deg] | positive upwards                            |
| `roll`                | [deg] | positive means glider is banking right      |
| `salinity`            | [ppt] | measured at the transducer head             |
| `temperature`         | [C]   | measured at the transducer head             |


### Water Profiling Fields 
| Variable Name         | Units | Description                                 |
| ---                   | :---: | ---                                         |
| `vel_cell#_beam#`     | [m/s] | velocity, depends on coordinate transform   |
| `cor_cell#_beam#`     |       | linear scale of correlation mag (255 = best)|
| `ech_cell#_beam#`     |       | echo intensity                              |
| `per_cell#_beam#`     |       | percent good data quality indicator         n|


### Bottom Track Fields 
| Variable Name               | Units | Description | 
| ---                         | :---: | --- |
| `btm_beam#_range`           | unit  | bottom track vertical range (NOT slant range) to detected bottom (0 = not detected)does not take into account pitch/roll  |
| `btm_beam#_velocity`        | unit  | bottom track velocity, meaning depends on `coordinate_transformation` |
| `btm_beam#_correlation`     | unit  | des |
| `btm_beam#_echo_intensity`  | unit  | des |
| `btm_beam#_percent_good`    | unit  | des |
| `btm_beam#_rssi`            | unit  | des |
| `btm_bottom_track_mode`     | unit  | des |
| `btm_max_tracking_depth`    | unit  | des |



<!---------------------------------------------->
## Helpful Commands 
- `python -m cProfile -s tottime simul.py`
  - run Python profiler over function



<!---------------------------------------------->
## Miscellaneous Notes
- Whenever possible, numpy or pandas vectorized operations should be used. In order of fastest to slowest: numpy vectorized functions, pandas vectorized functions, lambda functions, pandas built-in loop, python standard loop. Looping over pandas objects should be avoided at all costs.  
  - [Towards Data Science: How to make your pandas loop 71,803 times faster](https://towardsdatascience.com/how-to-make-your-pandas-loop-71-803-times-faster-805030df4f06)
  - [Medium: A Beginner’s Guide to Optimizing Pandas Code for Speed](https://engineering.upside.com/a-beginners-guide-to-optimizing-pandas-code-for-speed-c09ef2c6a4d6)
- the best way to incrementally build a numpy array, without knowing the final array size ahead of time, is to append numpy array rows to a python list and then cast the list into a 2D numpy array at the end. Using the `np.concatenate()` or `numpy.append()` functions are much slower. One downside of casting a python list to a numpy array is that both the list and array will be stored in memory at the same time. 
  - [Stack Overflow: Best way to incrementally build a numpy array](https://stackoverflow.com/questions/30468454/what-is-the-best-way-to-incrementally-build-a-numpy-array)


<!---------------------------------------------->
## List of TODOs

### General TODOs
- add parent class `PathfinderDVL` that defines variable names, derived variables, etc. (similar to Micron sonar)
- add "save compressed version" that does not include echo intensities, percent-good, bottom-track, etc. -- only the most relevant information in a small number of columns (add a flag for only considering the "compressed version of the data")
- change "cell" to "bin" -- will be easier to read

### `pd0_reader.py`
- try combing data from multiple files -- think about timestamps organization 

### `pd0_plotter.ipynb`
- IPython notebook for plotting DVL data -- notebook format encourages interaction with data visualization processing (and ensures that glider scripts are not burdened with any processing functions)

### `PathfinderEnsemble.py`
- make "get_data" function that is more similar to the micron sonar function
- remove the code that calls the `setattr` function (use get_data instead)
- better documentation about how to use the software 
- turn this into a sub-method: # store parsed values in the data array 
- change name of velocity variables? (instead of beam1, beam2, etc., could use velocity1, velocity2, etc. which may be less confusing because only one of the four coordinate system options includes velocities along the beam axis)
- think about what data-fields will be needed for on-board processing (not everything will be required and we want to be as light weight as possible)
- add another dict attribute that keeps track of units?
- determine how to access some of the more relevant variables from fixed_leader (i.e. coordinate_transformation, etc.) the answer might just be to do all the necessary parsing and transformation before saving to csv file format. Alternatively, can include the fixed leader variables in the ensemble itself.
- add some of the fixed-leader variables to the dataframe (when combining multiple missions it is possible that these would change over-time, i.e. if the backseat driver sends a command to the DVL during the mission)

### `PathfinderTimeSeries.py`
- encode various navigation functions (review Rich Matlab code for this)
- test ensemble rollover works in case when 65535 ensembles occur
- add additional class method constructors (checkout MicronTimeSeries)
  - add 'from_csv'
  - add 'from_csv_directory'
  - add 'from_frames'
  - note this is more complicated than the MicronSonar example because need to keep track of previous ensemble references 