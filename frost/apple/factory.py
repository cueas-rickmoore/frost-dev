
import os

import numpy as N

from frost.factory import FrostGridFactory

from frost.functions import fromConfig
from frost.apple.functions import chillFilepath, varietyFilepath

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleGridFactory(FrostGridFactory):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getTargetDateSpan(self, year_or_date, variety=None):
        return FrostGridFactory.getTargetDateSpan(self, year_or_date,
                                                  'apple', variety)

    def getTargetYear(self, date, variety=None):
        return FrostGridFactory.getTargetyear(self, date, 'apple', variety)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getChillFilePath(self, target_year, test_file=False):
        return chillFilepath(target_year, test_file)

    def getChillGridManager(self, target_year, mode='r', test_file=False):
        from frost.apple.chill.grid import AppleChillGridManager
        return AppleChillGridManager(target_year, mode, test_file)

    def getChillGridReader(self, target_year, test_file=False):
        from frost.apple.chill.grid import AppleChillGridReader
        return AppleChillGridReader(target_year, test_file)

    def newChillGridManager(self, target_year, models, gdd_thresholds=None,
                                  test_file=False, **kwargs):
        from frost.apple.chill.grid import AppleChillGridBuilder
        start_date, end_date = self.getTargetDateSpan(target_year)
        if models is None: models = fromConfig('crops.apple.chill.models')
        if gdd_thresholds is None:
            gdd_thresholds = fromConfig('crops.apple.gdd_thresholds')

        filepath = self.getChillFilePath(target_year, test_file)
        dest_dir = os.path.split(filepath)[0]
        if not os.path.exists(dest_dir): os.makedirs(dest_dir)

        if 'lons' in kwargs:
            return AppleChillGridBuilder(start_date, end_date, kwargs['lons'],
                                         kwargs['lats'], models, gdd_thresholds,
                                         test_file, **kwargs)
        else:
            reader = self.getTempGridReader(target_year)
            return AppleChillGridBuilder(start_date, end_date, reader.lons, 
                                         reader.lats, models, gdd_thresholds,
                                         test_file, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getVarietyFilePath(self, target_year, variety, test_file=False):
        if isinstance(variety, basestring): var_name = variety
        else: var_name = variety.name
        return varietyFilepath(target_year, var_name, test_file)

    def getVarietyGridManager(self, target_year, variety_name, mode='r',
                                    test_file=False):
        from frost.apple.variety.grid import AppleVarietyGridManager
        return  AppleVarietyGridManager(target_year, variety_name, mode, test_file)

    def getVarietyGridReader(self, target_year, variety_name, test_file=False):
        from frost.apple.variety.grid import AppleVarietyGridReader
        return AppleVarietyGridReader(target_year, variety_name, test_file)

    def getVarietyVisualizer(self, target_year, variety_name, mode='r',
                                    test_file=False):
        from frost.apple.variety.visual import AppleVarietyGridVisualizer
        visualizer = \
        AppleVarietyGridVisualizer(target_year, variety_name, mode, test_file)
        return visualizer

    def newVarietyGridManager(self, target_year, variety, models,
                                    gdd_thresholds, test_file=False,
                                    verbose=False, **kwargs):
        from frost.apple.variety.grid import AppleVarietyGridBuilder
        start_date, end_date = self.getTargetDateSpan(target_year)
        if models is None: models = fromConfig('crops.apple.chill.models')
        if gdd_thresholds is None:
            gdd_thresholds = fromConfig('crops.apple.gdd_thresholds')

        filepath = self.getVarietyFilePath(target_year, variety, test_file)
        dest_dir = os.path.split(filepath)[0]
        if not os.path.exists(dest_dir): os.makedirs(dest_dir)

        if 'lons' in kwargs:
            return AppleVarietyGridBuilder(variety, start_date, end_date,
                               kwargs['lons'], kwargs['lats'], models,
                               gdd_thresholds, test_file, verbose, **kwargs)
        else:
            reader = self.getTempGridReader(target_year, test_file)
            return AppleVarietyGridBuilder(variety, start_date, end_date,
                               reader.lons, reader.lats, models, 
                               gdd_thresholds, test_file, verbose, **kwargs)

