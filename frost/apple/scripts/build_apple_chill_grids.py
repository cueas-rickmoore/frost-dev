#! /Volumes/projects/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.options import stringToTuple
from atmosci.utils.timeutils import daysInYear, lastDayOfMonth

from frost.functions import fromConfig

from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getGddThresholds(options, manager):
    if options.gdd_thresholds is not None: # use thresholds passed via options
        return stringToTuple(options.gdd_thresholds, int)
    else: # no thresholds in options
        # check which GDD thresholds are in the current file
        if manager is not None:
            return manager.gddThresholds()
        # use the GDD thresholds in the configuration file
        return fromConfig('crops.apple.gdd_thresholds')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--gdd', action='store', type='string', dest='gdd_thresholds',
                  default=None)
parser.add_option('--grid', action='store', type='int', dest='acis_grid',
                  default=3)
parser.add_option('--models', action='store', type='string', dest='models',
                  default=None)

parser.add_option('-f', action='store_false', dest='forecast', default=False)
parser.add_option('-g', action='store_false', dest='calc_gdd', default=True)
parser.add_option('-u', action='store_false', dest='update', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

acis_grid = options.acis_grid
calc_gdd = options.calc_gdd
data_bbox = options.bbox
debug = options.debug
forecast = options.forecast
models = options.models
test_file = options.test_file
verbose = options.verbose or debug
update_db = options.update

factory = AppleGridFactory()

num_args = len(args)
if num_args == 0:
    start_date = datetime.now() - ONE_DAY
    end_date = None
elif num_args == 2:
    year = int(args[0])
    month = int(args[1])
    start_date = datetime(year,month,1)
    end_date = datetime(year, month, lastDayOfMonth(year, month))
elif num_args in (3,4,6):
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime(year,month,day)
    if num_args == 3: end_date = None
    elif num_args == 4:
        end_date = start_date + relativedelta(days=int(args[3])-1)
    elif num_args == 6:
        year = int(args[3])
        month = int(args[4])
        day = int(args[5])
        end_date = datetime(year,month,day)
else:
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise SyntaxError, errmsg

# target year is the year that we want to predict frost damage
target_year = factory.getTargetYear(start_date)
if verbose or test_file:
    print 'start date', start_date
    print 'end date', end_date
    print 'target year', target_year
if target_year is None: exit()

dates = factory.datesFromDateSpan(start_date, end_date)

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get maxt/mint from temperature file
temp_reader = factory.getTempGridReader(target_year, test_file)
if data_bbox is None:
    data_bbox = temp_reader.getFileAttribute('data_bbox')
if forecast:
    maxt = temp_reader.getTemp('forecast.maxt', start_date, end_date)
    mint = temp_reader.getTemp('forecast.mint', start_date, end_date)
else:
    temp_start = start_date + ONE_DAY
    if end_date is None:
        maxt = temp_reader.getTemp('reported.maxt', temp_start, None)
        mint = temp_reader.getTemp('reported.mint', temp_start, None)
    else:
        temp_end = end_date + ONE_DAY
        maxt = temp_reader.getTemp('reported.maxt', temp_start, temp_end)
        mint = temp_reader.getTemp('reported.mint', temp_start, temp_end)
temp_reader.close()
del temp_reader

# some versions of HDF5 return a 3D array even if only one day is requested
if maxt.ndim == 3 and maxt.shape[0] == 1:
    maxt = maxt[0]
    mint = mint[0]
maxt_nan_indexes = N.where(N.isnan(maxt))

# get a chill data file manger
filepath = factory.getChillFilePath(target_year, test_file)
if verbose:
    print 'chill file path exists :', os.path.exists(filepath), ':',filepath
if not os.path.exists(filepath):
    if models in (None, 'all'):
        models = fromConfig('crops.apple.chill.models')
    elif ',' in models: models = models.split(',')
    else: models = [models,]
    gdd_thresholds = getGddThresholds(options, None)
    manager = factory.newChillGridManager(target_year, models, gdd_thresholds,
                                          test_file, acis_grid=acis_grid,
                                          data_bbox=data_bbox)
else:
    manager = factory.getChillGridManager(target_year, 'r', test_file)
    if data_bbox != manager.data_bbox:
        errmsg = "'%d' bbox option does not match '%s' bbox already in Chill file %s"
        raise ValueError, errmsg % (data_bbox, manager.data_bbox, filepath)
    if models in (None, 'all'):
        models = [name.lower() for name in manager.file_chill_models]
    elif ',' in models: models = models.split(',')
    else: models = [models,]
    gdd_thresholds = getGddThresholds(options, manager)

midpoint = (manager.lats.shape[0] / 2, manager.lats.shape[1] / 2)
y, x = midpoint
if verbose:
    print 'GDD thresholds', gdd_thresholds
    print 'Chill start date', manager.start_date
    print 'Chill end date', manager.end_date
    print 'Latitude at node[%d,%d] :' % midpoint, manager.lats[y,x]
    print 'Longitude at node[%d,%d] :' % midpoint, manager.lons[y,x]

if verbose:
    if end_date is None:
        print '\nMax Temp in degeees F @ node[%d,%d] :' % midpoint
        print maxt[y,x]
        print 'Min Temp in degress F @ node[%d,%d] :' % midpoint
        print mint[y,x]
        print 'Average Temp in degrees F @ node[%d,%d] :' % midpoint
        print mint[y,x] + ((maxt[y,x] - mint[y,x]) / 2.)
    else:
        print '\nMax Temp @ in degrees F node[%d,%d] :' % midpoint
        print maxt[:,y,x]
        print 'Min Temp @ in degrees F node[%d,%d] :' % midpoint
        print mint[:,y,x]
        print 'Average Temp @ in degrees F node[%d,%d] :' % midpoint
        print mint[:,y,x] + ((maxt[:,y,x] - mint[:,y,x]) / 2.)

# interpolate hourly temperatures from mint,maxt using Linvill algorithm
linvill_array = manager.linvill(dates, mint, maxt, 'F', verbose)

if verbose:
    print '\nLinvill hourly @ node[%d,%d]' % (y,x)
    if len(linvill_array.shape) == 3:
        print linvill_array[:,y,x]
    else: print linvill_array[:,:,y,x]

# build the argument dictionary for the chill calculation method
chill_kwargs = { 'hourly':linvill_array, 'units':'F', 'debug':verbose }
if end_date is None: chill_kwargs['date'] = dates[0]
else: chill_kwargs['dates'] = dates

# accumulate chill hours for each model using hourly temperatures
# derived from the Linvill interpolation algorithm
for model_name in models:
    proper_name = manager.properName(model_name)
    if verbose:
        msg = 'Chill data for %s model' %  model_name
        print '\n\n', msg
        print '=' * len(msg)
    if not manager.chillModelExists(proper_name):
        manager.open('a')
        manager._initChillDatasets(model_name)
        manager.close()
        
    manager.open('r')
    daily_chill, accumulated_chill = manager.estimateChill(model_name, 
                                                           **chill_kwargs)
    manager.close()
    # make sure we didn't get bogus chill
    accumulated_chill[maxt_nan_indexes] = N.nan
    daily_chill[maxt_nan_indexes] = N.nan

    if update_db:
        manager.open('a')
        manager.updateChill(model_name, daily_chill, accumulated_chill,
                            start_date)
        manager.close()
    del daily_chill, accumulated_chill

    # Growing Degree Days
    if calc_gdd:
        if verbose:
            msg = 'Growing Degree Days for %s' % start_date.strftime('%Y-%m-%d')
            if end_date is not None:
                msg += ' thru %s' % end_date.strftime('%Y-%m-%d')
            print '\n\n', msg

        for low_threshold, high_threshold in gdd_thresholds:
            # make sure that the daily dataset is initialized
            manager.open('r')
            # estimate GDD for this low/high threshold combination
            daily_gdd = manager.estimateGDD(low_threshold, high_threshold,
                                            mint, maxt, debug)
            manager.close()

            if update_db:
                group_name = manager.gddGroupName(low_threshold, high_threshold)
                if not manager.hasGroup(group_name):
                    manager.open('a')
                    manager._initGddDatasets(low_threshold, high_threshold)
                    manager.close()
                manager.open('a')
                manager.updateGdd(low_threshold, high_threshold, daily_gdd,
                                  start_date)
                manager.close()
            del daily_gdd

# turn annoying numpy warnings back on
warnings.resetwarnings()
