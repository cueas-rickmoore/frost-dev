
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def generateStageGrid(model, variety, chill_manager, gdd_manager):
    # chill date is earliest date that chill threshold was a
    chill_threshold = variety.chill
    chill_date = chill_manager.chillThresholdDate(model, chill_threshold)
    if chill_date is None: # chill threshold not reached
        shape = self.getModelDatasetShape(model_name, 'accumulated')
        dormant = N.zeros(shape[1:], dtype=float)
        return None, dormant # all nodes at dormant stage

    # start 1 day before chill date so that there will be an initial
    # zero gdd acumulation
    start_date = chill_date - ONE_DAY

    # get chill model data and find the indexes of all nodes where the chill
    # threshold has been reached
    chill = chill_manager.getModelData(model, 'accumulated',
                                       start_date=start_date)
    chill[N.isnan(chill)] = 0 # eliminates iterference of nans in N.where
    indexes = N.where(chill >= chill_threshold) # indexes where GDD is valid

    # initialize GDD accumulation grid to be all zeros
    gdd = N.zeros(chill.shape, dtype=float)
    del chill

    # get the daily GDD for the nodes in indexes and insert them into the
    # GDD accumulation array
    dataset_name = 'daily.%s.data' % gdd_manager.listGroupsIn('daily')[0]
    gdd[indexes] = gdd_manager.getDataSince(dataset_name, start_date)[indexes]
    # calculate the cumulative accumulation for each day at each grid node
    gdd = N.cumsum(gdd, axis=0)

    # use the accumulated GDD to determine the phenology stage at each grid node
    thresholds = tuple(variety.phenology.values())
    stages = N.zeros(gdd.shape, dtype=float)
    for indx in range(1,len(thresholds),1):
        indexes = N.where((gdd >= thresholds[indx-1]) & (gdd < thresholds[indx]))
        stages[indexes] = float(indx)
    stages[N.where(gdd >= thresholds[-1])] = float(len(thresholds))

    return start_date, stages

