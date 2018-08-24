#!/Users/rem63/venvs/frost/bin/python

import os, sys

from frost.factory import FrostGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-x', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
test_file = options.test_file
verbose = options.verbose or debug

target_year = int(args[0])

frost_factory = FrostGridFactory()

temp_manager = frost_factory.getTempGridManager(target_year, 'a')
bbox = temp_manager.getFileAttribute('search_bbox')
temp_manager.setFileAttribute('data_bbox', bbox)
temp_manager.deleteFileAttribute('search_bbox')
temp_manager.close()

