
import os

import numpy as N

from frost.factory import FrostGridFactory

from frost.functions import fromConfig
from frost.grape.functions import varietyFilepath

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GrapeGridFactory(FrostGridFactory):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getTargetDateSpan(self, year_or_start_date, variety=None):
        return FrostGridFactory.getTargetDateSpan(self, year_or_start_date,
                                                  'grape', variety)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getVarietyFilePath(self, target_year, variety, test_file=False):
        if isinstance(variety, basestring):
            _variety_ = fromConfig('crops.grape.variety.%s' % variety)
            return varietyFilepath(target_year, _variety_, test_file)
        else: return varietyFilepath(target_year, variety, test_file)

    def getVarietyManager(self, target_year, variety, mode, test_file=False):
        from frost.grape.grid import GrapeVarietyFileManager
        return GrapeVarietyFileManager(target_year, variety, mode, test_file)

    def getVarietyReader(self, target_year, variety, test_file=False):
        from frost.grape.grid import GrapeVarietyFileReader
        return GrapeVarietyFileReader(target_year, variety, test_file)

    def getVarietyVisualizer(self, target_year, variety, test_file=False):
        from frost.grape.visual import GrapeVarietyGridVisualizer
        return GrapeVarietyGridVisualizer(target_year, variety, test_file)

    def newVarietyManager(self, target_year, variety, test_file=False,
                                verbose=False, **kwargs):
        from frost.grape.builder import GrapeVarietyFileBuilder
        default = fromConfig('default')
        start_date, end_date = self.getTargetDateSpan(target_year)
        
        reader = self.getTempGridReader(target_year, test_file)
        if 'bbox' in kwargs:
            return GrapeVarietyFileBuilder(variety, start_date, end_date,
                                           reader.lons, reader.lats, test_file,
                                           verbose, **kwargs)
        else:
            return GrapeVarietyFileBuilder(variety, start_date, end_date,
                                           reader.lons, reader.lats, test_file,
                                           verbose, bbox=reader.data_bbox,
                                           **kwargs)

