
from collections import OrderedDict

import numpy as N

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


APPLE_KILL_COLORS = ( ('10%','#1E90FF'), ('50%','#FFD700'), ('90%','#FF0000') )
# kill probabilities
APPLE_KILL_PROBS = (10,50,90)

APPLE_STAGE_COLORS = ( ('dormant','#FFEBCD'), ('stip','#C0C0C0'),
                       ('gtip','#32CD32'), ('ghalf','#008000'),
                       ('cluster','#87CEEB'), ('pink','#FF00FF'),
                       ('bloom','#FFFF00'), ('petalfall','#FF0000'),
                       ('fruit','#A0522D') )

APPLE_STAGE_NAMES = ( ('dormant','Dormant'), ('stip','Silver Tip'),
                      ('gtip','Green Tip'), ('ghalf','1/2 inch Green'),
                      ('cluster','Tight Cluster'), ('pink','Pink Bud'),
                      ('bloom','Bloom'), ('petalfall','Petal Fall'),
                      ('fruit','Fruit Set') )
APPLE_STAGES = tuple([stage[0] for stage in APPLE_STAGE_NAMES])

APPLE_STAGE_LABELS = ( 'Dormant', 'Silver\nTip', 'Green\nTip', '1/2"\nGreen',
                       'Tight\nCluster', 'Pink Bud', 'Bloom', 'Petal\nFall' )

PROVENANCE_EMPTY_BASE = ('', '')
PROVENANCE_FORMATS_BASE = ['|S10', '|S20']
PROVENANCE_NAMES_BASE = ['obs_date', 'processed']

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

VARIETY = ConfigObject('variety', None)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance record configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('provenance', VARIETY, 'empty', 'formats', 'names')

# KILL
empty = [ -32768 for n in range(len(APPLE_KILL_PROBS)+1) ]
empty.insert(0, '') # obs date
empty.append('') # processed date
VARIETY.provenance.empty.kill = tuple(empty)
# one additional format for no kill (not in APPLE_KILL_PROBS)
formats = [ '<i8' for prob in range(len(APPLE_KILL_PROBS)+1) ]
formats.insert(0, '|S10') # obs date
formats.append('|S20') # processed time
VARIETY.provenance.formats.kill = formats
names = ['%d%%' % prob for prob in APPLE_KILL_PROBS]
VARIETY.provenance.names.kill = ['obs_date','no kill'] + names + ['processed',]

# STAGE
empty = [ -32768 for n in range(len(APPLE_STAGE_NAMES)-1) ]
empty.insert(0, '') # obs date
empty.append('') # processed date
VARIETY.provenance.empty.stage = tuple(empty)
# stage formats do not include 'fruit'
formats = [ '<i8' for stage in range(len(APPLE_STAGES)-1) ]
formats.insert(0, '|S10') # obs date
formats.append('|S20') # processed time
VARIETY.provenance.formats.stage = formats
# stage names do not include 'fruit'
names = ['obs_date',] + list(APPLE_STAGES[:-1]) + ['processed',]
VARIETY.provenance.names.stage = names

del empty, formats, names

# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - #
# Map Configurations
# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - #

VARIETY.map_types = ('gdd','kill','stage')

ConfigObject('maps', VARIETY, 'no_data', 'options', 'titles')

VARIETY.maps.min_gdd_to_post = 20.
VARIETY.maps.min_percent_nodes = 0.025

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Growing Degree Day
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


gdd_contours = (25,125,225,325,475,525,625,725)
#    (250,375,500,625,750,875,1000,1125,1250,1375,1500,1625,1750,1825,2000)
VARIETY.maps.no_data.gdd = { 'area_template':'NortheastNoData_template.png',
                             'create_with':'NortheastNoData_template.png',
                             'mask_coastlines':False,
                             'shape_resolution':None,
                             'title_x':0.45, 'title_y':0.78, 
                             'title_box_alpha':0.0,
                           }
VARIETY.maps.titles.gdd =\
'%(variety)s\nAccumulated Growing Degree Days'
VARIETY.maps.options.gdd = { 'map_type':'gdd', 'area':'northeast',
                             'area_template':'NortheastEmpty_template.png',
                             'mask_coastlines':False,
                             'shape_resolution':None,
                             'colorbar':True, 'cmap':'jet',
                             'contourbounds':gdd_contours,
                             'title_x':0.45, 'title_y':0.78, 
                             #'titleyoffset':0.125, 'title_box_alpha':0.0,
                             'title_box_alpha':0.0,
                           }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# kill probability
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

kill_name_map = [ (indx,'%d%%' % level)
                  for indx,level in enumerate(APPLE_KILL_PROBS,start=1) ]
kill_name_map.insert(0, (0, 'no kill'))
VARIETY.kill_name_map = OrderedDict(tuple(kill_name_map))
VARIETY.kill_probabilities = APPLE_KILL_PROBS

kill_map_colors = tuple([kill[1] for kill in APPLE_KILL_COLORS])
kill_color_key = tuple([kill[0] for kill in APPLE_KILL_COLORS])
kill_indexes = tuple(range(len(APPLE_KILL_COLORS)+1,1))

VARIETY.maps.no_data.kill = { 'area_template':'NortheastNoData_template.png',
                              'create_with':'NortheastNoData_template.png',
                              'mask_coastlines':False,
                              'shape_resolution':None,
                              'title_x':0.45, 'title_y':0.78, 
                              'title_box_alpha':0.0,
                            }
