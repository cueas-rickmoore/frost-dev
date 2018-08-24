#!/Users/rem63/venvs/frost/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from frost.crops import crops
from frost.factory import FrostDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('-a', action='store_true', dest='test_array', default=False)
parser.add_option('-g', action='store_true', dest='test_grid', default=False)
parser.add_option('-p', action='store_true', dest='test_point', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

target_year = int(args[0])
model = args[1]

factory = FrostDataFactory()


# get variety configuration
variety = eval('crops.apple.%s' % args[2])
chill_threshold = variety.chill
print 'finding earliest date where chill threshold =', chill_threshold

# determine the date when chill threshold was first reached at any grid node
manager = factory.getDataManager('chill', target_year)
chill_date = manager.chillThresholdDate(model, chill_threshold)
print model.title(), chill_date
# first date that data will be retrieved for ... 1 day before chill date
start_date = chill_date - ONE_DAY

# get chill model data and find the indexes of all nodes where the chill
# threshold has been reached
chill = manager.getModelData(model, 'accumulated', start_date=start_date)
print 'chill dataset', chill.shape
chill[N.isnan(chill)] = 0 # eliminates iterference of nans in N.where
indexes = N.where(chill >= chill_threshold) # indexes where GDD is valid

# initialize GDD accumulation grid to be all zeros
gdd = N.zeros(chill.shape, dtype=float)
del chill

# get the daily GDD for the nodes in indexes and insert them into the
# GDD accumulation array
manager = factory.getDataManager('gdd', target_year)
dataset_name = 'daily.%s.data' % manager.listGroupsIn('daily')[0]
gdd[indexes] = manager.getDataSince(dataset_name, start_date)[indexes]
# calculate the cumulative accumulation for each day at each grid node
gdd = N.cumsum(gdd, axis=0)

# use the accumulated GDD to determine the phenology stage at each grid node
stage = N.zeros(gdd.shape, dtype=int)
for indx, threshold in enumerate(variety.phenology.values()):
    stage[N.where(gdd > threshold)] = indx + 1

print '\n\n', stage[100:,125:129,190:195]

