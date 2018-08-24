#!/Users/rem63/venvs/frost/bin/python

import os, sys
import re
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.options import stringToTuple
from atmosci.utils.timeutils import daysInYear, lastDayOfMonth
from atmosci.utils.timeutils import timeSpanToIntervals

from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def copyAttrs(source_obj, dest_obj):
    attrs = dict(source_obj.attrs)
    for name, value in attrs.items():
        dest_obj.attrs[name] = value

def copyDataset(name, source_obj, dest_obj, **kwargs):
    print 'copying dataset', name
    shape = source_obj.shape
    if source_obj.chunks is not None:
        compression = kwargs.get('compression','gzip')
        dataset = dest_obj.create_dataset(name, data=source_obj.value,
                                          chunks=source_obj.chunks,
                                          compression=source_obj.compression,
                                          compression_opts=source_obj.compression_opts,
                                          fletcher32=source_obj.fletcher32)
    else:
        dataset = dest_obj.create_dataset(name, data=source_obj.value)
    copyAttrs(source_obj, dataset)
    return dataset

def copyGroup(name, source_obj, dest_obj, **kwargs):
    print 'copying group', name
    group = dest_obj.create_group(name)
    for name in source_obj.keys():
        copyObject(name, source_obj[name], group, **kwargs)
    copyAttrs(source_obj, group)
    return group

def copyObject(name, source_obj, dest_obj, **kwargs):
    if isinstance(source_obj, h5py.Dataset):
        copyDataset(name, source_obj, dest_obj, **kwargs)
    else: # is a group
        copyGroup(name, source_obj, dest_obj, **kwargs)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser, OptionValueError
parser = OptionParser()

parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
test_run = options.test_run
test_file = debug | test_run
verbose = options.verbose or debug

variety_name = args[0]
target_year = int(args[1])

factory = AppleGridFactory()

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get the chill data file manger for the target year ... IT MUST ALREADY EXIST


# need to save the indexes where NANs occur
mint_nan_indexes = N.where(N.isnan(mint))

# get a Variety grid manager for the target year
old_manager = \
factory.getVarietyGridManager(target_year, variety_name, 'a', test_run)
models = [name.lower() for name in old_manager.file_chill_models]
gdd_thresholds = old_manager.gddThresholds()

new_manager = \
factory.newVarietyGridManager(target_year, variety_name, models, 
                              gdd_thresholds, old_manager.search_bbox,
                              old_manager.acis_grid, True)

def copyTemp(temp_type, new_manager, old_manager, old_prov_name):
    old_temp_dataset = old_manager.getDataset(temp_type)
    old_prov_dataset = old_manager.getDataset(old_prov_name)

    new_temp_dataset = new_manager.getDataset(temp_type)
    new_temp_dataset.attrs['created'] = old_temp_dataset.attrs['created']
    new_prov_dataset = new_manager.getDataset('%s_provenance' %temp_type)
    new_prov_dataset.attrs['created'] = old_temp_dataset.attrs['created']

    for day in range(old_temp_dataset.shape[0]):
        data = old_temp_dataset[day][:,:]
        dates = old_prov_dataset[day]
        record = [ dates.obs_date, dates.processed
                   int(N.nanmin(data)), int(N.nanmax(data)),
                   'acis' ]
        new_prov_dataset[day] = \
        N.rec.fromrecords(record, TEMP_PROVENANCE_TYPE, (1,))

for model in models:
    for lo_gdd_th, hi_gdd_th in gdd_thresholds:



# save the temperature grid to the variety grid file
variety_manager.updateDataset('mint', mint, start_date)
variety_manager.close()
if verbose:
    print 'Min Temp @ in degrees F node[%d,%d] :' % midpoint
    if end_date is None: print mint[y,x]
    else:    print mint[:,y,x]

# make sure managers can read their data files
chill_manager.open('r')
variety_manager.open('r')

# get variety specific phenology factors
kill_levels = variety_manager.kill_levels
kill_temps = variety_manager.kill_temps
stage_thresholds = variety_manager.stage_thresholds

# estimate GDD accumulation, stage and kill probability for this variety
for model_name in models:
    proper_name = chill_manager.properName(model_name)
    accumulation_factor = chill_manager.gddAccumulationFactor(model_name)

    # get the Chill accumulation
    accumulated_chill = \
    chill_manager.getChillData(model_name, 'accumulated',
                               start_date=start_date, end_date=end_date)

    #  loop trough all GDD thresholds
    gdd_thresholds = getGddThresholds(options, chill_manager)
    for lo_gdd_th, hi_gdd_th in gdd_thresholds:
        # get dialy GDD from the chill grid file
        daily_gdd = \
        chill_manager.getGdd(lo_gdd_th, hi_gdd_th, 'daily', start_date, end_date)

        # calculuate accumulated GDD from daily gdd
        # let GDD manger get accumulated GDD for previous day
        variety_manager.open('r')

        # get previously accumulatedg GDD
        accumulated_gdd, chill_mask =\
        variety_manager.accumulateGdd(model_name, lo_gdd_th, hi_gdd_th,
                                      start_date, accumulated_chill,
                                      daily_gdd)
        # no longer need grid for daily GDD
        del daily_gdd

        if verbose:
            print '\npositve accumulation',
            print accumulated_gdd[N.where(accumulated_gdd > 0)]

        if update_db:
            variety_manager.open('a')
            variety_manager.updateGdd(model_name, lo_gdd_th, hi_gdd_th,
                                      accumulated_gdd, chill_mask, start_date)
            variety_manager.close()

        # generate stage grid from accumulated GDD
        stage_grid = variety_manager.gddToStages(accumulated_gdd)
        # no longer need grid for accumulated GDD
        del accumulated_gdd

        if verbose:
            print '\nstage set to',
            print stage_grid[N.where(stage_grid > 0)]

        if update_db:
            variety_manager.open('a')
            variety_manager.updateStage(model_name, lo_gdd_th, hi_gdd_th,
                                    stage_grid, start_date)
            variety_manager.close()
    
        # estimate kill probability from stages and predicted mint
        kill_grid = variety_manager.estimateKill(stage_grid, mint)
        # no longer need stage grid
        del stage_grid

        if verbose:
            print '\nkill probability',
            print kill_grid[N.where(kill_grid > 0)]

        if update_db:
            variety_manager.open('a')
            variety_manager.updateKill(model_name, lo_gdd_th, hi_gdd_th, kill_grid,
                                  start_date)
            variety_manager.close()
        # no longer need grid for kill
        del kill_grid

# turn annoying numpy warnings back on
warnings.resetwarnings()
