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

from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getAppleVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser, OptionValueError
parser = OptionParser()

parser.add_option('-f', action='store_true', dest='forecast', default=False)
parser.add_option('-u', action='store_false', dest='update', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
forecast = options.forecast
test_file = options.test_file
verbose = options.verbose or debug
update_db = options.update

variety = getAppleVariety(args[0])

num_args = len(args[1:])
if num_args in (3,4,6):
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    start_date = datetime(year,month,day)
    if num_args == 3: end_date = None
    elif num_args == 4:
        end_date = start_date + relativedelta(days=int(args[4])-1)
    elif num_args == 6:
        year = int(args[4])
        month = int(args[5])
        day = int(args[6])
        end_date = datetime(year,month,day)
else:
    print sys.argv
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise ValueError, errmsg

factory = AppleGridFactory()
target_year = factory.getTargetYear(start_date)

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

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

# get a Variety grid manager for the target year
variety_manager = \
    factory.getVarietyGridManager(target_year, variety, 'a', test_file)
models = [name.lower() for name in variety_manager.file_chill_models]
variety_manager.close()

# estimate GDD accumulation, stage and kill probability for this variety
for model_name in models:
    #  loop trough all GDD thresholds
    for lo_gdd_th, hi_gdd_th in variety_manager.gddThresholds(model_name):
        variety_manager.open('r')
        stage_grid = variety_manager.getStage(model_name, lo_gdd_th, hi_gdd_th,
                                              start_date, end_date)
    
        # estimate kill probability from stages and predicted mint
        kill_grid = variety_manager.estimateKill(stage_grid, mint)
        # no longer need stage grid
        del stage_grid

        # update the kill probability dataset
        variety_manager.open('a')
        variety_manager.updateKill(model_name, lo_gdd_th, hi_gdd_th, kill_grid,
                                   start_date)
        variety_manager.close()
        # no longer need grid for kill
        del kill_grid

# turn annoying numpy warnings back on
warnings.resetwarnings()

