
from collections import OrderedDict

import numpy as N
from scipy import stats as SS

from atmosci.utils.config import ConfigObject
from atmosci.utils.timeutils import asAcisQueryDate


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DORMANCY_STAGES = OrderedDict( ( ('para','paradormancy'),
                                 ('endo','endodormancy'),
                                 ('eco','ecodormancy'),
                              ) )

GRAPE_STAGES = ('woolly','break','leaf1','leaf2','leaf4','petalfall')

GRAPE_STAGE_COLORS = ( ('dormant','#B0C4DE'), ('woolly','#D2B48C'),
                       ('break','#FFD700'), ('leaf1','#90EE90'),
                       ('leaf2','#3CB371'), ('leaf4','#008000'),
                       ('fruit','#9932CC') )

GRAPE_STAGE_NAMES = ( ('dormant','Dormant'), ('woolly','Wooly Bud'),
                      ('break','Bud Break'), ('leaf1','1st Leaf'),
                      ('leaf2','2nd Leaf'), ('leaf4','4th Leaf'),
                      ('fruit','Fruit Set') )

GRAPE_KILL_LEVELS = ( ('(diff >= 0) & (diff <= 0.5)', 'Low', '#1E90FF'),
                      ('(diff > 0.5) & (diff < 2)', 'Medium', '#FFD700'),
                      ('diff >= 2', 'High', '#FF0000') )

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

GRAPE = ConfigObject('grape', None, 'chill', 'datasets', 'descriptons',
                     'dormancy', 'groups', 'packers', 'unpackers', 'variety')
GRAPE.end_day = (5,15) 
GRAPE.start_day = (9,15)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# chill group configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def chillThresholdString(group_name, variety):
    if group_name == 'common': return('threshold', 10.)
    elif group_name == 'dormancy':
        endo = variety.stage_thresholds.endo
        eco = variety.stage_thresholds.eco
        thresholds = 'endodormancy=%-4.2f, ecodormancy=%-4.2f' % (endo,eco)
        return 'thresholds', thresholds
GRAPE.chill.getThresholdString = chillThresholdString
GRAPE.chill.common_threshold = 10.

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# dormancy stage/index mapping
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Paradormancy : when growth is regulated by physiological factors originating
#                outside the bud
# Endodormancy : when inhibition of growth originates within the bud meristem
#                and chilling is required before growth can resume
# Ecodormancy : when one or more environmental factors are inadequate to
#               support growth.
GRAPE.dormancy.stages = DORMANCY_STAGES

def dormancyIndexFromStage(stage):
    return {'para':0, 'endo':1,'eco':2}.get(stage, None)
GRAPE.dormancy.indexFromStage = dormancyIndexFromStage

def dormancyStageFromIndex(indx):
    return {0:'para',1:'endo',2:'eco'}.get(indx, None)
GRAPE.dormancy.stageFromIndex = dormancyStageFromIndex

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# group and dataset definitions 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# acclimation/deacclimation
datasets = { 'factor' : { 'units':'C*100', 'dtype':'<i4', 'missing':65536,
                          'description':'Acclimation' }, }
GRAPE.groups.acclimation = { 'datasets':datasets,
             'description':'Degree of acclimation to cold temps', }

datasets = { 'factor' : { 'units':'C*100', 'dtype':'<i4', 'missing':65536,
                          'description':'Deacclimation'}, }
GRAPE.groups.deacclimation = { 'datasets':datasets,
      'description':'Loss of acclimation to cold temps due to occurrence of warm temperatures',
      }

# chill
GRAPE.groups.chill = { 
      'common': { 'description':'Common (base 10C) Chilling Degree Days', },
      'dormancy': { 'description':'Stage-dependent Chilling Degree Days', }
      }
GRAPE.groups.chill.common.datasets = {
        'accumulated' : {'units':'DD*100', 'dtype':'<i4', 'missing':65536,
                         'description':'Accumulated common chill',
                         'threshold':10.},
        'daily' : {'units':'DD*100', 'dtype':'<i4', 'missing':65536,
                   'description':'Daily common chill', 'threshold':10.},
      }
GRAPE.groups.chill.dormancy.datasets = {
        'accumulated' : {'units':'DD*100', 'dtype':'<i4', 'missing':65536,
                         'description':'Accumulated stage-dependent chill'},
        'daily' : {'units':'DD*100', 'dtype':'<i4', 'missing':65536,
                    'description':'Daily stage-dependent chill'},
        }

# dormancy stage
ds_attrs = { 'dtype':'<i2', 'missing':-999, 'description':'Bud dormancy stage' }
stages = [ ]
for indx, description in enumerate(DORMANCY_STAGES.values()):
    stages.append('%s=%d' % (description, indx))
