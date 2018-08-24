#! /Users/rem63/venvs/frost/bin/python

import os, sys

from frost.functions import fromConfig, nameToFilepath

from frost.grape.factory import GrapeGridFactory
from frost.grape.functions import getGrapeVariety, animationFilepath
from frost.grape.functions import mapFilename, mapWorkingDir

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

# grape variety
variety = getGrapeVariety(args[1])

# type of map to animate
map_key = args[2]

map_filepath = mapFilename('date', variety, map_key)

anim_map_key = nameToFilepath(map_key)
png_path = '*%s' % map_filepath[map_filepath.find(anim_map_key):]

anim_filepath = animationFilepath(target_year, variety, map_key)

working_dir = \
mapWorkingDir(target_year, variety, *map_key.split(','))
os.chdir(working_dir)

_cmd_ = _cmd_tmpl_ % (png_path, anim_filepath)
if debug: print _cmd_
os.system(_cmd_)
print 'animation saved to :', anim_filepath

