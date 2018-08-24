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
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
test_file = options.test_file
verbose = options.verbose

variety = fromConfig('crops.apple.variety.%s.self' % args[0])
model_name = args[1]
group = args[2]

factory = AppleGridFactory()

num_args = len(args[3:])
print args[2:]
if num_args == 1:
    target_year = int(args[3])
    start_date = None
    end_date = None
elif num_args == 2:
    year = int(args[3])
    month = int(args[4])
    start_date = datetime(year,month,1)
    last_day = lastDayOfMonth(year, month)
    end_date = datetime(year, month, last_day)
    target_year = factory.getTargetYear(start_date)
elif num_args in (3,4,6):
    year = int(args[3])
    month = int(args[4])
    day = int(args[5])
    start_date = datetime(year,month,day)
    if num_args == 3: end_date = None
    elif num_args == 4:
        end_date = start_date + relativedelta(days=int(args[6])-1)
    elif num_args == 6:
        year = int(args[6])
        month = int(args[7])
        day = int(args[8])
        end_date = datetime(year,month,day)
    target_year = factory.getTargetYear(start_date)
else:
    print sys.argv
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise ValueError, errmsg

# get a Variety grid manager for the target year
manager = factory.getVarietyGridManager(target_year, variety.name, 'a', test_file)

#  loop trough all GDD thresholds
for lo_gdd_th, hi_gdd_th in manager.gddThresholds(model_name):
    if group == 'stage':
        grid = manager.getStage(model_name, lo_gdd_th, hi_gdd_th, start_date,
                                end_date)
        for stage in range(len(manager.stages)+1):
            indexes = N.where(grid == stage)
            print 'stage', stage, len(indexes[0])
            print indexes
    elif group == 'kill':
        grid = manager.getKill(model_name, lo_gdd_th, hi_gdd_th, start_date,
                               end_date)
    elif group == 'gdd':
        grid = manager.getKill(model_name, lo_gdd_th, hi_gdd_th, start_date,
                               end_date)
    else:
        raise ValueError, 'Unknown group name', group

    manager.updateProvenance(model_name, lo_gdd_th, hi_gdd_th, group,
                             start_date, grid, verbose)

