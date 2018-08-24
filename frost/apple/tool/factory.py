#! /usr/bin/env python

import os
import datetime

from atmosci.seasonal.factory import SeasonalSourceFileFactory
from atmosci.seasonal.methods.crop import CropVarietyPathMethods
from atmosci.utils.timeutils import timeSpanToIntervals

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from frost.config import CONFIG
from frost.apple.tool.config import TOOLCFG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleToolFactory(CropVarietyPathMethods, SeasonalSourceFileFactory):

    def __init__(self):
        SeasonalSourceFileFactory.__init__(self)
        self.apple = CONFIG.crops.apple.copy('apple',None)
        self.tool = TOOLCFG.copy('tool',None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataDirpath(self, key, app, target_year, region, source, subdir,
                          filetype=None):
        template_keys = \
            self.dirTemplateKeys(app, target_year, region, source, subdir)
        if filetype == 'variety':
            data_dir = self.tool.dirpaths.data[app] % template_keys
            dirpath = os.path.join(self.tool.dirpaths.root[key], data_dir)
        else:
            data_dir = self.tool.dirpaths.data[app] % template_keys
            dirpath = \
                os.path.join(self.tool.dirpaths.root[key], data_dir)
        if not os.path.exists(dirpath): os.makedirs(dirpath)
        return dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataFilename(self, app, target_year, region, source, subdir,
                           filetype=None):
        if filetype == 'variety':
            template_keys = \
                self.fileTemplateKeys(target_year, region, source, subdir)
        else:
            template_keys = self.fileTemplateKeys(target_year, region, source)
        if filetype is None:
            return self.tool.filenames[app][subdir] % template_keys
        else: return self.tool.filenames[app][filetype] % template_keys

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def datesFromDateSpan(self, start_date, end_date=None):
        if end_date is None or end_date == start_date: return (start_date,)
        else: return timeSpanToIntervals(start_date, end_date, 'day', 1)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def devFilepath(self, app, target_year, region, source, subdir,
                          filetype=None):
        data_dirpath = self.dataDirpath('dev', app, target_year, region,
                                        source, subdir, filetype)
        filename = self.dataFilename(app, target_year, region, source, subdir,
                                     filetype)
        return os.path.join(data_dirpath, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dirTemplateKeys(self, app, target_year, region, source, subdir):
        key_dict = { 'region': self.regionToDirpath(region),
                     'source': self.sourceToDirpath(source),
                     'year': target_year }
        if isinstance(subdir, basestring):
            if app == 'frost' and subdir != 'temp':
                key_dict['subdir'] = os.path.join('apple', subdir)
            else: key_dict['subdir'] = subdir
        else:
            variety_dir = self.varietyToDirpath(subdir)
            if app == 'frost':
                key_dict['subdir'] = os.path.join('apple', variety_dir)
            else: key_dict['subdir'] = variety_dir
        return key_dict

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fileTemplateKeys(self, target_year, region, source, variety=None):
        key_dict = { 'region': self.regionToFilepath(region),
                     'source': self.sourceToFilepath(source),
                     'year': target_year }
        if variety is not None:
            key_dict['variety'] = self.varietyToFilepath(variety)
        return key_dict

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def region(self, region=None):
        if region is None:
            return self.tool.regions[self.tool.project.region]
        elif isinstance(region, basestring):
            return self.tool.regions[region]
        else: return region

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def seasonDates(self, date_or_year):
        end_day = self.tool.project.end_day
        start_day = self.tool.project.start_day
        if type(date_or_year) == int:
            year = date_or_year
        else: 
            if date_or_year.month > end_day[0]: year = date_or_year.year + 1
            else: year = date_or_year.year
        season = (year, datetime.date(year-1, *start_day), 
                        datetime.date(year, *end_day))
        return season

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def source(self, source=None):
        if source is None:
            return self.tool.sources[self.tool.project.source]
        elif isinstance(source, basestring):
            return self.tool.sources[source]
        else: return source

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def toolFilepath(self, app, target_year, region, source, subdir,
                           filetype=None):
        data_dirpath = self.dataDirpath('tool', app, target_year, region,
                                        source, subdir, filetype)
        filename = self.dataFilename(app, target_year, region, source, subdir,
                                     filetype)
        return os.path.join(data_dirpath, filename)

