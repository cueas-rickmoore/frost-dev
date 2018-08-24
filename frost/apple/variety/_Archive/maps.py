
import os, sys

from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N
import PIL.Image

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot
from matplotlib import cm
from mpl_toolkits.basemap import Basemap

from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from frost import ROOT_DIR
MAPS_DIR = os.path.join(ROOT_DIR, 'maps') + os.sep

MAP_OPTIONS = { "area": "northeast",       # northeast, westny, eastny, ny, etc.
                "bbox": [-82.70, 37.20, -66.90, 47.60],  # plot coordinate bounding box
                "maptype": "contourf",     # contourf, interpf or dotmap
                "size_tup": (6.8, 6.55),   # new standard size is (6.8, 6.55), thumbnail is (2.3, 2.3), original standard is (4.7, 4.55), large is (12,8.3)
                "titlefontsize": 12,       # standard is 12, original is 10, large is 15, (none for thumbnail)
                "titlexoffset": 0.05,      # 0.05 for all but those specified below
                "titleyoffset": 0.10,      # 0.10 for all but those specified below
                "pltshow": False,          # boolean
                "datesfromfile": False,    # boonean
                #
                "cmap": "jet",
                "colorbar": False,          # whether or not to plot a colorbar
                # or "cmap": 'RdYlGn',
                #"numlevels": 8,           # number of contour levels
                #"levelmult": None,        # contour bounds are multiples of this value (None = pick based on data)
                "cbarlabelsize": 8,                             # small is 8, large is 10
                "cbarsettings": [0.25, 0.11, 0.5, 0.02],        # small is [0.25, 0.11, 0.5, 0.02], large is [0.25, 0.06, 0.5, 0.03] -- [left, bottom, width, height]
                #
                "logo": "%s/PoweredbyACIS-rev2010-08.png" % MAPS_DIR,  # also available ...PoweredbyACIS_NRCC.jpg (False for no logo)
                "shapelocation": MAPS_DIR, # location of template or shapefiles (old basemap)
                }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def plot_setup(lats, lons, map_options):
    # setup plot figure
    fig = pyplot.figure(figsize=(map_options['size_tup']))

    # initialize basmap
    if map_options['area'].find("gulfmaine") < 0:
        lon_min = N.nanmin(lons)
        lat_min = N.nanmin(lats)
        lat_max = N.nanmax(lats)
        lon_max = N.nanmax(lons)
    else:
        lon_min = -77.0
        lat_min = 41.2
        lat_max = 49.5
        lon_max = -59.0

    _base_map_ = Basemap(resolution='i', projection='merc', llcrnrlon=lon_min,
                         llcrnrlat=lat_min, urcrnrlon=lon_max,
                         urcrnrlat=lat_max, lat_ts=(lat_max+lat_min)/2.0)
    x_max, y_max = _base_map_(lon_max,lat_max)
    x_min, y_min = _base_map_(lon_min,lat_min)

    # add logo
    logo = map_options.get('logo', None)
    if logo is not None:
        img = PIL.Image.open(logo)
        xdiff = x_max-x_min
        ydiff = y_max-y_min
        extent = (x_max-0.30*xdiff, x_max-0.01*xdiff,
                  y_min+0.01*ydiff, y_min+0.15*ydiff)
        pyplot.imshow(img, extent=extent)

    # add title
    title = map_options['title']
    title2 = map_options.get('title2',None)
    if title2 is not None: title += '\n%s' % title2
    date = map_optons.get('date', None)
    if date is not None:
        if isinstance(date, basestring): title += '\n%s' % date
        else: title += '\n%s' % date.strftime('%B %d, %Y')

    title = pyplot.text(x_min + map_options['titlexoffset'] * (x_max-x_min),
                        y_max - map_options['titleyoffset'] * (y_max-y_min),
                        title, backgroundcolor="white",
                        fontsize=map_options['titlefontsize'],
                        multialignment="center", zorder=10)
    title_box_alpha = map_options.get('title_box_alpha', None)
    if title_box_alpha is not None:
        title.set_bbox({'alpha':title_box_alpha})

    # add area template image
    area = map_options.get('area',None)
    if area is not None:
        filename = "%s_template.png" % area
        path = os.path.join(map_options['shapelocation'], filename)
        img = PIL.Image.open(path)
        pyplot.imshow(img, extent=(x_min+.0015*(x_max-x_min),x_max,y_min,y_max),
                      zorder=3)

    # add box around the map
    _base_map_.drawmapboundary(linewidth=1.0, color="black", zorder=15)

    return _base_map_, fig

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def plot_finishup(options):
    pyplot.savefig(options['outputfile'], bbox_inches='tight', pad_inches=0.02)
    if options['pltshow']: pyplot.show()
    else: pyplot.close()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def drawScatterPlot(stage_grid, lats, lons):
    figure = pyplot.figure(figsize=(8,6),dpi=100)
    pyplot.xlim(N.nanmin(lons),N.nanmax(lons))
    pyplot.ylim(N.nanmin(lats),N.nanmax(lats))
    axis = pyplot.gca()
    scatter = axis.scatter(lons, lats, c=stage_grid, marker='s', 
                           s=15, linewidths=0)
    axis.grid(True)

    #ax_pos = axis.get_position()
    #l,b,w,h = ax_pos.bounds
    #color_axis = pyplot.axes([l+w, b, 0.025, h])
    #pyplot.colorbar(scatter, cax=color_axis, ticks=ticks)

    pyplot.axes(axis)

    #pyplot.suptitle(title, fontsize=16)
    #pyplot.title(subtitle, fontsize=12)
    figure.savefig('test_plot.png')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def setupMap(options, lons=None, lats=None):
    map_options = MAP_OPTIONS.copy()
    map_options.update(options)
    del map_options['map_type']

    if lons is not None:
        _basemap_, fig = plot_setup(lats, lons, map_options)

    if lons is None: return map_options
    else: return map_options, _basemap_, fig

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def finishMap(fig, fig1, map_options):
    if map_options['colorbar']:
        axis1 = fig.add_axes(map_options['cbarsettings'])
        cbar = fig.colorbar(fig1, axis1, orientation='horizontal')
        label_size = map_options.get("cbarlabelsize",None)
        if label_size is not None:
            cbar.ax.tick_params(labelsize=label_size)

    labels = map_options.get("keylabels",None)
    if labels is not None:
        colors = map_options['colors']
        labelsize = map_options['cbarlabelsize']
        num_labels = len(labels)
        ypos = map_options['cbarsettings'][1]

        for i in range(num_labels):
            xpos = 0.16 + ( (2.0*i+1.0) * (1.0/(num_labels)*2.0) ) * 0.7
            fig.text(xpos, ypos, labels[i], color=colors[i],
                     fontsize=labelsize, horizontalalignment="center")       
    
    plot_finishup(map_options)
    print 'completed', map_options['outputfile']

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def highResolutionGrid(lons, lats, grid, apply_mask=False):
    from mpl_toolkits.basemap import interp
    from mpl_toolkits.basemap import maskoceans
    # interpolate data to higher resolution grid in order to better match
    # the builtin land/sea mask. Output looks less 'blocky' near coastlines.
    ##      rbf = Rbf(lons[0], lats[:,0], map_val, epsilon=2)       ##
    nlats = 5 * lats.shape[0]
    nlons = 5 * lats.shape[1]
    interp_lons = N.linspace(N.min(lons), N.max(lons),nlons)
    interp_lats = N.linspace(N.min(lats), N.max(lats),nlats)
    interp_lons, interp_lats = N.meshgrid(interp_lons, interp_lats)

    # interpolated high resolution data grid
    interp_grid = interp(grid, lons[0], lats[:,0], interp_lons, interp_lats)
    ##map_val to rbf

    # interpolate land/sea mask to data grid, then mask nodes in ocean
    if apply_mask:
        interp_grid = maskoceans(interp_lons, interp_lats, interp_grid,
                                 resolution='i', grid=1.25, inlands=False)
        interp_grid[interp_grid == -999] = N.nan

    return interp_lons, interp_lats, interp_grid

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def drawFilledContours(grid, lats, lons, **options):
    map_options, _basemap_, fig = setupMap(options, lons, lats)

    _lons_, _lats_, _grid_ = highResolutionGrid(lons, lats, grid, True)
    x, y = _basemap_(_lons_, _lats_)

    # get color to use for contours
    colors = map_options.get('colors', None)
    map_args = { 'extend':'both', }
    if colors is None:
        map_args['cmap'] = cm.get_cmap(map_options['cmap'])
    else: map_args['colors'] = colors
    
    # draw filled contours
    color_bounds = map_options.get('contourbounds',None)
    if color_bounds is None:
        fig1 = _basemap_.contourf(x, y, _grid_, **map_args)
    else:
        fig1 = _basemap_.contourf(x, y, _grid_, color_bounds, **map_args)

    finishMap(fig, fig1, map_options)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawContours(grid, lats, lons, **options):
    map_options, _basemap_, fig = setupMap(options, lons, lats)

    _lons_, _lats_, _grid_ = highResolutionGrid(lons, lats, grid, True)
    x, y = _basemap_(_lons_, _lats_)

    # draw filled contours
    colors = options.get('colors', None)
    color_bounds = map_options['contourbounds']
    if colors is None:
        fig1 = _basemap_.contour(x, y, _grid_, color_bounds, extend='both',
                                 cmap=cm.get_cmap(map_options['cmap']))
    else:
        fig1 = _basemap_.contour(x, y, _grid_, color_bounds, extend='both',
                                 colors=colors)

    finishMap(fig, fig1, map_options)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawScatterMap(grid, lats, lons, **options):
    map_options, _basemap_, fig = setupMap(options, lons, lats)
    x, y = _basemap_(lons,lats)

    fig1 = _basemap_.scatter(x, y, s=grid, c=map_options['colors'])

    finishMap(fig, fig1, map_options)

