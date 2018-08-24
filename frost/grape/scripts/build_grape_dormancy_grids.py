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

usage = '%prog variety_name year [month day] [num_days | [thru_year thru_month thru_day]] [options]'

from optparse import OptionParser, OptionValueError
parser = OptionParser(usage=usage)

parser.add_option('-u', action='store_false', dest='update', default=True,
                        help='update variety file - bool - default=True')
parser.add_option('-v', action='store_true', dest='verbose', default=False,
                        help='verbose output - bool - default=False')
parser.add_option('-z', action='store_true', dest='test_run', default=False,
                        help='test run, no permanent affects - bool - default=False')

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

test_run = options.test_run
verbose = options.verbose
update_db = options.update

factory = GrapeGridFactory()

variety = getGrapeVariety(args[0])

is_current_date = False
num_date_args = len(args[1:])
if num_date_args == 0:
    start_date = datetime.now()
    end_date = None
    is_current_date = True
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

# also need data from previous day(s)
# begin one day before start_date
prev_start = start_date - ONE_DAY
if end_date is None: num_days = 1
else: num_days = (end_date - start_date).days + 1
if verbose: print 'number of days', num_days

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# temperatrue file manager
temp_manager = factory.getTempGridReader(target_year, test_run)
# get maxt/mint from temperatrue grid file
# ACIS grid temps for start_date thru end_date are actually for previous days
maxt = temp_manager.getTemp('reported.maxt', start_date, end_date, units='C')
mint = temp_manager.getTemp('reported.mint', start_date, end_date, units='C')
# need to use average temp in all GDD and chill calculations
avgt = mint + ((maxt - mint) / 2.)
if avgt.ndim == 2: avgt_nan_indexes = N.where(N.isnan(avgt))
else: avgt_nan_indexes = N.where(N.isnan(avgt[0]))

# get a variety data file manger
filepath = factory.getVarietyFilePath(target_year, variety, test_run)
if not os.path.exists(os.path.normpath(filepath)):
    variety_manager = \
    factory.newVarietyManager(target_year, variety, test_run, verbose)
else:
    variety_manager = \
    factory.getVarietyManager(target_year, variety, 'r', test_run)

target_start_date, target_end_date = factory.getTargetDateSpan(target_year)

# start date is at a point where dormacy grids should already exist
if start_date > target_start_date:
    prev_common_accum = \
        variety_manager.getChillData('common', 'accumulated', prev_start)
    prev_dormancy_accum = \
        variety_manager.getChillData('dormancy', 'accumulated', prev_start)
    prev_gdd_accum = variety_manager.getGDD('accumulated', prev_start)

# start date is target date, so model hasn't been run yet (is being restarted)
else:
    shape = variety_manager.lons.shape
    # initialize to zero
    prev_common_accum = N.zeros(shape, dtype=float)
    prev_dormancy_accum = N.zeros(shape, dtype=float)
    prev_gdd_accum = N.zeros(shape, dtype=float)
    # overwrite with missing data nodes from avgt
    prev_common_accum[avgt_nan_indexes] = N.nan
    prev_dormancy_accum[avgt_nan_indexes] = N.nan
    prev_gdd_accum[avgt_nan_indexes] = N.nan

# estimate common chill
common_threshold = fromConfig('crops.grape.chill.common_threshold')
daily = variety_manager.estimateChill(avgt, common_threshold)
# current accumulated common chill requires previous day's common chill
accumulated = variety_manager.accumulateChill(daily, prev_common_accum)
if update_db:
    variety_manager.open('a')
    variety_manager.updateChill('common', daily, accumulated, start_date)
    variety_manager.close()

# dormancy stage from common accumulated chill
dormancy_stage = variety_manager.dormancyStageFromChill(accumulated)
if update_db:
    variety_manager.open('a')
    variety_manager.updateDormancy(dormancy_stage, start_date)
    variety_manager.close()

# dormancy-based chill from avgt and dormancy stage
daily = variety_manager.dormancyBasedChill(avgt, dormancy_stage)
accumulated = variety_manager.accumulateChill(daily, prev_dormancy_accum)
if update_db:
    variety_manager.open('a')
    variety_manager.updateChill('dormancy', daily, accumulated, start_date)
    variety_manager.close()

# dormancy-based GDD from avgt and dormancy stage
daily = variety_manager.dormancyBasedGDD(avgt, dormancy_stage)
accumulated = \
    variety_manager.accumulateGDD(daily, dormancy_stage, prev_gdd_accum)
if update_db:
    variety_manager.open('a')
    variety_manager.updateGDD(daily, accumulated, start_date)
    variety_manager.close()

# turn annoying numpy warnings back on
warnings.resetwarnings()
