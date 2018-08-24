#!/Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from frost.crops import crops
from frost.factory import FrostDataFactory
from frost.stage import generateStageGrid
from frost.maps.stage import drawStageMap

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
# map target date
if len(args) == 5:
    target_date = datetime(int(args[2]), int(args[3]), int(args[4]))
else: target_date = datetime.now()

# determine the date when chill threshold was first reached at any grid node
factory = FrostDataFactory()
chill_manager = factory.getDataManager('chill', target_date.year)
gdd_manager = factory.getDataManager('gdd', target_date.year)

start_date, stage_grid =\
generateStageGrid(model, variety, chill_manager, gdd_manager)
if start_date is None:
    errmsg = 'Chill hour threshold has not been met for %s using %s chill model'
    print errmsg % (variety.description, model.title())
    os._exit(99)

indx = (target_date - start_date).days
drawStageMap(target_date, model.title(), variety, stage_grid[indx],
             gdd_manager.lons, gdd_manager.lats, { })

