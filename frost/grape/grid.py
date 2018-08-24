
import os

from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.functions import fromConfig
from frost.grid import FrostGridFileReader, FrostGridFileManager

from frost.grape.functions import varietyFilepath
from frost.grape.model import GrapeModelMixin

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

GDD_ACCESS_ERR = "'model_name', 'lo_gdd_th' and 'hi_gdd_th' are required to access %s"
MISSING_DATE = '"date" argument is required to %s grid.'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GrapeGridAccessMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Acclimation/Deacclimation data acccess
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAcclimation(self, start_date, end_date=None, **kwargs):
        """ Retrieve data from acclimation factor dataset for a sequence
        of dates.

        Arguments
        --------------------------------------------------------------------
        start_date   : datetime, scalar - first date to access
        end_date     : datetime, scalar or None - last date to access

        Returns:
        --------------------------------------------------------------------
        float, grid : Numpy grid of retrieved data. If end_date is None,
                      returns a single day in a 2D grid. Else, returns
                      a 3D grid with number of days as first dimension.
        """
        return self.getModelData('acclimation', 'factor', start_date, end_date,
                                 **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDeacclimation(self, start_date, end_date=None, **kwargs):
        """ Retrieve data from deacclimation factor dataset for a sequence
        of dates.

        Arguments
        --------------------------------------------------------------------
        start_date   : datetime, scalar - first date to access
        end_date     : datetime, scalar or None - last date to access

        Returns:
        --------------------------------------------------------------------
        float, grid : Numpy grid of retrieved data. If end_date is None,
                      returns a single day in a 2D grid. Else, returns
                      a 3D grid with number of days as first dimension.
        """
        return self.getModelData('deacclimation', 'factor', start_date,
                                 end_date, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Chill data acccess
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def chillDatasetPath(self, chill_type, dataset_name):
        """ Get a string that can be used to access a chill dataset

        Arguments
        --------------------------------------------------------------------
        chill_type   : string - source of chill data. Value will be one of
                       'common' (for 10C baesed  chill) or 'dormancy' (for
                       chill based on dormancy stage)
        dataset_name : string - type of data to access. Value will be one
                       of 'daily', accumulated', 'provenance'.

        Returns:
        --------------------------------------------------------------------
        string - full path used to access dataset in HDF5 file.
        """

        return self.modelDatasetPath(self.chillGroupPath(chill_type),
                                     dataset_name)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def chillGroupPath(self, chill_type):
        """ Get a string that can be used to access a chill group

        Arguments
        --------------------------------------------------------------------
        chill_type   : string - source of chill data. Value will be one of
                       'common' (for 10C baesed  chill) or 'dormancy' (for
                       chill based on dormancy stage)

        Returns:
        --------------------------------------------------------------------
        string - full path used to access group in HDF5 file.
        """
        return 'chill.%s' % chill_type

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getChillData(self, chill_type, dataset_name, start_date, end_date=None,
                           **kwargs):
        """ Retrieve data from a chill dataset for a sequence of dates,

        Arguments
        --------------------------------------------------------------------
        chill_type   : string - source of chill data. Value will be one of
                       'common' (for 10C baesed  chill) or 'dormancy' (for
                       chill based on dormancy stage)
        dataset_name : string - type of data to access. Value will be one
                       of 'daily', accumulated', 'provenance'.
        start_time   : datetime, scalar - first date to access
        end_date     : datetime, scalar or None - last date to access

        Returns:
        --------------------------------------------------------------------
        float, grid : Numpy grid of retrieved data. If end_date is None,
                      returns a single day in a 2D grid. Else, returns
                      a 3D grid with number of days as first dimension.
        """
        chill_group = self.chillGroupPath(chill_type)
        return self.getModelData(chill_group, dataset_name, start_date,
                                 end_date, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Dormancy access
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDormancy(self, start_date, end_date=None, **kwargs):
        """ Retrieve data from dormancy stage dataset for a sequence of dates.

        Arguments
        --------------------------------------------------------------------
        start_date   : datetime, scalar - first date to access
        end_date     : datetime, scalar or None - last date to access

        Returns:
        --------------------------------------------------------------------
        float, grid : Numpy grid of retrieved data. If end_date is None,
                      returns a single day in a 2D grid. Else, returns
                      a 3D grid with number of days as first dimension.
        """
        return self.getModelData('dormancy', 'stage', start_date, end_date,
                                 **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Growing degree day access 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getGDD(self, dataset_name, start_date, end_date=None, **kwargs):
        """ Retrieve data from dormancy stage dataset for a sequence of dates.

        Arguments
        --------------------------------------------------------------------
        dataset_name : string - type of GDD data to access. Value will be
                       one of 'daily', accumulated', 'provenance'.
        start_date   : datetime, scalar - first date to access
        end_date     : datetime, scalar or None - last date to access

        Returns:
        --------------------------------------------------------------------
        float, grid : Numpy grid of retrieved data. If end_date is None,
                      returns a single day in a 2D grid. Else, returns
                      a 3D grid with number of days as first dimension.
        """
        return self.getModelData('gdd', dataset_name, start_date, end_date,
                                 **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Hardiness data access
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getHardiness(self, start_date, end_date=None, **kwargs):
        """ Retrieve data from hardiness temperature dataset for a sequence
        of dates.

        Arguments
        --------------------------------------------------------------------
        start_date   : datetime, scalar - first date to access
        end_date     : datetime, scalar or None - last date to access

        Returns:
        --------------------------------------------------------------------
        float, grid : Numpy grid of retrieved data. If end_date is None,
                      returns a single day in a 2D grid. Else, returns
                      a 3D grid with number of days as first dimension.
        """
        return self.getModelData('hardiness', 'temp', start_date, end_date,
                                 **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # data access methods used by multiple data types
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getModelData(self, group_path, dataset_name, start_date, end_date=None,
                           **kwargs):
        """ Retrieve data for a sequence of dates.

        Arguments
        --------------------------------------------------------------------
        group_path   : string - the name or path to one of the data
                       groups in the file
        dataset_name : string - name of a dataset group.
        start_date   : datetime, scalar - first date to access
        end_date     : datetime, scalar or None - last date to access

        Returns:
        --------------------------------------------------------------------
        float, grid : Numpy grid of retrieved data. If end_date is None,
                      returns a single day in a 2D grid. Else, returns
                      a 3D grid with number of days as first dimension.
        """
        full_dataset_path = self.modelDatasetPath(group_path, dataset_name)
        return self._getData(full_dataset_path, start_date, end_date, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getProvenance(self, group_path, start_date, end_date=None):
        """ Retrieve provenance data for a data group.

        Arguments
        --------------------------------------------------------------------
        group_path   : string - the name or path to one of the data groups
                       in the file
        start_date   : datetime, scalar - first date to access
        end_date     : datetime, scalar or None - last date to access

        Returns:
        --------------------------------------------------------------------
        float, grid : If end_date is None, returns a Numpy record scalar.
                      Else returns a 1D Numpy recarray.

        A Numpy record allows field access using named attributes. A Numpy 
        recarray is an array of Numpy records.

        You can get a list of "attributes" in a Numpy record using
        x.dtype.names, where x is a record instance. x[name] will return
        the value of the attribute. x.dtype.descr will return a list of
        (name, dtype) tuples fo
        r each record attribute.
        """
        full_dataset_path = self.modelDatasetPath(group_path, 'provenance')
        return self._getData(full_dataset_path, start_date, end_date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFilepath(self, target_year, variety, test_file=False):
        """Construct a complete file system path to the location of the
        appropriate data file for the variety being managed.

        Arguments
        --------------------------------------------------------------------
        target_year : int - year for which spring hardiness is/was estimated
        variety     : string or instance of GrapeVariety class. 
                      If string, it must be the key used to look up the
                      variety's instance in the configuration file.

        Returns:
        --------------------------------------------------------------------
        string : full directory path to the corresponding grid file
        """
        return varietyFilepath(target_year, variety, test_file)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def modelDatasetPath(self, group_path, dataset_name):
        """Construct a complete dotted path that can be used to access
        the requested dataset.

        Arguments
        --------------------------------------------------------------------
        group_path   : string - the name or path to one of the data
                       groups in the file
        dataset_name : string - name of a dataset group.

        Returns:
        --------------------------------------------------------------------
        string : complete dotted path to to dataset
        """
        return '%s.%s' % (group_path, dataset_name)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadGrapeDataPackers_(self):
        # register data packers
        packers = fromConfig('crops.grape.packers')
        # assign packer/unpacker for each gdd dataset
        for dataset_path in self._dataset_names:
            if not dataset_path.endswith('.provenance'):
                if 'acclim' in dataset_path:
                    self._packers[dataset_path] = packers['acclim']
                elif 'chill' in dataset_path:
                    self._packers[dataset_path] = packers['chill']
                elif 'dormancy' in dataset_path:
                    self._packers[dataset_path] = packers['dormancy']
                elif 'gdd' in dataset_path:
                    self._packers[dataset_path] = packers['gdd']
                elif 'hardiness' in dataset_path:
                    self._packers[dataset_path] = packers['hardiness']

    def _loadGrapeDataUnpackers_(self):
        # register data unpackers
        unpackers = fromConfig('crops.grape.unpackers')
        # assign packer/unpacker for each gdd dataset
        for dataset_path in self._dataset_names:
            if not dataset_path.endswith('.provenance'):
                if 'acclim' in dataset_path:
                    self._unpackers[dataset_path] = unpackers['acclim']
                elif 'chill' in dataset_path:
                    self._unpackers[dataset_path] = unpackers['chill']
                elif 'dormancy' in dataset_path:
                    self._unpackers[dataset_path] = unpackers['dormancy']
                elif 'gdd' in dataset_path:
                    self._unpackers[dataset_path] = unpackers['gdd']
                elif 'hardiness' in dataset_path:
                    self._unpackers[dataset_path] = unpackers['hardiness']

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _postInitGrape_(self, target_year, variety, **kwargs):
        """ Initialize class attributes that are common to all subclasses
        """
        self.target_year = target_year

        if isinstance(variety, basestring):
            _variety_ = fromConfig('crops.grape.varieties.%s' % variety)
        else: _variety_ = variety

        try:
            self.provenance.update(fromConfig('crops.grape.provenance'))
        except AttributeError:
            pass

        # cache the configuration so we don't do config lookups for every call
        self.variety = _variety_
        self.acclimation_rate = _variety_.acclimation_rate
        self.deacclimation_rate = _variety_.deacclimation_rate
        self.ecodormancy_threshold = _variety_.ecodormancy_threshold
        self.hardiness = _variety_.hardiness
        self.stage_thresholds = _variety_.stage_thresholds
        self.theta = _variety_.theta

        dormancy = fromConfig('crops.grape.dormancy')
        self.dormancy_descriptions = dormancy.stages.attributes
        self.dormancy_stages = dormancy.stages.attributes.keys()[1:]
        self.dormancyIndexFromStage = dormancy.indexFromStage
        self.dormancyStageFromIndex = dormancy.stageFromIndex


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GrapeVarietyFileReader(GrapeGridAccessMixin, GrapeModelMixin,
                             FrostGridFileReader):
    """ Grape variety data access and update manager
    """
    def __init__(self, target_year, variety, mode='r', test_file=False,
                       **kwargs):
        filepath = kwargs.get('filepath',None) 
        if filepath is None:
            filepath = varietyFilepath(target_year, variety, test_file)
            FrostGridFileReader.__init__(self, target_year, filepath)
        else: FrostGridFileReader.__init__(self, target_year, filepath)
        self._postInitGrape_(target_year, variety, **kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        """ Creates instance attributes specific to the content of the file
        to be managed.
        """
        # get superclass manager attributes
        FrostGridFileReader._loadManagerAttributes_(self)
        self._loadGrapeDataUnpackers_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GrapeVarietyFileManager(GrapeGridAccessMixin, GrapeModelMixin,
                              FrostGridFileManager):
    """ Grape variety data access and update manager
    """
    def __init__(self, target_year, variety, mode='r', test_file=False,
                       **kwargs):
        filepath = kwargs.get('filepath',None) 
        if filepath is None:
            filepath = varietyFilepath(target_year, variety, test_file)
            FrostGridFileManager.__init__(self, target_year, filepath, mode)
        else: FrostGridFileManager.__init__(self, target_year, filepath, mode)

        self._postInitGrape_(target_year, variety, **kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        """ Creates instance attributes specific to the content of the file
        to be managed.
        """
        # get superclass manager attributes
        FrostGridFileManager._loadManagerAttributes_(self)
        self._loadGrapeDataPackers_()
        self._loadGrapeDataUnpackers_()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Acclimation/Deacclimation data update
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateAcclimation(self, acclimation, start_date, **kwargs):
        """ Put acclimation data into the proper location in the stored
        datasets.  Also creates the provenance dataset based on statistics
        from each of the input grid.

        Arguments
        --------------------------------------------------------------------
        acclimation : int, 2D or 3D grid - acclimation factor
        start_date  : datetime, scalar - date where data is to be inserted.
                      if input data is 3D, it is the first date in the grid.
        """
        # update acclimation dataset
        full_dataset_path = self.modelDatasetPath('acclimation', 'factor')
        self.updateDataset(full_dataset_path, acclimation, start_date)
        # update acclimation provenance dataset
        self.updateProvenance('acclimation', acclimation, start_date,
                              prov_key='stats', **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateDeacclimation(self, deacclimation, start_date, **kwargs):
        """ Put deacclimation data into the proper location in the stored
        datasets.  Also creates the provenance dataset based on statistics
        from each of the input grid.

        Arguments
        --------------------------------------------------------------------
        deacclimation : int, 2D or 3D grid - acclimation factor
                        If 3D, first dimension must be number of days.
        start_date    : datetime, scalar - date where data is to be inserted.
                        if input data is 3D, it is the first date in the grid.
        """
        # update deacclimation dataset
        full_dataset_path = self.modelDatasetPath('deacclimation', 'factor')
        self.updateDataset(full_dataset_path, deacclimation, start_date)
        # update deacclimation provenance dataset
        self.updateProvenance('deacclimation', deacclimation, start_date,
                              prov_key='stats', **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Chill data update
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateChill(self, chill_type, daily, accumulated, start_date, **kwargs):
        """ Put chill data into the roper place in the stored datasets.
        Also creates the provenance dataset based on statistics from each of
        the input grids. 

        Arguments
        --------------------------------------------------------------------
        chill_type  : string - source of chill data. Value will be one of
                      'common' (for 10C baesed  chill) or 'dormancy' (for
                      chill based on dormancy stage)
        daily       : float, 2D or 3D grid - daily chill values
                      if 3D, time must be first dimension
        accumulated : float, 2D or 3D grid - accumulated chill values
                      if 3D, time must be first dimension
        start_date  : datetime, scalar - date where data is to be inserted.
                      if input data is 3D, it is the first date in the grid.
        NOTE: daily and accumulated data MUST have the same dimensions.
        """
        # update accumulated chill dataset
        full_dataset_path = self.chillDatasetPath(chill_type, 'accumulated')
        self.updateDataset(full_dataset_path, accumulated, start_date)
        # update daily chill dataset
        full_dataset_path = self.chillDatasetPath(chill_type, 'daily')
        self.updateDataset(full_dataset_path, daily, start_date)
        # update chill provenance dataset
        self.updateAccumulateProvenance(self.chillGroupPath(chill_type),
                                        daily, accumulated, start_date, 
                                        **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Dormancy update
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateDormancy(self, dormancy_stage, start_date, **kwargs):
        """ Put dormancy stage data into the proper location in the stored
        datasets.  Also creates the provenance dataset based on statistics
        from each of the input grid. 

        Arguments
        --------------------------------------------------------------------
        dormancy_stage : int, 2D or 3D grid - estimated dormancy stage
                         If 3D, first dimension must be number of days.
        start_date     : datetime, scalar - date where data is to be inserted.
                         if input data is 3D, it is the first date in the grid.
        """
        # update dormancy stage dataset
        full_dataset_path = self.modelDatasetPath('dormancy', 'stage')
        self.updateDataset(full_dataset_path, dormancy_stage, start_date)
        # update dormancy stage provenance dataset
        self.updateProvenance('dormancy', dormancy_stage, start_date, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Growing degree day update
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateGDD(self, daily, accumulated, start_date, **kwargs):
        """ Put GDD data into the proper location in the stored datasets.
        Also creates the provenance dataset based on statistics from each
        of the input grids. 

        Arguments
        --------------------------------------------------------------------
        daily       : float, 2D or 3D grid - daily GDD values.
                      If 3D, time must be first dimension
        accumulated : float, 2D or 3D grid - accumulated GDD values
                      If 3D, time must be first dimension
        start_date  : datetime, scalar - date where data is to be inserted.
                      If input data is 3D, it is the first date in the grid.
        If grids are 3D, first dimension must be number of days.
        NOTE: daily and accumulated data MUST have the same dimensions.
        """
        # update accumulated GDD dataset
        full_dataset_path = self.modelDatasetPath('gdd', 'accumulated')
        self.updateDataset(full_dataset_path, accumulated, start_date)
        # update daily GDD dataset
        full_dataset_path = self.modelDatasetPath('gdd', 'daily')
        self.updateDataset(full_dataset_path, daily, start_date)
        # update GDD provenance dataset
        self.updateAccumulateProvenance('gdd', daily, accumulated, start_date,
                                        **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Hardiness data update
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateHardiness(self, hardiness, start_date, **kwargs):
        """ Put hardiness data into the proper location in the stored datasets. 
        Also creates the provenance dataset based on statistics from each
        of the input grid.

        Arguments
        --------------------------------------------------------------------
        hardiness  : int, 2D or 3D grid - estimated hardiness temperature
                     If 3D, first dimension must be number of days.
        start_date : datetime, scalar - date where data is to be inserted.
                     if input data is 3D, it is the first date in the grid.
        """
        # update daily hardiness temperature dataset (acclim + deacclim)
        full_dataset_path = self.modelDatasetPath('hardiness', 'temp')
        self.updateDataset(full_dataset_path, hardiness, start_date)
        # update dormancy stage provenance dataset
        self.updateProvenance('hardiness', hardiness, start_date,
                              prov_key='stats', **kwargs)

