
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
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle, PathPatch
from matplotlib.path import Path

from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

MAPS_DIR = os.path.split(os.path.abspath(__file__))[0]

MAP_OPTIONS = { "area": "northeast",       # northeast, westny, eastny, ny, etc.
                "bbox": [-82.70, 37.20, -66.90, 47.60],  # plot coordinate bounding box
                "maptype": "contourf",     # contourf, interpf or dotmap
                "size_tup": (6.8, 6.55),   # new standard size is (6.8, 6.55), thumbnail is (2.3, 2.3), original standard is (4.7, 4.55), large is (12,8.3)
                "titlefontsize": 12,       # standard is 12, original is 10, large is 15, (none for thumbnail)
                "titlexoffset": 0.05,      # 0.05 for all but those specified below
                "titleyoffset": 0.10,      # 0.10 for all but those specified below
                "pltshow": False,          # boolean
                "datesfromfile": False,    # boonean
                'inputfile': None,                                                      # tab-delimited input file for dotmap or interpf
                "grid": 3,
                "numlevels": 8,            # number of contour levels
                "autolevels":None,
                "levelmult": None,         # contour bounds are multiples of this value (None = pick based on data)
                #
                "cmap": 'RdYlGn',
                "colorbar": False,          # whether or not to plot a colorbar
                "cbarlabelsize": 8,                             # small is 8, large is 10
                "cbarsettings": [0.25, 0.11, 0.5, 0.02],        # small is [0.25, 0.11, 0.5, 0.02], large is [0.25, 0.06, 0.5, 0.03] -- [left, bottom, width, height]
                #
                "logo": "%s/PoweredbyACIS-rev2010-08.png" % MAPS_DIR,  # also available ...PoweredbyACIS_NRCC.jpg (False for no logo)
                "metalocation": MAPS_DIR, 
                "shapelocation": MAPS_DIR, # location of template or shapefiles (old basemap)
                }

AREA_BBOX = { 'northeast':          [-82.70, 37.20, -66.90, 47.60],
              'ny':                 [-79.90, 40.45, -71.80, 45.05],
              'westny':             [-80.00, 41.95, -74.75, 45.00],
              'eastny':             [-77.00, 40.45, -71.80, 43.45],
              'midatlantic':        [-79.75, 37.25, -73.00, 41.75],
              'newengland':         [-73.80, 40.95, -66.85, 47.60],
              'easternregion':      [-85.10, 31.90, -66.80, 47.60],
              'gulfmaine_masked':   [-77.00, 41.20, -59.00, 49.50],
              'gulfmaine_unmasked': [-77.00, 41.20, -59.00, 49.50],
              'greatlakes_unmasked':[-94.30, 40.00, -74.00, 51.50],
              'vt':                 [-74.00, 42.50, -71.20, 45.25],
              'me':                 [-72.00, 42.75, -66.85, 47.60],
              'wv':                 [-83.00, 37.00, -77.50, 40.80],
              'wv_state':           [-83.00, 37.00, -77.50, 40.80],
              'pa':                 [-80.75, 39.50, -74.25, 42.25],
              'nh':                 [-72.75, 42.50, -70.25, 45.50],
              'ma':                 [-73.75, 41.25, -69.75, 43.00],
              'ct':                 [-73.75, 40.75, -71.25, 42.25], 
              'ri':                 [-72.50, 41.00, -70.50, 42.25],
              'md':                 [-80.00, 37.50, -74.75, 40.00],
              'nj':                 [-76.00, 38.75, -73.50, 41.75],
            }

TITLE_OFFSETS = { 'default':       (0.05, 0.10),
                  'northeast':     (0.05, 0.10),
                  'easternregion': (0.25, 0.10),
                  'midatlantic':   (0.25, 0.10),
                  'newengland':    (0.15, 0.10),
                  'ny':            (0.01, 0.10),
                  'eastny':        (0.23, 0.10),
                  'gulfmaine':     (0.65, 0.90), # not tested
                  'greatlakes':    (0.55, 0.15), # not tested
                  'wv':            (0.48, 0.09),
                  'wv_state':      (0.48, 0.09),
                }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# contour levels (from options, if available)
