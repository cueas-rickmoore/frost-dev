#! /Volumes/projects/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.options import stringToTuple
from atmosci.utils.timeutils import daysInYear, lastDayOfMonth

from frost.factory import FrostGridFactory
from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-f', action='store_true', dest='forecast', default=False)
parser.add_option('-r', action='store_true', dest='reported', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
forecast = options.forecast
reported = options.reported | (not options.reported and not options.forecast)
test_file = options.test_file
test_file = test_file
verbose = options.verbose or debug

if debug: print '\ndownload_latest_temp_grids.py', args

num_args = len(args)
if num_args == 0:
    start_date = datetime.now()
elif num_args == 3:
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime(year,month,day)
else:
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise SyntaxError, errmsg

factory = FrostGridFactory()
# target year is the year that we want to predict frost damage
target_year = factory.getTargetYear(start_date)
if target_year is None: exit()

if debug: print 'dates', target_year, start_date

season_start = datetime(target_year-1, *fromConfig('crops.apple.start_day'))
season_end = datetime(target_year, *fromConfig('crops.apple.end_day'))
temp_end = season_end + ONE_DAY
if start_date > temp_end and start_date < season_start: exit()

# get a temperature data file manger
filepath = factory.getTempGridFilePath(target_year, test_file)
if debug:
    print 'temp filepath', os.path.exists(os.path.normpath(filepath)), filepath
if not os.path.exists(os.path.normpath(filepath)):
    manager = factory.newTempGridManager(target_year, None, verbose,
                                         test_file)
else: manager = factory.getTempGridManager(target_year, 'r', test_file)
if debug:
    print 'temp manager', manager
    print 'temp manager file', manager.filepath

# download current ACIS mint,maxt for current date
acis_grid = manager.getDatasetAttribute('reported.maxt', 'acis_grid')
manager.close()
data = factory.getAcisGridData('mint,maxt', start_date, None, None, 
                                manager.data_bbox, int(acis_grid),
                                debug=debug)
if debug: print 'temp data\n', data

manager.open('a')
manager.updateTemp('reported.maxt', data['maxt'], start_date)
manager.updateTemp('reported.mint', data['mint'], start_date)
manager.close()

# download forecast NDFD mint,maxt for several days ahead
#data = factory.getNdfdGridData('mint,maxt', start_date, end_date, None, 
#                               manager.search_bbox, debug=debug)
#manager.open('a')
#manager.updateTemp('forecast.maxt', data['maxt'], start_date)
#manager.updateTemp('forecast.mint', data['mint'], start_date)
##manager.close()

os._exit(0)

