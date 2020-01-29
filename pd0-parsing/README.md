## Overall Project TODOs
- write up a proper README file 
- create parent classes `Ensemble.py` and `TimeSeries.py` that `PathfinderEnsemble.py` and `NavigatorEnsemble.py` etc. can inherit from 
- rename files to `PathfinderEnsemble.py` and `PathfinderTimeSeries.py` (this is done to disambiguate between `MicronEnsembly.py` and `MicronTimeSeries.py` - both instruments use sonar and doppler, so need to pick a better naming convention 


### Plotting file 
- name and create file 
- add plotting functionality - create a new file / class for this (dont want to overburden main function with)
- experiment with visualization capabilities in a jupyter notebook


### `Ensemble.py` TODOs 
- change `data` dictionary into object parameters that are directly callable
- add properties and setters to each attribute of the ensemble
- implement `to_dataframe()` function that returns DataFrame ensemble
- add function that automatically parse to standard metric values of the parameters(store unit information for each parameter)
- avoid parsing 


### `TimeSeries.py` TODOs
- use `memoryview()` function somehow?
- convert `pd0_reader.py` into `TimeSeries.py`
- remove all TODO flags in the code
- turn TimeSeries.data into a dataframe instead of a dictionary
- add saving functionality (in .csv format)
- change variable names and function names accordingly 
- test ensemble rollover works in case when 65535 ensembles occur