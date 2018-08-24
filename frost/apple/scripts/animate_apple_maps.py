#! /Users/rem63/venvs/frost/bin/python

import os, sys

from frost.functions import fromConfig, nameToFilepath
from frost.apple.functions import animationFilepath, mapFilename, mapWorkingDir

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('-d', action='store', type='int', dest='delay', default=30)
parser.add_option('-y', action='store_true', dest='test_path', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

delay = options.delay
debug = options.debug
test_path = options.test_path

animate_cmd_path = fromConfig('animate_cmd_path')
_cmd_tmpl_ = '%s -delay %d %%s -loop 0 %%s' % (animate_cmd_path, delay)

# target year
target_year = int(args[0])

# chill model 
if args[1] == 'all':
    model_names = fromConfig('crops.apple.chill.models')
else: model_names = (args[1],)
model_keys = tuple( [model_name.title() for model_name in model_names] )

# apple variety
if len(args) > 3:
    map_group = 'variety'
    if args[3] == 'all':
        varieties = fromConfig('crops.apple.varieties.child_names')
    else: varieties = (args[3],)

    # map type
    if args[2] == 'all':
        map_types = tuple( [map_type for map_type in 
                            fromConfig('crops.apple.variety.map_types')] )
    else: map_types = (map_type.title(),)

    # generate a set of parameters for each plot
    plots = [ ]
    for variety in varieties:
        for model_name in model_names:
            for map_type in map_types:
                plots.append( (variety, model_name, map_group, map_type) ) 
else:
    # map type
    if args[2] == 'chill':
        map_group = 'chill'
        map_type = 'accumulated'
    else: map_group, map_type = args[2].split('.')

    # generate a set of parameters for each plot
    plots = [ ]
    for model_name in model_names:
        plots.append( (None, model_name, map_group, map_type) )

for variety, model_name, map_group, map_type in plots:
    if debug:
        print '\nanimating', variety, model_name, map_group, map_type
    map_filepath = \
    mapFilename('date', variety, model_name, map_group, map_type)
    if map_type == 'gdd': plot_key = 'GDD'
    else: plot_key = nameToFilepath(map_type)
    png_path = '*%s' % map_filepath[map_filepath.find(plot_key):]

    anim_filepath = \
    animationFilepath(target_year, variety, model_name, map_group, map_type)

    working_dir = \
    mapWorkingDir(target_year, variety, model_name, map_group, map_type)
    os.chdir(working_dir)

    _cmd_ = _cmd_tmpl_ % (png_path, anim_filepath)
    if debug: print _cmd_
    os.system(_cmd_)