VARIETY.maps.options.kill = { 'map_type':'kill', 'area':'northeast',
                              'area_template':'NortheastEmpty_template.png',
                              'mask_coastlines':False,
                              'shape_resolution':None,
                              'colorbar':True,
                              'colors':kill_map_colors,
                              'cbarsettings':[0.27, 0.08, 0.50, 0.04],
                              'cbarlabelsize':8,
                              'marker':'o', 'marker_size':5,
                              'contourbounds':APPLE_KILL_PROBS,
                              'markercolors':kill_map_colors,
                              'keylabels':kill_color_key,
                              'extend':'neither',
                              'title_x':0.45, 'title_y':0.78, 
                              #'titlexoffset':0.15, 'titleyoffset':0.125, 
                              'title_box_alpha':0.0,
                              'linewidths':0,
                            }
VARIETY.maps.titles.kill = '%(variety)s\nKill Probability'

del kill_color_key, kill_map_colors, kill_indexes
del kill_name_map

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# chill mask
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

VARIETY.maps.no_data.mask = { 'area_template':'NortheastNoData_template.png',
                              'create_with':'NortheastNoData_template.png',
                              'mask_coastlines':False,
                              'shape_resolution':None,
                              'title_x':0.45, 'title_y':0.78, 
                              'title_box_alpha':0.0,
                            }
VARIETY.maps.options.mask = { 'map_type':'mask', 'area':'northeast',
                              'area_template':'NortheastEmpty_template.png',
                              'mask_coastlines':False,
                              'shape_resolution':None,
                              'colorbar':False,
                              'marker':'+', 'marker_size':3,
                              'markercolors':('r','o','b'),
                              'extend':'neither',
                              'title_x':0.45, 'title_y':0.78, 
                              #'titlexoffset':0.15, 'titleyoffset':0.125, 
                              'title_box_alpha':0.0,
                              'linewidths':0,
                            }
VARIETY.maps.titles.mask = '%(variety)s\nChill Mask'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# phenological stage
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

stage_name_map = OrderedDict(APPLE_STAGE_NAMES)
VARIETY.stage_name_map = stage_name_map

stage_color_map = OrderedDict(APPLE_STAGE_COLORS)
VARIETY.stage_color_map = stage_color_map

stage_contours = list(N.arange(0, len(stage_color_map), 1))
#stage_contours.insert(0, 0)
stage_map_colors = tuple([color for color in stage_color_map.values()[:-1]])

VARIETY.maps.no_data.stage = { 'area_template':'NortheastDormant_template.png',
                               'create_with':'NortheastDormant_template.png',
                               'mask_coastlines':False,
                               'shape_resolution':None,
                               #'draw_map_border':False, 'logo':None,
                               'title_x':0.45, 'title_y': 0.78,
                               'title_va':'top', 'title_box_alpha':0.0,
                               'title_box_alpha':0.0,
                             }
VARIETY.maps.options.stage = { 'map_type':'stage', 'area':'northeast',
                               'area_template':'NortheastEmpty_template.png',
                               'mask_coastlines':False,
                               'shape_resolution':None,
                               'colorbar':True,
                               'colors':stage_map_colors,
                               # cbar @ [left, bottom, width, height]
                               'cbarsettings':[0.13, 0.08, .76, 0.04],
                               'cbarlabelsize':8,
                               'cbarfontweight':'bold',
                               'marker':'o', 'marker_size':3,
                               'markercolors':stage_map_colors,
                               'contourbounds':stage_contours,
                               'keylabels':APPLE_STAGE_LABELS,
                               'extend':'neither',
                               'title_x':0.45, 'title_y':0.78, 
                               'title_va':'top', 'title_box_alpha':0.0,
                               'title_box_alpha':0.0,
                               'linewidths':0,
                             }
VARIETY.maps.titles.stage = '%(variety)s\nPhenological Stages'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# plot options configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

ConfigObject('plots', VARIETY, 'options', 'titles')

mint_options = {'color':'b', 'linestyle':'-', 'linewidth':2, 'label':'Min Temp'}
stage_options = { 'color':'k', 'linestyle':':', 'markersize':3, 'linewidth':3,
                  'label':'Current Stage' }
VARIETY.plots.options.kill_at_stage = { 'mint':mint_options,
                                        'stage':stage_options }

del mint_options, stage_options

def hardtVsTempTimespan(start_date, end_date):
    return '%s thru %s' % (start_date.strftime('%B %d, %Y'),
                           end_date.strftime('%B %d, %Y'))

VARIETY.plots.options.hardiness_vs_temp = {
                    'plot_group':'kill.@.%(location)s',
                    'plot_key':'Kill-vs-Hardiness-@-%(location)s',
                    'figsize':(8,6),
                    'temp_units':'F',
                    'timeSpan':hardtVsTempTimespan,
                    'colorbar':True,
                    'colors':stage_map_colors[1:],
                    # cbar @ [left, bottom, width, height]
                    'cbar_alpha':0.15,
                    #'cbarsettings':[0.13, 0.08, .76, 0.04],
                    'cbarsettings':[0.125, 0.09, .775, 0.05],
                    'cbarlabelsize':8,
                    'cbarfontweight':'bold',
                    'keylabels':APPLE_STAGE_LABELS[1:],
                    'extend':'neither',
                    }

VARIETY.plots.titles.hardiness_vs_temp = \
      '%(variety)s at %(location)s\nModelled Hardiness Temp vs Observed Temp'

del stage_color_map, stage_contours, stage_map_colors

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from .phenology import AppleVariety
from .varieties import APPLES

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# apple cultivar configurations
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

VARIETIES = ConfigObject('varieties', None,)

for name, apple in APPLES.items():
    variety = AppleVariety(name, None, apple['phenology'], apple['kill_temps'],
                           APPLE_KILL_PROBS, APPLE_STAGE_NAMES,
                           apple['min_chill_units'], apple['description'])
    VARIETIES.addChild(variety)

VARIETIES.build = ('empire','mac_geneva','red_delicious')
