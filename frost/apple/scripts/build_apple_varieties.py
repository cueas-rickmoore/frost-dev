#! /usr/bin/env python

import os, sys

from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser = OptionParser(usage="usage: %prog [year month day] [options]")
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug

script_dir = os.path.split(os.path.abspath(__file__))[0]
script = os.path.join(script_dir, 'build_apple_stage_grids.py')

command = '%s variety %s' % (script, str(args[1:])[1:-1].replace(',',' '))
if debug: command = '%s -z' % command

if args[0] == 'all':
    for variety in fromConfig('crops.apple.varieties.build'):
        if debug: print '\nbuilding', variety
        os.system(command.replace('variety', variety))
else: os.system(command.replace('variety', args[0]))

