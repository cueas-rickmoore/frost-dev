#!/Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.grape.factory import GrapeGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-t', action='store_true', dest='from_temp', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-x', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
from_temp = options.from_temp
test_file = options.test_file
verbose = options.verbose or debug

target_year = int(args[0])
grape_variety = args[1]
grape_factory = GrapeGridFactory()

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

if from_temp:
    from frost.factory import FrostGridFactory
    from frost.grape.builder import GrapeVarietyGridBuilder

    start_date, end_date = grape_factory.getTargetDateSpan(target_year)

    frost_factory = FrostGridFactory()
    frost_manager = frost_factory.getTempGridManager(target_year, 'r')
    lats = frost_manager.lats
    lons = frost_manager.lons
    frost_manager.close()

    grape_manager = GrapeVarietyGridBuilder(grape_variety, start_date, end_date,
                                lons, lats, frost_manager.search_bbox,
                                frost_manager.acis_grid, verbose=verbose)
    grape_manager.close()
    frost_manager.close()
else:
    grape_manager = grape_factory.newVarietyManager(target_year, grape_variety)
    grape_manager.close()

print 'created grape variety file :', grape_manager._hdf5_filepath

# turn annoying numpy warnings back on
warnings.resetwarnings()

