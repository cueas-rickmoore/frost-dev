#! /Volumes/projects/venvs/grape/bin/python

import os, sys
import datetime

from atmosci.hdf5.dategrid import Hdf5DateGridFileManager, \
                                  Hdf5DateGridFileReader

#from frost.grape.grid import GrapeVarietyFileReader
from atmosci.seasonal.methods.paths import PathConstructionMethods

from grapehard.factory import GrapeHardinessToolFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from frost.grape.config import VARIETIES
from grapehard.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PathConstuctor(PathConstructionMethods):
    def __init__(self):
        self.config = CONFIG.copy()
        self.project = self.config.project

    def varietyToFilepath(self, variety):
        return self.normalizeFilepath(variety.name)

    def varietyToDirpath(self, variety):
        return self.normalizeDirpath(variety.name)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-d', action='store_true', dest='is_dev_mode', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

time_attrs = { 'period':'date', 'scope':'season', 'view':'tyx' }

debug = options.debug
exit_quietly = not debug
is_dev_mode = options.is_dev_mode

if len(args) == 1: target_year = int(args[0])
else: 
    ght_factory = GrapeHardinessToolFactory()
    target_year = ght_factory.targetYear(datetime.date.today())
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

if is_dev_mode: dirpaths = CONFIG.modes.dev.dirpaths
else: dirpaths = CONFIG.modes.build.dirpaths
template_args = { 'year':target_year, }

frost_template = CONFIG.filenames.frost_variety
frost_dirpath = os.path.join(dirpaths.frost, str(target_year), 'grape')

build_template = CONFIG.filenames.build
build_dirpath = os.path.join(dirpaths.build, region_dirpath, source_dirpath)
if not (os.path.exists(build_dirpath)): os.makedirs(build_dirpath)

# crops.grape.varieties.build has list of varieties currently being built
for variety_key in CONFIG.project.varieties:
    variety = VARIETIES[variety_key]
    template_args['variety'] = path_finder.varietyToFilepath(variety)
    variety_path = path_finder.varietyToDirpath(variety)

    # filepath to frost file for this variety
    filename = frost_template % template_args
    frost_filepath = os.path.join(frost_dirpath, variety_path, filename)

    # frost grape file reader for the variety
    reader = Hdf5DateGridFileReader(frost_filepath)
    print 'Copying : ', reader.filepath

    # filepath to grapehard file for this variety
    filename = build_template % template_args
    variety_dirpath = os.path.join(build_dirpath, variety_path)
    build_filepath = os.path.join(variety_dirpath, filename)
    if not(os.path.exists(variety_dirpath)): os.makedirs(variety_dirpath)
    elif os.path.exists(build_filepath): os.remove(build_filepath)

    # grapehard build file manager for the variety
    manager = Hdf5DateGridFileManager(build_filepath, mode='a')
    print 'TO : ', manager.filepath
    manager.setFileAttributes(**dict(reader.getFileAttributes()))
    manager.close()

    for name in reader.group_names:
        attrs = reader.getGroupAttributes(name)
        if debug: print "creating '%s' group" % name
        manager.open('a')
        manager.createGroup(name)
        manager.setGroupAttributes(name, **attrs)
        manager.close()

    for name in reader.dataset_names:
        if debug: print "creating '%s' dataset" % name
        dataset = reader.getDataset(name)
        chunks = dataset.chunks
        attrs = dict(dataset.attrs)
        if name not in ('lon','lat'):
            attrs['last_obs_date'] = attrs['last_valid_date']
            manager.open('a')
            manager.createDataset(name, dataset, start_date=attrs['start_date'],
                                  end_date=attrs['end_date'], chunks=chunks)
            manager.close()

            manager.open('a')
            manager.setDatasetAttributes(name, **time_attrs)
            manager.close()
        else:
            manager.open('a')
            manager.createDataset(name, dataset)
            manager.close()

        manager.open('a')
        manager.setDatasetAttributes(name, **attrs)
        manager.close()

    reader.close()

