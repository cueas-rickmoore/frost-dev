#! /Volumes/projects/venvs/grape/bin/python

import os
import datetime
import warnings

import numpy as N

from atmosci.utils.timeutils import elapsedTime

from grapehard.factory import GrapeHardinessBuildFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-d', action='store_true', dest='is_dev_build',
                  default=False)
parser.add_option('-r', action='store', dest='region', default=None)
parser.add_option('-s', action='store', dest='source', default=None)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

build_start = datetime.datetime.now()

debug = options.debug
is_dev_build = options.is_dev_build
verbose = options.verbose

if is_dev_build: factory = GrapeHardinessBuildFactory('dev')
else: factory = GrapeHardinessBuildFactory('build')
project = factory.projectConfig()

if len(args) > 0: target_year = int(args[0])
else:
    today = datetime.date.today()
    target_year = factory.targetYear(today)
    if target_year is None: exit() # die gracefully during daily cron builds
season, season_start, season_end = factory.seasonDates(target_year)
days_in_target = (season_end - season_start).days + 1
season_start_str = season_start.strftime('%Y-%m-%d')
season_end_str = season_end.strftime('%Y-%m-%d')
if debug: print 'season dates', season_start, season_end

# iterate over list of varieties currently being built
chunks = list(factory.config.datasets.hardtemp.chunks)
chunks[chunks.index("num_days")] = days_in_target
chunks = tuple(chunks)

region_key = options.region
if region_key is None: region_key = project.region
if len(region_key) == 2: region_key = region_key.upper()
region = factory.regionConfig(region_key)

source_key = options.source
if source_key is None: source_key = project.source
source = factory.sourceConfig(source_key)

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# will use the same temperature extremes for all varieties
reader = factory.buildFileReader('tempext', target_year, source, region)

# build a new file
builder = factory.tempextFileBuilder(target_year, source, region,
                                     root='tooldata', bbox=reader.data_bbox)
print 'building file :', builder.filepath
print ' from data in :', reader.filepath

builder.initLonLatData(lons=reader.lons, lats=reader.lats)
builder.close()
builder.open('a')
builder.initFileAttributes()
builder.close()

if debug: print '\nbuilding target maxt dataset'
builder.config.datasets.maxt.chunks = chunks
data = reader.dateSlice('reported.maxt', season_start, season_end)
builder.open('a')
builder.buildDataset('maxt', data=data)
builder.close()
attrs = reader.dateAttributes('reported.maxt')
attrs['start_date'] = season_start_str
attrs['end_date'] = season_end_str
if debug: print '    setting maxt attributes :\n    ', attrs
builder.open('a')
builder.setDatasetAttributes('maxt', **attrs)
builder.close()

if debug: print '\nbuilding target mint dataset'
builder.config.datasets.mint.chunks = chunks
data = reader.dateSlice('reported.mint', season_start, season_end)
builder.open('a')
builder.buildDataset('mint', data=data)
builder.close()
attrs = reader.dateAttributes('reported.mint')
attrs['start_date'] = season_start_str
attrs['end_date'] = season_end_str
if debug: print '    setting mint attributes :\n   ', attrs
builder.open('a')
builder.setDatasetAttributes('mint', **attrs)
builder.close()

for variety_key in project.varieties:
    if debug: print '\nbuilding tool file for', variety_key
    variety = factory.varietyConfig(variety_key)

    # delete existing file
    reader = factory.buildFileReader('build', target_year, source, region, variety)
    # build a new file
    builder = factory.varietyFileBuilder(variety, target_year, season_start,
                                         season_end, source, region,
                                         root='tooldata',
                                         bbox=reader.data_bbox)
    print '    building file :', builder.filepath
    print '    from data in :', reader.filepath
    builder.config.datasets.hardtemp.chunks = chunks

    builder.initLonLatData(lons=reader.lons, lats=reader.lats)
    builder.close()
    builder.open('a')
    builder.initFileAttributes()
    builder.close()

    if debug: print '    building hardtemp dataset'
    builder.config.datasets.hardtemp.chunks = chunks
    data = reader.dateSlice('hardiness.temp', season_start, season_end,
                            dtype=float, missing=N.nan, units='F')

    builder.open('a')
    builder.buildDataset('hardtemp', data=data, start_date=season_start,
                         end_date=season_end)
    builder.close()
    attrs = reader.dateAttributes('hardiness.temp')
    attrs['start_date'] = season_start_str
    attrs['end_date'] = season_end_str
    attrs['units'] = 'F'
    if debug: print '    setting hardtemp attributes :\n    ', attrs
    builder.open('a')
    builder.setDatasetAttributes('hardtemp', **attrs)
    builder.close()

# turn annoying numpy warnings back on
warnings.resetwarnings()

msg = '... finished building files for temp extremes and %d grape varieties in %s' 
print msg % (len(project.varieties), elapsedTime(build_start,True))

