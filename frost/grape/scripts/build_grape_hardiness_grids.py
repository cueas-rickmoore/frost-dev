#!/Users/rem63/venvs/frost/bin/python

import os, sys
import re
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.options import stringToTuple
from atmosci.utils.timeutils import daysInYear, lastDayOfMonth
from atmosci.utils.timeutils import timeSpanToIntervals

from frost.functions import fromConfig

from frost.grape.factory import GrapeGridFactory
from frost.grape.functions import getGrapeVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser, OptionValueError
parser = OptionParser()

parser.add_option('-u', action='store_false', dest='update', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
test_run = options.test_run
verbose = options.verbose or debug
update_db = options.update

factory = GrapeGridFactory()

variety = getGrapeVariety(args[0])

num_date_args = len(args[1:])
if num_date_args == 0:
    start_date = datetime.now()
    end_date = None
elif num_date_args == 1:
    target_year = int(args[1])
    start_date, end_date = factory.getTargetDateSpan(target_year)
elif num_date_args == 2:
    year = int(args[1])
    month = int(args[2])
    start_date = datetime(year,month,1)
    last_day = lastDayOfMonth(year, month)
    end_date = datetime(year, month, last_day)
    target_year = factory.getTargetYear(start_date)
elif num_date_args in (3,4,6):
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    start_date = datetime(year,month,day)
    end_date = None #!TODO: remove when allowing multiple days
    if num_date_args == 3: end_date = None
    elif num_date_args == 4:
        end_date = start_date + relativedelta(days=int(args[4])-1)
    elif num_date_args == 6:
        year = int(args[4])
        month = int(args[5])
        day = int(args[6])
        end_date = datetime(year,month,day)
    target_year = factory.getTargetYear(start_date)
else:
    print sys.argv
    errmsg = 'Invalid number of arguments (%d).' % num_date_args
    raise ValueError, errmsg
# need data from day previous to start date
prev_start = start_date - ONE_DAY

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get a variety data file manger
filepath = factory.getVarietyFilePath(target_year, variety, test_run)
if not os.path.exists(os.path.normpath(filepath)):
    variety_manager = \
    factory.newVarietyManager(target_year, variety, test_run, verbose)
else:
    variety_manager = \
    factory.getVarietyManager(target_year, variety, 'r', test_run)

# make sure managers can read their data files
variety_manager.open('r')
target_start_date = variety_manager.start_date
if start_date < target_start_date:
    errmsg = 'Start date is before beginnig of dormancy period for the model.'
    raise ValueError, errmsg

# get required data for date previous to single day
if end_date is None:
    # single day, not first day in season
    if start_date > target_start_date:
        dormancy_stage = variety_manager.getDormancy(start_date)
        # dormancy-based chill
        prev_accum_chill = \
        variety_manager.getChillData('dormancy', 'accumulated', prev_start)
        prev_daily_chill = \
        variety_manager.getChillData('dormancy', 'daily', prev_start)
        # dormancy-based GDD
        prev_gdd = variety_manager.getGDD('daily', prev_start)
        # previous hardiness is always one day
        prev_hardiness = variety_manager.getHardiness(prev_start)

    # first day of season, nothing to estimate yet because it is, in fact,
    # the previous day to the entire season, so create default grids
    elif start_date == target_start_date:
        shape = variety_manager.lons.shape

        # use reported mint grid to fill invalid grid nodes with nans
        temp_manager = factory.getTempGridReader(target_year, test_run)
        mint = temp_manager.getTemp('reported.mint', start_date, units='C')
        temp_manager.close()
        nan_indexes = N.where(N.isnan(mint))
        del temp_manager, mint

        dormancy_stage = N.zeros(shape, dtype=int)
        dormancy_stage[nan_indexes] = \
            fromConfig('crops.grape.groups.dormancy.datasets.stage.missing')
        # dormancy-based chill
        prev_accum_chill = N.zeros(shape, dtype=float)
        prev_accum_chill[nan_indexes] = N.nan
        prev_daily_chill = N.zeros(shape, dtype=float)
        prev_daily_chill[nan_indexes] = N.nan
        # accumulated dormancy-based GDD
        prev_gdd = N.zeros(shape, dtype=float)
        prev_gdd[nan_indexes] = N.nan
        # previous hardiness is always one day
        prev_hardiness = N.empty(shape, dtype=float)
        # fill hardiness grid with the appropriate initial hardiness temp
        prev_hardiness.fill(variety.hardiness.init)
        prev_hardiness[nan_indexes] = N.nan

# processing multiple days at once
else:
    prev_end = end_date - ONE_DAY
    if start_date > target_start_date:
        dormancy_stage = variety_manager.getDormancy(prev_start, prev_end)
        # dormancy-based chill
        prev_accum_chill = variety_manager.getChillData('dormancy',
                                           'accumulated', prev_start, prev_end)
        prev_daily_chill = \
            variety_manager.getChillData('dormancy','daily',prev_start,prev_end)
        # dormancy-based GDD
        prev_gdd = variety_manager.getGDD('daily', prev_start)
        # previous hardiness is always one day
        prev_hardiness = variety_manager.getHardiness(prev_start)

    elif start_date == target_start_date:

        num_days = (end_date - start_date).days + 1
        shape_2D = variety_manager.lons.shape
        shape_3D = (num_days,) + variety_manager.lons.shape

        # use reported mint grid to fill invalid grid nodes with nans
        temp_manager = factory.getTempGridReader(target_year, test_run)
        mint = temp_manager.getTemp('reported.mint', start_date, units='C')
        temp_manager.close()
        nan_indexes = N.where(N.isnan(mint))
        del temp_manager, mint
        prev_zeros = N.zeros(shape_2D, dtype=float)
        prev_zeros[nan_indexes]  = N.nan

        dormancy_stage = N.empty(shape_3D, dtype=int)
        dormancy_stage[0] = N.zeros(shape_2D, dtype=int)
        dormancy_stage[0][nan_indexes] = \
            fromConfig('crops.grape.groups.dormancy.datasets.stage.missing')
        dormancy_stage[1:] = variety_manager.getDormancy(start_date, prev_end)

        # dormancy-based chill
        prev_accum_chill = N.empty(shape_3D, dtype=float)
        prev_accum_chill[0] = prev_zeros
        prev_accum_chill[1:] = variety_manager.getChillData('dormancy',
                                       'accumulated', start_date, prev_end)
        prev_daily_chill = N.empty(shape_3D, dtype=float)
        prev_daily_chill[0] = prev_zeros
        prev_daily_chill[1:] = variety_manager.getChillData('dormancy',
                                       'daily', start_date, prev_end)
        # dormancy-based GDD
        prev_gdd = N.empty(shape_3D, dtype=float)
        prev_gdd[0] = prev_zeros
        prev_gdd[1:] = variety_manager.getGDD('daily', start_date, prev_end)

        # previous hardiness is always one day
        # create grid with default initial hardiness
        prev_hardiness = N.zeros(shape_2D, dtype=float)
        prev_hardiness.fill(variety_manager.hardiness.init)
        prev_hardiness[nan_indexes] = N.nan

hardiness, acclimation, deacclimation = \
variety_manager.estimateHardiness(dormancy_stage, prev_daily_chill,
                                  prev_accum_chill, prev_gdd, prev_hardiness)

if update_db:
    variety_manager.open('a')
    variety_manager.updateAcclimation(acclimation, start_date)
    variety_manager.updateDeacclimation(deacclimation, start_date)
    variety_manager.updateHardiness(hardiness, start_date)
    variety_manager.close()
else:
    print '\nacclimation\n', acclimation
    print '\ndeacclimation\n', deacclimation
    print '\nhardiness\n', hardiness

# turn annoying numpy warnings back on
warnings.resetwarnings()
