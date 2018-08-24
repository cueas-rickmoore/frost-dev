
import numpy as N

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TOOLCFG = ConfigObject('tool', None, 'dirpaths', 'filenames')

TOOLCFG.dirpaths = {
        'root': {'dev': '/Volumes/Transport/data/app_data',
                 'tool': '/Volumes/data/app_data'}, 
        'data': {'frost': 'frost/grid/%(year)d/%(subdir)s',
                 'shared': 'shared/grid/%(region)s/%(source)s/%(subdir)s',
                 'tool': 'frapple/build/%(region)s/%(source)s/%(subdir)s'},
        }

TOOLCFG.filenames = {
        'frost': {'chill':'%(year)d-Frost-Apple-Chill.h5',
                  'tempext':'%(year)d_temperatures.h5',
                  'variety':'%(year)d-Frost-Apple-%(variety)s.h5',
                 },
        'shared': {'tempext':'%(year)d-%(source)s-%(region)s-Daily.h5',},
        'tool': {'chill':'%(year)d-Frost-Apple-Chill.h5',
                 'tempext':'%(year)d-Frost-Temperatures.h5',
                 'variety':'%(year)d-Frost-Apple-%(variety)s.h5',
                },
        }

TOOLCFG.datasets = {'data':{'acis_grid':3,
                            'node_spacing':0.0416667,
                            'search_radius':0.03125,
                            'source':'ACIS-HiRes',
                            'source_detail':'ACIS HiRes grid 3'},
                    'lat':{'description':'Latitude','missing':N.nan,
                           'units':'degrees', 'view':'lat,lon'},
                    'lon':{'description':'Longitude','missing':N.nan,
                           'units':'degrees', 'view':'lat,lon'},
                    'provenance':{'acis_grid':3, 'source':'ACIS-HiRes',
                                  'source_detail':'ACIS HiRes grid 3',
                                  'period':'date','scope':'season',
                                  'view':'t'},
                    'time':{'period':'date','scope':'season','view':'tyx'},
                   }

TOOLCFG.fileattrs= {'data_bbox':'-82.75,37.125,-66.83,47.70',
                    'node_spacing':0.0416667,
                    'scope':'season',
                    'search_radius':0.03125, 
                    'source':'ACIS HiRes grid 3',
                   }

TOOLCFG.project = {'end_day':(6,30),
                   'gdd_thresholds':((43,86),),
                   'models':('carolina',),
                   'region':'NE',
                   'source':'acis',
                   'start_day':(9,15),
                   'varieties':('empire','mac_geneva','red_delicious'),
                  }


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.seasonal.config import CFGBASE
CFGBASE.regions.copy('regions', TOOLCFG)
CFGBASE.sources.copy('sources', TOOLCFG)
del CFGBASE

