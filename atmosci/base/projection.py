""" Abstract base class for coordinate projections.
"""

from pyproj import Proj

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BaseProjection(object):

    def index2ll(self, x_index, y_index):
        """ Convert index of a grid point to lon,lat coordinates
        """
        msg = 'index2ll method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__
        # return lon, lat

    def ll2index(self, lon, lat):
        """ Convert lon, lat coordinates to the x and y indexes of the
        nearest grid point.
        """
        msg = 'll2index method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__
        #return x_index, y_index

    def ll2xy(self, lon, lat):
        """ Convert lon, lat coordinates to x,y coordinates.
        """
        msg = 'll2xy method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__
        #return x_coord, y_coord

    def xy2ll(self, x_coord, y_coord):
        """ Convert x,y coordinates to lon,lat coordinates
        """
        msg = 'xy2ll method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__
        # return lon, lat

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def testIndex2LL(self, lons, lats, first_node=(0,0), frequency=(10,10),
                           precision=2):
        if isinstance(first_node, (tuple,list)):
            x_start = first_node[0]
            y_start = first_node[1]
        else:
            x_start = y_start = first_node

        if isinstance(frequency, (tuple,list)):
            x_frequency = frequency[0]
            y_frequency = frequency[1]
        else:
            x_frequency = y_frequency = frequency

        decimals = precision + 1

        print '\n\nTESTING index2ll\n'
        lon_errors = 0
        lat_errors = 0
        count = 0
        for yi in range(y_start, lons.shape[0], y_frequency):
            for xi in range(x_start, lons.shape[1], x_frequency):
                count+=1
                lon, lat = self.index2ll(xi,yi)
                if str(lon)[:decimals] != str(lons[yi,xi])[:decimals]:
                    print 'lon at [%d,%d]' % (yi,xi), lon, ' != ', lons[yi,xi]
                    lon_errors += 1
                if str(lat)[:decimals] != str(lats[yi,xi])[:decimals]:
                    print 'lat at [%d,%d]' % (yi,xi), lat, ' != ', lats[yi,xi]
                    lat_errors += 1
         
        print '\n%d of %d nodes encountered longitude errors' % (lon_errors,count)
        print '%d of %d nodes emcountered latitude errors' % (lat_errors,count)

    def testLL2Index(self, lons, lats, first_node=(0,0), frequency=(10,10)):
        if isinstance(first_node, (tuple,list)):
            x_start = first_node[0]
            y_start = first_node[1]
        else:
            x_start = y_start = first_node

        if isinstance(frequency, (tuple,list)):
            x_frequency = frequency[0]
            y_frequency = frequency[1]
        else:
            x_frequency = y_frequency = frequency

        print '\n\nTESTING ll2index\n'
        x_errors = 0
        y_errors = 0
        count = 0
        for yi in range(x_start, lons.shape[0], y_frequency):
            for xi in range(y_start, lons.shape[1], x_frequency):
                count+=1
                lon, lat = lons[yi,xi], lats[yi,xi]
                x,y = self.ll2index(lon, lat)
                if x != xi:
                    x_errors += 1
                    print 'x %d != %d at [%6.2f , %6.2f]' % (xi,x,lon,lat)
                if y != yi:
                    y_errors += 1
                    print 'y %d != %d at [%6.2f , %6.2f]' % (yi,y,lon,lat)
        print '\n%d of %d nodes encountered x index errors' % (x_errors,count)
        print '%d of %d nodes emcountered y index errors' % (y_errors,count)


    def testXYCoords(self, lons, lats, first_node=(0,0), frequency=(10,10),
                           precision=5):
        if isinstance(first_node, (tuple,list)):
            x_start = first_node[0]
            y_start = first_node[1]
        else:
            x_start = y_start = first_node

        if isinstance(frequency, (tuple,list)):
            x_frequency = frequency[0]
            y_frequency = frequency[1]
        else:
            x_frequency = y_frequency = frequency

        decimals = precision + 1

        print '\n\nTESTING ll2xy => xy2ll\n'
        lon_errors = 0
        lat_errors = 0
        count = 0
        for xi in range(x_start, lons.shape[0], x_frequency):
            for yi in range(y_start, lons.shape[1], y_frequency):
                count += 1
                x,y = self.ll2xy(lons[xi,yi], lats[xi,yi])
                lon, lat = self.xy2ll(x,y)
                if str(lon)[:decimals] != str(lons[xi,yi])[:decimals]:
                    lon_errors += 1
                    print 'lon at [%d,%d]' % (xi,yi), lon, ' != ', lons[xi,yi]
                if str(lat)[:decimals] != str(lats[xi,yi])[:decimals]:
                    lat_errors += 1
                    print 'lat at [%d,%d]' % (xi,yi), lat, ' != ', lats[xi,yi]

        print '\n%d of %d nodes encountered longitude errors' % (lon_errors,count)
        print '%d of %d nodes emcountered latitude errors' % (lat_errors,count)
        

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Proj4Projection(BaseProjection):

    X_SCALE_FACTOR = 1.
    X_OFFSET = 0.

    Y_SCALE_FACTOR = 1.
    Y_OFFSET = 0.

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self, proj4_params):
        if type(proj4_params) in (str,unicode):
            self.transform = Proj(proj4_params)
        elif type(proj4_params) == dict:
            self.transform = Proj(self._proj4String_(proj4_params))
        else:
            raise TypeError, 'Invalid type for projection parameters.'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def index2ll(self, xi, yi):
        """ Convert index of a grid point to lon,lat coordinates
        """
        xm = (xi + self.X_OFFSET) * self.X_SCALE_FACTOR
        ym = (yi + self.Y_OFFSET) * self.Y_SCALE_FACTOR
        return self.transform(xm,ym,inverse=True)

    def ll2findex(self, lon, lat):
        """ Convert lon, lat coordinates to the floating point index into the
        grid ... this is very useful for certain types of interpolations.
        """
        xm,ym = self.transform(lon,lat)
        xf = (xm / self.X_SCALE_FACTOR) - self.X_OFFSET
        yf = (ym / self.Y_SCALE_FACTOR) - self.Y_OFFSET
        return xf, yf

    def ll2index(self, lon, lat):
        """ Convert lon, lat coordinates to the index of the nearest grid point.
        """
        xm,ym = self.transform(lon,lat)
        xi = int( round(xm / self.X_SCALE_FACTOR ) - self.X_OFFSET)
        yi = int( round(ym / self.Y_SCALE_FACTOR ) - self.Y_OFFSET)
        return xi, yi

    def ll2xy(self, lon, lat):
        """ Convert lon, lat coordinates to x,y coordinates.
        """
        return self.transform(lon,lat)

    def xy2ll(self, x, y):
        """ Convert x,y coordinates to lon,lat coordinates
        """
        return self.transform(x,y,inverse=True)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _proj4String_(proj4_param_dict):
        proj4_string = '+proj=' + proj4_param_dict['proj']
        for key, value in proj4_param_dict.items():
            if key != 'proj':
                proj4_string += ' +%s=%s' % (key, str(value))
        return proj4_string

