# pd0_reader.py
#
# Represents a time series of Doppler Velocity Log ensembles. 
#   2020-01-27  zduguid@mit.edu         TODO

import glob
import os
import sys
import time
import pandas as pd
import seaborn as sns 
from matplotlib import pyplot as plt
from PathfinderEnsemble import PathfinderEnsemble


def pd0_reader(filename, save=True):
    """
    TODO
    """
    pd0_file = open(filename, 'rb').read()
    ensemble_count = 0
    print('parsing new file')
    print('  input file:    %s' % (filename,))
    parse_start = time.time()

    # parse first ensemble to initialize time-series 
    time_series = PathfinderEnsemble(pd0_file)
    ensemble_len = time_series.num_bytes + 2
    pd0_file = pd0_file[ensemble_len:]
    ensemble_count += 1


    # parse ensembles until the end of the pd0 file is reached    
    while len(pd0_file) > 0:

        # parse an ensemble from the pd0 file
        ensemble = PathfinderEnsemble(pd0_file)
        time_series.df = pd.concat([time_series.df, ensemble.df], axis=0)

        # chop off the ensemble we just ensemble
        ensemble_len = ensemble.num_bytes + 2
        pd0_file     = pd0_file[ensemble_len:]
        ensemble_count   += 1

    parse_stop = time.time()
    extension_length = 4
    savename = filename[:-extension_length] + '.csv'
    print('  num ensembles: %d'    % (ensemble_count))
    print('  parsing time:  %f'    % (parse_stop-parse_start))

    # save the data 
    save_start = time.time()
    time_series.df.to_csv(savename)
    save_stop  = time.time()
    print('  saving time:   %f'    % (save_stop-save_start))
    print('  output file:   %s \n' % (savename))
    print('  plotting:')

    # plotting
    plt.figure(figsize=(15, 7))
    sns.lineplot(x="roll", y="pitch",
                 data=time_series.df)
    plt.show()



if __name__ == '__main__': 
    # for filename in sys.argv[1:]:
    #     pd0_reader(filename)

    # TODO adjust file path
    directory_path = '/Users/zduguid/Documents/Arctic-NNA/data/2019-Santorini/gliders/unit_770/from-glider'

    # TODO check if directory or file 
    # for filename in glob.glob(os.path.join(directory_path, '*.pd0')):
    #     # pd0_reader(filename)
    #     print(filename)

    for filename in sys.argv[1:]:
        pd0_reader(filename)  