ds_attrs['stages'] = ', '.join(stages)
ds_attrs['units'] = 'index from 0 to %d' % indx
GRAPE.groups.dormancy = { 'datasets':{'stage' : ds_attrs},
                          'description':'Bud Dormacy Stage' }
del ds_attrs

# growing degree days
datasets = { 'accumulated' : {'units':'DD*100', 'dtype':'<i4', 'missing':65536,
                              'description':'Accumulated stage-dependent GDD'},
             'daily' : {'units':'DD*100', 'dtype':'<i4', 'missing':65536,
                        'description':'Daily stage-dependent GDD'}, }
GRAPE.groups.gdd = { 'datasets':datasets,
                     'description':'Stage-dependent Growing Degree Days', }

# hardiness temperaure
datasets = { 'temp' : { 'units':'C*100', 'dtype':'<i4', 'missing':65536,
                        'description':'Estimated minimum hardiness temperature'}, }
GRAPE.groups.hardiness = { 'datasets':datasets,
      'description':'Estimated Cold Hardiness',
      }

del datasets

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance dataset configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
PROVENANCE = ConfigObject('provenance', GRAPE, 'empty', 'formats',
                          'generators', 'names')

# Dormancy Stage
num_stages = len(GRAPE.dormancy.stages.attrs) - 1

def dormancyProvenanceGenerator(date, timestamp, data):
    provenance = [asAcisQueryDate(date),]
    for stage in range(1,num_stages+1):
        provenance.append(len(N.where(data==stage)[0]))
    provenance.append(timestamp)
    return tuple(provenance)

GRAPE.provenance.empty.dormancy =\
      ('',) + tuple([-32768 for stage in range(num_stages)]) + ('',)
GRAPE.provenance.formats.dormancy =\
      ['|S10',] + ['<i8' for stage in range(num_stages)] + ['|S20',]
GRAPE.provenance.generators.dormancy = dormancyProvenanceGenerator
GRAPE.provenance.names.dormancy =\
      ['date',] + list(GRAPE.dormancy.stages.attr_names[1:]) + ['processed',]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# data packers
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def packDormancy(data, missing=-999, dtype='<i2'):
    if data.dtype.kind == 'f': nan_indexes = N.where(N.isnan(data))
    packed = data.astype(dtype)
    if data.dtype.kind == 'f' and len(nan_indexes[0]) > 0:
        packed[nan_indexes] = missing
    return packed
GRAPE.packers.dormancy = packDormancy

def packFloat(data, missing=65536, dtype='<i4', multiplier=100.):
    nan_indexes = N.where(N.isnan(data))
    if multiplier is None: packed = data
    else: packed = data * multiplier
    packed = packed.astype(dtype)
    if len(nan_indexes[0]) > 0: packed[nan_indexes] = missing
    return packed
GRAPE.packers.acclim = packFloat
GRAPE.packers.chill = packFloat
GRAPE.packers.gdd = packFloat
GRAPE.packers.hardiness = packFloat

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# data unpackers
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def unpackDormancy(raw_data):
    return raw_data
GRAPE.unpackers.dormancy = unpackDormancy

def unpackInt(raw_data, missing=65536, multiplier=100.):
    if missing > 0: nan_indexes = N.where(raw_data >= missing)
    else: nan_indexes = N.where(raw_data <= missing)
    data = raw_data.astype(float)
    if len(nan_indexes[0]) > 0: data[nan_indexes] = N.nan
    if multiplier is not None:
        data = data / multiplier
    return data

GRAPE.unpackers.acclim = unpackInt
GRAPE.unpackers.chill = unpackInt
GRAPE.unpackers.gdd = unpackInt
GRAPE.unpackers.hardiness = unpackInt

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# map options configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('maps', GRAPE, 'no_data', 'options', 'titles')
GRAPE.maps.options.gdd = { 'map_type':'gdd', 'area':'northeast',
                          'colorbar':True, 'cmap':'jet',
                          'titleyoffset':0.175, 'title_box_alpha':0.0,
                        }

GRAPE.maps.titles.gdd=\
'%(variety)s\nCumulative GDD (%(thresholds)s)\n%(model)s'


