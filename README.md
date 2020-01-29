# slocum-nav

README documentation coming soon...
Right now, I am using this document to maintain a list of open TODO items:


### Overall Project TODOs
- write up a proper README file 
- create parent classes `Ensemble.py` and `TimeSeries.py` that `PathfinderEnsemble.py` and `NavigatorEnsemble.py` etc. can inherit from? 


### `pd0_reader.py` and `pd0_plotter.py` TODOs 
- used `PathfinderTimeSeries.py` object for collecting pd0 data 
- try combing data from multiple files -- how are timestamps organized? 
- implement separate plotting function (might be helpful to experiment with Jupyter notebooks here)


### `PathfinderEnsemble.py` TODOs 
- add `MultiIndex` functionality for hierarchical variable accessing (this is the pandas solution for working with higher dimensional datasets) (potentially add some helper functions here to make array access easier)
- look into how importing and exporting csv files with MultiIndex works 
- think about what data-fields will be needed for on-board processing (not everything will be required and we want to be as light weight as possible)


### `PathfinderTimeSeries.py` TODOs
- extract header information (i.e. num_bins) from ensemble and add to TimeSeries object as well (need to keep track of which parameters are part of the fixed header)
- use `memoryview()` function somehow?
- combine `PathfinderEnsemble` objects into single time-series data frame
- encode various navigation functions (review Rich Matlab code for this)
- add saving functionality (in .csv format)
- change variable names and function names accordingly 
- test ensemble rollover works in case when 65535 ensembles occur