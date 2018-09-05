#!  /Volumes/projects/venvs/frost/bin/python

import os, sys
import warnings

import datetime
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

end_date = None
num_args = len(args)
if num_args == 0:
    start_date = datetime.datetime.now()
elif num_args in (3,4,5,6):
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime.datetime(year,month,day)
    if num_args == 4:
        day = int(args[3])
        end_date = datetime.datetime(year,month,day)
    elif num_args == 5:
        month = int(args[3])
        day = int(args[4])
        end_date = datetime.datetime(year,month,day)
    elif num_args == 6:
        year = int(args[3])
        month = int(args[4])
        day = int(args[5])
        end_date = datetime.datetime(year,month,day)
else:
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise SyntaxError, errmsg

factory = FrostGridFactory()

# target year is the year that we want to predict frost damage
target_year = factory.getTargetYear(start_date)
if debug:
    print 'dates', target_year, start_date, end_date

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
    print 'temp manager file', manager._hdf5_filepath

# download current ACIS mint,maxt for current date
acis_grid = manager.getDatasetAttribute('reported.maxt', 'acis_grid')
data = factory.getAcisGridData('mint,maxt', start_date, end_date, None, 
                                manager.data_bbox, int(acis_grid),
                                debug=debug)
if debug: print 'temp data\n', data

manager.open('a')
manager.updateTemp('reported.maxt', data['maxt'], start_date)
last_valid = manager.getDatasetAttribute('reported.maxt', 'last_valid_date')
manager.updateTemp('reported.mint', data['mint'], start_date)
manager.close()

last_valid = datetime.date(*tuple([int(d) for d in last_valid.split('-')]))
today = datetime.date.today()
if last_valid > today:
    today = today.strftime('%Y-%m-%d')
    manager.open('a')
    manager.setDatasetAttribute('reported.maxt', 'last_valid_date', today)
    manager.setDatasetAttribute('reported.mint', 'last_valid_date', today)
    manager.close()

# download forecast NDFD mint,maxt for several days ahead
#data = factory.getNdfdGridData('mint,maxt', start_date, end_date, None, 
#                               manager.search_bbox, debug=debug)
#manager.open('a')
#manager.updateTemp('forecast.maxt', data['maxt'], start_date)
#manager.updateTemp('forecast.mint', data['mint'], start_date)
##manager.close()

os._exit(0)

