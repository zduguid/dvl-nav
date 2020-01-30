# slocum-nav

README documentation coming soon...
Right now, I am using this document to maintain a list of open TODO items:

## Helpful Commands 
- `python -m cProfile -s tottime simul.py`
  - run Python profiler over function


### Overall Project TODOs
- write up a proper README file 
- create parent classes `Ensemble.py` and `TimeSeries.py` that `PathfinderEnsemble.py` and `NavigatorEnsemble.py` etc. can inherit from? 


### `pd0_reader.py` and `pd0_plotter.py` TODOs 
- try combing data from multiple files -- how are timestamps organized? 
- implement separate plotting function (might be helpful to experiment with Jupyter notebooks here)


### `PathfinderEnsemble.py` TODOs 
- add `MultiIndex` functionality for hierarchical variable accessing (this is the pandas solution for working with higher dimensional datasets) (potentially add some helper functions here to make array access easier)
- look into how importing and exporting csv files with MultiIndex works 
- think about what data-fields will be needed for on-board processing (not everything will be required and we want to be as light weight as possible)


### `PathfinderTimeSeries.py` TODOs
- use `memoryview()` function somehow?
- combine `PathfinderEnsemble` objects into single time-series data frame
- encode various navigation functions (review Rich Matlab code for this)
- add saving functionality (in .csv format)
- change variable names and function names accordingly 
- test ensemble rollover works in case when 65535 ensembles occur