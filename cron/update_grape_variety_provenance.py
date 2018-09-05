#! /Volumes/projects/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from frost.grape.factory import GrapeGridFactory
from frost.grape.functions import getGrapeVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser, OptionValueError
parser = OptionParser()

parser.add_option('-u', action='store_false', dest='update', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
update = options.update
verbose = options.verbose or debug

variety = getGrapeVariety(args[0])

factory = GrapeGridFactory()

num_args = len(args[1:])
if num_args in (3,4,6):
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    start_date = datetime(year,month,day)
    if num_args == 3: end_date = start_date
    elif num_args == 4:
        end_date = start_date + relativedelta(days=int(args[4])-1)
    elif num_args == 6:
        year = int(args[4])
        month = int(args[5])
        day = int(args[6])
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
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

if update: mode = 'a'
else: mode = 'r'

# get a Variety grid manager for the target year
variety_manager = factory.getVarietyManager(target_year, variety, mode)

date = start_date
while date <= end_date:
    # get hardiness temp
    temps = variety_manager.getModelData('hardiness', 'temp', start_date, end_date)
    if update:
        variety_manager.open('a')
        variety_manager.updateProvenance('hardiness', 'temp', temp, start_date)
        variety_manager.close()
        print 'updated hardiness provenance for', date.strftime('%m %d, %Y')
    else:
        print date.strftime('%m %d, %Y'), 'hardiness provenance =', N.nanmax(temps), N.nanmin(temps)

# turn annoying numpy warnings back on
warnings.resetwarnings()

