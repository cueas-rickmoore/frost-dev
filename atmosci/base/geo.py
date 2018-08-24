""" Mixin classes that define the minimum API for data file managers that
support subsetting by geographic coordinates.
"""

import numpy as N


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GeoDataFileMixin:
    """ Mixin class that defines the minimum API for data file managers that
    support subsetting by geographic coordinates.
    """

    PROJECTION = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getCoordinateLimits(self):
        limits = { }
        limits['min_avail_lon'] = self._min_avail_lon
        limits['max_avail_lon'] = self._max_avail_lon
        limits['min_avail_lat'] = self._min_avail_lat
        limits['max_avail_lat'] = self._max_avail_lat

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

    def setLonLatBounds(self, bbox=None):
        msg = 'setLonLatBounds method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataSubset(self, dataset_key, dataset):
        if self.indexes is not None:
            return dataset[self.indexes]
        else:
            return dataset

    def _initCoordinateLimits(self):
        """ Sets the absolute limts for lon/lat and index coordinates for
        grids present in the file.
        """
        # initialize index bounds
        self.bounds = None

        try:
            lons, attrs = self.getRawData('lon')
            lats, attrs = self.getRawData('lat')
        except:
            raise
            raise RuntimeError, 'No latitiude or longitude data vailable.'

        self._min_avail_lat = N.nanmin(lats)
        self._max_avail_lat = N.nanmax(lats)
        self._min_avail_lon = N.nanmin(lons)
        self._max_avail_lon = N.nanmax(lons)

        return lons, lats

    def _projectLonLat_(self):
        msg = '_projectLonLat_ method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__

