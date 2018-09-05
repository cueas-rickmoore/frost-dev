#! /Volumes/projects/venvs/grape/bin/python

import os, sys
import datetime
ONE_DAY = datetime.timedelta(days=1)
import warnings

import numpy as N

from atmosci.utils.timeutils import asDatetime, asDatetimeDate, elapsedTime
from atmosci.hdf5.dategrid import Hdf5DateGridFileReader
from atmosci.seasonal.methods.paths import PathConstructionMethods

from frost.functions import fromConfig
from frost.grape.grid import GrapeVarietyFileManager

from grapehard.factory import GrapeHardinessBuildFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from grapehard.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PathConstuctor(PathConstructionMethods):
    def __init__(self):
        self.config = CONFIG.copy()
        self.project = self.config.project

    def varietyToFilepath(self, variety):
        if isinstance(variety, basestring):
            return self.normalizeFilepath(variety)
        return self.normalizeFilepath(variety.name)

    def varietyToDirpath(self, variety):
        if isinstance(variety, basestring):
            return self.normalizeDirpath(variety)
        else: return self.normalizeDirpath(variety.name)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-d', action='store_true', dest='is_dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

build_start = datetime.datetime.now()

debug = options.debug
exit_quietly = not debug
is_dev_mode = options.is_dev_mode
verbose = options.verbose or debug

today = datetime.date.today()

factory = GrapeHardinessBuildFactory()

if len(args) == 1: target_year = int(args[0])
else:
    target_year = factory.targetYear(datetime.date.today())
    if target_year is None:
        if exit_quietly: sys.exit(0)
        errmsg = "Taday's date is not within season limits. Try passing the"
        errmsg += " target year as an argument on the command line."
        raise ValueError, errmsg

season_end_date = datetime.date(target_year, 6, 30)

path_finder = PathConstuctor()

source = CONFIG.sources[CONFIG.project.source]
source_dirpath = path_finder.sourceToDirpath(source)
source_filepath = path_finder.sourceToFilepath(source)

region = CONFIG.regions[CONFIG.project.region]
region_dirpath = path_finder.regionToDirpath(region)
region_filepath = path_finder.regionToFilepath(region)

if is_dev_mode: dirpaths = CONFIG.modes.dev.dirpaths
else: dirpaths = CONFIG.modes.build.dirpaths
template_args = { 'year':target_year, 'source':source_filepath,
                  'region':region_filepath }

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

template = CONFIG.filenames.tempext
temps_filename =  template % template_args
temps_dirpath = \
    os.path.join(dirpaths.build, region_dirpath, source_dirpath, 'temps')
temps_filepath = os.path.join(temps_dirpath, temps_filename)
print 'Reading forecast from :', temps_filepath
temps = Hdf5DateGridFileReader(temps_filepath)
try:
    date_attrs = temps.dateAttributes('temps.maxt')
    maxt_path = 'temps.maxt'
    mint_path = 'temps.mint'
except:
    date_attrs = temps.dateAttributes('reported.maxt')
    maxt_path = 'reported.maxt'
    mint_path = 'reported.mint'
del date_attrs['start_date']
del date_attrs['end_date']

fcast_start = temps.dateAttribute(maxt_path, 'fcast_start_date', None)
fcast_end = temps.dateAttribute(maxt_path, 'fcast_end_date', None)
temps.close()
if fcast_start is None:
    print 'No forecast available.'
    exit()
if fcast_end < datetime.date.today():
    print 'No forecast available beyond', datetime.date.today()
    exit()

if fcast_end > season_end_date: fcast_end = season_end_date

last_valid = asDatetimeDate(fcast_end)
date_attrs['last_valid_date'] = last_valid.strftime('%Y-%m-%d')
print '\n\n', fcast_start, fcast_end, last_valid

temps_last_obs = asDatetimeDate(date_attrs['last_obs_date'])

if debug:
    print 'temps last obs, last valid', temps_last_obs, last_valid
    print 'facast_start, fcast_end', fcast_start, fcast_end
    print 'num days to retrieve', (fcast_end - fcast_start).days + 1

#last_valid = max(last_valid, fcast_end)
#if debug: print 'usable last valid', last_valid

