#!/Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from frost.crops import crops
from frost.stage import generateStageGrid
from frost.maps.helpers import makeTitle
from frost.maps.stage import drawStageMap

from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from frost.maps.stage import MAP_OPTIONS, STAGE_COLORS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('-z', action='store_true', dest='test_run', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# chill model 
model = args[0]
# apple variety config
variety = eval('crops.apple.%s' % args[1])
stages = list(variety.phenology.stages)
# map target date
target_year = int(args[2])

# determine the date when chill threshold was first reached at any grid node
factory = FrostDataFactory()
chill_manager = factory.getDataManager('chill', target_year)
gdd_manager = factory.getDataManager('gdd', target_year)
lats = gdd_manager.lats
lons = gdd_manager.lons

start_date, stage_grid = generateStageGrid(model, variety, chill_manager,
                                           gdd_manager)
if start_date is None:
    errmsg = 'Chill hour threshold has not been met for %s using %s chill model'
    print errmsg % (variety.description, model.title())
    os._exit(99)

map_options = { }
contours = list(N.arange(1, len(stages), 1))
contours.insert(0, 0.)
map_options['contourbounds'] = contours
stages.insert(0,'dormant')
map_options['keylabels'] = stages
map_options['colors'] = tuple([STAGE_COLORS[stage] for stage in stages])
map_title = MAP_OPTIONS['title_template'] % (variety.description, model)

indx = 0
end_indx = stage_grid.shape[0]
while indx < end_indx:
    date = start_date + relativedelta(days=indx)
    map_options['title'] = map_title
    map_options['title2'] = date.strftime('%B %d, %Y')
    map_options['title'] = makeTitle(map_options, sdate=None, edate=None)
    drawStageMap(date, model.title(), variety, stage_grid[indx], lons, lats,
                 map_options)
    indx += 1

