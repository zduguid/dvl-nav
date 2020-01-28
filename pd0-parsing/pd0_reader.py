# TimeSeries.py
#
# Represents a time series of Doppler Velocity Log ensembles. 
#   2020-01-27  zduguid@mit.edu         TODO


import glob
import json
import os 
import sys
import time
from Ensemble import Ensemble


def pd0_read(filename):
    """
    TODO
    """
    timeseries = init_timeseries_dict()
    pd0_file   = open(filename, 'rb').read()
    ensembles  = 0
    print('parsing new file')
    print('  input file:    %s' % (filename,))
    parse_start = time.time()

    # parse ensembles until the end of the pd0 file is reached    
    while len(pd0_file) > 0:

        # parse an ensemble from the pd0 file
        ensemble = Ensemble(pd0_file)
        # ensemble = Ensemble(memoryview(pd0_file))
        
        # chop off the ensemble we just ensemble
        ensemble_len = ensemble.data['header']['num_bytes'] + 2
        pd0_file     = pd0_file[ensemble_len:]
        ensembles   += 1

        # TODO make all of these individual functions?
        # TODO think of better way to avoid repeated code 
        
        ensemble_val = ensemble.data['timestamp']
        timeseries['timestamp'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['bin_1_distance']
        timeseries['bin_1_distance'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['blank_after_transmit']
        timeseries['blank_after_transmit'].append(ensemble_val)

        ensemble_val = ensemble.data['bottom_track']
        timeseries['bottom_track'].append(ensemble_val)

        ensemble_val = ensemble.data['correlation']['data']
        timeseries['correlation'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['coordinate_transformation']
        timeseries['coordinate_transformation'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['depth_cell_length']
        timeseries['depth_cell_length'].append(ensemble_val)

        ensemble_val = ensemble.data['variable_leader']['depth_of_transducer']
        timeseries['depth_of_transducer'].append(ensemble_val)

        ensemble_val = ensemble.data['echo_intensity']['data']
        timeseries['echo_intensity'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['ending_depth_cell']
        timeseries['ending_depth_cell'].append(ensemble_val)

        ensemble_val = ensemble.data['variable_leader']['heading']
        timeseries['heading'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['num_beams']
        timeseries['num_beams'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['num_cells']
        timeseries['num_cells'].append(ensemble_val)

        ensemble_val = ensemble.data['percent_good']['data']
        timeseries['percent_good'].append(ensemble_val)

        ensemble_val = ensemble.data['variable_leader']['pitch']
        timeseries['pitch'].append(ensemble_val)

        ensemble_val = ensemble.data['variable_leader']['roll']
        timeseries['roll'].append(ensemble_val)

        ensemble_val = ensemble.data['variable_leader']['speed_of_sound']
        timeseries['speed_of_sound'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['starting_depth_cell']
        timeseries['starting_depth_cell'].append(ensemble_val)

        ensemble_val = ensemble.data['variable_leader']['temperature']
        timeseries['temperature'].append(ensemble_val)

        ensemble_val = ensemble.data['fixed_leader']['transmit_lag_distance']
        timeseries['transmit_lag_distance'].append(ensemble_val)

        ensemble_val = ensemble.data['velocity']['data']
        timeseries['velocity'].append(ensemble_val)

    parse_stop = time.time()
    extension_length = 4
    savename = filename[:-extension_length] + '.json'
    print('  num ensembles: %d'    % (ensembles))
    print('  parsing time:  %f'    % (parse_stop-parse_start))
    print('  output file:   %s' % (savename))

    # save the data 
    save_start = time.time()
    json.dump(timeseries, open(savename, 'w'), 
               sort_keys=True, indent=2, default=str,
               separators=(',', ': '))  
    save_stop  = time.time()
    print('  saving time:   %f \n' % (save_stop-save_start))


def init_timeseries_dict():
    '''
    TODO
    '''
    timeseries = {}
    fixed_leader_fields = [] 
    timeseries_fields = ['timestamp',
                         'bin_1_distance',
                         'blank_after_transmit',
                         'bottom_track',
                         'correlation',
                         'coordinate_transformation',
                         'depth_cell_length',
                         'depth_of_transducer',
                         'echo_intensity',
                         'ending_depth_cell',
                         'heading',
                         'num_beams',
                         'num_cells',
                         'percent_good',
                         'pitch',
                         'roll',
                         'speed_of_sound',
                         'starting_depth_cell',
                         'temperature',
                         'transmit_lag_distance',
                         'velocity']
    for field in timeseries_fields:
        timeseries[field] = []
    return(timeseries)


if __name__ == '__main__': 
    # for filename in sys.argv[1:]:
    #     pd0_read(filename)

    # TODO adjust file path
    directory_path = '/Users/zduguid/Documents/Arctic-NNA/data/2019-Santorini/gliders/unit_770/from-glider'

    # TODO check if directory or file 
    # for filename in glob.glob(os.path.join(directory_path, '*.pd0')):
    #     # pd0_read(filename)
    #     print(filename)

    for filename in sys.argv[1:]:
        pd0_read(filename)  
