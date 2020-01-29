# pd0_reader.py
#
# TODO
#   2020-01-27  zduguid@mit.edu         Initial pd0_reader.py implementation 

# TODO
# import cProfile
# import re

import glob
import os
import sys
import time
import pandas as pd
from PathfinderEnsemble import PathfinderEnsemble
from PathfinderTimeSeries import PathfinderTimeSeries


def pd0_reader(filepath, save=True):
    """TODO 
    TODO
    """
    pd0_file = open(filepath, 'rb').read()
    count = 0
    print('- Parsing New File ---------------------')
    print('     input file: %s' % (filepath,))
    parse_start = time.time()

    # parse first ensemble to initialize time-series 
    ensemble     = PathfinderEnsemble(pd0_file)
    time_series  = PathfinderTimeSeries(ensemble)
    ensemble_len = time_series.num_bytes + 2
    pd0_file     = pd0_file[ensemble_len:]
    count       += 1

    # parse ensembles until the end of the pd0 file is reached    
    while len(pd0_file) > 0:

        # parse an ensemble from the pd0 file and add it to the time series
        ensemble = PathfinderEnsemble(pd0_file)
        time_series.add_ensemble(ensemble)

        # chop off the ensemble we just ensemble
        ensemble_len = ensemble.num_bytes + 2
        pd0_file     = pd0_file[ensemble_len:]
        count       += 1

    # parsing completed 
    parse_stop = time.time()
    print('    # ensembles: %d'    % (count))
    print('   parsing time: %f'    % (parse_stop - parse_start))

    # save the file to .csv format
    if save:

        # create the name of the file to be saved 
        filename = filepath.rsplit('/',1)[1].split('.',1)[0]
        savedir  = 'pd0-parsed/'
        saveext  = '.csv'
        savename = savedir + filename + saveext

        # save the file using pandas 
        save_start = time.time()    
        time_series.df.to_csv(savename)
        save_stop  = time.time()
        print('    saving time: %f'    % (save_stop - save_start))
        print('    output file: %s \n' % (savename))


if __name__ == '__main__': 
    # TODO check if directory or file 
    # for filename in glob.glob(os.path.join(directory_path, '*.pd0')):
    #     # pd0_reader(filename)
    #     print(filename)

    for filename in sys.argv[1:]:
        # TODO
        # cProfile.run('pd0_reader(filename)')
        pd0_reader(filename)  
