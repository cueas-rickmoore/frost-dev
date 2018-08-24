#! /usr/bin/env python

import os, sys
from copy import deepcopy
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)

import numpy as N

from atmosci.hdf5.dategrid import Hdf5DateGridFileManager, \
                                  Hdf5DateGridFileReader
from atmosci.utils.options import stringToTuple
from atmosci.utils.timeutils import DateIterator, asDatetime
from atmosci.utils.timeutils import daysInYear, lastDayOfMonth

from frost.functions import fromConfig

from frost.apple.grid import AppleGridFileReader
from frost.apple.chill.grid import AppleChillGridManager
from frost.apple.tool.factory import AppleToolFactory
from frost.apple.tool.copyfile import copyHdf5DategridFile


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

today = datetime.date.today()
fcast_year = today.year

factory = AppleToolFactory()
region = factory.region()
source = factory.source()

if len(args) == 1:
    target_year, season_start, season_end = factory.seasonDates(int(args[0]))
else:
    target_year, season_start, season_end = factory.seasonDates(today)
    if today < season_start or today > season_end:
        # quietly exit when outside season ... useful when in cron
        if exit_quitely: os.exit(0)
        errmsg = "Taday's date is not within season limits. Try passing the"
        errmsg += "%s target year as an argument on the command line."
        raise ValueError, errmsg

season_dates = {'start_date':season_start.strftime('%Y-%m-%d'),
                'end_date':season_end.strftime('%Y-%m-%d'),
               }

# root directory is possibly different for development and production cases
if is_dev_build:
    frost_filepath = factory.devFilepath('frost', target_year, region,
                                          source, 'chill')
    chill_filepath = factory.devFilepath('tool', target_year, region,
                                         source, 'chill')
    temps_filepath = factory.devFilepath('tool', target_year, region,
                                         source, 'temps', 'tempext')
else:
    frost_filepath = factory.toolFilepath('frost', target_year, region,
                                          source, 'chill')
    chill_filepath = factory.toolFilepath('tool', target_year, region,
                                          source, 'chill')
    temps_filepath = factory.toolFilepath('tool', target_year, region,
                                          source, 'temps', 'tempext')
if os.path.exists(chill_filepath): os.remove(chill_filepath)

# set parameters for copy function
exclusions = ('Utah', 'Utah.accumulated', 'Utah.daily', 'Utah.provenance')

datasets = {'lat': factory.tool.datasets.lat.attrs,
            'lon': factory.tool.datasets.lon.attrs,
           }
data_attrs = factory.tool.datasets.data.attrs
datasets['lat'].update(data_attrs)
datasets['lon'].update(data_attrs)
datasets['Carolina.accumulated'] = deepcopy(data_attrs)
datasets['Carolina.daily'] = deepcopy(data_attrs)
datasets['gdd.L43H86.daily'] = deepcopy(data_attrs)
provenance_attrs = factory.tool.datasets.provenance.attrs
datasets['Carolina.provenance'] = deepcopy(provenance_attrs)
datasets['gdd.L43H86.provenance'] = deepcopy(provenance_attrs)
# time attributes used by date grid handlers to access data by date
time_attrs = factory.tool.datasets.time.attrs
datasets['Carolina.accumulated'].update(time_attrs)
datasets['Carolina.daily'].update(time_attrs)
datasets['Carolina.provenance'].update(time_attrs)
datasets['gdd.L43H86.daily'].update(time_attrs)
datasets['gdd.L43H86.provenance'].update(time_attrs)

# copy frost chill file to frapple build directory
reader = Hdf5DateGridFileReader(frost_filepath)
print 'Copying : ', reader.filepath
builder = Hdf5DateGridFileManager(chill_filepath, mode='a')
print 'To : ', builder.filepath
copyHdf5DategridFile(reader, builder, factory.tool.fileattrs.attrs, datasets,
                     exclusions)
builder.close()
del builder, reader

# set last obs date in relevant datasets
builder = AppleChillGridManager(target_year, mode='a', filepath=chill_filepath)
for name in builder.dataset_names:
    builder.open('a')
    attrs = builder.getDatasetAttributes(name)
    if 'last_valid_date' in attrs:
        builder.setDatasetAttribute(name, 'last_obs_date',
                                    attrs['last_valid_date'])
    builder.close()
builder.open('a')
chill_last_obs = builder.dateAttribute('Carolina.daily', 'last_obs_date')
builder.close()

