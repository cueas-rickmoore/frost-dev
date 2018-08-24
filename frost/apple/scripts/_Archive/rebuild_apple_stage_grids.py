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
from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser, OptionValueError
parser = OptionParser()

parser.add_option('-k', action='store_false', dest='rebuild_kill', default=True)
parser.add_option('-u', action='store_false', dest='update', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
rebuild_kill = options.rebuild_kill
test_run = options.test_run
test_file = debug | test_run
verbose = options.verbose or debug
update_db = options.update

variety = args[0]

factory = AppleGridFactory()

num_args = len(args)
if num_args == 2:
    target_year = int(args[1])
    start_date = None
    end_date = None
elif num_args == 3:
    year = int(args[1])
    month = int(args[2])
    start_date = datetime(year,month,1)
    last_day = lastDayOfMonth(year, month)
    end_date = datetime(year, month, last_day)
    target_year = factory.getTargetYear(start_date)
elif num_args in (4,5,7):
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    start_date = datetime(year,month,day)
    if num_args == 4: end_date = None
    elif num_args == 5:
        end_date = start_date + relativedelta(days=int(args[4])-1)
    elif num_args == 7:
        year = int(args[4])
        month = int(args[5])
        day = int(args[6])
        end_date = datetime(year,month,day)
    target_year = factory.getTargetYear(start_date)
else:
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise ValueError, errmsg

if end_date is not None:
    dates = tuple( [ start_date + relativedelta(days=day)
                     for day in range((end_date-start_date).days + 1) ] )
else: dates = (start_date,)
num_days = len(dates)

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get a Variety grid manager for the target year
manager = factory.getVarietyGridManager(target_year, variety, 'r', test_run)

# estimate GDD accumulation, stage and kill probability for this variety
models = [name.lower() for name in manager.file_chill_models]
for model_name in models:
    #  loop trough all GDD thresholds
    gdd_thresholds = manager.gddThresholds(model_name)
    for lo_gdd_th, hi_gdd_th in gdd_thresholds:
        print '\n', model_name, lo_gdd_th, hi_gdd_th
        # get previously calculated GDD accumulation
        manager.open('r')
        accumulated_gdd = manager.getGdd(model_name, lo_gdd_th, hi_gdd_th,
                                         start_date, end_date)

        # generate stage grid from accumulated GDD
        print '\nrecalculating stages\n'
        stage_grid = manager.gddToStages(accumulated_gdd, True)
        # no longer need grid for accumulated GDD
        del accumulated_gdd

        if verbose:
            print '\nstage set to',
            print stage_grid[N.where(stage_grid > 0)]

        if update_db:
            manager.open('a')
            manager.updateStage(model_name, lo_gdd_th, hi_gdd_th, stage_grid,
                                start_date)
            manager.close()
    
        if rebuild_kill:
            # need mint to recalculate kill probability
            manager.open('r')
            if end_date is not None:
                mint = manager.getDataForDates('mint', start_date, end_date)
            else: mint = manager.getDataForDate('mint', start_date)

            # estimate kill probability from stages and predicted mint
            kill_grid = manager.estimateKill(stage_grid, mint, True)
            # no longer need mint or stage grid
            del mint, stage_grid

            if verbose:
                print '\nkill probability',
                print kill_grid[N.where(kill_grid > 0)]

            if update_db:
                manager.open('a')
                manager.updateKill(model_name, lo_gdd_th, hi_gdd_th, kill_grid,
                                   start_date)
                manager.close()
            # no longer need grid for kill
            del kill_grid

# turn annoying numpy warnings back on
warnings.resetwarnings()
