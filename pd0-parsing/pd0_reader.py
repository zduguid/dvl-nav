# pd0_reader.py
# wrapper around USF PD0 code, reads a TWR pd0 file, parses individual
# ensembles out ot it
#   2018-11-26  dpingal@teledyne.com    Initial
#   TODO        zduguid@mit.edu         TODO


import glob
import json
import os 
import sys
from Ensemble import Ensemble


def pd0_read(filename):
    """
    TODO
    """
    timeseries = init_timeseries_dict()
    pd0_file   = open(filename, 'rb').read()
    # print(pd0_file)
    ensembles  = 0
    print('parsing: ', filename)
    
    # TODO
    # for i in range(2):
    while len(pd0_file) > 0:
        # parse an ensemble from the pd0 file
        ensemble = Ensemble(pd0_file)
        # ensemble = pd0_parser.parse_ensemble(pd0_file)
        
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

        try:
            ensemble_val = ensemble.data['bottom_track']
        except KeyError:
            ensemble_val = None
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

    extension_length = 4
    savename = filename[:-extension_length] + '.json'
    print('parsing: ', savename, '(ensembles = ', ensembles, ') \n')

    # save the data 
    json.dump(timeseries, open(savename, 'w'), 
               sort_keys=True, indent=2, default=str,
               separators=(',', ': '))  


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
    # TODO add option for combining multiple .pd0 files 

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