# need last obs/valid and forecast start/end dates from temps file
reader = Hdf5DateGridFileReader(temps_filepath)

temps_last_obs = reader.dateAttribute('temps.maxt', 'last_obs_date')
last_obs = min(chill_last_obs, temps_last_obs)
if last_obs > season_end:
    errmsg = 'EXITING: last obs (%s) beyond the end of the season (%s)'
    print(errmsg % (last_obs.strftime('%Y-%m-%d'),
                    season_end.strftime('%Y-%m-%d')))

temps_last_valid = reader.dateAttribute('temps.maxt', 'last_valid_date')
if temps_last_valid > season_end: temps_last_valid = season_end
date_attrs = { 'last_obs_date': last_obs.strftime('%Y-%m-%d'),
               'last_valid_date': temps_last_valid.strftime('%Y-%m-%d'),
             }

fcast_start = reader.dateAttribute('temps.maxt','fcast_start_date',None)
if fcast_start is None:
    print('EXITING : temperature extremes file does not contain a forecast.')
    os.exit(99)
elif fcast_start > season_end:
    print('EXITING : temperature forecast is beyond the end of the season.')
    os.exit(99)

start_chill = last_obs + ONE_DAY

fcast_end = reader.dateAttribute('temps.maxt', 'fcast_end_date', None)
if fcast_end > season_end: fcast_end = season_end
date_attrs.update( { 'fcast_start_date': fcast_start.strftime('%Y-%m-%d'),
                     'fcast_end_date': fcast_end.strftime('%Y-%m-%d') } )
maxt = reader.dateSlice('temps.maxt', start_chill, fcast_end)
maxt_nan_indexes = N.where(N.isnan(maxt))
mint = reader.dateSlice('temps.mint', start_chill, fcast_end)
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
dates = factory.datesFromDateSpan(start_chill, fcast_end)
linvill_array = builder.linvill(dates, mint, maxt, 'F', verbose)

# build the argument dictionary for the chill calculation method
chill_kwargs = { 'hourly':linvill_array, 'units':'F', 'debug':verbose }
if len(dates) > 1: chill_kwargs['dates'] = dates
else: chill_kwargs['date'] = dates[0]

# generate chill forecasts for each model
for model_name in factory.tool.project.models:
    proper_name = builder.properName(model_name)
    if verbose:
        print('estimating chill for %(model)s model' % {'model':proper_name,})
    builder.open('r')
    daily_chill, accumulated_chill = builder.estimateChill(model_name, 
                                                           **chill_kwargs)
    builder.close()
    # make sure we didn't get bogus chill
    accumulated_chill[maxt_nan_indexes] = N.nan
    daily_chill[maxt_nan_indexes] = N.nan

    builder.open('a')
    builder.updateChill(model_name, daily_chill, accumulated_chill,
                        asDatetime(start_chill))
    builder.close()
    builder.open('a')
    dataset_name = builder.chillDatasetPath(model_name, 'accumulated')
    builder.setDatasetAttributes(dataset_name, **date_attrs)
    dataset_name = builder.chillDatasetPath(model_name, 'daily')
    builder.setDatasetAttributes(dataset_name, **date_attrs)
    dataset_name = dataset_name.replace('daily','provenance')
    builder.setDatasetAttributes(dataset_name, **date_attrs)
    builder.close()
    del daily_chill, accumulated_chill

    # Growing Degree Days
    for lo_gdd, hi_gdd in factory.tool.project.gdd_thresholds:
        if verbose:
            msg = 'estimating daily %(group)s GDD'
            gdd_group = builder.gddGroupName(lo_gdd, hi_gdd)
            print(msg % {'group':gdd_group,})
        # make sure that the daily dataset is initialized
        builder.open('a')
        # estimate GDD for this low/high threshold combination
        daily_gdd = builder.estimateGDD(lo_gdd, hi_gdd, mint, maxt, debug)
        builder.updateGdd(lo_gdd, hi_gdd, daily_gdd, asDatetime(start_chill))
        builder.close()
        builder.open('a')
        dataset_name = builder.gddDatasetPath(lo_gdd, hi_gdd, 'daily')
        builder.setDatasetAttributes(dataset_name, **date_attrs)
        dataset_name = dataset_name.replace('daily','provenance')
        builder.setDatasetAttributes(dataset_name, **date_attrs)
        builder.close()
        del daily_gdd

# turn annoying numpy warnings back on
warnings.resetwarnings()
