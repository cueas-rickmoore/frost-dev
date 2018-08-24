#! /usr/bin/env python

import os, sys
from copy import deepcopy
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)

import numpy as N

from atmosci.hdf5.dategrid import Hdf5DateGridFileReader
from atmosci.utils.timeutils import asDatetime
from atmosci.utils.timeutils import daysInYear, lastDayOfMonth

from frost.apple.functions import getAppleVariety
from frost.apple.variety.grid import AppleVarietyGridManager

from frost.apple.tool.factory import AppleToolFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-d', action='store_true', dest='is_dev_build',
                        default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

is_dev_build = options.is_dev_build
verbose = options.verbose
debug = options.debug or verbose

today = datetime.date.today()
fcast_year = today.year

factory = AppleToolFactory()
region = factory.region()
source = factory.source()

target_year, season_start, season_end = factory.seasonDates(int(args[0]))
key_dates = { 'last_obs_date':season_end.strftime('%Y-%m-%d'),
              'last_valid_date':season_end.strftime('%Y-%m-%d') }
season_end_time = asDatetime(season_end)

variety = getAppleVariety(args[1])

# root directory is possibly different for development and production cases
if is_dev_build:
    chill_filepath = factory.devFilepath('tool', target_year, region,
                                         source, 'chill')
    temps_filepath = factory.devFilepath('tool', target_year, region,
                                         source, 'temps', 'tempext')
    tool_filepath = factory.devFilepath('tool', target_year, region,
                                        source, variety, 'variety')
else:
    chill_filepath = factory.toolFilepath('tool', target_year, region,
                                          source, 'chill')
    temps_filepath = factory.toolFilepath('tool', target_year, region,
                                          source, 'temps', 'tempext')
    tool_filepath = factory.toolFilepath('tool', target_year, region,
                                         source, variety, 'variety')

# get mint and key dates
reader = Hdf5DateGridFileReader(temps_filepath)
mint = reader.dataForDate('temps.mint', season_end)
reader.close()
del reader


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# create a chill file reader
reader = Hdf5DateGridFileReader(chill_filepath)

# update the stage grids with 6-day forecast
manager = AppleVarietyGridManager(target_year, variety, mode='a',
                                  filepath=tool_filepath)
manager.start_date = season_start
manager.end_date = season_end

for model in factory.tool.project.models:
    proper_name = manager.properName(model)
    # get the Chill accumulation
    dataset_path = '%s.accumulated' % model.title()
    accumulated_chill = reader.dataForDate(dataset_path, season_end)
    #  loop trough all GDD thresholds
    for lo_gdd, hi_gdd in factory.tool.project.gdd_thresholds:
        # get daily GDD from the chill grid file
        dataset_path = 'gdd.L%dH%d.daily' % (lo_gdd, hi_gdd)
        daily_gdd = reader.dataForDate(dataset_path, season_end)

        # calculuate accumulated GDD from daily gdd
        # let manager get accumulated GDD for previous day
        manager.open('a')
        accumulated_gdd, chill_mask = \
        manager.accumulateGdd(model, lo_gdd, hi_gdd, season_end,
                              accumulated_chill, daily_gdd)
        manager.updateGdd(model, lo_gdd, hi_gdd, accumulated_gdd, chill_mask,
                          season_end_time)
        dataset_path = manager.modelDatasetPath(model, lo_gdd, hi_gdd, 'gdd',
                                                'accumulated')
        manager.setDatasetAttributes(dataset_path, **key_dates)
        dataset_path = dataset_path.replace('accumulated','chill_mask')
        manager.setDatasetAttributes(dataset_path, **key_dates)
        dataset_path = dataset_path.replace('chill_mask','provenance')
        manager.setDatasetAttributes(dataset_path, **key_dates)
        manager.close()
        # no longer need grid for daily GDD
        del daily_gdd

        # generate stage grid from accumulated GDD
        stage_grid = manager.gddToStages(accumulated_gdd)
        manager.open('a')
        manager.updateStage(model, lo_gdd, hi_gdd, stage_grid, season_end_time)
        dataset_path = \
            manager.modelDatasetPath(model, lo_gdd, hi_gdd, 'stage', 'index')
        manager.setDatasetAttributes(dataset_path, **key_dates)
        dataset_path = dataset_path.replace('index','provenance')
        manager.setDatasetAttributes(dataset_path, **key_dates)
        manager.close()
        # no longer need grid for accumulated GDD
        del accumulated_gdd

        # estimate kill probability from stages and predicted mint
        kill_grid = manager.estimateKill(stage_grid, mint)
        manager.open('a')
        manager.updateKill(model, lo_gdd, hi_gdd, kill_grid, season_end_time)
        dataset_path = \
            manager.modelDatasetPath(model, lo_gdd, hi_gdd, 'kill', 'level')
        manager.setDatasetAttributes(dataset_path, **key_dates)
        dataset_path = dataset_path.replace('level','provenance')
        manager.setDatasetAttributes(dataset_path, **key_dates)
        manager.close()
        # no longer need stage or kill grids
        del stage_grid, kill_grid

# turn annoying numpy warnings back on
warnings.resetwarnings()

