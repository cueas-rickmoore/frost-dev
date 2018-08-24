#!/Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-g', action='store_false', dest='update_gdd', default=True)
parser.add_option('-m', action='store_false', dest='update_models', default=True)
parser.add_option('-n', action='store_false', dest='new_file', default=True)
parser.add_option('-t', action='store_false', dest='update_temps', default=True)
parser.add_option('-v', action='store_true',  dest='verbose', default=False)
parser.add_option('-z', action='store_true',  dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

new_file = options.new_file
test_file = options.test_file
update_gdd = options.update_gdd
update_models = options.update_models
update_temps = options.update_temps
verbose = options.verbose

target_year = int(args[0])

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get a chill grid file manger
factory = AppleGridFactory()
reader = factory.getChillGridReader(target_year)

if len(args) > 1: to_filepath = os.path.abspath(args[1])
else: to_filepath = reader._hdf5_filepath.replace('.h5','.new.h5')

start_date = reader.start_date
end_date = reader.end_date
num_days = (end_date - start_date).days + 1
models = [name.lower() for name in reader.file_chill_models]

# get a manager for the restructured file
if new_file:
    from frost.apple.chill.grid import AppleChillGridBuilder

    builder_attributes = { 'filepath':to_filepath,
                           'node_spacing':reader.node_spacing,
                           'data_bbox':reader.search_bbox }

    to_manager = AppleChillGridBuilder(start_date, end_date, reader.lons,
                                reader.lats, models, reader.gddThresholds(),
                                test_file, verbose, **builder_attributes)
# fix an existing file
else:
    from frost.apple.chill.grid import AppleChillGridManager
    to_manager = AppleChillGridManager(target_year, 'a', filepath=to_filepath)

# copy daily and accumulated chill units for each model
updated = to_manager.timestamp
if update_models:
    for model_name in models:
        from_accum = \
        reader.getChill(model_name, 'accumulated', start_date, end_date)
        from_daily = \
        reader.getChill(model_name, 'daily', start_date, end_date)

        full_path = reader.chillDatasetPath(model_name, 'daily')
        created = reader.getDataset(full_path).attrs['created']

        full_path = reader.chillDatasetPath(model_name, 'provenance')
        from_prov = reader.getDataset(full_path)

        to_manager.open(mode='a')
        for day in range(num_days):
            date = start_date + relativedelta(days=day)
            processed = from_prov[day][1]
            to_manager.updateChill(model_name, from_daily[day,:,:],
                        from_accum[day,:,:], date, timestamp=processed)

        full_path = to_manager.chillDatasetPath(model_name, 'accumulated')
        to_manager.setDatasetAttributes(full_path, created=created,
                                        updated=updated)
        full_path = to_manager.chillDatasetPath(model_name, 'daily')
        to_manager.setDatasetAttributes(full_path, created=created,
                                        updated=updated)
        full_path = to_manager.chillDatasetPath(model_name, 'provenance')
        to_manager.setDatasetAttributes(full_path, created=created,
                                        updated=updated)

        to_manager.close()

        print 'chill datasets restructured for %s model' % model_name

# copy daily GDD for each set of thresholds
if update_gdd:
    for lo_gdd_th, hi_gdd_th in reader.gddThresholds():
        from_gdd = reader.getGdd(lo_gdd_th, hi_gdd_th, start_date, end_date)
        full_path = reader.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'daily')
        created = reader.getDataset(full_path).attrs['created']

        full_path =\
        reader.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'provenance')
        from_prov = reader.getDataset(full_path)

        to_manager.open(mode='a')
        for day in range(num_days):
            date = start_date + relativedelta(days=day)
            processed = from_prov[day][1]
            to_manager.updateGdd(lo_gdd_th, hi_gdd_th, from_gdd[day,:,:], date,
                                  timestamp=processed)
        
        full_path = to_manager.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'daily')
        to_manager.setDatasetAttributes(full_path, created=created,
                                        updated=updated)
        full_path = to_manager.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'provenance')
        to_manager.setDatasetAttributes(full_path, created=created,
                                        updated=updated)
        to_manager.close()
 
        print 'GDD datasets restructured for %d:%d' % (lo_gdd_th, hi_gdd_th)

# turn annoying numpy warnings back on
warnings.resetwarnings()

