#! /Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from frost.functions import fromConfig, targetDateSpan
from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getAppleVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
verbose = options.verbose
test_file = options.test_file

# apple variety and chill model
if not args[0].isdigit():
    varieties = (getAppleVariety(args[0]),)
    if not args[1].isdigit():
        models = (fromConfig('crops.apple.chill.%s.self' % args[1]),)
        date_indx = 2
    else:
        models = fromConfig('crops.apple.chill.getActiveModels()')
        date_indx = 1
else:
    varieties = fromConfig('crops.apple.varieties.children')
    models = fromConfig('crops.apple.chill.getActiveModels()')
    date_indx = 0

# get the date
date_args = args[date_indx:]
num_date_args = len(date_args)

if num_date_args == 1 : # target year is only argument
    start_date, end_date = targetDateSpan(int(date_args[0]))
elif num_date_args >= 3: # start date specified
    year = int(date_args[0])
    month = int(date_args[1])
    day = int(date_args[2])
    start_date = datetime(year,month,day)
    if num_date_args == 6: # end date specified
        year = int(date_args[3])
        month = int(date_args[4])
        day = int(date_args[5])
        end_date = datetime(year,month,day)
    elif num_date_args == 3: # only one day
        end_date = start_date
    else:
        errmsg = 'Invalid number of date arguments (%d).' % date_args
        raise ValueError, errmsg
else:
    errmsg = 'Invalid number of date arguments (%d).' % date_args
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

for variety in varieties:
    visualizer = \
        factory.getVarietyVisualizer(target_year,variety.name,'r', test_file)
    for model in models:
        gdd_thresholds = visualizer.gddThresholds(model.name)
        for lo_gdd_th, hi_gdd_th in gdd_thresholds:
            date = start_date
            while date <= end_date:
                path = visualizer.drawKillMap(date, model, lo_gdd_th,
                                              hi_gdd_th, verbose)
                print 'completed', path
                date += ONE_DAY


# turn annoying numpy warnings back on
warnings.resetwarnings()

