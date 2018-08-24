
from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PROVENANCE_RECORD_TYPE = ( ('obs_date', '|S10'), ('processed', '|S20'), )
PROVENANCE_STATS = ( ('daily min','<i2'), ('daily max','<i2'),
                     ('daily avg','<i2'), ('accum min','<i2'),
                     ('accum max','<i2'), ('accum avg','<i2') )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# CHILL options configuration
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CHILL = ConfigObject('chill', None, 'carolina.accumulators', 
                     'dynamic.accumulators', 'threshold.accumulators',
                     'utah.accumulators')
CHILL.models = ('carolina','utah') # config.chill.listChildren()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance record configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

CHILL.provenance_empty = ('', '', -32768, -32768, -32768, -32768, -32768, -32768)
CHILL.provenance_type = PROVENANCE_RECORD_TYPE + PROVENANCE_STATS

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# CHILL model acummulators
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

from .carolina import accumulators
for key, Klass in accumulators.items():
    CHILL.carolina.accumulators[key] = Klass
CHILL.carolina.accumulation_factor = 1.0
CHILL.carolina.description = 'North Carolina Chilling Unit Model'

CHILL.dynamic.accumulation_factor = 1.0
CHILL.dynamic.description = 'Dynamic Chill Accumulation Model'

from .threshold import accumulators
for key, Klass in accumulators.items():
    CHILL.threshold.accumulators[key] = Klass
CHILL.threshold.accumulation_factor = 1.0
CHILL.threshold.description = 'Simple Temperature Threshold Chilling Model'

from .utah import accumulators
for key, Klass in accumulators.items():
    CHILL.utah.accumulators[key] = Klass
CHILL.utah.accumulation_factor = 1.0
CHILL.utah.description = 'Utah Chilling Unit Model'

def getActiveModels():
    return tuple([CHILL[model] for model in CHILL.models])
CHILL.getActiveModels = getActiveModels

# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - #
# Map Configurations
# - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - #
ConfigObject('maps', CHILL, 'no_data', 'options', 'titles')

# minimum percent of nodes with accumulated chill
CHILL.maps.min_percent_nodes = 0.025
CHILL.maps.min_chill_to_post = 100.

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# CHILL
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

#chill_contours = (250,375,500,625,750,875,1000,1125,1250,1375,1500,1625,1750,1825,2000)
#chill_contours = (250,500,750,1000,1250,1500,1750,2000)
chill_contours = tuple(range(200,1400,100))
CHILL.maps.no_data.accumulated = { 'area_template':'NortheastNoData_template.png',
                                   'create_with':'NortheastNoData_template.png',
                                   'title_x':0.45, 'title_y':0.78, 
                                   'title_va':'top', 'title_box_alpha':0.0,
                                   'title_box_alpha':0.0,
                                   'shape_resolution':None,
                                 }
CHILL.maps.options.accumulated = { 'map_type':'chill', 'area':'northeast',
                                   'area_template':'NortheastEmpty_template.png',
                                   'mask_coastlines':False,
                                   'shape_resolution':None,
                                   'colorbar':True, 'cmap':'jet_r',
                                   #'over_color':'#CD853F', # tan
                                   #'over_color':'#9370DB', # mdeium purple
                                   'over_color':'#9999FF', # lilac purple
                                   #'over_color':'#6A5ACD', # lilac purple
                                   #'vmin':250.,'vmax':2000,
                                   'contourbounds':chill_contours,
                                   'title_x':0.45, 'title_y':0.78, 
                                   'title_va':'top', 'title_box_alpha':0.0,
                                   'title_box_alpha':0.0,
                                 }
CHILL.maps.titles.accumulated = 'Accumulated Chill'
del chill_contours

CHILL.maps.no_data.gdd = { 'template':'NortheastNoData_template.png',
                           'create_with':'NortheastNoData_template.png',
                           'title_x':0.45, 'title_y':0.78, 
                           'title_va':'top', 'title_box_alpha':0.0,
                           'title_box_alpha':0.0,
                         }
CHILL.maps.options.gdd = { 'map_type':'gdd', 'area':'northeast',
                           'colorbar':True, 'cmap':'jet',
                           'title_x':0.45, 'title_y':0.78, 
                           'title_va':'top', 'title_box_alpha':0.0,
                           'title_box_alpha':0.0,
                         }
CHILL.maps.titles.gdd = '%(map_type)s Growing Degree Days'

CHILL.maps.options.temp = { 'map_type':'temp', 'area':'northeast',
                            'colorbar':True, 'cmap':'jet', 'autobounds': 20,
                            'title_x':0.45, 'title_y':0.78, 
                            'title_va':'top', 'title_box_alpha':0.0,
                            'title_box_alpha':0.0,
                          }

