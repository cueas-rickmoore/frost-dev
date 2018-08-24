
import numpy as N

from atmosci.hdf5.manager import Hdf5TimeSeriesFileManager
from atmosci.utils.timeutils import asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostDataFileManager(Hdf5TimeSeriesFileManager):

    def __init__(self, serializers, packers, filepath,  mode='r'):
        Hdf5TimeSeriesFileManager.__init__(self, filepath, mode, serializers,
                                           packers)

        # 0.125 is DEM 5k node spacing
        # search radius is sqrt(2*(0.125**2) + a litle fudge
        self._node_search_radius = 0.18 

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataForDate(self, dataset_name, date):
        indx = self.indexFromDate(date)
        return self.getData(dataset_name, index=indx)

    def getDataForDates(self, dataset_name, start_date, end_date):
        indexes = self.indexesFromDates(start_date, end_date)
        return self.getData(dataset_name, indexes=indexes)

    def getDataSince(self, dataset_name, date):
        indexes = self.indexesFromDates(date, self.end_date)
        return self.getData(dataset_name, indexes=indexes)

    def getDataThru(self, dataset_name, date):
        indexes = (0, self.indexFromDate(date)+1)
        return self.getData(dataset_name, indexes=indexes)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insertDataForDate(self, dataset_name, date, data):
        indx = self.indexFromDate(date)
        self._insertDataByIndex(dataset_name, data, indx)

    def insertDataForDates(self, dataset_name, start_date, end_date, data):
        indexes = self.indexesFromDates(start_date, end_date)
        self._insertDataByIndex(dataset_name, data, *indexes)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _clearManagerAttributes_(self):
        Hdf5TimeSeriesFileManager._clearManagerAttributes_(self)
        self.grid = None
        self.node_spacing = None
        self.search_bbox = None
        self.target_year = None

    def _getDataByIndex(self, dataset_name, start_index, end_index=None):
        dataset_key = self._dotPathToKey(dataset_name)
        dataset = self._hdf5_file[dataset_key]
        serialize = self._getSerializer(dataset_names)
        if serialize is not None:
            if end_index is None: return serialize(dataset.value[start_index])
            else: return serialize(dataset.value[start_index:end_index])
        else:
            if end_index is None: return dataset.value[start_index]
            else: return dataset.value[start_index:end_index]

    def _getPacker(self, dataset_name):
        return self._packers.get(dataset_name, None)

    def _getSerializer(self, dataset_name):
        return self._serializers.get(dataset_name, None)

    def _insertDataByIndex(self, dataset_name, data, start_index,
                                 end_index=None):
        dataset_key = self._dotPathToKey(dataset_name)
        dataset = self._hdf5_file[dataset_key]
        pack = self._getPacker(dataset_name)
        if pack is not None:
            if end_index is None: dataset[start_index] = pack(data)
            else: dataset[start_index:end_index] = pack(data)
        else:
            if end_index is None: dataset[start_index] = data
            else: dataset[start_index:end_index] = data

    def _loadManagerAttributes_(self):
        Hdf5TimeSeriesFileManager._loadManagerAttributes_(self)
        if self.start_date is not None:
            self.start_date = asDatetime(self.start_date)
        if self.end_date is not None:
            self.end_date = asDatetime(self.end_date)
        attrs = self.getFileAttributes()
        grid = attrs.get('acis_grid', None)
        if grid is not None: self.acis_grid = int(grid)
        else: self.acis_grid = None
        self.node_spacing = attrs.get('node_spacing', None)
        self.search_bbox = attrs.get('search_bbox', None)
        self.target_year = attrs.get('target_year', None)

