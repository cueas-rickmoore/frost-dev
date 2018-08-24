""" Abstract base class that define the minimum API for derived classes.
        if self._xform_count == 0 or if self._xform_count/1000 == 0:
"""

import math
from copy import deepcopy

import numpy as N

from atmosci.base.manager import DataFileManager
from .geo import GeoDataFileMixin
from .datasets import DatasetKey
from .search import gridSearch, radialSearch, relativeSearch
from .subset import getXYDataSubset, getYXDataSubset

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GridFileManager(DataFileManager):
    """ Abstract base class to define API for grid file managers.
    """

    def __init__(self, managed_filepath, keep_open=False, allow_updates=False):
        DataFileManager.__init__(self,managed_filepath,keep_open,allow_updates)
        self._area_mask = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def applyAreaMask(self, dataset_key, data):
        if self._area_mask is not None:
            return N.ma.array(data, mask=self._area_mask, keep_mask=True)
        return data

    def maskInvalidData(self, dataset_key, data_array, data_attrs):
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_array self.applyAreaMask(decoded_key, data_array)
        return DataFileManager.maskInvalidData(self, dataset_key, data_array,
                                                     data_attrs)

    def setAreaMask(self, mask_name='mask'):
        """ Returns the area mask as an array.
        """
        mask_array, attrs = self.getRawData(mask_name)
        self._area_mask = mask_array

    def _validData(self, dataset_key, data_array, data_attrs):
        decoded_key = self._decodeDatasetKey(dataset_key)
        valid = self.applyAreaMask(decoded_key, data_array)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getIndexBounds(self):
        """ Returns a tuple containg the minimum and maximum x and y indexes
        """
        if self.min_x is not None:
            min_x = max(self.min_x, self._min_avail_x)
            max_x = min(self.max_x+1, self._max_avail_x)
            min_y = max(self.min_y, self._min_avail_y)
            max_y = min(self.max_y+1, self._max_avail_y)
            return (min_x, max_x, min_y, max_y)
        else:
            return (self._min_avail_x, self._max_avail_x,
                    self._min_avail_y, self._max_avail_y)

    def setIndexBounds(self, point_or_bbox=None):
        if point_or_bbox is not None:
            if len(point_or_bbox) == 2:
                self.x = point_or_bbox[0]
                self.y = point_or_bbox[1]
            elif len(point_or_bbox) == 4:
                self.min_x = point_or_bbox[0]
                self.min_y = point_or_bbox[1]
                self.max_x = point_or_bbox[2]
                self.max_y = point_or_bbox[3]
            else:
                errmsg = "Invalid value for 'point_or_bbox'. It must contain "
                errmsg += "either a point (x,y) or a bounding box "
                errmsg += "(min_x,min_y,max_x,max_y)."
                raise ValueError, errmsg

        else:
            self.min_x = None
            self.min_y = None
            self.max_x = None
            self.max_y = None
            self.x = None
            self.y = None

        self.bounds = None

    def _setCoordinateLimits(self):
        """ Capture coordinate limits of grids in data file.
        """
        #self._min_avail_x = 0
        #self._min_avail_y = 0
        #self._max_avail_x = x element from shape of a representative grid 
        #self._max_avail_y = y element from shape of a representative grid
        msg = '_setCoordinateLimits method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataSubset_(self, dataset_key, dataset):
        return getXYDataSubset(self, dataset)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GeoGridFileManager(GridFileManager):
    """ Abstract base class to define API for geographic grid file managers.
    """
    REGULAR_GRID = True
    COORDINATE_ORDER = 'xy'
    BBOX_ATTR_NAME = 'bbox'

    DATA_TYPES = deepcopy(GridFileManager.DATA_TYPES)
    DATA_TYPES['lon'] = N.dtype(float)
    DATA_TYPES['lat'] = N.dtype(float)

    DATA_UNITS = deepcopy(GridFileManager.DATA_UNITS)
    DATA_UNITS['lon'] = 'DD'
    DATA_UNITS['lat'] = 'DD'

    DESCRIPTIONS = deepcopy(GridFileManager.DESCRIPTIONS)
    DESCRIPTIONS['lon'] = 'longitude'
    DESCRIPTIONS['lat'] = 'latitude'

    MASKED = deepcopy(GridFileManager.MASKED)
    MASKED['lon'] =  N.nan
    MASKED['lat'] =  N.nan
 
    PROJECTION = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self, managed_filepath, keep_open=False, allow_updates=False):
        GridFileManager.__init__(self, managed_filepath,  keep_open=keep_open,
                                       allow_updates=allow_updates)
        self._initCoordinateLimits()

    def _initCoordinateLimits(self):
        """ Sets the absolute limts for lon/lat and index coordinates for
        grids present in the file.
        """
        # capture lon,lat limits for grids in data file
        lons, lats = GeoDataFileMixin._initCoordinateLimits(self)

        # initialize index bounds
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None
        self.x = None
        self.y = None

        # determine base x,y indexes for projection
        self._base_x, self._base_y = self.PROJECTION.ll2index(lons[0,0],
                                                              lats[0,0])

        # capture index limits for grids in data file
        self._min_avail_x = 0
        self._min_avail_y = 0
        if self.COORDINATE_ORDER == 'xy':
            self._max_avail_x = lons.shape[0] 
            self._max_avail_y = lons.shape[1]
        else:
            self._max_avail_x = lons.shape[1] 
            self._max_avail_y = lons.shape[0]

        return lons, lats

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getCoordinateLimits(self):
        limits = { }
        limits['min_avail_lon'] = self._min_avail_lon
        limits['max_avail_lon'] = self._max_avail_lon
        limits['min_avail_lat'] = self._min_avail_lat
        limits['max_avail_lat'] = self._max_avail_lat
        limits['max_avail_x'] = self._max_avail_x
        limits['min_avail_x'] = self._min_avail_x
        limits['max_avail_y'] = self._max_avail_y
        limits['min_avail_y'] = self._min_avail_y
        return limits

    def getDataBounds(self):
        bounds = { }
        if self.bounds is None:
            bounds['llcrnrlon'] = self._min_avail_lon
            bounds['llcrnrlat'] = self._min_avail_lat
            bounds['urcrnrlon'] = self._max_avail_lon
            bounds['urcrnrlat'] = self._max_avail_lat
        else:
            bounds['llcrnrlon'] = self.bounds[0]
            bounds['llcrnrlat'] = self.bounds[1]
            bounds['urcrnrlon'] = self.bounds[2]
            bounds['urcrnrlat'] = self.bounds[3]
        return bounds

    def getIndexBounds(self):
        if self.min_x is not None:
            min_x = max(self.min_x, self._min_avail_x)
            max_x = min(self.max_x+1, self._max_avail_x)
            min_y = max(self.min_y, self._min_avail_y)
            max_y = min(self.max_y+1, self._max_avail_y)
            return (min_x, max_x, min_y, max_y)
        else:
            return (self._min_avail_x, self._max_avail_x,
                    self._min_avail_y, self._max_avail_y)

    def getLonLat(self):
        """ Returns lon, lat coordinate arrays.
        """
        self.openFile('r')
        try:
            lons,attrs = self.getRawData('lon')
            lats,attrs = self.getRawData('lat')
            self.conditionalClose()
        except IOError:
            self.conditionalClose()
            return self._projectLonLat_()
        except Exception:
            raise
        return N.array(lons,dtype=float), N.array(lats,dtype=float)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setLonLatBounds(self, point_or_bbox=None):
        self.bounds = point_or_bbox
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None
        self.x = None
        self.y = None
        if point_or_bbox is not None:
            if len(point_or_bbox) == 2:
                self.x, self.y = self.ll2index(*point_or_bbox)
            elif len(point_or_bbox) == 4:
                if self.REGULAR_GRID:
                    self._setBoundsForRegularGrid(point_or_bbox)
                else:
                    self._setBoundsForIrregularGrid(point_or_bbox)
            else:
                errmsg = "Invalid value for 'point_or_bbox'. It must contain "
                errmsg += "either a point (lon,lat) or a bounding box "
                errmsg += "(min_lon,min_lat,max_lon,max_lat)."
                raise ValueError, errmsg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def index2ll(self, x, y):
        """ Returns the lon/lat coordinates of the grid node at the x,y index
        point.
        """
        if self.PROJECTION is not None:
            return self.PROJECTION.index2ll(x+self._base_x ,y+self._base_y)
        errmsg = "Cannot execute transform, 'PROJECTION' attribute has no value."
        raise AttributeError, errmsg

    def ll2index(self, lon, lat):
        """ Returns the x,y indexes of the grid node that is closest to the
        lon/lat coordinate point.
        """
        if self.PROJECTION is not None:
            x,y = self.PROJECTION.ll2index(lon,lat)
            return x-self._base_x, y-self._base_y
        errmsg = "Cannot execute transform, 'PROJECTION' attribute has no value."
        raise AttributeError, errmsg

    def ll2findex(self, lon, lat):
        """ Returns the floating point x,y indexes into the grid.
        """
        if self.PROJECTION is not None:
            x,y = self.PROJECTION.ll2findex(lon,lat)
            return x-self._base_x, y-self._base_y
        errmsg = "Cannot execute transform, 'PROJECTION' attribute has no value."
        raise AttributeError, errmsg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataSubset(self, dataset_key, dataset):
        if self.COORDINATE_ORDER == 'xy':
            return getXYDataSubset(self, dataset)
        else:
            return getYXDataSubset(self, dataset)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _postCreateHook_(manager, file_attributes, datasets):
        """ Allows a class to handle special requirements when creating new
        files via the 'newFile' method.
        """
        if 'x_offset' not in file_attributes and\
           'y_offset' not in file_attributes:
            manager.setFileAttributes(x_offset=manager._base_x,
                                      y_offset=manager._base_y)
            
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _setBoundsForRegularGrid(self, point_or_bbox):
        x1, y1 = self.ll2index(*point_or_bbox[:2])
        x2, y2 = self.ll2index(*point_or_bbox[2:])
        self.min_x = x1
        self.max_x = x2
        self.min_y = y1
        self.max_y = y2

    def _setBoundsForIrregularGrid(self, point_or_bbox):
        lons, lats = self.getLonLat()
        indexes = N.where( (lons >= point_or_bbox[0]) &
                           (lons <= point_or_bbox[2]) &
                           (lats >= point_or_bbox[1]) &
                           (lats <= point_or_bbox[3]) )
        if self.COORDINATE_ORDER == 'xy':
            self.min_x = min(indexes[0])
            self.max_x = max(indexes[0])
            self.min_y = min(indexes[1])
            self.max_y = max(indexes[1])
        else:
            self.min_y = min(indexes[0])
            self.max_y = max(indexes[0])
            self.min_x = min(indexes[1])
            self.max_x = max(indexes[1])
