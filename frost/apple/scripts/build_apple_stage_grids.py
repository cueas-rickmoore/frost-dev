#! /Volumes/projects/venvs/frost/bin/python

import os, sys
import re
import warnings

import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.options import stringToTuple
from atmosci.utils.timeutils import daysInYear, lastDayOfMonth
from atmosci.utils.timeutils import timeSpanToIntervals

from frost.functions import fromConfig
from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getAppleVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getGddThresholds(options, manager, model_name=None):
    if options.gdd_thresholds is not None: # use thresholds passed via options
        return stringToTuple(options.gdd_thresholds, int)
    else: # no thresholds in options
        # check which GDD thresholds are in the current file
        if manager is not None:
            if model_name is None: return manager.gddThresholds()
            else: return manager.gddThresholds(model_name)
        else: # current file has no GDD data
            # use the GDD thresholds in the configuration file
            return fromConfig('crops.apple.gdd_thresholds')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser, OptionValueError
parser = OptionParser()

parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--gdd', action='store', type='string', dest='gdd_thresholds',
                  default=None)
parser.add_option('--grid', action='store', type='int', dest='acis_grid',
                  default=3)
parser.add_option('--models', action='store', type='string', dest='models',
                  default=None)

parser.add_option('-d', action='store_false', dest='download_mint',
                   default=True)
