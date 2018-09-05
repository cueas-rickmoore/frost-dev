#! /Volumes/projects/venvs/grape/bin/python

import os, sys
import datetime
ONE_DAY = datetime.timedelta(days=1)

#from frost.temperature import FrostTempFileReader
#from frost.temperature import FrostTempFileManager

from atmosci.hdf5.dategrid import Hdf5DateGridFileManager, \
                                  Hdf5DateGridFileReader
from atmosci.seasonal.methods.paths import PathConstructionMethods

from grapehard.factory import GrapeHardinessToolFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from grapehard.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PathConstuctor(PathConstructionMethods):
    def __init__(self):
        self.config = CONFIG.copy()
        self.project = self.config.project

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-d', action='store_true', dest='is_dev_mode',
                        default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

time_attrs = { 'period':'date', 'scope':'season', 'view':'tyx' }

debug = options.debug
exit_quietly = not debug
is_dev_mode = options.is_dev_mode 
verbose = options.verbose or debug

today = datetime.date.today()
last_usable_obs = today - ONE_DAY
last_usable_obs_str = last_usable_obs.strftime('%Y-%m-%d')

fcast_year = today.year

if len(args) == 1: target_year = int(args[0])
else: 
    ght_factory = GrapeHardinessToolFactory()
    target_year = ght_factory.targetYear(today)
    if target_year is None:
        if exit_quietly: sys.exit(0)
        errmsg = "Taday's date is not within season limits. Try passing the"
        errmsg += " target year as an argument on the command line."
        raise ValueError, errmsg

path_finder = PathConstuctor()

source = CONFIG.sources[CONFIG.project.source]
source_dirpath = path_finder.sourceToDirpath(source)
source_filepath = path_finder.sourceToFilepath(source)

region = CONFIG.regions[CONFIG.project.region]
region_dirpath = path_finder.regionToDirpath(region)
region_filepath = path_finder.regionToFilepath(region)

template_args = { 'region': region_filepath, 'source': source_filepath,
                  'year': target_year }

season_start = datetime.date(target_year-1, *CONFIG.project.start_day)
season_end = datetime.date(target_year, *CONFIG.project.end_day)

if is_dev_mode: dirpaths = CONFIG.modes.dev.dirpaths
else: dirpaths = CONFIG.modes.build.dirpaths

frost_dirpath = os.path.join(dirpaths.frost, str(target_year), 'temp')
template = CONFIG.filenames.frost_temp
frost_filename = template % { 'year':target_year }
frost_filepath = os.path.join(frost_dirpath, frost_filename)

template = CONFIG.filenames.tempext
build_filename =  template % template_args
build_dirpath = \
    os.path.join(dirpaths.build, region_dirpath, source_dirpath, 'temps')
build_filepath = os.path.join(build_dirpath, build_filename)
if not (os.path.exists(build_dirpath)): os.makedirs(build_dirpath)
elif os.path.exists(build_filepath): os.remove(build_filepath)

#reader = FrostTempFileReader(target_year, filepath=frost_filepath)
reader = Hdf5DateGridFileReader(frost_filepath)
print 'Copying : ', reader.filepath

#manager = FrostTempFileManager(target_year, mode='a', filepath=build_filepath)
manager = Hdf5DateGridFileManager(build_filepath, mode='a')
print 'To : ', manager.filepath

manager.setFileAttributes(**dict(reader.getFileAttributes()))
manager.close()

for name in reader.group_names:
    if name != 'forecast':
        attrs = reader.getGroupAttributes(name)
        if debug: print "creating '%s' group" % name
        manager.open('a')
        manager.createGroup(name)
        manager.setGroupAttributes(name, **attrs)
        manager.close()

for name in reader.dataset_names:
    if 'forecast' not in name:
        if debug: print "creating '%s' dataset" % name
        dataset = reader.getDataset(name)
        chunks = dataset.chunks
        attrs = dict(dataset.attrs)
        if 'last_valid_date' in attrs:
            last_valid = last_valid = datetime.date(*tuple([int(d) for d in attrs['last_valid_date'].split('-')]))
            if last_valid > last_usable_obs:
                attrs['last_valid_date'] = last_usable_obs_str
            attrs['last_obs_date'] = attrs['last_valid_date']
        manager.open('a')
        manager.createDataset(name, dataset, chunks=chunks)
        manager.close()
        manager.open('a')
        manager.setDatasetAttributes(name, **attrs)
        manager.close()
        manager.open('a')
        manager.setDatasetAttributes(name, **time_attrs)
        manager.close()

