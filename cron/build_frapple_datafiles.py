#! /Volumes/projects/venvs/apple/bin/python

import os, sys
import datetime
import warnings
import numpy as N

from atmosci.hdf5.dategrid import Hdf5DateGridFileManager, \
                                  Hdf5DateGridFileReader

from frapple.factory import AppleFrostToolFactory, AppleFrostToolBuildFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def datesToDateAttributes(dates):
    date_attrs = { }
    for key, date in dates.items():
        date_attrs[key] = date.strftime('%Y=%m-%d')
    return date_attrs

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-d', action='store_true', dest='is_dev_build',
                        default=False)
parser.add_option('-q', action='store_false', dest='exit_quietly', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
exit_quietly = options.exit_quietly
is_dev_build = options.is_dev_build
verbose = options.verbose or debug

if is_dev_build:
    build_factory = AppleFrostToolBuildFactory('dev')
    tool_factory = AppleFrostToolFactory('dev')
else: 
    build_factory = AppleFrostToolBuildFactory('build')
    tool_factory = AppleFrostToolFactory('build')

if len(args) == 1:
    year = int(args[0])
    target_year, season_start, season_end = tool_factory.seasonDates(year)
else:
    today = datetime.date.today()
    target_year, season_start, season_end = tool_factory.seasonDates(today)
    if today < season_start or today > season_end:
        # quietly exit when outside season ... useful when used in cron
        if exit_quietly: sys.exit(0)
        errmsg = "Taday's date is not within season limits. Try passing the"
        errmsg += "%s target year as an argument on the command line."
        raise ValueError, errmsg

season_dates = {'start_date':season_start.strftime('%Y-%m-%d'),
                'end_date':season_end.strftime('%Y-%m-%d'),
               }

source = tool_factory.sourceConfig(tool_factory.tool.data_source_key)
region = tool_factory.regionConfig(tool_factory.tool.data_region_key)

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# extract mint and it's dates from the temperature file
reader = build_factory.tempsFileReader(target_year, source, region)
print reader.filepath
try:
    mint = reader.dateSlice('temps.mint', season_start, season_end)
    mint_dates = reader.dateAttributes('temps.mint')
except:
    mint = reader.dateSlice('reported.mint', season_start, season_end)
    mint_dates = reader.dateAttributes('reported.mint')
reader.close()
del reader

# chunks definition to be used for date matrix datasets
num_days = (season_end - season_start).days + 1
chunks = (num_days, 1, 1)

# path to stage index dataset in original file
stage_index_path = 'Carolina.L43H86.stage.index'

# build files for each variety
for key in tool_factory.tool.varieties.keys():
    print('\nprocessing %s variety' % key)
    variety = tool_factory.tool.varieties[key]
    # create a reader for the variety file in the tool's build directory
    reader = \
        build_factory.varietyFileReader(variety, target_year, source, region)
    # get stage data now because it will be used when building each files
    stages = \
    reader.dateSlice(stage_index_path, season_start, season_end)
    # stage season dates will be used for all constructed datasets
    dates = reader.dateAttributes(stage_index_path)
    print variety.name, 'dates :\n', dates
    #exit()
    #dates.update(season_dates)
    #if 'last_obs_date' not in dates:
    #    dates['last_obs_date'] = dates['last_valid_date']

    # 
    # build Freeze Risk file
    #
    print('building Freeze Risk file and installing lat,lon datasets')
    builder = \
        tool_factory.riskFileBuilder(variety, target_year, source, region)
    builder.build(False, False)
    builder.initLonLatData(reader.lons, reader.lats)
    builder.close()

    # create a arrays for kill potential
    print('    creating kill temperature arrays')
    kill_t10 = N.full(stages.shape, N.nan, float)
    kill_t50 = N.full(stages.shape, N.nan, float)
    kill_t90 = N.full(stages.shape, N.nan, float)
    # fill the arrays with actual kill temperatures for each stage
    kill_temps = [ item[1]
                   for item in tool_factory.tool.kill_temps.attrs.items() ]
    for stage, temps in enumerate(kill_temps):
        indexes = N.where(stages == stage)
        if len(indexes[0]) > 0:
            kill_t10[indexes] = temps[0]
            kill_t50[indexes] = temps[1]
            kill_t90[indexes] = temps[2]

    print('    initializing T10 dataset')
    builder.open('a')
    builder.buildDataset('T10', data=kill_t10, chunks=chunks, **dates)
    builder.close()

    print('    initializing T50 dataset')
    builder.open('a')
    builder.buildDataset('T50', data=kill_t50, chunks=chunks, **dates)
    builder.close()

    print('    initializing T90 dataset')
    builder.open('a')
    builder.buildDataset('T90', data=kill_t90, chunks=chunks, **dates)
    builder.close()

    print('    initializing mint dataset')
    builder.open('a')
    builder.buildDataset('mint', data=mint, chunks=chunks, **dates)
    builder.close()
    del builder

    #
    # build tool stage file
    #
    print('building Stage file and installing lat,lon datasets')
    builder = \
        tool_factory.stageFileBuilder(variety, target_year, source, region)
    builder.build(False, False)
    builder.initLonLatData(reader.lons, reader.lats)
    builder.close()

    print('    initializing stage dataset')
    builder.open('a')
    builder.buildDataset('stage', data=stages, chunks=chunks, **dates)
    builder.close()
    # copy key provenance attributes from original stage grid
    attrs = { }
    for key, value in reader.datasetAttributes(stage_index_path).items():
        if 'Stage' in key or 'threshold' in key: attrs[key] = value
    if attrs:
        builder.open('a')
        builder.setDatasetAttributes('stage', **attrs)
        builder.close()

    # also put min temp dataset in the Stage file
    print('    initializing mint dataset')
    builder.open('a')
    builder.buildDataset('mint', data=mint, chunks=chunks, **dates)
    builder.close()

# turn annoying numpy warnings back on
warnings.resetwarnings()
