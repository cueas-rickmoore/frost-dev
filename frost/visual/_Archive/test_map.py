#!/Users/rem63/venvs/frost/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from frost.maps.modularmap import filled_contour
from frost.maps.helpers import makeTitle

from frost.crops import crops
from frost.factory import FrostDataFactory

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
                #"inputfile": None,         # tab-delimited input file for dotmap or interpf
                #"numlevels": 8,            # number of contour levels
                #"grid": 3,                 # GridData grid id
                #"levelmult": None,         # contour bounds are multiples of this value (None = pick based on data)
                "shapelocation": MAPS_DIR,   # location of template or shapefiles (old basemap)
                #"metalocation": "/Users/"+user+"/BaseMapper/metadata/",     # location of saved metadata files
                "logo": "%s/PoweredbyACIS-rev2010-08.png" % MAPS_DIR,  # also available ...PoweredbyACIS_NRCC.jpg (False for no logo)
                "title": "Total Precipitation (inches)",
                "outputfile": "",
                "colorbar": True,          # whether or not to plot a colorbar
                #"colors": tuple(color names),
                # or "cmap": 'RdYlGn',
                "contourbounds": [-1, 0, 1, 2, 3, 4, 5, 6, 7],
                "cbarlabelsize": 8,                             # small is 8, large is 10
                "cbarsettings": [0.25, 0.11, 0.5, 0.02],        # small is [0.25, 0.11, 0.5, 0.02], large is [0.25, 0.06, 0.5, 0.03] -- [left, bottom, width, height]
                "cbarlabels": ['dormant','stip','grtip','ghalf','cluster','pink','bloom','petalfall'],
                }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('-a', action='store_true', dest='test_array', default=False)
parser.add_option('-g', action='store_true', dest='test_grid', default=False)
parser.add_option('-p', action='store_true', dest='test_point', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

map_title_template = '%s Phenology Stage, %s Model'
plot_file_template = '%s-%s-%s.png'

# chill model 
model = args[0]
# apple variety config
variety = eval('crops.apple.%s' % args[1])

# map target date
target_date = datetime(int(args[2]), int(args[3]), int(args[4]))

# determine the date when chill threshold was first reached at any grid node
factory = FrostDataFactory()
manager = factory.getDataManager('chill', target_date.year)

# chill date is earliest date that chill threshold was a
chill_threshold = variety.chill
chill_date = manager.chillThresholdDate(model, chill_threshold)
# first date that data is useful is 1 day before chill date
start_date = chill_date - ONE_DAY

# get chill model data and find the indexes of all nodes where the chill
# threshold has been reached
chill = manager.getModelData(model, 'accumulated', start_date=start_date)
chill[N.isnan(chill)] = 0 # eliminates iterference of nans in N.where
indexes = N.where(chill >= chill_threshold) # indexes where GDD is valid

# initialize GDD accumulation grid to be all zeros
gdd = N.zeros(chill.shape, dtype=float)
del chill

# get the daily GDD for the nodes in indexes and insert them into the
# GDD accumulation array
manager = factory.getDataManager('gdd', target_date.year)
dataset_name = 'daily.%s.data' % manager.listGroupsIn('daily')[0]
gdd[indexes] = manager.getDataSince(dataset_name, start_date)[indexes]
# calculate the cumulative accumulation for each day at each grid node
gdd = N.cumsum(gdd, axis=0)
indx = (target_date - start_date).days
last_indx = max(N.where(gdd == variety.phenology.bloom)[0]) + 3

# use the accumulated GDD to determine the phenology stage at each grid node
stage = N.zeros(gdd.shape, dtype=int)
for indx, threshold in enumerate(variety.phenology.values()):
    stage[N.where(gdd > threshold)] = indx + 1

# create the map title
MAP_OPTIONS['title'] = map_title_template % (variety.description, model.title())


MAP_OPTIONS['title2'] = target_date.strftime('%B %d, %Y')
MAP_OPTIONS['title'] = makeTitle(MAP_OPTIONS, sdate=None, edate=None)
MAP_OPTIONS['outputfile'] = plot_file_template % (target_date.strftime('%Y-%m-%d'),
                                                  variety.description.replace(' ','_'), model.title())
# create the map
indx = (target_date - start_date).days
filled_contour(gdd[indx], manager.lats, manager.lons, MAP_OPTIONS['contourbounds'], MAP_OPTIONS)

