
import numpy as N

from frost.manager import FrostDataFileManager

from atmosci.utils.timeutils import asAcisQueryDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PROVENANCE_EMPTY_RECORD = ('', '',)
PROVENANCE_RECORD_TYPE = [ ('obs_date', '|S10'), ('processed', '|S20'), ]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostGDDFileManager(FrostDataFileManager):

    def __init__(self, filepath,  mode='r'):
        packers = { 'daily' : FrostGDDFileManager._packGDD, }
        serializers = { 'daily' : FrostGDDFileManager._serializeGDD, }

        FrostDataFileManager.__init__(self,serializers,packers,filepath,mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dailyDatasetName(self, low_threshold, high_threshold, key='data'):
        group_name = self.dailyGroupName(low_threshold, high_threshold)
        return '%s.%s' % (group_name, key)

    def dailyGroupName(self, low_threshold, high_threshold):
        return 'daily.L%dH%d' % (low_threshold, high_threshold)

    def getDailyData(self, low_threshold, high_threshold, **kwargs):
        full_name = self.dailyDatasetName(low_threshold, high_threshold)
        if 'date' in kwargs:
            return self.getDataForDate(full_name, kwargs['date'])
        elif 'start_date' in kwargs:
            if 'end_date' in kwargs:
                return self.getDataForDates(full_name, kwargs['start_date'],
                                             kwargs['end_date'])
            else: return self.getDataSince(full_name, kwargs['start_date'])
        elif 'end_date' in kwargs:
            return self.getDataThru(full_name, kwargs['end_date'])
        else: return self.getData(full_name, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insertDailyData(self, low_threshold, high_threshold, data, start_date,
                              end_date=None):
        full_name = self.dailyDatasetName(low_threshold, high_threshold)
        if end_date is not None:
            self.insertDataForDates(full_name, start_date, end_date,
                                    N.array(data, dtype='<i2'))
        else:
            self.insertDataForDate(full_name, start_date,
                                    N.array(data, dtype='<i2'))

    def insertDailyProvenance(self, low_threshold, high_threshold, provenance,
                                    start_date, end_date):
        full_name = self.dailyDatasetName(low_threshold, high_threshold,
                                          'provenance')
        num_records = len(provenance)
        data = N.rec.fromrecords([provenance,], PROVENANCE_RECORD_TYPE,
                                 (num_records,))
        if end_date is not None:
            self.insertDataForDates(full_name, start_date, end_date, data)
        else: self.insertDataForDate(full_name, start_date, data)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _packGDD(self, data):
        nan_indexes = N.where(N.isnan(data))
        packed = data.astype('<i2')
        if len(nan_indexes[0]) > 0: packed[nan_indexes] = -32768
        return packed

    def _serializeGDD(self, raw_data):
        nan_indexes = N.where(raw_data < -32767)
        data = raw_data.astype(float)
        if len(nan_indexes[0]) > 0: data[nan_indexes] = N.nan
        return data

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initDailyDataset(self, low_threshold, high_threshold):
        self.assertFileWritable()

        # make sure that the daily group exists
        if 'daily' not in self.allGroupNames(): self._initDailyGroup()

        thresholds = '%d =< AVGT <= %d' % (low_threshold, high_threshold)
        attributes = { 'low threshold' : low_threshold,
                       'high threshold' : high_threshold }

        # add a group for the low/high combination
        group_name = self.dailyGroupName(low_threshold, high_threshold)
        if group_name not in self.allGroupNames():
            self.createGroup(group_name, **attributes)
            self.close()
            self.open('a')

        # add daily gdd dataset for this low/high combination
        dataset_name = '%s.data' % group_name
        if dataset_name not in self.allDatasetNames():
            attributes['description'] = 'Daily GDD for %s' % thresholds
            attributes['start_date'] = asAcisQueryDate(self.start_date)
            attributes['end_date'] = asAcisQueryDate(self.end_date)

            chunks = (1,) + self.lons.shape
            num_days = (self.end_date - self.start_date).days + 1
            shape = (num_days,) + self.lons.shape
            self.createEmptyDataset(dataset_name, shape, '<i2', -32768,
                                    chunks=chunks, compression='gzip')
            self.setDatasetAttributes(dataset_name, **attributes)
            self.setDatasetAttribute(dataset_name, 'units', 'GDD')

            # also add provenance dataset
            dataset_name = '%s.provenance' % group_name
            records = [PROVENANCE_EMPTY_RECORD for day in range(num_days)]
            empty = N.rec.fromrecords(records, PROVENANCE_RECORD_TYPE,
                                      (num_days,))
            attributes['description'] = 'Daily GDD Processing Provencance'
            self.createDataset(dataset_name, empty)
            self.setDatasetAttributes(dataset_name, **attributes)
            self.close()
            self.open('a')

        # cannot recreate an existing dataset
        else: raise KeyError, '%s dataset already exists' % dataset_name

    def _initDailyGroup(self):
        self.assertFileWritable()
        self.createGroup('daily', description='Daily Growing Degree Days')
        self.close()
        self.open('a')

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    @staticmethod
    def newManager(filepath, start_date, end_date, lons, lats, bbox, grid):
        """ create a new, fully configured HDF5 file for Frost Model data.
        """
        target_year = end_date.year

        # capture longitude/latitude limits of grids
        min_lon = N.nanmin(lons)
        max_lon = N.nanmax(lons)
        min_lat = N.nanmin(lats)
        max_lat = N.nanmax(lats)

        manager = FrostGDDFileManager(filepath,'w')
        manager.setFileAttributes(created=manager.timestamp, search_bbox=bbox,
                                  target_year=target_year, acis_grid=grid,
                                  start_date=asAcisQueryDate(start_date),
                                  end_date=asAcisQueryDate(end_date),
                                  node_spacing='5 km',
                                  min_lon=min_lon, max_lon=max_lon,
                                  min_lat=min_lat, max_lat=max_lat)
        manager.close()

        # cache the lon/lat grids
        manager.open('a')
        manager.createDataset('lon', lons)
        manager.setDatasetAttributes('lon', min=min_lon, max=max_lon)
        manager.createDataset('lat', lats)
        manager.setDatasetAttributes('lat', min=min_lat, max=max_lat)
        manager.close()

        manager.open('a')
        manager._initDailyGroup()
        return manager