# contour bounds in degrees F (~ -26.1 to -1.1 C)
hardiness_contour_bounds = [-25. + (n * 2.5) for n in range(23)]
GRAPE.maps.options.hardiness = { 'map_type':'hardiness',
                   'area':'northeast',
                   'area_template':'NortheastEmpty_template.png',
                   'mask_coastlines':False,
                   'shape_resolution':None,
                   'cmap':'jet',
                   'colorbar':True,
                   'contourbounds':hardiness_contour_bounds,
                   # cbar @ [left, bottom, width, height]
                   'cbarsettings': [0.15, 0.11, 0.7, 0.02], 
                   'extend':'both',
                   'ticks':(-25.,-15.,-7.5,0.,7.5,15.,22.5,30.),
                   'title_x':0.45, 'title_y':0.78, 
                   'title_va':'top', 'title_box_alpha':0.0,
                   'title_box_alpha':0.0,
                   }

GRAPE.maps.titles.hardiness = \
    u"%(variety)s\nModeled Hardiness Temperature (%(units)s)"

GRAPE.maps.no_data.kill = { 'area_template':'NortheastEmpty_template.png',
                            'create_with':'NortheastEmpty_template.png',
                            'mask_coastlines':False,
                            'shape_resolution':None,
                            'title_x':0.45, 'title_y':0.78, 
                            'title_box_alpha':0.0,
                            }
where_potential, kill_map_labels, kill_map_colors = zip(*GRAPE_KILL_LEVELS)
GRAPE.maps.options.kill = { 'map_type':'kill', 'area':'northeast',
                            'area_template':'NortheastEmpty_template.png',
                            'mask_coastlines':False,
                            'shape_resolution':None,
                            'colorbar':True,
                            'colors':kill_map_colors,
                            'cbarsettings':[0.27, 0.08, 0.50, 0.04],
                            'cbarlabelsize':8,
                            'marker':'o', 'marker_size':5,
                            'markercolors':kill_map_colors,
                            'keylabels':kill_map_labels,
                            'extend':'neither',
                            'title_x':0.45, 'title_y':0.78, 
                            #'titlexoffset':0.15, 'titleyoffset':0.125, 
                            'title_box_alpha':0.0,
                            'linewidths':0,
                            'where_potential':where_potential,
                          }
GRAPE.maps.titles.kill = '%(variety)s\nBud Injury Potential'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# plot options configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('plots', GRAPE, 'no_data', 'options', 'titles')

def hardtVsTempTimespan(start_date, end_date):
    return '%s thru %s' % (start_date.strftime('%B %d, %Y'),
                           end_date.strftime('%B %d, %Y'))

GRAPE.plots.options.hardiness_vs_temp = {
                    'plot_group':'kill.@.%(location)s',
                    'plot_key':'Kill-vs-Temp-@-%(location)s',
                    'coords':(-76.5,42.45),
                    'figsize':(8,8),
                    'location':'Geneva, NY',
                    'temp_limits':(-30.,70.),
                    'temp_units':'F',
                    'timeSpan':hardtVsTempTimespan,
                    }

GRAPE.plots.titles.hardiness_vs_temp = \
      '%(variety)s at %(location)s\nModelled Hardiness Temp vs Observed Temp'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# graphics publishing configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('publish', GRAPE, 'anim', 'maps', 'plots')

animpub_template = \
'\nPublished %(variety)s %(group)s.%(key)s animation for %(date)s to :\n%(filepath)s'
GRAPE.publish.anim = (
      { 'group':'hardiness', 'key':'temp', 'msg':animpub_template },
      { 'group':'kill', 'key':'potential', 'msg':animpub_template },
      )

mappub_template = \
'\nPublished %(variety)s %(group)s.%(key)s map for %(date)s to :\n%(filepath)s'
GRAPE.publish.maps = (
      { 'group':'hardiness', 'key':'temp', 'msg':mappub_template },
      { 'group':'kill', 'key':'potential', 'msg':mappub_template },
      )

plotpub_template = \
'\nPublished %(variety)s %(key)s plot for %(date)s to :\n%(filepath)s'
GRAPE.publish.plots = (
      { 'group':'kill.@.GenevaNY', 'key':'Kill-vs-Temp-@-Geneva-NY',
        'msg':plotpub_template },
      )

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# grape variety configurations
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

from frost.grape.phenology import GrapeVariety
from frost.grape.varieties import PHENOLOGY, GRAPES

VARIETIES = ConfigObject('varieties', GRAPE)

for grape in GRAPES:
    cultivar = grape['cultivar']
    variety = GrapeVariety(grape['name'], None, grape['description'],
                      cultivar, PHENOLOGY[cultivar], grape['hardiness'],
                      grape['ecodormancy_threshold'], grape['acclimation_rate'],
                      grape['deacclimation_rate'], grape['stage_thresholds'],
                      grape['theta'])
    VARIETIES.addChild(variety)

