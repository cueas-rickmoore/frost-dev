
from dateutil.relativedelta import relativedelta

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.manager import FrostDataFileManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from frost.config import config as CONFIG

PROVENANCE_EMPTY_RECORD = ('', '',)
PROVENANCE_RECORD_TYPE = [ ('obs_date', '|S10'), ('processed', '|S20'), ]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostChillFileManager(FrostDataFileManager):


    def __init__(self, filepath,  mode='r'):
        packers = { 'accumulated' : FrostChillFileManager.packChillUnits,
                    'daily' : FrostChillFileManager.packChillUnits,
                    'maxt' : FrostChillFileManager.packTemps,
                    'mint' : FrostChillFileManager.packTemps }

        serializers = { 
                    'accumulated' : FrostChillFileManager.serializeChillUnits,
                    'daily' : FrostChillFileManager.serializeChillUnits,
                    'maxt' : FrostChillFileManager.serializeTemps,
                    'mint' : FrostChillFileManager.serializeTemps }

        FrostDataFileManager.__init__(self,serializers,packers,filepath,mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def chillThresholdDate(self, model_name, chill_threshold):
        days = self.chillThresholdIndex(model_name, chill_threshold)
        if days is None: return None
        else: return self.start_date + relativedelta(days=days)

    def chillThresholdIndex(self, model_name, chill_threshold):
        dataset_name = self.getModelDatasetName(model_name, 'accumulated')
        indexes = N.where(self.getData(dataset_name) >= chill_threshold)
        if len(indexes[0] > 0): return indexes[0].min()
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getModelData(self, model_name, dataset_name, **kwargs):
        full_name = self.modelDatasetName(model_name, dataset_name)
        if 'date' in kwargs:
            return self.getDataForDate(full_name, kwargs['date'])
        elif 'start_date' in kwargs:
            if 'end_date' in kwargs:
                return self.getDataForDates(full_name, kwargs['start_date'],
                                             kwargs['end_date'])
            else:
                return self.getDataSince(full_name, kwargs['start_date'])
        elif 'end_date' in kwargs:
            return self.getDataThru(full_name, kwargs['end_date'])
        else:
            return self.getData(full_name, **kwargs)

    def modelDatasetName(self, model_name, dataset_name):
        group_name = self.modelName(model_name)
        return '%s.%s' % (group_name, dataset_name)

    def modelDatasetShape(self, model_name, dataset_name):
        full_name = self.modelDatasetName(model_name, dataset_name)
        return self.getDatasetShape(full_name)

    def modelGroupName(self, model_name):
        return '%s' % model_name.title()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insertModelData(self, model_name, dataset_name, data, start_date,
                              end_date=None):
        full_name = self.getModelDatasetName(model_name, dataset_name)
        if end_date is not None:
            self.insertDataForDates(full_name, start_date, end_date, data)
        else: self.insertDataForDate(full_name, start_date, data)

    def insertModelProvenance(self, model_name, provenance, start_date,
                                    end_date=None):
        full_name = self.getModelDatasetName(model_name, 'provenance')
        num_records = len(provenance)
        data = N.rec.fromrecords([provenance,], PROVENANCE_RECORD_TYPE,
                                    (num_records,))
        if end_date is not None:
            self.insertDataForDates(full_name, start_date, end_date, data)
        else: self.insertDataForDate(full_name, start_date, data)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _chillModels(self):
        return tuple([name for name in self.allGroupNames()
                      if name.lower() in CONFIG.chill.models])
    chillModels = property(_chillModels)

    def _getPacker(self, dataset_name):
        if dataset_name in self._packers:
            return self._packers[dataset_name]
        else:
            path = dataset_name.split('.')
            return self._packers.get(path[-1], None)

    def _getSerializer(self, dataset_name):
        if dataset_name in self._serializers:
            return self._serializers[dataset_name]
        else:
            path = dataset_name.split('.')
            return self._serializers.get(path[-1], None)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initChillModelDatasets(self, model_name):
        self.assertFileWritable()

        model = model_name.title()
        chunks = (1,) + self.lons.shape
        num_days = (self.end_date - self.start_date).days + 1
        shape = (num_days,) + self.lons.shape

        model_group = self.modelGroupName(model_name)
        if model_group not in self.allGroupNames():
            self.open('a')
            description = 'Chill Unit Grids for %s Model' % model
            self.createGroup(model_group, description=description)
            self.open('r')

        attributes = { 'start_date'  : asAcisQueryDate(self.start_date),
                       'end_date'    : asAcisQueryDate(self.end_date),
                       'units'       : 'CU*10'
                     }
        
        dataset_name = self.modelDatasetName(model_name, 'daily')
        if dataset_name not in self.allDatasetNames():
            self.open('a')
            description = 'Daily Chill Units for %s Model' % model
            attributes['description'] = description
            self.createEmptyDataset(dataset_name, shape, '<i2', -32768,
                                    chunks=chunks, compression='gzip')
            self.setDatasetAttributes(dataset_name, **attributes)
            self.open('r')

        dataset_name = self.modelDatasetName(model_name, 'accumulated')
        if dataset_name not in self.allDatasetNames():
            self.open('a')
            self.createEmptyDataset(dataset_name, shape, '<i2', -32768,
                                    chunks=chunks, compression='gzip')
            description = 'Accumulated Chill Units for %s Model' % model
            attributes['description'] = description
            self.setDatasetAttributes(dataset_name, **attributes)
            self.open('r')

        self.open('a')
        del attributes['units']
        dataset_name = self.modelDatasetName(model_name, 'provenance')
        records = [PROVENANCE_EMPTY_RECORD for day in range(shape[0])]
        empty = N.rec.fromrecords(records, PROVENANCE_RECORD_TYPE, (shape[0],))
        self.createDataset(dataset_name, empty)
        attributes['description'] = '%s Chill Processing Provencance' % model
        self.setDatasetAttributes(dataset_name, **attributes)
        self.open('r')

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    @staticmethod
    def packChillUnits(data):
        nans = N.where(N.isnan(data))
        packed = (data * 10.).astype('<i2')
        if len(nans[0]) > 0: packed[nans] = -32768
        return packed

    @staticmethod
    def packTemps(data):
        nans = N.where(N.isnan(data))
        packed = data.astype('<i2')
        if len(nans[0]) > 0: packed[nans] = -32768
        return packed

    @staticmethod
    def serializeChillUnits(raw_data):
        nans = N.where(raw_data < -32767)
        serialized = raw_data.astype(float) / 10.
        if len(nans[0]) > 0: serialized[nans] = N.nan
        return serialized

    @staticmethod
    def serializeTemps(raw_data):
        nans = N.where(raw_data < -32767)
        serialized = raw_data.astype(float)
        if len(nans[0]) > 0: serialized[nans] = N.nan
        return serialized

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    @staticmethod
    def newManager(filepath, start_date, end_date, lons, lats, bbox, grid,
                   models=None):
        """ create a new, fully configured HDF5 file for Frost Model data.
        """
        end_str = asAcisQueryDate(end_date)
        num_days = (end_date - start_date).days + 1
        start_str = asAcisQueryDate(start_date)
        target_year = end_date.year

        # capture longitude/latitude limits of grids
        min_lon = N.nanmin(lons)
        max_lon = N.nanmax(lons)
        min_lat = N.nanmin(lats)
        max_lat = N.nanmax(lats)

        manager = FrostChillFileManager(filepath,'w')
        manager.setFileAttributes(created=manager.timestamp, search_bbox=bbox,
                                  target_year=target_year, acis_grid=grid,
                                  start_date=start_str, end_date=end_str,
                                  node_spacing='5 km',
                                  min_lon=min_lon, max_lon=max_lon,
                                  min_lat=min_lat, max_lat=max_lat)
        manager.close()

        # cache the lon/lat grids
        manager.open('a')
        manager.createDataset('lon', lons, dtype=float)
        manager.setDatasetAttributes('lon', min=min_lon, max=max_lon,
                                     node_spacing='5 km',
                                     description='Degrees West Longitude')
        manager.createDataset('lat', lats, dtype=float)
        manager.setDatasetAttributes('lat', min=min_lat, max=max_lat,
                                     node_spacing='5 km',
                                     description='Degrees North Latitude')
        manager.close()

        # create empty temperature grids
        chunks = (1,) + lons.shape
        shape = (num_days,) + lons.shape
        manager.open('a')
        manager.createEmptyDataset('maxt', shape, '<i2', -32768,
                                    chunks=chunks, compression='gzip')
        manager.setDatasetAttributes('maxt', units='F', node_spacing='5 km',
                                     start_date=start_str, end_date=end_str,
                                     description='Maximum Temperature')
        manager.createEmptyDataset('mint', shape, '<i2', -32768,
                                    chunks=chunks, compression='gzip')
        manager.setDatasetAttributes('mint', units='F',  node_spacing='5 km',
                                     start_date=start_str, end_date=end_str,
                                     description='Minimum Temperature')
        manager.close()

        # initialize the model grids
        if models is None: models = CONFIG.chill.models
        for model_name in models:
            manager.open('a')
            manager._initChillModelDatasets(model_name)
            manager.close()

        manager.open('a')
        return manager