def getBounds(data, options):
    bounds = options.get("contourbounds", options.get("autobounds", None))
    if bounds is None:
        bounds = plot_bound(data, options["numlevels"], options["levelmult"])
    return bounds

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# reasonable contour intervals
def plot_bound(data, num_bins, mult=None, missing=None):
    if data.dtype.kind == 'f':
        _array_ = data[N.where(N.isfinite(data))]
        if missing is not None:
            _array_ = _array_[N.where(_array_ != missing)]
        #_array_ = _array_.astype(int)
    elif data.dtype.kind == 'i':
        if missing is None: missing = -999
        _array_ = data[N.where(data != missing) & (data > -9000000000000000000)]
    _array_ = _array_.flatten()

    # added 4/28/2014 -kle
    if mult is None:
        array_max = N.max(_array_)
        array_min = N.min(_array_)
        array_size = _array_.size
        data_intvl = (array_max-array_min)/num_bins
        mult = 1
        for i in [500,100,50,10,5]:
            if data_intvl > i:
                mult = i
                break

    _array_ /= mult
    array_size = float(len(_array_))

    array_min = N.min(_array_)
    bin_mid = N.histogram(_array_, bins=num_bins)
    bin_minimum = bin_mid[1][0]
    bin_maximum = bin_mid[1][-1]
    bin_converge = 0

    while bin_converge == 0:
        bin_tot_low = 0
        bin_tot_hi = 0
        bin_start = bin_mid[1][1]
        bin_end = bin_mid[1][num_bins]

        for val in range(len(bin_mid[0])):
            bin_tot_low=bin_tot_low+bin_mid[0][val]
            if bin_tot_low/array_size < 0.01:
                bin_start =bin_mid[1][val+1]
            else: break

        for val in range(len(bin_mid[0])-1,-1,-1):
            bin_tot_hi=bin_tot_hi+bin_mid[0][val]
            if bin_tot_hi/array_size < 0.01:
                bin_end = bin_mid[1][val] ###changed to val from val -1 atd 2/14
            else: break
                                
        if bin_start > bin_end: bin_start = bin_end
        bin_final = N.histogram(_array_, bins=num_bins,
                                range=(bin_start,bin_end))
        bin_range = abs(bin_mid[0][1]-bin_mid[0][0])
        if (bin_final[0][0]/array_size >= 0.01) or (abs(bin_final[1][0] - bin_final[1][-1]) < 1):
            bin_converge = 1
        else: bin_mid = bin_final

        # round bin contours, omitting the first and last bins as these will be extended to all values less and greater
        bin_contours=[]
        for vals in range(1,len(bin_final[1])-1):
            bin_contours.append(round(bin_final[1][vals],0))
        
        # create bins of equal integer width
        crange = bin_contours[-1]-bin_contours[0]
        resid = crange%num_bins
        factor = 1
        if resid < num_bins/2. and resid <> 0:
            ### shorten end bins
            b_change = round(resid/2.)
            low_change = b_change
            hi_change=-1*b_change 
            if b_change>resid/2.:
                hi_change = -1*(b_change -1)
        if resid <> 0:
            ### length end bins
            b_change = round((num_bins-resid)/2.)
            low_change = -1*b_change
            hi_change = b_change
            if b_change>(num_bins-resid)/2.:
                hi_change = b_change -1 
        else:
            b_change=0
            low_change=0
            hi_change=0
                
        binw = (crange+abs(low_change)+abs(hi_change))/num_bins
        bin_contours_new = [bin_contours[0]+low_change]
        for bin in range(len(bin_contours)):
             if bin_contours_new[bin]+binw <= bin_contours[-1]+hi_change:
                 bin_contours_new.append(bin_contours_new[bin]+binw)
             else: break   

        # remove duplicates and contours less than the min value of the array
        for i in range(len(bin_contours_new)-1,0,-1):
            if bin_contours_new[i] == bin_contours_new[i-1] or bin_contours_new[i] < array_min:
                del bin_contours_new[i]
        if bin_contours_new[0] < array_min:
            del bin_contours_new[0]

        # need to have at least two levels for contouring
        if len(bin_contours_new) == 1:
            bin_contours_new.append(N.max(_array_) + 1)

        # convert back to non-scaled values
        return tuple(N.array(bin_contours_new,dtype=float) * mult)

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
        pyplot.imshow(img, extent=extent, zorder=10)

    # add title
    title = map_options.get('title',None)
    if title is not None:
        title2 = map_options.get('title2',None)
        if title2 is not None: title += '\n%s' % title2
        date = map_options.get('date', None)
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
    area_template = map_options.get('area_template',None)
    if area_template is None:
        area = map_options.get('area',None)
        if area is not None:
            filename = "%s_template.png" % area
            path = os.path.join(map_options['shapelocation'], filename)
        else: path = None
    else: path = os.path.join(map_options['shapelocation'], area_template)
    if path is not None:
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
    scatter = axis.scatter(lons, lats, c=stage_grid, marker='s', s=15, mew=0)
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

