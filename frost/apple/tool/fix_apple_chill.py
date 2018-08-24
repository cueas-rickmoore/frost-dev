#! /usr/bin/env python

import os
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)

import numpy as N

from atmosci.hdf5.dategrid import Hdf5DateGridFileReader
from atmosci.utils.timeutils import asDatetime

from frost.apple.chill.grid import AppleChillGridManager
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

debug = options.debug
is_dev_build = options.is_dev_build
verbose = options.verbose or debug

factory = AppleToolFactory()
region = factory.region()
source = factory.source()

target_year, season_start, season_end = factory.seasonDates(int(args[0]))
key_dates = { 'last_obs_date':season_end.strftime('%Y-%m-%d'),
              'last_valid_date':season_end.strftime('%Y-%m-%d') }
season_end_time = asDatetime(season_end)

# root directory is possibly different for development and production cases
if is_dev_build:
    chill_filepath = factory.devFilepath('tool', target_year, region,
                                         source, 'chill')
    temps_filepath = factory.devFilepath('tool', target_year, region,
                                         source, 'temps', 'tempext')
else:
    chill_filepath = factory.toolFilepath('tool', target_year, region,
                                          source, 'chill')
    temps_filepath = factory.toolFilepath('tool', target_year, region,
                                          source, 'temps', 'tempext')

# copy frost chill file to frapple build directory
reader = Hdf5DateGridFileReader(temps_filepath)
print 'reading temps from :', reader.filepath

maxt = reader.dataForDate('temps.maxt', season_end)
nan_indexes = N.where(N.isnan(maxt))
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

# interpolate hourly temperatures from mint,maxt using Linvill algorithm
manager = AppleChillGridManager(target_year, mode='a', filepath=chill_filepath)
print 'fixing chill in :', manager.filepath
linvill = manager.linvill([season_end,], mint, maxt, 'F', verbose)

# generate chill forecasts for each model
for model_name in factory.tool.project.models:
    proper_name = manager.properName(model_name)
    if verbose:
        print('estimating chill for %(model)s model' % {'model':proper_name,})
    manager.open('r')
    daily_chill, accumulated_chill = \
        manager.estimateChill(model_name,date=season_end_time, hourly=linvill, 
                              debug=verbose)
    manager.close()
    # make sure we didn't get bogus chill
    accumulated_chill[nan_indexes] = N.nan
    daily_chill[nan_indexes] = N.nan

    manager.open('a')
    manager.updateChill(model_name, daily_chill, accumulated_chill,
                        season_end_time)
    manager.close()
    manager.open('a')
    dataset_name = manager.chillDatasetPath(model_name, 'accumulated')
    manager.setDatasetAttributes(dataset_name, **key_dates)
    dataset_name = manager.chillDatasetPath(model_name, 'daily')
    manager.setDatasetAttributes(dataset_name, **key_dates)
    dataset_name = dataset_name.replace('daily','provenance')
    manager.setDatasetAttributes(dataset_name, **key_dates)
    manager.close()
    del daily_chill, accumulated_chill

    # Growing Degree Days
    for lo_gdd, hi_gdd in factory.tool.project.gdd_thresholds:
        if verbose:
            msg = 'estimating daily %(group)s GDD'
            gdd_group = manager.gddGroupName(lo_gdd, hi_gdd)
            print(msg % {'group':gdd_group,})
        # make sure that the daily dataset is initialized
        manager.open('a')
        # estimate GDD for this low/high threshold combination
        daily_gdd = manager.estimateGDD(lo_gdd, hi_gdd, mint, maxt, debug)
        manager.updateGdd(lo_gdd, hi_gdd, daily_gdd, season_end_time)
        manager.close()
        manager.open('a')
        dataset_name = manager.gddDatasetPath(lo_gdd, hi_gdd, 'daily')
        manager.setDatasetAttributes(dataset_name, **key_dates)
        dataset_name = dataset_name.replace('daily','provenance')
        manager.setDatasetAttributes(dataset_name, **key_dates)
        manager.close()
        del daily_gdd

# turn annoying numpy warnings back on
warnings.resetwarnings()
