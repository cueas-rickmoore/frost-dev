#!/Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store_true', dest='copy_from_apple',
                  default=False)
parser.add_option('-d', action='store_true', dest='download', default=False)
parser.add_option('-t', action='store_true', dest='copy_temps', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-x', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

copy_from_apple = options.copy_from_apple
copy_temps = options.copy_temps
debug = options.debug
test_file = options.test_file
verbose = options.verbose or debug

target_year = int(args[0])

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

from frost.factory import FrostGridFactory
factory = FrostGridFactory()

if copy_from_apple:
    from frost.apple.factory import AppleGridFactory
    from frost.temperature import FrostTempFileBuilder

    apple_factory = AppleGridFactory()
    start_date, end_date = factory.getTargetDateSpan(target_year)

    apple_manager = apple_factory.getChillGridManager(target_year, 'r')
    lats = apple_manager.lats
    lons = apple_manager.lons
    apple_manager.close()

    manager = FrostTempFileBuilder(start_date, end_date, lons, lats,
                                        bbox=apple_manager.search_bbox, 
                                        acis_grid=apple_manager.acis_grid,
                                        verbose=verbose)
    manager.close()

    if copy_temps:
        apple_manager.open(mode='r')
        manager.open(mode='a')

        apple_maxt = apple_manager.getTemp('maxt', start_date, end_date)
        created = apple_manager.getDatasetAttribute('maxt','created')
        num_days = apple_maxt.shape[0]

        apple_mint = apple_manager.getTemp('mint', start_date, end_date)

        apple_prov = apple_manager.getDataset('gdd.L45H86.provenance')

        for day in range(num_days):
            date = start_date + relativedelta(days=day)
            timestamp = apple_prov[day]['processed']
            manager.updateTemp('reported.maxt', apple_maxt[day,:,:], date,
                                    timestamp=timestamp)
            manager.updateTemp('reported.mint', apple_mint[day,:,:], date,
                                     timestamp=timestamp)

        manager.setDatasetAttribute('reported.maxt', 'created', created)
        manager.setDatasetAttribute('reported.mint', 'created', created)

        manager.close()
        apple_manager.close()
        print 'temperature datasets copied from :', apple_manager._hdf5_filepath

else:
    manager = factory.newTempGridManager(target_year)
    manager.close()
    if options.download:
        start_date, end_date = factory.getTargetDateSpan(target_year)
        current_date = datetime.now()
        current_year = current_date.year
        if current_date >= start_date and current_date <= end_date:
            end_date = current_date

        date = start_date
        while date <= end_date:
            if verbose: print 'downloading', date
            manager.open('a')
            acis_grid = manager.getDatasetAttribute('reported.maxt','acis_grid')
            data = factory.getAcisGridData('mint,maxt', date, None, None,
                                            manager.data_bbox, int(acis_grid),
                                            debug=debug)
            manager.updateTemp('reported.maxt', data['maxt'], date)
            manager.updateTemp('reported.mint', data['mint'], date)
            manager.close()
            date += ONE_DAY

print 'created temperature file :', manager._hdf5_filepath

# turn annoying numpy warnings back on
warnings.resetwarnings()