build_dirpath = os.path.join(dirpaths.build, region_dirpath, source_dirpath)
variety_template = CONFIG.filenames.build
common_chill_threshold = fromConfig('crops.grape.chill.common_threshold')

# crops.grape.varieties.build has list of varieties currently being built
for variety in CONFIG.project.varieties:
    print '\nAdding hardiness forecast for', variety
    # path to variety file
    template_args['variety'] = path_finder.varietyToFilepath(variety)
    filename = variety_template % template_args
    variety_dirpath = path_finder.varietyToDirpath(variety)
    filepath = os.path.join(build_dirpath, variety_dirpath, filename)
    if verbose: print filepath

    # get a reader for the variety file
    manager = GrapeVarietyFileManager(target_year, variety, filepath=filepath)
    var_last_obs = manager.dateAttribute('hardiness.temp', 'last_obs_date')
    print temps_last_obs, var_last_obs
    prev_date = min(temps_last_obs, var_last_obs)
    manager.close()
    start_date = prev_date + ONE_DAY
    print '!!! start_date, last_valid', start_date, last_valid

    # cannot assume all variety files are caught up to the same date
    # so, get maxt/mint again for each variety
    if verbose: print '    calculating averge temperature'
    temps.open()
    maxt = temps.dateSlice(maxt_path, start_date, last_valid).astype(float)
    mint = temps.dateSlice(mint_path, start_date, last_valid).astype(float)
    temps.close()
    # convert missing data to NaN
    maxt[N.where(maxt < -32760)] = N.nan
    mint[N.where(mint < -32760)] = N.nan
    if debug:
        print 'extracting forecast temps for', start_date, last_valid
        print '    maxt Fahrenheit', N.nanmax(maxt), N.nanmin(maxt)
        print '    mint Fahrenheit', N.nanmax(mint), N.nanmin(mint)
    # need temps in Celcius for Grape Hardiness model
    maxt = (maxt - 32.) * (5./9.)
    mint = (mint - 32.) * (5./9.)
    if debug:
        print '    maxt Celsius', N.nanmax(maxt), N.nanmin(maxt)
        print '    mint Celsius', N.nanmax(mint), N.nanmin(mint)

    # need to use average temp in all GDD and chill calculations
    avgt = mint + ((maxt - mint) / 2.)
    del maxt, mint
    if avgt.ndim == 2: avgt_nan_indexes = N.where(N.isnan(avgt))
    else: avgt_nan_indexes = N.where(N.isnan(avgt[0]))
    if debug: print '    forecast avgt', N.nanmin(avgt), N.nanmin(avgt)

    # current accumulated common chill requires previous day's common chill
    if verbose: print '    calculating common chill'
    daily = manager.estimateChill(avgt, common_chill_threshold)
    if debug:
        print 'forecast daily common chill', N.nanmin(daily), N.nanmax(daily)
    # estimate accumulated common chill
    manager.open('r')
    prev_accum = manager.getChillData('common', 'accumulated', prev_date)
    prev_accum[avgt_nan_indexes] = N.nan

    manager.close()
    accumulated = manager.accumulateChill(daily, prev_accum)
    if debug:
        minval = N.nanmin(accumulated)
        maxval = N.nanmax(accumulated)
        print 'forecast accummulated common chill', minval, maxval
    manager.open('a')
    manager.updateChill('common', daily, accumulated, start_date)
    manager.close()
    manager.open('a')

    manager.setDatasetAttributes('chill.common.daily', **date_attrs)
    manager.setDatasetAttributes('chill.common.accumulated', **date_attrs)
    manager.setDatasetAttributes('chill.common.provenance', **date_attrs)
    manager.close()

    # estimate dormancy stage from common accumulated chill
    if verbose: print '    determining phenological stage'
    stage = manager.dormancyStageFromChill(accumulated)
    if debug: print 'forecast stages', N.nanmin(stage), N.nanmax(stage)
    manager.open('a')
    manager.updateDormancy(stage, start_date)
    manager.setDatasetAttributes('dormancy.stage', **date_attrs)
    manager.setDatasetAttributes('dormancy.provenance', **date_attrs)
    manager.close()

    # estimate dormancy-based chill from avgt and dormancy stage
    if verbose: print '    calculating dormancy-based chill'
    manager.open('r')
    prev_accum = manager.getChillData('dormancy', 'accumulated', prev_date)
    prev_accum[avgt_nan_indexes] = N.nan
    manager.close()
    daily = manager.dormancyBasedChill(avgt, stage)
    accumulated = manager.accumulateChill(daily, prev_accum)
    if debug:
        print 'forecast daily dormancy chill', N.nanmin(daily), N.nanmax(daily)
        minval = N.nanmin(accumulated)
        maxval = N.nanmax(accumulated)
        print 'forecast accummulated dormancy chill', minval, maxval
    manager.open('a')
    manager.updateChill('dormancy', daily, accumulated, start_date)
    manager.close()
    manager.open('a')
    manager.setDatasetAttributes('chill.dormancy.daily', **date_attrs)
    manager.setDatasetAttributes('chill.dormancy.accumulated', **date_attrs)
    manager.setDatasetAttributes('chill.dormancy.provenance', **date_attrs)
    manager.close()

    # dormancy-based GDD from avgt and dormancy stage
    if verbose: print '    calculating dormancy-based GDD'
    manager.open('r')
    prev_accum = manager.getGDD('accumulated', prev_date)
    prev_accum[avgt_nan_indexes] = N.nan
    manager.close()
    daily = manager.dormancyBasedGDD(avgt, stage)
    del avgt
    accumulated = manager.accumulateGDD(daily, stage, prev_accum)
    if debug:
        print 'forecast daily GDD', N.nanmin(daily), N.nanmax(daily)
        minval = N.nanmin(accumulated)
        maxval = N.nanmax(accumulated)
        print 'forecast accummulated GDD', minval, maxval
    manager.open('a')
    manager.updateGDD(daily, accumulated, start_date)
    manager.close()
    manager.open('a')
    manager.setDatasetAttributes('gdd.daily', **date_attrs)
    manager.setDatasetAttributes('gdd.accumulated', **date_attrs)
    manager.setDatasetAttributes('gdd.provenance', **date_attrs)
    manager.close()

    # calculates the hardiness temps
    if verbose: print '    calculating acclimation and hardiness'
    manager.open('r')
    stage = manager.getDormancy(prev_date, last_valid)
    daily_chill = \
        manager.getChillData('dormancy', 'daily', prev_date, last_valid)
    accum_chill = \
        manager.getChillData('dormancy', 'accumulated', prev_date, last_valid)
    daily_gdd = manager.getGDD('daily', prev_date, last_valid)
    prev_hardiness = manager.getHardiness(prev_date)
    estimates = manager.estimateHardiness(stage, daily_chill, accum_chill,
                                          daily_gdd, prev_hardiness)
    manager.close()
    
    # estimates = [hardiness, acclimation, deacclimation]
    hardiness = estimates[0]
    if debug:
        maxval = N.nanmax(hardiness)
        minval = N.nanmin(hardiness)
        print 'forecast hardiness temps', minval, maxval
    # save the datasets
    manager.open('a')
    manager.updateHardiness(hardiness, prev_date)
    manager.setDatasetAttributes('hardiness.temp', **date_attrs)
    manager.setDatasetAttributes('hardiness.provenance', **date_attrs)
    manager.close()

    acclimation = estimates[1]
    if debug:
        maxval = N.nanmax(acclimation)
        minval = N.nanmin(acclimation)
        print 'forecast acclimation factor', minval, maxval
    manager.open('a')
    manager.updateAcclimation(acclimation, prev_date)
    manager.setDatasetAttributes('acclimation.factor', **date_attrs)
    manager.setDatasetAttributes('acclimation.provenance', **date_attrs)
    manager.close()

    deacclimation = estimates[2]
    if debug:
        maxval = N.nanmax(deacclimation)
        minval = N.nanmin(deacclimation)
        print 'forecast deacclimation factor', minval, maxval
    manager.open('a')
    manager.updateDeacclimation(deacclimation, prev_date)
    manager.setDatasetAttributes('deacclimation.factor', **date_attrs)
    manager.setDatasetAttributes('deacclimation.provenance', **date_attrs)
    manager.close()

# turn annoying numpy warnings back on
warnings.resetwarnings()

