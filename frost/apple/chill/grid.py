
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig
from frost.grid import FrostGridBuilderMixin

from frost.apple.functions import chillFilepath, chillModelDescription
from frost.apple.grid import AppleGridFileReader, AppleGridFileManager

from frost.apple.chill.model import AppleChillModelMixin


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ChillGridAccessMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataFilepath(self, target_year, test_file=False):
        return chillFilepath(target_year, test_file)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Chill data access
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def chillDatasetPath(self, model_name, dataset):
        group_name = self.modelGroupName(model_name)
        return '%s.%s' % (group_name, dataset)

    def chillDatasetShape(self, model_name, dataset):
        full_path = self.chillDatasetPath(model_name, dataset)
        return self.getDatasetShape(full_path)

    def chillModelExists(self, model_name):
        return self.groupExists(self.modelGroupName(model_name))
 
    def getChill(self, model_name, dataset, start_date, end_date=None,
                       **kwargs):
        full_path = self.chillDatasetPath(model_name, dataset)
        return self._getData(full_path, start_date, end_date, **kwargs)
 
    def getChillProvenance(self, model_name, dataset, start_date,
                                 end_date=None):
        if dataset is not None:
            full_path =\
            self.chillDatasetPath(model_name, '%s_provenance' % dataset)
        else: full_path = self.chillDatasetPath(model_name, 'provenance')
        return self._getData(full_path, start_date, end_date)

    def thresholdGroupPath(self, lo_gdd_th, hi_gdd_th):
        return 'gdd.%s' % self.thresholdName(lo_gdd_th, hi_gdd_th)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Growing Degree Day data access and storage methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getGdd(self, lo_gdd_th, hi_gdd_th, start_date, end_date=None, **kwargs):
        full_path = self.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'daily')
        return self._getData(full_path, start_date, end_date, **kwargs)

    def getGddProvenance(self, lo_gdd_th, hi_gdd_th, start_date, end_date=None):
        full_path = self.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'provenance')
        return self._getData(full_path, start_date, end_date)

    def gddDatasetPath(self, lo_gdd_th, hi_gdd_th, dataset):
        group_name = self.gddGroupName(lo_gdd_th, hi_gdd_th)
        return 'gdd.L%dH%d.%s' % (lo_gdd_th, hi_gdd_th, dataset)

    def gddGroupName(self, lo_gdd_th, hi_gdd_th):
        return 'gdd.L%dH%d' % (lo_gdd_th, hi_gdd_th)

    def gddThresholds(self):
        thresholds  = [ ]
        for group_name in self._group_names:
            if group_name.startswith('gdd.L'):
                names = group_name.split('.')
                if len(names) == 2:
                    low, high = names[1][1:].split('H')
                    thresholds.append( (int(low), int(high)) )
        return thresholds

    def hasThreshold(self, lo_gdd_th, hi_gdd_th):
        full_path = self.thresholdGroupPath(lo_gdd_th, hi_gdd_th)
        return full_path in self._group_names

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Cache file attributes and dataset packers/unpakcers
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadChillFileAttributes_(self):
        ThisClass = self.__class__
        for group_name in self._group_names:
            for dataset_path in self.getGroupHierarchy(group_name)[1:]:
                if dataset_path.split('.')[-1] in ('daily','accumulated'):
                    if 'gdd' in group_name:
                        self._packers[dataset_path] = ThisClass.packGdd
                        self._unpackers[dataset_path] = ThisClass.unpackGdd
                    else:
                        self._packers[dataset_path] = ThisClass.packChill
                        self._unpackers[dataset_path] = ThisClass.unpackChill

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # static methods for data packing and unpacking (serialization)
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    @staticmethod
    def packChill(data):
        nans = N.where(N.isnan(data))
        packed = (data * 10.).astype('<i2')
        if len(nans[0]) > 0: packed[nans] = -32768
        return packed

    @staticmethod
    def packGdd(data):
        nan_indexes = N.where(N.isnan(data))
        packed = data.astype('<i2')
        if len(nan_indexes[0]) > 0: packed[nan_indexes] = -32768
        return packed

    @staticmethod
    def unpackChill(raw_data):
        nans = N.where(raw_data == -32768)
        unpacked = raw_data.astype(float)
        if len(nans[0]) > 0: unpacked[nans] = N.nan
        return unpacked / 10.

    @staticmethod
    def unpackGdd(raw_data):
        nan_indexes = N.where(raw_data < -32767)
        unpacked = raw_data.astype(float)
        if len(nan_indexes[0]) > 0: unpacked[nan_indexes] = N.nan
        return unpacked


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleChillGridReader(AppleGridFileReader, ChillGridAccessMixin,
                           AppleChillModelMixin):

    def __init__(self, target_year, test_file=False, **kwargs):
        filepath = kwargs.get('filepath', chillFilepath(target_year, test_file))
        AppleGridFileReader.__init__(self, target_year, filepath)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        """ Creates instance attributes specific to the content of the file
        to be managed.
        """
        # get superclass manager attributes
        AppleGridFileReader._loadManagerAttributes_(self)
        self._loadChillFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleChillGridManager(AppleGridFileManager, ChillGridAccessMixin,
                            AppleChillModelMixin):

    def __init__(self, target_year, mode='r', test_file=False, **kwargs):
        filepath = kwargs.get('filepath', chillFilepath(target_year, test_file))
        AppleGridFileManager.__init__(self, target_year, filepath, mode)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # chill model data update
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def updateChill(self, model_name, daily, accumulated, start_date, **kwargs):
        # update daily chill
        full_path = self.chillDatasetPath(model_name, 'accumulated')
        self.updateDataset(full_path, accumulated, start_date)
        # update accumulated chill
        full_path = self.chillDatasetPath(model_name, 'daily')
        self.updateDataset(full_path, daily, start_date)
        # update chill provenance
        group_path = self.modelGroupName(model_name)
        self.updateAccumulateProvenance(group_path, daily, accumulated,
                                        start_date, **kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Growing degree day update
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def updateGdd(self, lo_gdd_th, hi_gdd_th, data, start_date, **kwargs):
        # update daily GDD
        full_path = self.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'daily')
        self.updateDataset(full_path, data, start_date)
        # update chill provenance
        group_path = self.gddGroupName(lo_gdd_th, hi_gdd_th)
        self.updateProvenance(group_path, data, start_date, **kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        """ Creates instance attributes specific to the content of the file
        to be managed.
        """
        # get superclass manager attributes
        AppleGridFileManager._loadManagerAttributes_(self)
        self._loadChillFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleChillGridRepair(AppleChillGridManager, FrostGridBuilderMixin):

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _resolveChillDatasetAttributes_(self, model_name, dataset_name,
                                        **kwargs):
        model = chillModelDescription(model_name)
        attrs = { 'chill_model':model, 'missing':-32768, 'units':'CU*10' }
        attrs.update(self._resolveCommonAttributes(**kwargs))
        if dataset_name == 'daily':
            attrs['description'] = 'Daily chill units'
        elif dataset_name == 'accumulated':
            attrs['description'] = 'Accumulated Chill Units'
        return attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def _resolveGddDatasetAttributes_(self, lo_gdd_th, hi_gdd_th, **kwargs):
        attrs = self._resolveCommonAttributes(**kwargs)
        attrs['low_threshold'] = lo_gdd_th
        attrs['high_threshold'] = hi_gdd_th
        attrs['missing'] = -32768
        attrs['units'] = 'GDD'
        return attrs


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleChillGridBuilder(AppleChillGridRepair):

    def __init__(self, start_date, end_date, lons, lats, models,
                       gdd_thresholds, test_file=False, verbose=False,
                       **kwargs):
        """ Create a new, fully configured Apple Chill file
        """
        target_year = self._builder_preinit(start_date, end_date)
        AppleChillGridRepair.__init__(self, target_year, 'w', test_file,
                                             **kwargs)
        self._builder_postinit(lons, lats, **kwargs)

        # initialize the model grids
        for model_name in models:
            self._initChillDatasets(model_name, **kwargs)
            self.close()
        # initialize the GDD group
        self._initGddGroup()
        # initialize GDD threshold groups and datasets
        for lo_gdd_th, hi_gdd_th in gdd_thresholds:
            self._initGddDatasets(lo_gdd_th, hi_gdd_th)

        self.open('a')

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # dataset initiailzation methods                                        #
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initChillDatasets(self, model_name, **kwargs):
        # make sure that the model group exists
        if not self.chillModelExists(model_name):
            self._initModelGroup(model_name)

        # variables used for dataset construction
        chunks = (1,) + self.lons.shape
        model = self.properName(model_name)
        num_days = (self.end_date - self.start_date).days + 1
        shape = (num_days,) + self.lons.shape

        # common dataset attributes
        date_attrs = self._resolveDateAttributes(**kwargs)
        dataset_attrs = \
        self._resolveChillDatasetAttributes_(model_name, 'daily', **kwargs)
        dataset_attrs.update(date_attrs)

        # make sure there is a daily chill dataset
        dataset_name = self.chillDatasetPath(model_name, 'daily')
        if not self.datasetExists(dataset_name):
            self.open('a')
            self.createEmptyDataset(dataset_name, shape, '<i2',
                                    dataset_attrs['missing'],
                                    chunks=chunks, compression='gzip')
            self.setDatasetAttributes(dataset_name, **dataset_attrs)
            self.close() # saves the initialized dataset to the file

        # make sure there is an accumulated chill dataset
        dataset_name = self.chillDatasetPath(model_name, 'accumulated')
        if not self.datasetExists(dataset_name):
            dataset_attrs['description'] = 'Accumulated Chill Units'
            self.open('a')
            self.createEmptyDataset(dataset_name, shape, '<i2',
                                    dataset_attrs['missing'],
                                    chunks=chunks, compression='gzip')
            self.setDatasetAttributes(dataset_name, **dataset_attrs)
            self.close() # saves the initialized dataset to the file

        # make sure there is an accumulated chill dataset
        dataset_name = self.chillDatasetPath(model_name, 'provenance')
        if not self.datasetExists(dataset_name):
            description = 'Chill Processing Provencance'
            self.open('a')
            self._createEmptyProvenance(dataset_name, 'accum', description)
            self.setDatasetAttributes(dataset_name, **date_attrs)
            self.setDatasetAttribute(dataset_name, 'chill_model', 
                                     dataset_attrs['chill_model'])
            self.close()

    def _initModelGroup(self, model_name):
        group_name = self.modelGroupName(model_name)
        self.open('a')
        self.createGroup(group_name,
                         description=chillModelDescription(model_name))
        self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initGddDatasets(self, lo_gdd_th, hi_gdd_th, **kwargs):
        # make sure that the gdd group exists
        if not self.groupExists('gdd'): self._initGddGroup()

        thresholds = '%d =< AVGT <= %d' % (lo_gdd_th, hi_gdd_th)
        date_attrs = self._resolveDateAttributes(**kwargs)

        # add a group for the low/high combination
        group_name = self.gddGroupName(lo_gdd_th, hi_gdd_th)
        if not self.groupExists(group_name):
            date_attrs['description'] = 'GDD datasets for %s' % thresholds
            self.open('a')
            self.createGroup(group_name, **date_attrs)
            self.close()

        # add a gdd dataset for this low/high combination
        dataset_name = '%s.daily' % group_name
        if not self.datasetExists(dataset_name):
            dataset_attrs = \
            self._resolveGddDatasetAttributes_(lo_gdd_th, hi_gdd_th, **kwargs)
            dataset_attrs.update(date_attrs)
            dataset_attrs['description'] = 'Daily GDD for %s' % thresholds

            chunks = (1,) + self.lons.shape
            num_days = (self.end_date - self.start_date).days + 1
            shape = (num_days,) + self.lons.shape
            self.open('a')

            self.createEmptyDataset(dataset_name, shape, '<i2',
                                    dataset_attrs['missing'],
                                    chunks=chunks, compression='gzip')
            self.setDatasetAttributes(dataset_name, **dataset_attrs)
            self.close()

            # also add provenance dataset
            dataset_name = '%s.provenance' % group_name
            description = 'Daily GDD Processing Provencance'
            self.open('a')
            self._createEmptyProvenance(dataset_name, 'stats', description)
            self._setDateAttributes(dataset_name, **date_attrs)
            self.close()

        # cannot recreate an existing dataset
        else: raise KeyError, '%s dataset already exists' % dataset_name

    def _initGddGroup(self, **kwargs):
        self.open('a')
        self.createGroup('gdd', description='Growing Degree Days')
        self.close()

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # overide parent class methods                                          #
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _emptyProvenanceRecords_(self, start_date, num_days,
                                       empty_prov_record):
        record_tail = empty_prov_record[1:]
        records = [ ]
        for day in range(num_days):
            date = start_date + relativedelta(days=day)
            record = (asAcisQueryDate(date),) + record_tail
            records.append(record)
        return records