parser.add_option('-f', action='store_true', dest='forecast', default=False)
parser.add_option('-g', action='store_false', dest='calc_gdd', default=True)
parser.add_option('-u', action='store_false', dest='update', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

acis_grid = options.acis_grid
calc_gdd = options.calc_gdd
debug = options.debug
download_mint = options.download_mint
forecast = options.forecast
test_file = options.test_file
verbose = options.verbose or debug
update_db = options.update

variety = getAppleVariety(args[0])

factory = AppleGridFactory()

num_args = len(args[1:])
if num_args == 1:
    target_year = int(args[1])
    start_date = None
    end_date = None
elif num_args == 2:
    year = int(args[1])
    month = int(args[2])
    start_date = datetime.datetime(year,month,1)
    last_day = lastDayOfMonth(year, month)
    end_date = datetime.datetime(year, month, last_day)
    target_year = factory.getTargetYear(start_date)
elif num_args in (3,4,6):
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    start_date = datetime.datetime(year,month,day)
    if num_args == 3: end_date = None
    elif num_args == 4:
        end_date = datetime.datetime(year,month,int(args[4]))
    elif num_args == 6:
        year = int(args[4])
        month = int(args[5])
        day = int(args[6])
        end_date = datetime.datetime(year,month,day)
    target_year = factory.getTargetYear(start_date)
else:
    print sys.argv
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise ValueError, errmsg
if target_year is None: exit()

# in case script goes haywire
max_valid_date = datetime.date.today() - ONE_DAY
max_valid_str = max_valid_date.strftime('%Y-%m-%d')


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get the chill data file manger for the target year ... IT MUST ALREADY EXIST
chill_manager = factory.getChillGridManager(target_year, 'r', test_file)

if options.bbox is None:
    data_bbox = chill_manager.data_bbox
elif options.bbox != chill_manager.data_bbox:
    errmsg = "'%d' bbox option does not match '%s' bbox already in Chill file : %s"
    errmsg = errmsg % (data_bbox, chill_manager.data_bbox, filepath)
    raise ValueError, errmsg

if start_date is None:
    start_date = chill_manager.start_date
    end_date = chill_manager.end_date

print 'start/end date :', start_date, end_date

if options.models is None:
    models = [name.lower() for name in chill_manager.file_chill_models]
elif options.models == 'all':
    models = fromConfig('crops.apple.chill.models')
elif ',' in options.models: models = stringToTuple(options.models)
else: models = (options.models,)

gdd_thresholds = getGddThresholds(options, chill_manager)

# y,x indexes for midpoint of data arays
midpoint = (chill_manager.lats.shape[0] / 2, chill_manager.lats.shape[1] / 2)
y, x = midpoint

# get mint from temperature file
temp_reader = factory.getTempGridReader(target_year, test_file)
if forecast:
    mint = temp_reader.getTemp('forecast.mint', start_date, end_date)
else:
    temp_start = start_date + ONE_DAY
    if end_date is None:
        mint = temp_reader.getTemp('reported.mint', temp_start, None)
    else: 
        temp_end = end_date + ONE_DAY
        mint = temp_reader.getTemp('reported.mint', temp_start, temp_end)
temp_reader.close()
del temp_reader

# need to save the indexes where NANs occur in mint
mint_nan_indexes = N.where(N.isnan(mint))
if verbose:
    print '\n min temp :', mint.shape, ': nans =', len(mint_nan_indexes[0]), 'of ', N.prod(mint.shape)

# get a Variety grid manager for the target year
filepath = factory.getVarietyFilePath(target_year, variety, test_file)
if os.path.exists(filepath):
    variety_manager = \
    factory.getVarietyGridManager(target_year, variety, 'a', test_file)
else: # create a new Variety grid file
    gdd_thresholds = chill_manager.gddThresholds()
    variety_manager = \
    factory.newVarietyGridManager(target_year, variety, models,
               gdd_thresholds, test_file, verbose, data_bbox=data_bbox)

# save the temperature grid to the variety grid file
variety_manager.close()
if debug:
    print 'Min Temp @ in degrees F node[%d,%d] :' % midpoint
    if end_date is None: print mint[y,x]
    else:    print mint[:,y,x]

# make sure managers can read their data files
chill_manager.open('r')
variety_manager.open('r')

variety_titled = variety.name.replace('_',' ').title()
# estimate GDD accumulation, stage and kill probability for this variety
for model_name in models:
    model_titled = model_name.title()
    # get the Chill accumulation
    accumulated_chill = chill_manager.getChill(model_name, 'accumulated',
                                               start_date, end_date)
    if verbose:
        num_zeros = len(N.where(accumulated_chill == 0)[0])
        print '\nchill accumulation :', accumulated_chill.shape, ': zeros =', num_zeros, 'of ', N.prod(accumulated_chill.shape)
    if debug: print accumulated_chill[N.where(accumulated_chill > 0)], '\n'

    #  loop trough all GDD thresholds
    for lo_gdd_th, hi_gdd_th in gdd_thresholds:
        model_group = '%s.L%dH%d' % (model_name.title(), lo_gdd_th, hi_gdd_th)

        # get daily GDD from the chill grid file
        daily_gdd = chill_manager.getGdd(lo_gdd_th, hi_gdd_th,
                                         start_date, end_date)
        if verbose:
            num_zeros = len(N.where(daily_gdd == 0)[0])
            print 'daily_gdd (from chill manager) :', daily_gdd.shape, ': zeros =', num_zeros, 'of ', N.prod(daily_gdd.shape)
        if debug: print daily_gdd[N.where(accumulated_chill > 0)], '\n'

        # calculuate accumulated GDD from daily gdd
        # let GDD manger get accumulated GDD for previous day
        variety_manager.open('r')
        # get previously accumulatedg GDD
        accumulated_gdd, chill_mask =\
        variety_manager.accumulateGdd(model_name, lo_gdd_th, hi_gdd_th,
                                      start_date, accumulated_chill, daily_gdd)
        variety_manager.close()

        # no longer need grid for daily GDD
        del daily_gdd

        if verbose:
            num_zeros = len(N.where(accumulated_gdd == 0)[0])
            print 'accumulated_gdd :', accumulated_gdd.shape, ': zeros =', num_zeros, 'of ', N.prod(accumulated_gdd.shape)
        if debug:
            print '\nnodes with GDD accumulation > 0 :',
            print accumulated_gdd[N.where(accumulated_gdd > 0)], '\n'

        if update_db:
            subgroup = '%s.gdd' % model_group
            variety_manager.open('a')
            variety_manager.updateGdd(model_name, lo_gdd_th, hi_gdd_th,
                                      accumulated_gdd, chill_mask, start_date)
            last_valid = variety_manager.getDatasetAttribute('%s.accumulated' % subgroup, 'last_valid_date')
            variety_manager.close()
            print 'updated', variety_titled, model_titled, 'accumulated gdd'

            last_valid = datetime.date(*tuple([int(d) for d in last_valid.split('-')]))
            if last_valid > max_valid_date:
                variety_manager.open('a')
                variety_manager.setDatasetAttribute('%s.accumulated' % subgroup, 'last_valid_date', max_valid_str)
                variety_manager.setDatasetAttribute('%s.chill_mask' % subgroup, 'last_valid_date', max_valid_str)
                variety_manager.setDatasetAttribute('%s.provenance' % subgroup, 'last_valid_date', max_valid_str)
                variety_manager.close()

        # generate stage grid from accumulated GDD
        stage_grid = variety_manager.gddToStages(accumulated_gdd)
        if verbose:
            print '\n', variety_titled, 'stage grid :', stage_grid.shape, 'total nodes =', N.prod(stage_grid.shape)
            print '            stage  > 0 =', len(N.where(stage_grid > 0)[0])
            print '            stage == 0 =', len(N.where(stage_grid == 0)[0])
        # no longer need grid for accumulated GDD
        del accumulated_gdd

        if debug:
            print '\nnodes with stage > 0 :'
            print stage_grid[N.where(stage_grid > 0)]

        if update_db:
            subgroup = '%s.stage' % model_group
            variety_manager.open('a')
            variety_manager.updateStage(model_name, lo_gdd_th, hi_gdd_th, stage_grid, start_date)
            last_valid = variety_manager.getDatasetAttribute('%s.index' % subgroup, 'last_valid_date')
            variety_manager.close()
            print 'updated', variety_titled, model_titled, 'stage'

            last_valid = datetime.date(*tuple([int(d) for d in last_valid.split('-')]))
            if last_valid > max_valid_date:
                variety_manager.open('a')
                variety_manager.setDatasetAttribute('%s.index' % subgroup, 'last_valid_date', max_valid_str)
                variety_manager.setDatasetAttribute('%s.provenance' % subgroup, 'last_valid_date', max_valid_str)
                variety_manager.close()
    
        # estimate kill probability from stages and predicted mint
        kill_grid = variety_manager.estimateKill(stage_grid, mint)
        if verbose:
            print '\n', variety_titled, 'kill grid :', kill_grid.shape, 'total nodes =', N.prod(kill_grid.shape)
            print '            kill  > 0 =', len(N.where(kill_grid > 0)[0])
            print '            kill == 0 =', len(N.where(kill_grid == 0)[0])
        # no longer need stage grid
        del stage_grid

        if debug:
            print '\nnodes with kill probability > 0 :'
            print kill_grid[N.where(kill_grid > 0)], '\n'

        if update_db:
            subgroup = '%s.kill' % model_group
            variety_manager.open('a')
            variety_manager.updateKill(model_name, lo_gdd_th, hi_gdd_th,
                                       kill_grid, start_date)
            last_valid = variety_manager.getDatasetAttribute('%s.level' % subgroup, 'last_valid_date')
            variety_manager.close()
            print 'updated', variety_titled, model_titled, 'kill'

            last_valid = datetime.date(*tuple([int(d) for d in last_valid.split('-')]))
            if last_valid > max_valid_date:
                variety_manager.open('a')
                variety_manager.setDatasetAttribute('%s.level' % subgroup, 'last_valid_date', max_valid_str)
                variety_manager.setDatasetAttribute('%s.provenance' % subgroup, 'last_valid_date', max_valid_str)
                variety_manager.close()

        # no longer need grid for kill
        del kill_grid

# turn annoying numpy warnings back on
warnings.resetwarnings()
