#!/Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getGrapeVariety
from frost.apple.variety.manager import AppleVarietyGridManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-g', action='store_false', dest='update_gdd', default=True)
parser.add_option('-k', action='store_false', dest='update_kill', default=True)
parser.add_option('-n', action='store_false', dest='new_file', default=True)
parser.add_option('-t', action='store_false', dest='update_temp', default=True)
parser.add_option('-s', action='store_false', dest='update_stage', default=True)
parser.add_option('-v', action='store_true',  dest='verbose', default=False)
parser.add_option('-z', action='store_true',  dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
new_file = options.new_file
update_gdd = options.update_gdd
update_kill = options.update_kill
update_stage = options.update_stage
update_temp = options.update_temp
verbose = options.verbose or debug

target_year = int(args[0])

# apple variety config
variety = getGrapeVariety(args[1])

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get a chill data file manger
factory = AppleGridFactory()
from_manager = factory.getVarietyGridManager(target_year, variety.name, 'r')

acis_grid = from_manager.acis_grid
models = [name.lower() for name in from_manager.file_chill_models]
start_date = from_manager.start_date
end_date = from_manager.end_date
num_days = (end_date - start_date).days + 1

# get a manager for the restructured file
to_filepath = from_manager._hdf5_filepath.replace('.h5','.new.h5')
if new_file:
    to_manager =\
    AppleVarietyGridManager.newManager(variety.name, from_manager.start_date,
                from_manager.end_date, from_manager.lons, from_manager.lats,
                from_manager.search_bbox, models, 
                from_manager.gddThresholds('carolina'), acis_grid, 
                filepath=to_filepath, verbose=verbose)

    # copy old file's attributes
    to_manager.setFileAttributes(**from_manager.getFileAttributes())
else: to_manager = AppleVarietyGridManager(target_year, variety.name, 'a',
                                           filepath=to_filepath)

# copy daily and accumulated chill units for each model
updated = to_manager.timestamp
for model_name in models:
    for lo_gdd_th, hi_gdd_th in from_manager.gddThresholds(model_name):
        # restructure the GDD datasets
        if update_gdd:
            print '\nRestructuring GDD datasets for %s model' % model_name
            to_manager.open(mode='a')

            accum_path = from_manager.modelDatasetPath(model_name, lo_gdd_th,
                                      hi_gdd_th, 'gdd', 'accumulated')
            from_gdd = from_manager.getDataset(accum_path)
            created = from_manager.getDataset(accum_path).attrs['created']
            to_manager.getDataset(accum_path).attrs['created'] = created

            mask_path = from_manager.modelDatasetPath(model_name, lo_gdd_th,
                                     hi_gdd_th, 'gdd', 'chill_mask')
            from_mask = from_manager.getDataset(mask_path)
            created = from_manager.getDataset(mask_path).attrs['created']
            to_manager.getDataset(mask_path).attrs['created'] = created

            prov_path = from_manager.modelDatasetPath(model_name, lo_gdd_th,
                                     hi_gdd_th, 'gdd', 'provenance')
            from_prov = from_manager.getDataset(prov_path)
            created = from_manager.getDataset(prov_path).attrs['created']
            to_manager.getDataset(prov_path).attrs['created'] = created

            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                processed = from_prov[day][1]
                to_manager.updateGdd(model_name, lo_gdd_th, hi_gdd_th,
                                     from_gdd[day,:,:], from_mask[day,:,:],
                                     date,
                                     processed=processed)

            updated = to_manager.timestamp
            to_manager.getDataset(accum_path).attrs['updated'] = updated
            to_manager.getDataset(mask_path).attrs['updated'] = updated
            to_manager.getDataset(prov_path).attrs['updated'] = updated

            to_manager.close()

            print 'GDD datasets restructured for %s model' % model_name

        # restructure the Stage datasets
        if update_stage:
            print '\nRestructuring Stage datasets for %s model' % model_name
            to_manager.open(mode='a')

            stage_path = from_manager.modelDatasetPath(model_name, lo_gdd_th,
                                      hi_gdd_th, 'stage', 'index')
            from_stage = from_manager.getDataset(stage_path)
            created = from_manager.getDataset(stage_path).attrs['created']
            to_manager.getDataset(stage_path).attrs['created'] = created

            prov_path = from_manager.modelDatasetPath(model_name, lo_gdd_th,
                                     hi_gdd_th, 'stage', 'provenance')
            from_prov = from_manager.getDataset(prov_path)
            created = from_manager.getDataset(prov_path).attrs['created']
            to_manager.getDataset(prov_path).attrs['created'] = created

            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                processed = from_prov[day][1]
                to_manager.updateStage(model_name, lo_gdd_th, hi_gdd_th,
                                       from_stage[day,:,:], date,
                                       processed=processed)

            updated = to_manager.timestamp
            to_manager.getDataset(stage_path).attrs['updated'] = updated
            to_manager.getDataset(prov_path).attrs['updated'] = updated

            to_manager.close()

            print 'Stage datasets restructured for %s model' % model_name

        # restructure the Kill datasets
        if update_kill:
            print '\nRestructuring Kill datasets for %s model' % model_name
            to_manager.open(mode='a')

            kill_path = from_manager.modelDatasetPath(model_name, lo_gdd_th,
                                      hi_gdd_th, 'kill', 'level')
            from_kill = from_manager.getDataset(kill_path)
            created = from_manager.getDataset(kill_path).attrs['created']
            to_manager.getDataset(kill_path).attrs['created'] = created

            prov_path = from_manager.modelDatasetPath(model_name, lo_gdd_th,
                                     hi_gdd_th, 'kill', 'provenance')
            from_prov = from_manager.getDataset(prov_path)
            created = from_manager.getDataset(prov_path).attrs['created']
            to_manager.getDataset(prov_path).attrs['created'] = created

            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                processed = from_prov[day][1]
                to_manager.updateKill(model_name, lo_gdd_th, hi_gdd_th,
                                      from_kill[day,:,:], date,
                                      processed=processed)

            updated = to_manager.timestamp
            to_manager.getDataset(stage_path).attrs['updated'] = updated
            to_manager.getDataset(prov_path).attrs['updated'] = updated

            to_manager.close()

            print 'Kill datasets restructured for %s model' % model_name


# copy temperatures and fill temp provenance records
if update_temp:
    print '\nRestructuring Min Temp datasets'
    # mint processed date will come from Carolina GDD provenance   
    lo_gdd_th, hi_gdd_th = from_manager.gddThresholds('carolina')[0]
    prov_path = from_manager.modelDatasetPath('carolina', lo_gdd_th, hi_gdd_th,
                                              'gdd', 'provenance')
    gdd_prov = from_manager.getDataset(prov_path)
    created = from_manager.getDataset(prov_path).attrs['created']

    from_mint = from_manager.getTemp('mint', start_date, end_date)
    num_days = from_mint.shape[0]
    
    to_manager.open(mode='a')
    mint_prov = to_manager.getDataset('mint_provenance')

    for day in range(num_days):
        date = start_date + relativedelta(days=day)
        processed = gdd_prov[day][1]
        to_manager.updateTemp('mint', acis_grid, from_mint[day,:,:], date,
                              processed=processed)

    updated = to_manager.timestamp
    to_manager.getDataset('mint').attrs['updated'] = updated
    to_manager.getDataset('mint_provenance').attrs['updated'] = updated

    to_manager.close()
    print 'Min Temp datasets restructured'

# turn annoying numpy warnings back on
warnings.resetwarnings()

