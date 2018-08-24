
import os, sys
import numpy as N
from scipy import stats as SS

from atmosci.utils.config import ConfigObject, OrderedConfigObject
from atmosci.utils.timeutils import asAcisQueryDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CONFIG = ConfigObject('config', None, 'crops', 'packers', 'unpackers')
CONFIG.animate_cmd_path = '/opt/ImageMagick/bin/convert'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

PROVENANCE = ConfigObject('provenance', CONFIG, 'empty', 'formats',
                          'generators', 'names')

if 'win32' in sys.platform:
    CONFIG.webapps_dir = 'C:\\Work\\Frost\\web_apps\\frost'
    CONFIG.working_dir = 'C:\\Work\\Frost\\app_data\\frost'
else:
    CONFIG.webapps_dir = '/Volumes/data/web_apps/frost'
    CONFIG.working_dir = '/Volumes/data/app_data/frost'

# global defaults
DEFAULT = ConfigObject('default', CONFIG, 'bbox', 'grid', 'missing', 'source')
CONFIG.default.bbox.data = "-82.75,37.125,-66.83,47.70"
CONFIG.default.bbox.maps = "-82.70,37.20,-66.90,47.60"
CONFIG.default.bbox.test = "-72.5,41.5,-71.5,42.5"
CONFIG.default.compression = 'gzip'
CONFIG.default.end_day = (6,30)
CONFIG.default.missing.float = N.nan
CONFIG.default.missing.int = 65535
CONFIG.default.missing.temp = -32768
CONFIG.default.start_day = (9,1)

# default to ACIS HiRes DEM 5k grid
CONFIG.default.data_source = 'ACIS - Applied Climate Information System'
CONFIG.default.grid_type = 'ACIS 5 km'
CONFIG.default.acis_grid = 3
CONFIG.default.node_spacing = 0.0416667
# 0.125 is lat/lon increment for DEM 5k node spacing 
# so search radius is sqrt(2*(0.125**2) + a litle fudge
#CONFIG.default.node_search_radius = 0.18
CONFIG.default.node_search_radius = 0.25

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# global temparature dataset configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.default.source.forecast = 'NDFD - National Digital Forecast Database'
CONFIG.default.source.reported = 'ACIS - Applied Climate Information System'
CONFIG.default.temp_datasets = (('maxt','Maximum'),('mint','Minimum'))

def packTemps(data):
    nans = N.where(N.isnan(data))
    packed = data.astype('<i2')
    if len(nans[0]) > 0: packed[nans] = -32768
    return packed

def unpackTemps(raw_data):
    nans = N.where(raw_data < -32767)
    unpacked = raw_data.astype(float)
    if len(nans[0]) > 0: unpacked[nans] = N.nan
    return unpacked

CONFIG.packers.temp = packTemps
CONFIG.unpackers.temp = unpackTemps

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance statistics construction

# daily statistics only
def statsProvenanceGenerator(date, timestamp, data):
    return ( asAcisQueryDate(date), N.nanmin(data), N.nanmax(data),
             N.nanmean(data), SS.nanmedian(data,axis=None), timestamp )

CONFIG.provenance.empty.stats = ('',N.nan,N.nan,N.nan,N.nan,'')
CONFIG.provenance.formats.stats = ['|S10','f4','f4','f4','f4','|S20']
CONFIG.provenance.generators.stats = statsProvenanceGenerator
CONFIG.provenance.names.stats = ['date','min','max','mean','median','processed']

# daily stats plus accumulation stats
def accumStatsProvenanceGenerator(date, timestamp, data_1, data_2):
    return ( asAcisQueryDate(date), N.nanmin(data_1), N.nanmax(data_1),
             N.nanmean(data_1), SS.nanmedian(data_1,axis=None),
             N.nanmin(data_2), N.nanmax(data_2), N.nanmean(data_2),
             SS.nanmedian(data_2,axis=None), timestamp ) 

