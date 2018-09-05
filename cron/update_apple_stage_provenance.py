#! /Volumes/projects/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getAppleVariety

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

variety = getAppleVariety(args[0])
model = args[1]

factory = AppleGridFactory()

num_args = len(args[2:])
if num_args in (3,4,6):
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
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

if update: mode = 'a'
else: mode = 'r'

# get a Variety grid manager for the target year
filepath = factory.getVarietyFilePath(target_year, variety, test_file)
variety_manager = \
factory.getVarietyGridManager(target_year, variety, mode, test_file)
gdd_thresholds = getGddThresholds(options, variety_manager)

#  loop trough all GDD thresholds
for lo_gdd_th, hi_gdd_th in gdd_thresholds:

    # get previously accumulatedg GDD
    gdd = variety_manager.getModelData(model_name, lo_gdd_th, hi_gdd_th, 'gdd',
                                       'accumulated', start_date, end_date)

    if update:
        variety_manager.open('a')
        variety_manager.updateProvenance(model_name, lo_gdd_th, hi_gdd_th,
                                         'gdd', gdd, start_date)
        variety_manager.close()
        print 'updated', variety.name, model, 'gdd provenance'

    # generate stage grid from accumulated GDD
    stage = variety_manager.getModelData(model_name, lo_gdd_th, hi_gdd_th,
                                         'stage', 'index', start_date,
                                         end_date)

    if update:
        variety_manager.open('a')
        variety_manager.updateProvenance(model_name, lo_gdd_th, hi_gdd_th,
                                         'stage', stage, start_date)
        variety_manager.close()
        print 'updated', variety,name, model, 'stage provenance'

    # estimate kill probability from stages and predicted mint
    kill = variety_manager.getModelData(model_name, lo_gdd_th, hi_gdd_th,
                                         'kill', 'level', start_date,
                                         end_date)

    if update:
        variety_manager.open('a')
        variety_manager.updateProvenance(model_name, lo_gdd_th, hi_gdd_th,
                                         'kill', kill, start_date)
        variety_manager.close()
        print 'updated', variety.name, model, 'kill provenance'

# turn annoying numpy warnings back on
warnings.resetwarnings()

