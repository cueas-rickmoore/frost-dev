#!/Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import daysInYear, lastDayOfMonth, asAcisQueryDate

from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
test_run = options.test_run
test_path = debug | test_run
verbose = options.verbose or debug

factory = AppleGridFactory()

num_args = len(args)
if num_args == 2:
    year = int(args[0])
    month = int(args[1])
    start_date = datetime(year,month,1)
    last_day = lastDayOfMonth(year, month)
    end_date = datetime(year, month, last_day)
elif num_args in (4,6):
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime(year,month,day)
    if num_args == 4:
        end_date = start_date + relativedelta(days=int(args[3]))
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
if verbose or test_run:
    print 'start date', start_date
    print 'end date', end_date
    print 'target year', target_year

num_days = (end_date - start_date).days + 1
dates = [asAcisQueryDate(start_date+relativedelta(days=day)) 
         for day in range(num_days)]
print dates[0], dates[-1]

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get a chill data file manger
filepath = factory.getChillGridPath(target_year, test_path)
if os.path.exists(os.path.normpath(filepath)):
    manager = factory.getChillGridManager(target_year, 'r', test_path)
else:
    raise IOError, 'Chill date file for %d does not exist.' % target_year
models = [name.lower() for name in manager.file_chill_models]

# re-estimate daily and accumulated chill units for each model
for model_name in models:
    manager.open('r')
    daily, accumulated = manager.estimateChill(model_name, dates=dates)
    manager.close()
    manager.open('a')
    manager.updateChill(model_name, 'daily', daily, start_date)
    manager.close()
    manager.open('a')
    manager.updateChill(model_name, 'accumulated', accumulated, start_date)
    manager.close()
    del daily, accumulated

# turn annoying numpy warnings back on
warnings.resetwarnings()