CONFIG.provenance.empty.accum = \
('',N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,'')
CONFIG.provenance.formats.accum = \
['|S10','f4','f4','f4','f4','f4','f4','f4','f4','|S20']
CONFIG.provenance.generators.accum = accumStatsProvenanceGenerator
CONFIG.provenance.names.accum = ['date','min','max','mean','median',
      'min accum','max accum', 'mean accum','median accum','processed']

# temperature
def tempProvenanceGenerator(date, timestamp, data):
    return ( asAcisQueryDate(date), N.nanmin(data), N.nanmax(data), 
             N.nanmean(data), SS.nanmedian(data,axis=None), timestamp )

CONFIG.provenance.empty.temp = ('',N.nan,N.nan,N.nan,N.nan,'')
CONFIG.provenance.formats.temp = ['|S10','f4','f4','f4','f4','|S20']
CONFIG.provenance.generators.temp = tempProvenanceGenerator
CONFIG.provenance.names.temp = ['date','min','max','avg','median','dowmloaded']

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# import APPLE crop configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

from frost.apple.config import APPLE
CONFIG.crops.addChild(APPLE.copy())
APPLE_FILES = ConfigObject('filenames', CONFIG.crops.apple, 'animation',
                           'data', 'maps', 'web_anim', 'web_maps')

APPLE_FILES.animation.chill = \
'%(date_str)s-Frost-Apple-%(model)s-%(map_type)s-Chill-animation.gif'
APPLE_FILES.animation.gdd = '%d-Frost-Apple-CDD.gif'
'%(date_str)s-Frost-Apple-%(map_type)s-GDD-animation.gif'
APPLE_FILES.animation.variety = \
'%(date_str)s-Frost-Apple-%(variety)s-%(map_type)s-animation.gif'

APPLE_FILES.data.chill = '%d-Frost-Apple-Chill.h5'
APPLE_FILES.data.gdd = '%d-Frost-Apple-Chill.h5'
APPLE_FILES.data.variety = '%d-Frost-Apple-%s.h5'

APPLE_FILES.maps.chill =\
'%(date_str)s-Frost-Apple-%(model)s-%(map_type)s-Chill.png'
APPLE_FILES.maps.gdd =\
'%(date_str)s-Frost-Apple-%(map_type)s-GDD.png'
APPLE_FILES.maps.variety =\
'%(date_str)s-Frost-Apple-%(variety)s-%(model)s-%(map_type)s.png'

APPLE_FILES.web_anim.chill = 'Frost-Apple-%(map_type)s-Chill.gif'
APPLE_FILES.web_anim.gdd = 'Frost-Apple-%(map_type)s-GDD.gif'
APPLE_FILES.web_anim.variety = 'Frost-Apple-%(variety)s-%(map_type)s.gif'

APPLE_FILES.web_maps.chill = 'Frost-Apple-%(map_type)s-Chill.png'
APPLE_FILES.web_maps.gdd = 'Frost-Apple-%(map_type)s-GDD.png'
APPLE_FILES.web_maps.variety = 'Frost-Apple-%(variety)s-%(map_type)s.png'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# import GRAPE crop configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

from frost.grape.config import GRAPE
CONFIG.crops.addChild(GRAPE.copy())

#CONFIG.crops.grape.varieties.build = ('cab_franc','chard','concord',
#                                      'lemberger','malbac','merlot',
#                                      'pin_gris','riesling','sauv_blanc',
#                                      'syrah')
CONFIG.crops.grape.varieties.build = ('cab_franc','concord','riesling')

GRAPE_FILES = ConfigObject('filenames', CONFIG.crops.grape, 'anim',
                            'data', 'maps', 'plots', 'web_graphic')

GRAPE_FILES.anim.variety = \
'%(year)s-Frost-Grape-%(variety)s-%(anim_key)s-animation.gif'
GRAPE_FILES.data.variety = '%d-Frost-Grape-%s.h5'
GRAPE_FILES.maps.variety = \
'%(date_str)s-Frost-Grape-%(variety)s-%(map_key)s.png'
GRAPE_FILES.plots.variety = \
'%(date_str)s-Frost-Grape-%(variety)s-%(plot_key)s.png'
GRAPE_FILES.web_graphic.variety = 'Frost-Grape-%(variety)s-%(keywords)s%(ext)s'

