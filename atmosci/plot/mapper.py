
import datetime
import os
import string
from cStringIO import StringIO

import numpy as N

import matplotlib
#matplotlib.use('Agg')
from mpl_toolkits.basemap import Basemap
from matplotlib import pyplot

from .colormaps import isHexColor
from .colormaps import ColormapManager
from .htmlcolors import htmlColorName2Hex

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from nrcc.utils import BOGUS_VALUE

from .htmlcolors import HTML_COLOR_NAME_MAP
from .htmlcolors import HTML_COLOR_NAMES 
from .htmlcolors import HTML_COLOR_NAMES_LOWER

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

NOT_FOUND = 'value not set'

RSPHERE_ERROR_MSG = "Value for 'rsphere' must contain either the radius of "\
                    "the major axis or a Python tuple with the radii of the "\
                    "major and minor axes. Values must be numbers."

from mpl_toolkits.basemap import _projnames 
VALID_PROJECTIONS = _projnames.keys()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def hexColor(_string):
    hex_string = _string.strip()
    if hex_string[0] != '#':
        hex_string = '#' + hex_string
    for char in hex_string[1:]:
        if char not in string.hexdigits: return None
    return hex_string.upper()

def toHexColors(colors):
    hex_colors = [ ]
    invalid_colors = 0
    for color in colors:
        if color in HTML_COLOR_NAMES:
            hex_colors.append(HTML_COLOR_NAME_MAP[color.lower()])
        elif color in HTML_COLOR_NAMES_LOWER:
            hex_colors.append(HTML_COLOR_NAME_MAP[color])
        else:
            hex_colors.append(hexColor(color))
    return tuple(hex_colors)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GridMapper(object):

    DEFAULT_COLORMAP = 'jet'
    DEFAULT_FIGSIZE = (8,6)
    DEFAULT_MAP_HEIGHT = None
    DEFAULT_MAP_WIDTH = None
    DEFAULT_CBAR_OFFSET = 0.25

    DEFAULT_PROJECTION = 'lcc'
    DEFAULT_PROJPARAMS = { 'lat_1':33., 'lat_2':45., 'lon_0':-95. }
    DEFAULT_RESOLUTION = 'c'

    DEFAULT_X_INCR = 5000.
    DEFAULT_Y_INCR = 5000.

    MAX_VALID_LAT = 90.
    MIN_VALID_LAT = -90.

    MAX_VALID_LON = 180.
    MIN_VALID_LON = -180.

    def __init__(self, data_file_manager, cmap_mgr=None, debug=False,
                       perf=False, **kwargs):
        
        self.data_file_manager = data_file_manager

        if cmap_mgr is not None:
            self._cmap_mgr = cmap_mgr
        else:
            self._cmap_mgr = ColormapManager()
        self._debug = debug
        self._perf = perf

        self._basemap = None
        self._cmap = None
        self._cmap_bounds = None
        self._cmap_ticks = None
        self._cbar_offset = self.DEFAULT_CBAR_OFFSET
        self._outline_color = 'k'
        self._outline_size = 0.2

        self._fig_dpi = None
        self._fig_size = self.DEFAULT_FIGSIZE
        self._tight_box = False
        self._map_height = self.DEFAULT_MAP_HEIGHT
        self._map_width = self.DEFAULT_MAP_WIDTH
        self._show_frame = False
        
        self._area_thresh = None
        self._resolution = self.DEFAULT_RESOLUTION
        self._axis_ticks = False

        self._llcrnrlat = None
        self._llcrnrlon = None
        self._urcrnrlat = None
        self._urcrnrlon = None

        self._x_incr = self.DEFAULT_X_INCR
        self._y_incr = self.DEFAULT_Y_INCR

        self._projection = self.DEFAULT_PROJECTION
        self._proj_params = self.DEFAULT_PROJPARAMS

        self._title = None

        # by default, only draw the filled contours
        self._show_filled_contours = True
        self._show_coastlines = False
        self._show_countries = False
        self._show_states = False
        self._show_colorbar = False

        # extract configuration from keyword arguments
        self._errors = [ ]
        self._initPlot(kwargs)
        self._initBounds(kwargs)
        self._initProjection(kwargs)
        if self._errors: raise ValueError, self._errors

        # initialize the basemap
        self._initBasemap()

    def setTitle(self, title):
        self._title = title

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawMap(self, grid, **kwargs):
        if self._debug:
            print 'drawMap : grid shape =', grid.shape
            print 'drawMap : kwargs =', kwargs
        if not isinstance(grid, N.ndarray) or len(grid.shape) != 2:
            raise ValueError, "'grid' must be a 2-dimensional Numpy array"

        if kwargs:
            self.setup(kwargs)
            if self._errors: raise ValueError, self._errors

        map_args = self._getMapArgs()

        if self._debug: print 'drawMap : map_args =', map_args
        if self._perf: before = datetime.datetime.now()

        basemap = self._basemap
        grid = self.transformGrid(grid)

        fig_args = self._getFigArgs()
        figure = pyplot.figure(**fig_args)
        #figure.set_facecolor(0)
        #figure.set_frameon(False) # sets Transparent background
        #figure.subplots_adjust(left=.2, right=1.15, bottom=.2, top=1.2,
        #                       wspace=0.5, hspace=0.5)
        if not self._show_frame:
            pyplot.setp(pyplot.gca(), xticks=[], yticks=[], frame_on=False)

        if self._cmap_bounds is None:
            image = basemap.imshow(grid, cmap=self._cmap)
        else:
            bounds = self._cmap_bounds
            image = basemap.imshow(grid, cmap=self._cmap, norm=bounds,
                                   vmax=bounds.vmax, vmin=bounds.vmin)

        if self._perf:
            after = datetime.datetime.now()
            delta = after - before
            print  'image built in %d.%06d seconds' % (delta.seconds,
                                                       delta.microseconds)
            before = datetime.datetime.now()

        if self._show_coastlines:
            self.drawcoastlines(linewidth=self._outline_size,
                                color=self._outline_color)
        if self._show_countries:
            self.drawcountries(linewidth=self._outline_size,
                               color=self._outline_color)
        if self._show_states:
            self.drawstates(linewidth=self._outline_size,
                            color=self._outline_color)

        if self._perf:
            after = datetime.datetime.now()
            delta = after - before
            print  'basemap plotted in %d.%06d seconds' % (delta.seconds,
                                                           delta.microseconds)

        if self._show_colorbar:
            axis = pyplot.gca()
            ax_pos = axis.get_position()
            l,b,w,h = ax_pos.bounds
            color_axis = pyplot.axes([l+w-0.05, b, 0.025, h])
            if self._cmap_ticks is not None:
                pyplot.colorbar(image, cax=color_axis, ticks=self._cmap_ticks)
            else:
                pyplot.colorbar(image, cax=color_axis)
            pyplot.axes(axis)

        if self._title:
            pyplot.suptitle(self._title, fontsize=16)
            #pyplot.suptitle(self._title, y=1.05, fontsize=16)
        if self._subtitle:
            pyplot.title(self._subtitle, fontsize=12)
            #pyplot.title(self._subtitle, y=1.0, fontsize=12)

        return figure

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def saveMap(self, filename, grid, **kwargs):
        figure = self.drawMap(grid, **kwargs)
        if self._tight_box:
            figure.savefig(filename, bbox_inches='tight', pad_inches=0.0)
        else:
            figure.savefig(filename)

    def mapToImageBuffer(self, grid, **kwargs):
        figure = self.drawMap(grid, **kwargs)
        image = StringIO()
        if self._tight_box:
            figure.savefig(image, format=kwargs.get('format','PNG'),
                                  bbox_inches='tight', pad_inches=0.0)
        else:
            figure.savefig(image, format=kwargs.get('format','PNG'))
        return image

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # coordinate transform and projection utilities
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def transformGrid(self, grid, nx=None, ny=None, x_incr=None, y_incr=None):
        """ Transforms grid data to a fixed interval x,y grid.

        Arguments:
        ---------
        grid   -- the grid to be transformed
        nx     -- number of interplotated points in x direction
        ny     -- number of interplotated points in y direction
        x_incr -- distance b/w interplotated points in x direction
        y_incr -- distance b/w interplotated points in y direction

        """
        return grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # override basemap methods to dynamically load outlines if not cached
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawcoastlines(self, linewidth=1., color='k', antialiased=1, ax=None,
                             zorder=None):
        """ Draw coastlines. Loads coastlines on-demand unless previously
        cached.
        returns a matplotlib.patches.LineCollection object.
        """
        basemap = self._basemap
        if not hasattr(basemap, 'coastpolygons'):
            if basemap.resolution is None:
                raise AttributeError,\
                      "'resolution' must be set before coastline polygons can be loaded."
            self._getCoastPolygons()

        return basemap.drawcoastlines(linewidth, color, antialiased, ax, zorder)

    def drawcountries(self, linewidth=0.5, color='k', antialiased=1, ax=None,
                            zorder=None):
        """ Draw country boundaries. Loads country polygons on-demand unless
        previously cached.
        returns a matplotlib.patches.LineCollection object.
        """
        basemap = self._basemap
        if not hasattr(basemap, 'cntrysegs'):
            if basemap.resolution is None:
                raise AttributeError,\
                      "'resolution' must be set before country polygons can be loaded."
            basemap.cntrysegs, _types = basemap._readboundarydata('countries')

        return basemap.drawcountries(linewidth, color, antialiased, ax, zorder)

    def drawstates(self, linewidth=0.5, color='k', antialiased=1, ax=None,
                         zorder=None):
        """ Draw state boundaries in Americas. Loads state polygons on-demand
        unless previously cached.
        returns a matplotlib.patches.LineCollection object.
        """
        basemap = self._basemap
        if not hasattr(basemap, 'statesegs'):
            if basemap.resolution is None:
                raise AttributeError,\
                      "'resolution' must be set before state polygons can be loaded."
            basemap.statesegs, _types = basemap._readboundarydata('states')
        return basemap.drawstates(linewidth, color, antialiased, ax, zorder)

    def drawrivers(self, linewidth=0.5, color='k', antialiased=1, ax=None,
                         zorder=None):
        """
        Draw major rivers. Loads river vectors on-demand unless previously
        cached. 
        returns a matplotlib.patches.LineCollection object.
        """
        basemap = self._basemap
        if not hasattr(basemap,'riversegs'):
            if basemap.resolution is None:
                raise AttributeError,\
                      "'resolution' must be set before river vectors can be loaded."
            basemap.riversegs, _types = basemap._readboundarydata('rivers')
        return basemap.drawrivers(linewidth, color, antialiased, ax, zorder)

    def fillcontinents(self, color='0.8', lake_color=None, ax=None,
                             zorder=None):
        """ Fill continents. Loads coastlines on-demand unless previously
        cached.
        returns a list of matplotlib.patches.Polygon objects.
        """
        basemap = self._basemap
        if not hasattr(basemap, 'coastpolygons'):
            if basemap.resolution is None:
                raise AttributeError,\
                      "'resolution' must be set before continent polygons can be drawn."
            self._getCoastPolygons()

        return basemap.fillcontinents(color,lake_color,ax,zorder)

    def is_land(self, xpt, ypt):
        """ Boolean check whether point (in projected coordinates) is on
        land. True = on land, False = not on land.
        returns None if coastline polygons have not been loaded.
        """
        basemap = self._basemap
        if basemap.resolution is None or not hasattr(basemap, 'coastpolygons'):
            return None
        if not hasattr(basemap, 'landpolygons'): self._createLandPolygons()
        return basemap.is_land(xpt, ypt)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # methods to provide functionality extracted from Basemap.__init__
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _createLandPolygons(self):
        """ Create geos Polygon structures for land areas. Currently only used
        in is_land method.
        """
        basemap = self._basemap
        if basemap.resolution is None:
            raise AttributeError,\
                  "'resolution' must be set before land polygons can be created."

        if not hasattr(basemap, 'coastpolygons'): self._getCoastPolygons()

        basemap.landpolygons=[]
        basemap.lakepolygons=[]
        if len(basemap.coastpolygons) > 0:
            x, y = zip(*basemap.coastpolygons)
            for x,y,type in zip(x,y,basemap.coastpolygontypes):
                b = N.asarray([x,y]).T
                if type == 1: basemap.landpolygons.append(_geoslib.Polygon(b))
                if type == 2: basemap.lakepolygons.append(_geoslib.Polygon(b))

    def _getCoastPolygons(self):
        basemap = self._basemap
        basemap.coastsegs, basemap.coastpolygons, basemap.coastpolygontypes =\
                self._readCoastPolygons()

    def _readCoastPolygons(self):
        """ Read coastline polygon files, only keeping polygons that intersect
        the map boundary polygon.
        """
        basemap = self._basemap
        if basemap.resolution is None:
            raise AttributeError, "'resolution' must be set before coastline polygons can be loaded."

        in_coastsegs, coastpolygontypes = basemap._readboundarydata('gshhs')
        # reformat for use in matplotlib.patches.Polygon.
        coastpolygons = []
        # also, split coastline segments that jump across entire plot.
        coastsegs = []
        for seg in in_coastsegs:
            x, y = zip(*seg)
            coastpolygons.append((x,y))
            x = N.array(x,N.float64); y = N.array(y,N.float64)
            xd = (x[1:]-x[0:-1])**2
            yd = (y[1:]-y[0:-1])**2
            dist = N.sqrt(xd+yd)
            split = dist > 5000000.
            if N.sum(split) and basemap.projection not in _cylproj:
                ind = (N.compress(split,N.squeeze(split*N.indices(xd.shape)))+1).tolist()
                iprev = 0
                ind.append(len(xd))
                for i in ind:
                    # don't add empty lists.
                    if len(range(iprev,i)):
                        coastsegs.append(zip(x[iprev:i],y[iprev:i]))
                    iprev = i
            else:
                coastsegs.append(seg)
        return coastsegs, coastpolygons, coastpolygontypes

    def _useCachedPolygonData(self, coastpolygons=None, coastpolygontypes=None,
                                    coastsegs=None, riversegs=None,
                                    cntrysegs=None, statesegs=None):
        basemap = self._basemap
        if coastpolygons is not None:
            basemap.coastpolygons = coastpolygons
        if coastpolygontypes is not None:
            basemap.coastpolygontypes = coastpolygontypes
        if coastsegs is not None:
            basemap.coastsegs = coastsegs
        if riversegs is not None:
            basemap.riversegs = riversegs
        if cntrysegs is not None:
            basemap.cntrysegs = cntrysegs
        if statesegs is not None:
            basemap.statesegs = statesegs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # plot configuration methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initBasemap(self):
        map_args = self._getMapArgs()
        if self._show_coastlines or self._show_countries or self._show_states:
            try:
                self._basemap = Basemap(**map_args)
            except Exception, e:
                raise e

        else:
            area_thresh = map_args['area_thresh']
            resolution = map_args['resolution']
            map_args['area_thresh'] = None # don't load polygons unless needed
            map_args['resolution'] = None # don't load polygons unless needed

            try:
                self._basemap = Basemap(**map_args)
            except Exception, e:
                raise e

            # need this bit extracted from MplTk Basemap.__init__ so that
            # resolution and area_thresh are properly set, otherwise on-demand
            # polygon loading will fail.
            if resolution is None:
                resolution = 'c'
            self._basemap.resolution = resolution
            if area_thresh is None:
                if resolution == 'c':
                    area_thresh = 10000.
                elif resolution == 'l':
                    area_thresh = 1000.
                elif resolution == 'i':
                    area_thresh = 100.
                elif resolution == 'h':
                    area_thresh = 10.
                elif resolution == 'f':
                    area_thresh = 1.
                else:
                    errmsg = "boundary resolution must be one of 'c','l','i','h' or 'f'"
                    raise ValueError, errmsg
            self._basemap.area_thresh = area_thresh

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initBounds(self, kwargs):
        # set basemap lat/lon bounds
        # first look for 'bbox'
        bbox = kwargs.get('bbox', NOT_FOUND)
        if bbox != NOT_FOUND and self._isValidBbox(bbox):
            self._llcrnrlon, self._llcrnrlat, \
            self._urcrnrlon, self._urcrnrlat = bbox

        # no 'bbox', look for individual corners
        else:
            lon = self._validCoord('llcrnrlon', kwargs,
                                   self.MIN_VALID_LON, self.MAX_VALID_LON)
            if lon not in (NOT_FOUND, BOGUS_VALUE):
                self._llcrnrlon = lon
            lon = self._validCoord('urcrnrlon', kwargs,
                                   self.MIN_VALID_LON, self.MAX_VALID_LON)
            if lon not in (NOT_FOUND, BOGUS_VALUE):
                self._urcrnrlon = lon
            lat = self._validCoord('llcrnrlat', kwargs,
                                   self.MIN_VALID_LAT, self.MAX_VALID_LAT)
            if lat not in (NOT_FOUND, BOGUS_VALUE):
                self._llcrnrlat = lat
            lat = self._validCoord('urcrnrlat', kwargs,
                                   self.MIN_VALID_LAT, self.MAX_VALID_LAT)
            if lat not in (NOT_FOUND, BOGUS_VALUE):
                self._urcrnrlat = lat
        #
        # get transformed grid increment prameters
        #
        value = self._validFloat('x_incr', kwargs)
        if value is not None: self._x_incr = value
        value = self._validFloat('y_incr', kwargs)
        if value is not None: self._y_incr = value

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initColormap(self, kwargs):
        self._edetail = self._validBoolean('edetail', kwargs, False)
        cmap_mgr = self._cmap_mgr
        # 
        # handle color map args
        # 
        cmap_bounds = kwargs.get('discrete', None)
        if cmap_bounds is not None:
            if type(cmap_bounds) not in (tuple, list):
                self._errors.append("Invalid value in 'discrete'.")

        colors = kwargs.get('cmap_colors', None)
        if colors is not None:
            hex_colors = None
            if type(colors) in (tuple, list):
                hex_colors = self._validHexColors(colors, 'cmap_colors')
            if hex_colors is not None:
                if cmap_bounds is not None:
                    cmap, cmap_bounds = cmap_mgr.getDiscreteColormap(hex_colors,
                                                                    cmap_bounds)
                else:
                    cmap = cmap_mgr.getColormap(hex_colors)
            else:
                self._errors.append("Invalid value for 'cmap_colors'.")

        else:
            cmap_name = kwargs.get('cmap', self.DEFAULT_COLORMAP)
            if cmap_mgr.isDiscreteColormap(cmap_name):
                cmap, cmap_bounds = cmap_mgr.getColormapByName(cmap_name)
            else:
                if cmap_bounds is not None:
                    cmap, cmap_bounds = cmap_mgr.getDiscreteColormap(cmap_name,
                                                                    cmap_bounds)
                else:
                    cmap = cmap_mgr.getColormapByName(cmap_name)

        cmap_ticks = kwargs.get('cmap_ticks', None)
        if cmap_ticks is not None:
            if type(cmap_ticks) not in (tuple, list):
                self._errors.append("Invalid value in 'cmap_ticks'.")

        self._cmap = cmap
        self._cmap_bounds = cmap_bounds
        self._cmap_ticks = cmap_ticks
        if 'cbar_offset' in kwargs:
            self._cbar_offset = kwargs['cbar_offset'] 

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initPlot(self, kwargs):
        self._edetail = self._validBoolean('edetail', kwargs, False)
        #
        # set figure size and resolution
        #
        value = kwargs.get('figsize', None)
        if value is not None:
            error = True
            if type(value) in (tuple, list):
                if len(value) == 2:
                    if type(value[0]) == int and type(value[1]) == int:
                        self._fig_size = value
                        error = False
            if error:
                self._errors.append("Invalid value for 'figsize'.")
                if self._edetail:
                    self._errors.append("Value for 'figsize' must be a Python list"\
                                        " or tuple containing two integer values.")
        value = self._validInt('dpi', kwargs)
        if value is not None: self._fig_dpi = value
        self._tight_box = self._validBoolean('tight', kwargs, False)

        value = self._validInt('height', kwargs)
        if value is not None: self._height = value

        value = self._validInt('width', kwargs)
        if value is not None: self._width = value

        value = kwargs.get('title', None)
        self._title = value

        value = kwargs.get('subtitle', None)
        self._subtitle = value

        value = kwargs.get('resolution', NOT_FOUND)
        if value != NOT_FOUND:
            if value in ('c','l','i','h','f',None):
                self._resolution = value
            else:
                self._errors.append("Invalid value for 'resolution'.")

        value = kwargs.get('area_thresh', NOT_FOUND)
        if value != NOT_FOUND:
            if value is None:
                self._area_thresh = value
            elif type(value) == float:
                if value < 1. or value > 10000.:
                    self._errors.append("Invalid value for 'area_thresh'.")
                else:
                    self._area_thresh = value
            else:
                self._errors.append("Invalid value for 'area_thresh'.")

        value = kwargs.get('ticks', NOT_FOUND)
        if value != NOT_FOUND:
            if value in (True,False):
                self.axis_ticks = value
            else:
                self._errors.append("Invalid value for 'ticks'.")
                
        #
        # look for color map attributes
        #
        self._initColormap(kwargs)
                
        #
        # look for basemap features
        #
        value = kwargs.get('outline_size', None)
        if value is not None:
            self._outline_size = value
        value = kwargs.get('outline_color', None)
        if value is not None:
            self._outline_color = value

        show = kwargs.get('show',())
        if 'frame' in show:
            self._show_frame = True
        if 'coast' in show or 'coastlines' in show:
            self._show_coastlines = True
        if 'country' in show or 'countries' in show:
            self._show_countries = True
        if 'state' in show or 'states' in show:
            self._show_states = True
        if 'color' in show or 'colorbar' in show:
            self._show_colorbar = True

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initProjection(self, kwargs):
        value = kwargs.get('projection', kwargs.get('proj',NOT_FOUND))
        if value != NOT_FOUND:
            if value in VALID_PROJECTIONS:
                self._projection = value
            else:
                self._errors.append("Invalid value for 'projection'.")
        #
        # set projection parameters
        #
        proj_params = { }
        value = self._validCoord('lat_0', kwargs, -90., 90.)
        if value not in (NOT_FOUND, BOGUS_VALUE):
            proj_params['lat_0'] = value
        value = self._validCoord('lat_1', kwargs, -90., 90.)
        if value not in (NOT_FOUND, BOGUS_VALUE):
            proj_params['lat_1'] = value
        value = self._validCoord('lat_2', kwargs, -90., 90.)
        if value not in (NOT_FOUND, BOGUS_VALUE):
            proj_params['lat_2'] = value
        value = self._validCoord('lat_ts', kwargs, -90., 90.)
        if value not in (NOT_FOUND, BOGUS_VALUE):
            proj_params['lat_ts'] = value

        value = self._validCoord('lon_0', kwargs, -360., 720.)
        if value not in (NOT_FOUND, BOGUS_VALUE):
            proj_params['lon_0'] = value
        value = self._validCoord('lon_1', kwargs, -360., 720.)
        if value not in (NOT_FOUND, BOGUS_VALUE):
            proj_params['lon_1'] = value
        value = self._validCoord('lon_2', kwargs, -360., 720.)
        if value not in (NOT_FOUND, BOGUS_VALUE):
            proj_params['lon_2'] = value

        value = self._validCoord('boundinglat', kwargs, -90., 90.)
        if value not in (NOT_FOUND, BOGUS_VALUE):
            proj_params['boundinglat'] = value

        value = kwargs.get('no_rot', NOT_FOUND)
        if value != NOT_FOUND:
            if value in (True, False):
                proj_params['no_rot'] = value
            else:
                self._errors.append("Invalid value for 'no_rot'.")

        value = kwargs.get('satellite_height', NOT_FOUND)
        if value != NOT_FOUND:
            if type(value) == float:
                proj_params['satellite_height'] = value
            else:
                self._errors.append("Invalid value for 'satellite_height'.")

        #
        # rsphere is tricky as it can either be a single value or a 2 tuple
        #
        value = kwargs.get('rsphere', NOT_FOUND)
        if value != NOT_FOUND:
            error = True
            if type(value) == float:
                proj_params['rsphere'] = value
                error = False
            elif type(value) == int:
                proj_params['rsphere'] = float(value)
                error = False
            elif type(value) in (tuple, list):
                if len(value) == 2:
                    if type(value[0]) == int:
                        value[0] = float(value[0])
                    if type(value[1]) == int:
                        value[1] = float(value[1])
                    if type(value[0]) == float and type(value[1]) == float:
                        proj_params['rsphere'] = value
                        error = False
            if error:
                self._errors.append("Invalid value for 'rsphere'.")
                self._errors.append(RSPHERE_ERROR_MSG)
        else:
            a_radius = kwargs.get('a', NOT_FOUND)
            if a_radius != NOT_FOUND:
                b_radius = kwargs.get('b', NOT_FOUND)
                if b_radius != NOT_FOUND:
                    proj_params['rsphere'] = (a_radius, b_radius)
                else:
                    proj_params['rsphere'] = a_radius

        # save projection parameters
        if proj_params:
            self._proj_params = proj_params

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # configuration accessors
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getFigArgs(self):
        fig_args = { }
        if self._fig_dpi is not None:
            fig_args['dpi'] = self._fig_dpi
        if self._fig_size is None:
            fig_args['figsize'] = self.DEFAULT_FIGSIZE
        else:
            fig_args['figsize'] = self._fig_size
        return fig_args

    def _getMapArgs(self):
        map_args = { }
        if self._llcrnrlon is not None:
            map_args['llcrnrlon'] = self._llcrnrlon
        if self._llcrnrlat is not None:
            map_args['llcrnrlat'] = self._llcrnrlat
        if self._urcrnrlon is not None:
            map_args['urcrnrlon'] = self._urcrnrlon
        if self._urcrnrlat is not None:
            map_args['urcrnrlat'] = self._urcrnrlat
        if self._projection is None:
            raise ValueError, "Missing value for 'projection'."
        map_args['projection'] = self._projection
        if self._proj_params is None:
            raise ValueError, "Missing projection parameters."
        map_args.update(self._proj_params)
        map_args['resolution'] = self._resolution
        map_args['area_thresh'] = self._area_thresh
        map_args['suppress_ticks'] = not self._axis_ticks
        if self._map_height is not None: map_args['height'] = self._map_height
        if self._map_width is not None: map_args['width'] = self._map_width
        return map_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # parameter validation methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _isValidBbox(self, bbox):
        if type(bbox) in (tuple, list) and len(bbox) == 4:
            if type(bbox[0]) == float and type(bbox[1]) == float and\
               type(bbox[2]) == float and type(bbox[3]) == float:
                return True
            else:
                self._errors.append("Invalid value in 'bbox'.")
        else:
            self._errors.append("Invalid value for 'bbox'.")
            self._errors.append("'bbox' must be a list with exactly 4 numbers.")
        return False

    def _isValidCoord(self, coord, min_allowed, max_allowed):
        if type(bbox) in (tuple, list) and len(bbox) == 4:
            if type(bbox[0]) == float and type(bbox[1]) == float and\
               type(bbox[2]) == float and type(bbox[3]) == float:
                return True
            else:
                self._errors.append("Invalid value in 'bbox'.")
        else:
            self._errors.append("Invalid value for 'bbox'.")
            self._errors.append("'bbox' must be a list with exactly 4 numbers.")
        return False

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _invalidOrMissing(self, name, value, default, required):
        if value is None:
            if default is None and not required:
                return value
            else:
                self._errors.append("Invalid value for '%s.'" % name)
        elif value is BOGUS_VALUE:
            if not required:
                return default
            else:
                self._errors.append("Missing value for '%s'." % name)
        else:
            self._errors.append("Invalid value for '%s'." % name)
        return BOGUS_VALUE

    def _validBoolean(self, name, kwargs, default):
        value = kwargs.get(name, default)
        if value in (True,False):
            return value
        self._errors.append("Invalid value for boolean '%s.'" % name)
        return BOGUS_VALUE

    def _validCoord(self, name, kwargs, min_allowed, max_allowed):
        value = kwargs.get(name, NOT_FOUND)
        if value == NOT_FOUND or ( type(value) == float and
           not (value < min_allowed) and not (value > max_allowed) ):
            return value
        self._errors.append("'%s' must be a number in the range %d to %d" %
                            (name, min_allowed, max_allowed))
        return BOGUS_VALUE

    def _validHexColor(self, color, context):
        if isHexColor(color):
           return color
        else:
            hex_color = htmlColorName2Hex(color)
            if hex_color is None:
                self._errors.append("Invalid color in '%s.'" % context)
            return hex_color

    def _validHexColors(self, colors, context):
        valid_colors = [ ]
        for color in colors:
            hex_color = self._validHexColor(color, context)
            if hex_color is not None:
                valid_colors.append(hex_color)
            else:
                return None
        return valid_colors

    def _validCoords(self, min_coord, max_coord, kwargs, min_allowed,
                           max_allowed, required=False):
        min_value = self._validFloatInRange(min_coord, kwargs, min_allowed,
                                            max_allowed, None, required)
        max_value = self._validFloatInRange(max_coord, kwargs, min_allowed,
                                            max_allowed, None, required)
        if type(min_value) == float and type(max_value) == float:
            if min_value >= max_value:
                self._errors.append("'%s' coordinate must be les than '%s'."
                                    % (min_coord, max_coord))
                return BOGUS_VALUE, BOGUS_VALUE
        return min_value, max_value

    def _validInList(self, name, kwargs, _list, default=None, required=False):
        value = kwargs.get(name, BOGUS_VALUE)
        if value in _list:
            return value
        # invalid value or missing
        return self._invalidOrMissing(name, value, default, required)

    def _validInt(self, name, kwargs, default=None, required=False):
        value = kwargs.get(name, BOGUS_VALUE)
        if type(value) == int:
                return value
        # wrong type or missing value
        return self._invalidOrMissing(name, value, default, required)

    def _validIntInRange(self, name, kwargs, min_value, max_value,
                             default=None, required=True):
        value = self._validInt(name, kewargs, default, required)
        if type(value) == int: # got an integer
            if value < min_value or value > max_value:
                self._errors.append("Value for '%s' is outside range %d to %d" %
                                    (name, min_value, max_value))
        return value

    def _validFloat(self, name, kwargs, default=None, required=False):
        value = kwargs.get(name, BOGUS_VALUE)
        if type(value) == float:
            return value
        # wrong type or missing value
        return self._invalidOrMissing(name, value, default, required)

    def _validFloatInRange(self, name, kwargs, min_value, max_value,
                                 default=None, required=False):
        value = self._validFloat(name, kwargs, default, required)
        if type(value) == float: # got a float
            if value < min_value or value > max_value:
                self._errors.append("Value for '%s' is outside range %d to %d" %
                                    (name, min_value, max_value))
        return value

