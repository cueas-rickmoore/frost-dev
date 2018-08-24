#!/Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getAppleVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-g', action='store_false', dest='update_gdd', default=True)
parser.add_option('-k', action='store_false', dest='update_kill', default=True)
parser.add_option('-n', action='store_false', dest='new_file', default=True)
parser.add_option('-s', action='store_false', dest='update_stage', default=True)
parser.add_option('-v', action='store_true',  dest='verbose', default=False)
parser.add_option('-z', action='store_true',  dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

new_file = options.new_file
test_file = options.test_file
update_gdd = options.update_gdd
update_kill = options.update_kill
update_stage = options.update_stage
verbose = options.verbose

target_year = int(args[0])

# apple variety config
variety = getAppleVariety(args[1])

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get a variety grid file manger
factory = AppleGridFactory()
reader = factory.getVarietyGridReader(target_year, variety)

if len(args) > 2: to_filepath = os.path.abspath(args[1])
else: to_filepath = reader._hdf5_filepath.replace('.h5','.new.h5')

start_date = reader.start_date
end_date = reader.end_date
num_days = (end_date - start_date).days + 1
models = [name.lower() for name in reader.file_chill_models]

# get a manager for the restructured file
if new_file:
    from frost.apple.variety.grid import AppleVarietyGridBuilder

    builder_attributes = { 'acis_grid':reader.acis_grid,
                           'filepath':to_filepath,
                           'node_spacing':reader.node_spacing,
                           'data_bbox':reader.search_bbox }

    to_manager = AppleVarietyGridBuilder(variety, start_date, end_date, 
                             reader.lons, reader.lats, models,
                             reader.gddThresholds(models[0]), verbose,
                             **builder_attributes)
# fix an existing file
else:
    from frost.apple.variety.grid import AppleVarietyGridManager
    to_manager = \
    AppleVarietyGridManager(target_year, variety, 'a', filepath=to_filepath)

# copy daily and accumulated chill units for each model
updated = to_manager.timestamp
for model_name in models:
    for lo_gdd_th, hi_gdd_th in reader.gddThresholds(model_name):
        # restructure the GDD datasets
        if update_gdd:
            print '\nRestructuring GDD datasets for %s model' % model_name

            accum_path = reader.modelDatasetPath(model_name, lo_gdd_th,
                                     hi_gdd_th, 'gdd', 'accumulated')
            from_gdd = reader.getDataset(accum_path)
            created = reader.getDataset(accum_path).attrs['created']
            to_manager.open(mode='a')
            to_manager.setDatasetAttribute(accum_path, 'created', created)
            to_manager.close()

            mask_path = reader.modelDatasetPath(model_name, lo_gdd_th,
                                    hi_gdd_th, 'gdd', 'chill_mask')
            from_mask = reader.getDataset(mask_path)
            created = reader.getDataset(mask_path).attrs['created']
            to_manager.open(mode='a')
            to_manager.setDatasetAttribute(mask_path, 'created', created)
            to_manager.close()

            prov_path = reader.modelDatasetPath(model_name, lo_gdd_th,
                                    hi_gdd_th, 'gdd', 'provenance')
            from_prov = reader.getDataset(prov_path)
            created = reader.getDataset(prov_path).attrs['created']
            to_manager.open(mode='a')
            to_manager.setDatasetAttribute(prov_path, 'created', created)
            to_manager.close()

            to_manager.open(mode='a')
            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                processed = from_prov[day][1]
                to_manager.updateGdd(model_name, lo_gdd_th, hi_gdd_th,
                                     from_gdd[day,:,:], from_mask[day,:,:],
                                     date, timestamp=processed)
            to_manager.close()

            to_manager.open(mode='a')
            updated = to_manager.timestamp
            to_manager.setDatasetAttribute(accum_path, 'updated', updated)
            to_manager.setDatasetAttribute(prov_path, 'updated', updated)
            to_manager.setDatasetAttribute(prov_path, 'updated', updated)
            to_manager.close()

            print 'GDD datasets restructured for %s model' % model_name

        # restructure the Stage datasets
        if update_stage:
            print '\nRestructuring Stage datasets for %s model' % model_name
            to_manager.open(mode='a')

            stage_path = reader.modelDatasetPath(model_name, lo_gdd_th,
                                      hi_gdd_th, 'stage', 'index')
            from_stage = reader.getDataset(stage_path)
            created = reader.getDataset(stage_path).attrs['created']
            to_manager.getDataset(stage_path).attrs['created'] = created

            prov_path = reader.modelDatasetPath(model_name, lo_gdd_th,
                                     hi_gdd_th, 'stage', 'provenance')
            from_prov = reader.getDataset(prov_path)
            created = reader.getDataset(prov_path).attrs['created']
            to_manager.getDataset(prov_path).attrs['created'] = created

            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                processed = from_prov[day][1]
                to_manager.updateStage(model_name, lo_gdd_th, hi_gdd_th,
                                       from_stage[day,:,:], date,
                                       timestamp=processed)

            updated = to_manager.timestamp
            to_manager.getDataset(stage_path).attrs['updated'] = updated
            to_manager.getDataset(prov_path).attrs['updated'] = updated

            to_manager.close()

            print 'Stage datasets restructured for %s model' % model_name

        # restructure the Kill datasets
        if update_kill:
            print '\nRestructuring Kill datasets for %s model' % model_name
            to_manager.open(mode='a')

            kill_path = reader.modelDatasetPath(model_name, lo_gdd_th,
                                      hi_gdd_th, 'kill', 'level')
            from_kill = reader.getDataset(kill_path)
            created = reader.getDataset(kill_path).attrs['created']
            to_manager.getDataset(kill_path).attrs['created'] = created

            prov_path = reader.modelDatasetPath(model_name, lo_gdd_th,
                                     hi_gdd_th, 'kill', 'provenance')
            from_prov = reader.getDataset(prov_path)
            created = reader.getDataset(prov_path).attrs['created']
            to_manager.getDataset(prov_path).attrs['created'] = created

            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                processed = from_prov[day][1]
                to_manager.updateKill(model_name, lo_gdd_th, hi_gdd_th,
                                      from_kill[day,:,:], date,
                                      timestamp=processed)

            updated = to_manager.timestamp
            to_manager.getDataset(stage_path).attrs['updated'] = updated
            to_manager.getDataset(prov_path).attrs['updated'] = updated

            to_manager.close()

            print 'Kill datasets restructured for %s model' % model_name

# turn annoying numpy warnings back on
warnings.resetwarnings()

