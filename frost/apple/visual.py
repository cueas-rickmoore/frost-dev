
import os

import numpy as N

#from frost.visual.maps import basemapSetup, addFigureText
from frost.visual.maps import mapInit, finishMap
from frost.visual.maps import resolveMapOptions, resolveColorMapOptions

# plyplot must imported AFTER frost.visual.maps becuase
# frost.visual.maps sets matplotlib backend
from matplotlib import pyplot

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def addModelText(fig, model, **text_options):
    options = { 'backgroundcolor':text_options.get('model_bgcolor','white'),
                'color':text_options.get('model_fgcolor','black'),
                'fontsize':text_options.get('model_fontsize',8),
                'ha':text_options.get('model_ha','right'),
                'va':text_options.get('model_va','center'),
                'zorder':text_options.get('model_zorder',20),
              }
    x = text_options.get('model_x',0.875)
    y = text_options.get('model_y',0.3)

    fig_text = fig.text(x, y, model.description, **options)
    fig_text.set_bbox({'alpha':0})

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def drawNoDataMap(lons, lats, **options):
    model = options['model']
    del options['model']
    map_options = resolveMapOptions(**options)

    no_data_config = options.get('config', None)
    if no_data_config is not None: map_options.update(no_data_config)
    _basemap_, map_fig, axes, xy_extremes = mapInit(lats, lons, **map_options)

    if 'contourbounds' in map_options:
        x_min = xy_extremes[0]
        x = N.array( [ [x_min, x_min+1.0], [x_min, x_min+1.0 ] ] )
        y_min = xy_extremes[2]
        y = N.array( [ [y_min, y_min], [y_min+1.0, y_min+1.0 ] ] )
        zero = N.array( [ [0.0, 0.0], [0.0, 0.0] ] )
        cmap_options = resolveColorMapOptions(**map_options)
        fig1 = _basemap_.contourf(x, y, zero, options['contourbounds'],
                                 **cmap_options)
    else: fig1 = map_fig

    addModelText(map_fig, model, **map_options)
    finishMap(map_fig, axes, fig1, **map_options)

    return map_options['outputfile']

