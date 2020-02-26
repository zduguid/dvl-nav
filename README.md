# dvl-nav

## Table of Contents 
- [Data Field Information](#data-field-information)
  - [Fixed Leader Fields](#fixed-leader-fields)
    - [System Configuration](#system-configuration)
    - [Coordinate Transformation](#coordinate-transformation)
  - [Variable Leader Fields](#variable-leader-fields)
  - [Water Profiling Fields](#water-profilingp-fields)
  - [Bottom Track Fields](#bottom-track-fields)
- [Helpful Commands](#helpful-commands)
- [List of TODOs](#list-of-todos)

<!-- 
-------------------------------------------------
Most Recent Changes:
- adding details to README 
  - better linking 
  - unit and variable name information 

README TODOs 
- finish writing system_configuration table (see pathfinder manual)
- finish writing bottom_track information table (see pathfinder manual)
- check for units of echo intensity (0.61 dB?)
-------------------------------------------------
 -->



-------------------------------------------------
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
| `per_cell#_beam#`     |       | percent good data quality indicator         |


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



-------------------------------------------------
## Helpful Commands 
- `python -m cProfile -s tottime simul.py`
  - run Python profiler over function



-------------------------------------------------
## List of TODOs

### `pd0_reader.py`
- try combing data from multiple files -- think about timestamps organization 

### `pd0_plotter.ipynb`
- IPython notebook for plotting DVL data -- notebook format encourages interaction with data visualization processing (and ensures that glider scripts are not burdened with any processing functions)

### `PathfinderEnsemble.py`
- add `MultiIndex` functionality for hierarchical variable accessing (this is the pandas solution for working with higher dimensional datasets) (potentially add some helper functions here to make array access easier)
- look into how importing and exporting csv files with MultiIndex works - might be better to pickle and un-pickle my own class objects (faster / more memory efficient / easier to work with in the future)
- think about what data-fields will be needed for on-board processing (not everything will be required and we want to be as light weight as possible)
- add another dict attribute that keeps track of units?
- determine how to access some of the more relevant variables from fixed_leader (i.e. coordinate_transformation, etc.) the answer might just be to do all the necessary parsing and transformation before saving to csv file format
- add some of the fixed-leader variables to the dataframe (when combining multiple missions it is possible that these would change over-time, i.e. if the backseat driver sends a command to the DVL during the mission)

### `PathfinderTimeSeries.py`
- encode various navigation functions (review Rich Matlab code for this)
- test ensemble rollover works in case when 65535 ensembles occur