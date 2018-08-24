#!/Users/rem63/venvs/frost/bin/python
""" Build historical temperature grid for all dates relevant to the target year
"""

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from atmosci.utils.timeutils import lastDayOfMonth, asAcisQueryDate

from frost.factory import FrostGridFactory
from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--grid', action='store', type='int', dest='acis_grid',
                  default=None)

parser.add_option('-d', action='store', type='int', dest='days_per_loop',
                  default=15)
parser.add_option('-r', action='store_true', dest='rebuild', default=False)
parser.add_option('-u', action='store_false', dest='update', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

acis_grid = options.acis_grid
if acis_grid is None: acis_grid = fromConfig('default.grid.acis')
# days_per_loop ... find a number that maximizes ACIS download performance 
days_per_loop = relativedelta(days=options.days_per_loop-1)
debug = options.debug
rebuild = options.rebuild
data_bbox = options.bbox
if data_bbox is None: data_bbox = fromConfig('default.bbox.data')
test_run = options.test_run
test_file = debug | test_run
verbose = options.verbose or debug
update_db = options.update

target_year = int(args[0])

# get a temperature data file manger
factory = FrostGridFactory()
filepath = factory.getTemperatureFilePath(target_year, test_file)
if not os.path.exists(os.path.normpath(filepath)):
    manager = factory.newTempGridManager(target_year, data_bbox, verbose,
                                         test_file)
else: manager = factory.getTemperatureManager(target_year, 'r', test_file)

# extract the time span for the target year
start_year = target_year - 1
start_month, day = fromConfig('default.start_day')
target_start_date = datetime(start_year, start_month, day)
month, day = fromConfig('default.end_day')
target_end_date = datetime(target_year, month, day)

# download several days at a time
start_date = target_start_date
end_date = start_date + days_per_loop

while start_date <= target_end_date:
    if end_date > target_end_date: end_date = target_end_date
    print 'downloading', asAcisQueryDate(start_date), asAcisQueryDate(end_date)

    # download historical temperatures for the time span
    data = factory.getAcisGridData('mint,maxt', start_date, end_date, None, 
                                   data_bbox, acis_grid, debug=debug)
    # update the file's temperature grid
    manager.open('a')
    manager.updateTemp('reported.maxt', data['maxt'], start_date)
    manager.updateTemp('reported.mint', data['mint'], start_date)
    manager.close()

    # next month
    start_date = end_date + ONE_DAY
    end_date = start_date + days_per_loop

