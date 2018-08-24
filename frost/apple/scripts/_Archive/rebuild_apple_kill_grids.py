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

parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
test_run = options.test_run
verbose = options.verbose or debug

variety = fromConfig('crops.apple.variety.%s.self' % args[0])
model_name = args[1]

factory = AppleGridFactory()

num_args = len(args[2:])
print args[2:]
if num_args == 1:
    target_year = int(args[2])
    start_date = None
    end_date = None
elif num_args == 2:
    year = int(args[2])
    month = int(args[3])
    start_date = datetime(year,month,1)
    last_day = lastDayOfMonth(year, month)
    end_date = datetime(year, month, last_day)
    target_year = factory.getTargetYear(start_date)
elif num_args in (3,4,6):
    year = int(args[2])
    month = int(args[3])
    day = int(args[4])
    start_date = datetime(year,month,day)
    if num_args == 3: end_date = None
    elif num_args == 4:
        end_date = start_date + relativedelta(days=int(args[5])-1)
    elif num_args == 6:
        year = int(args[5])
        month = int(args[6])
        day = int(args[7])
        end_date = datetime(year,month,day)
    target_year = factory.getTargetYear(start_date)
else:
    print sys.argv
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise ValueError, errmsg

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get a Variety grid manager for the target year
variety_manager = \
factory.getVarietyGridManager(target_year, variety.name, 'a', test_run)

# get the min temperature grid
mint = variety_manager.getTemp('mint', start_date, end_date)

if verbose:
    print '\n\n===================================================================='
    print '= rebuilding kill grid for', model_name, variety.description
    datespan = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    print '+ time span : %s thru %s' % datespan
    print '===================================================================='
#  loop trough all GDD thresholds
for lo_gdd_th, hi_gdd_th in variety_manager.gddThresholds(model_name):
    # generate stage grid from accumulated GDD
    stage_grid = variety_manager.getStage(model_name, lo_gdd_th, hi_gdd_th,
                                          start_date, end_date)

    # estimate kill probability from stages and predicted mint
    kill = variety_manager.estimateKill(stage_grid, mint, verbose)
    # no longer need this stage grid
    del stage_grid

    if not debug:
        variety_manager.open('a')
        variety_manager.updateKill(model_name, lo_gdd_th, hi_gdd_th, kill,
                                   start_date)
        variety_manager.close()
    # no longer need this kill grid
    del kill

# turn annoying numpy warnings back on
warnings.resetwarnings()
