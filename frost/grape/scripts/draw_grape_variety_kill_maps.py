#! /Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from frost.functions import fromConfig, targetDateSpan
from frost.grape.factory import GrapeGridFactory
from frost.grape.functions import getGrapeVariety

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

# grape variety and chill model
if not args[0].isdigit():
    varieties = (getGrapeVariety(args[0]),)
    date_indx = 1
else:
    varieties = [ ]
    for name in fromConfig('crops.grape.varieties.build'):
        varieties.append(getGrapeVariety(name))
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

factory = GrapeGridFactory()
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
    factory.getVarietyVisualizer(target_year, variety, test_file)
    date = start_date
    while date <= end_date:
        path = visualizer.drawKillMap(date, verbose)
        print 'completed', path
        date += ONE_DAY


# turn annoying numpy warnings back on
warnings.resetwarnings()