reader.close()
manager.open('r')
build_last_valid = manager.dateAttribute('reported.maxt', 'last_valid_date', None)
if build_last_valid is None:
    print 'BUILD FILE ERROR: ', factory.filepath
    msg = 'DATE MISSING: "last_valid_date" not found in "reported.maxt" dataset'
    print msg % build_last_valid.strftime("%Y-%m-%d")
    os.exit()
build_end_date = manager.dateAttribute('reported.maxt', 'end_date')

slice_start = build_last_valid + ONE_DAY
if slice_start > build_end_date:
    msg = 'EXITING: start of temperature slice (%s) is past end of season (%s)'
    print msf % (slice_start.strftime("%Y-%m-%d"),build_end_date.strftime("%Y-%m-%d"))
    os.exit()
build_start_date = manager.dateAttribute('reported.maxt', 'start_date')
manager.close()

# add forecast from shared temperature file to this season's temperature file
temps_dirpath = \
    os.path.join(dirpaths.shared, region_dirpath, source_dirpath, 'temps')
template = CONFIG.filenames.shared_temp
template_args['year'] = fcast_year
temps_filename = template % template_args
temps_filepath = os.path.join(temps_dirpath, temps_filename)

reader = Hdf5DateGridFileReader(temps_filepath)
if debug:
    print 'Reading from emperature extremes file :'
    print '    ', reader.filepath

last_obs = reader.dateAttribute('temps.maxt', 'last_obs_date')
if last_obs > build_end_date:
    msg = 'EXITING: last observed temp (%s) is past end of season (%s)'
    print msf % (last_obs.strftime("%Y-%m-%d"),build_file_end.strftime("%Y-%m-%d"))
    os.exit()

last_valid = reader.dateAttribute('temps.maxt', 'last_valid_date')
if last_valid > build_end_date: last_valid = build_end_date

fcast_start = reader.dateAttribute('temps.maxt', 'fcast_start_date', None)
if fcast_start is None:
    reader.close()
    print 'FILE: ', factory.filepath
    print 'DATE MISSING: "fcast_start_date" not specified in "temps.maxt"'
    print 'EXITING : temperature extremes file does not contain a forecast.'
    os.exit()
if fcast_start >= build_end_date:
    reader.close()
    print 'FILE: ', factory.filepath
    msg = 'TOO LATE: forecast start (%s) is after season end (%s)'
    print msg % (fcast_start.strftime("%Y-%m-%d"), build_end_date.strftime("%Y-%m-%d"))
    os.exit()

fcast_end = reader.dateAttribute('temps.maxt', 'fcast_end_date', None)
if fcast_end is None:
    reader.close()
    print 'FILE: ', factory.filepath
    print 'DATE MISSING: "fcast_end_date" not specified in "temps.maxt"'
    print 'EXITING : temperature extremes file does not contain a valid forecast.'
    os.exit()
if fcast_end < build_start_date:
    print 'FILE: ', factory.filepath
    reader.close()
    msg = 'TOO EARLY: forecast end (%s) is before season start (%s)'
    print msg % (fcast_end.strftime("%Y-%m-%d"), build_start_date.strftime("%Y-%m-%d"))
    os.exit()

if fcast_end > build_end_date: fcast_end = build_end_date
if last_valid > fcast_end: last_valid = fcast_end

attrs = { 'last_obs_date': last_obs.strftime('%Y-%m-%d'),
          'last_valid_date': last_valid.strftime('%Y-%m-%d'),
          'fcast_start_date': fcast_start.strftime('%Y-%m-%d'),
          'fcast_end_date': fcast_end.strftime('%Y-%m-%d')
}
if debug:
    print 'adding forecast to build file'
    print '      ', manager.filepath
print slice_start, 'to', fcast_end
print attrs

slice_start = min(last_obs, fcast_start)
for extreme in ('maxt','mint'):
    dataset_name = 'reported.%s' % extreme
    data = reader.dateSlice('temps.%s' % extreme, slice_start, fcast_end)
    manager.open('a')
    manager.insertByDate(dataset_name, data, slice_start)
    #manager.updateTemp(dataset_name, data, slice_start)
    manager.setDatasetAttributes(dataset_name, **attrs)
    #manager.setDatasetAttributes('%s_provenance' + dataset_name , **attrs)
    manager.close()

reader.close()

