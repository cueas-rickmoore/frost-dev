#! /Users/rem63/venvs/frost/bin/python

import os, sys
from datetime import datetime

import numpy as N

from frost.functions import fromConfig
from frost.visual.maps import setupMap, hiResMap, finishMap
from frost.visual.maps import drawFilledContours
from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

map_group = args[0]
map_type = args[1]

map_config = fromConfig('crops.apple.%s.maps' % map_group)
if len(args) > 2: output_file = args[2]
else: output_file = map_config.no_data[map_type].template

map_options = map_config.options[map_type].attrs
map_options = setupMap(map_options)
map_options['title'] = None
map_options['title2'] = None
map_options['area_template'] = map_config.no_data[map_type].create_with
if 'grid' in map_options: del map_options['grid']

dirpath = os.path.split(output_file)[0]
if dirpath:
    if not os.path.exists(dirpath): os.makedirs(dirpath)
    map_options['outputfile'] = output_file
else:
    dirpath = map_options['shapelocation']
    map_options['outputfile'] = os.path.join(dirpath, output_file)

factory = AppleGridFactory()
target_year = factory.getTargetYear(datetime.now())
reader = factory.getTempGridReader(target_year)

_map_ = hiResMap(reader.getTemp('reported.maxt',reader.start_date),
                  reader.lats, reader.lons, **map_options)
options = _map_[0]
fig1 = fig = _map_[2]
if map_type in ('gdd','accumulated'):
    grid = N.empty(reader.lons.shape, dtype=float)
    grid.fill(N.nan)
    drawFilledContours(grid, reader.lats, reader.lons, **map_options)
else: finishMap(fig, fig, options)