def setupMap(options, lats=None, lons=None):
    map_options = MAP_OPTIONS.copy()
    map_options.update(options)

    if 'area' in options and 'bbox' not in options:
        area = options['area']
        map_options['bbox'] = AREA_BBOX[area]

    if lons is not None:
        _basemap_, fig = plot_setup(lats, lons, map_options)

    if lons is None: return map_options
    else: return map_options, _basemap_, fig

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def hiResMap(grid, lats, lons, **options):
    map_options, _basemap_, fig = setupMap(options, lats, lons)

    apply_mask = options.get('apply_mask', True)
    _lons_, _lats_, _grid_ = highResolutionGrid(lats, lons, grid, apply_mask)
    x, y = _basemap_(_lons_, _lats_)
    return map_options, _basemap_, fig, x, y, _grid_

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def resolveColorMapOptions(map_options):
    cmap_options = { }
    colors = map_options.get('colors', None)
    if colors is not None: 
        cmap = matplotlib.colors.ListedColormap(colors)
    else: cmap = cm.get_cmap(map_options['cmap'])
    if 'under_color' in map_options: cmap.set_under(map_options['under_color'])
    if 'over_color' in map_options: cmap.set_over(map_options['over_color'])
    cmap_options['cmap'] = cmap
    cmap_options['extend'] = map_options.get('extend','both')
    return cmap_options

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawColorBar(fig, fig1, map_options):
    axis1 = fig.add_axes(map_options['cbarsettings'])
    cbar = fig.colorbar(fig1, axis1, orientation='horizontal')
    label_size = map_options.get("cbarlabelsize",None)
    if label_size is not None:
        cbar.ax.tick_params(labelsize=label_size)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawColoredTextBar(fig, fig1, map_options):
    labels = map_options["keylabels"]
    num_labels = len(labels)
    label_size = map_options['cbarlabelsize']
    colors = map_options['colors']
    ypos = map_options['cbarsettings'][1]
    for indx, label in enumerate(labels):
        xpos = 0.16 + ( ((2.*indx) + 1.) * (1. / (num_labels*2.)) ) * 0.5
        fig.text(xpos, ypos, label, color=colors[indx],
                 fontsize=label_size, horizontalalignment="center")       

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawLabeledColorBar(fig, fig1, map_options):
    colors = map_options['colors']
    cbar_specs = map_options['cbarsettings']
    labels = map_options["keylabels"]
    num_labels = len(labels)
    label_colors = map_options.get('label_colors', # else set to black
                                   ['k' for l in range(num_labels)])
    font_style = { 'horizontalalignment':'center',
                   'verticalalignment':'center',
                   'fontsize':map_options['cbarlabelsize'],
                   'fontweight':map_options.get('cbarfontweight','normal'),
                   'fontstyle':map_options.get('cbarfontstyle','normal'),
                 }

    rect_width = 1. / num_labels
    rect_half = rect_width / 2.
    x_left = 0.
    y_bottom = 0.
    y_mid = 0.5
    y_top = 1.

    moves = \
    [ Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY ]

    axis = \
    fig.add_axes(cbar_specs, xticks=[], yticks=[], xlim=(0.,1.), ylim=(0.,1.))

    for indx, label in enumerate(labels):
        x_right = x_left + rect_width
        corners = [ (x_left, y_bottom), (x_left, y_top), (x_right, y_top),
                    (x_right, y_bottom), (x_left, y_bottom) ]
        #print label_colors[indx], corners
        rectangle = PathPatch(Path(corners, moves), facecolor=colors[indx],
                              lw=0, zorder=1)
        axis.add_patch(rectangle)
        axis.text(x_left+rect_half, y_mid, label, color=label_colors[indx], 
                  zorder=2, **font_style)
        x_left = x_right

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def finishMap(fig, fig1, map_options):
    if map_options.get("keylabels",None) is not None:
        if map_options['colorbar']:
            drawLabeledColorBar(fig, fig1, map_options)
        else: drawColoredTextBar(fig, fig1, map_options)
    elif map_options['colorbar']: drawColorBar(fig, fig1, map_options)

    plot_finishup(map_options)
    print 'completed', map_options['outputfile']

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def highResolutionGrid(lats, lons, grid, apply_mask=False):
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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def drawBlankMap(lats, lons, **options):
    map_options, _basemap_, fig = setupMap(options, lats, lons)
    finishMap(fig, fig, map_options)
    print 'completed', map_options['outputfile']

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawNoDataMap(**options):
    map_options = MAP_OPTIONS.copy()
    map_options.update(options)

    fig = pyplot.figure(figsize=(map_options['size_tup']))
    fig.patch.set_visible = False
    axis = fig.gca()
    axis.xaxis.set_visible(False)
    axis.yaxis.set_visible(False)

    # add default map image
    image_filepath = \
    os.path.join(map_options['shapelocation'], map_options['template_file'])
    image = pyplot.imread(open(image_filepath))
    pyplot.imshow(image, zorder=1)

    # overlay map title
    title = map_options['title']
    title2 = map_options.get('title2',None)
    if title2 is not None: title += '\n%s' % title2
    date = map_options.get('date', None)
    if date is not None:
        if isinstance(date, basestring): title += '\n%s' % date
        else: title += '\n%s' % date.strftime('%B %d, %Y')

    title = pyplot.text(map_options['titlexoffset'] * image.shape[0],
                        map_options['titleyoffset'] * image.shape[1],
                        title, backgroundcolor="white",
                        fontsize=map_options['titlefontsize'],
                        multialignment="center", zorder=10)
    title_box_alpha = map_options.get('title_box_alpha', None)
    if title_box_alpha is not None:
        title.set_bbox({'alpha':title_box_alpha})

    plot_finishup(map_options)
    print 'completed', map_options['outputfile']

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawContours(grid, lats, lons, **map_options):
    options, _basemap_, fig, x, y, _grid_ = hiResMap(grid, lats, lons,
                                                     **map_options)

    # draw filled contours
    cmap_options = resolveColorMapOptions(options)
    color_bounds = getBounds(grid, options)
    fig1 = _basemap_.contour(x, y, _grid_, color_bounds, **cmap_options)
    options.update(cmap_options)
    finishMap(fig, fig1, options)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawFilledContours(grid, lats, lons, **map_options):
    options, _basemap_, fig, x, y, _grid_ = hiResMap(grid, lats, lons,
                                                     **map_options)
    # get color mapcontours
    cmap_options = resolveColorMapOptions(options)
    
    # draw filled contours
    color_bounds = getBounds(grid, options)
    if color_bounds == True:
        fig1 = _basemap_.contourf(x, y, _grid_, **cmap_options)
    else: fig1 = _basemap_.contourf(x, y, _grid_, color_bounds, **cmap_options)
    options.update(cmap_options)
    finishMap(fig, fig1, options)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def addScatterToMap(map_options, _basemap_, fig, data, lats=None, lons=None,
                    x=None, y=None, markercolor=None):
    marker_size = map_options.get('marker_size', 10)
    if markercolor is None:
        if markercolors is None:
            cmap = map_options.get('cmap','jet')
        else: cmap = matplotlib.colors.ListedColormap(markercolors)
    else: cmap = matplotlib.colors.ListedColormap(markercolor)
    plot_args = { 'cmap':cmap, 'linewidths':map_options.get('linewidths', 0),
                  'edgecolors':map_options.get('edgecolors',None),
                  'marker':map_options.get('marker','^') }

    if x is None: x ,y = _basemap_(lons, lats)
    fig1 = _basemap_.scatter(x, y, s=marker_size, c=data, **plot_args)
    return fig1

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def drawScatterMap(grid, lats, lons, **map_options):
    options, _basemap_, fig, x, y, _grid_ = hiResMap(grid, lats, lons,
                                                     **map_options)

    fig1 = addToScatterMap(options, _basemap_, fig, _grid_, x=x, y=y)

    finishMap(fig, fig1, options)

