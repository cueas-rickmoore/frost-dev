#! /Volumes/projects/venvs/frost/bin/python

import os, sys
import re
import warnings

from datetime import datetime

import numpy as N

from frost.functions import fromConfig
from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getAppleVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getGddThresholds(manager, model_name):
    return manager.gddThresholds(model_name)
    #return fromConfig('crops.apple.gdd_thresholds')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser, OptionValueError
parser = OptionParser()

parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
verbose = options.verbose or debug

variety = getAppleVariety(args[0])

factory = AppleGridFactory()

year = int(args[1])
month = int(args[2])
day = int(args[3])
date = datetime(year,month,day)
target_year = factory.getTargetYear(date)

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

variety_manager = factory.getVarietyGridManager(target_year, variety, 'r')
models = [name.lower() for name in variety_manager.file_chill_models]
variety_manager.close()

# make sure managers can read their data files

variety_titled = variety.name.replace('_',' ').title()
# estimate GDD accumulation, stage and kill probability for this variety
for model_name in models:
    variety_manager.open('r')
    gdd_thresholds = variety_manager.gddThresholds(model_name)
    
    #  loop trough all GDD thresholds
    for lo_gdd_th, hi_gdd_th in gdd_thresholds:
        # calculuate accumulated GDD from daily gdd
        # let GDD manger get accumulated GDD for previous day
        variety_manager.open('r')

        # get accumulated GDD for date
        accumulated = \
        variety_manager.getGdd(model_name, lo_gdd_th, hi_gdd_th, date)
        # find indexes of all nodes where values are not NAN
        valid_data_indexes = N.where(N.isfinite(accumulated))
        del accumulated

        # get chill mask for date
        chill_mask = \
        variety_manager.getChillMask(model_name, lo_gdd_th, hi_gdd_th, date)
        variety_manager.close()

        # force all valid grid nodes to be True
        chill_mask[valid_data_indexes] = True

        # update chill mask in data file
        dataset_path = variety_manager.modelDatasetPath(model_name, lo_gdd_th,
                                       hi_gdd_th, 'gdd', 'chill_mask')
        variety_manager.open('a')
        variety_manager.updateDataset(dataset_path, chill_mask, date)
        variety_manager.close()

# turn annoying numpy warnings back on
warnings.resetwarnings()
