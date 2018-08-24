#!/Volumes/projects/venvs/frost/bin/python

import os, sys
import warnings
import time

import datetime
ONE_DAY = datetime.timedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-s', action='store', type=int, dest='sleep', default=5)

parser.add_option('-d', action='store_true', dest='download', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

download_temps = options.download
debug = options.debug
sleep = options.sleep
verbose = options.verbose or debug

if len(args) == 1:
    target_year = int(args[0])
    today = None
else:
    target_year = datetime.date.today().year
    today = datetime.date.today()

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

from frost.factory import FrostGridFactory
factory = FrostGridFactory()
start_date, end_date = factory.getTargetDateSpan(target_year)
# handle case where new file is constructed in cron for the next year
if today is not None and today.month > end_date.month: target_year += 1

manager = factory.newTempGridManager(target_year)
print 'created frost temperature for', target_year
print manager._hdf5_filepath
manager.close()

if download_temps:
    current_date = datetime.datetime.now()
    if target_year <= current_date.year:
        if target_year == current_date.year:
            if current_date >= start_date and current_date <= end_date:
                end_date = current_date

    date = start_date
    while date <= end_date:
        if verbose: print '\ndownloading', date
        manager.open('a')
        acis_grid = manager.getDatasetAttribute('reported.maxt','acis_grid')
        data = factory.getAcisGridData('mint,maxt', date, None, None,
                                        manager.data_bbox, int(acis_grid),
                                        debug=debug)
        manager.updateTemp('reported.maxt', data['maxt'], date)
        manager.updateTemp('reported.mint', data['mint'], date)
        manager.close()
        date += ONE_DAY
        if sleep > 0 and date < end_date: time.sleep(sleep)


# turn annoying numpy warnings back on
warnings.resetwarnings()

