## Overall Project TODOs
- write up a proper README file 
- add ability to parse Navigator ensembles also (different byte allocations)

### `Ensemble.py` TODOs 
- fix byte order (big endian vs little endian) and unsigned vs signed issue 
- change `data` dictionary into object parameters that are directly callable
- add properties and setters to each attribute of the ensemble
- implement `to_dataframe()` function that returns DataFrame ensemble
- keep track of the units of all measured values -- automatically parse to standard metric values of the parameters(store unit information for each parameter)
- implement bytes [60, 77] for variable leader in-case we see those in the future

### `TimeSeries.py` TODOs
- convert `pd0_reader.py` into `TimeSeries.py`
- remove all TODO flags in the code
- turn TimeSeries.data into a dataframe instead of a dictionary
- add plotting functionality
- add saving functionality (in .csv format)
- change variable names and function names accordingly 
- test ensemble rollover works in case when 65535 ensembles occur