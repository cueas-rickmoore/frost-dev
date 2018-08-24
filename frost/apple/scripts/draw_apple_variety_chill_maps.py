#!/Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig, nameToFilepath
from frost.maps.drawmaps import drawFilledContours

from frost.apple.functions import getAppleVariety, mapWorkingDir, mapFilename
from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-d', action='store', type='string', dest='dataset',
                  default='accumulated')
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

dataset = options.dataset
map_type = 'chill.%s' % dataset
test_file = options.test_file

# apple variety config
variety = getAppleVariety(args[0])
# chill model
model = fromConfig('crops.apple.chill.%s.self' % args[1])

# get the date
date_args = len(args[2:])
if date_args >= 3:
    year = int(args[2])
    month = int(args[3])
    day = int(args[4])
    start_date = datetime(year,month,day)
    if date_args == 3: end_date = None
    elif date_args == 4:
        end_date = start_date + relativedelta(days=int(args[5])-1)
    elif date_args == 6:
        year = int(args[5])
        month = int(args[6])
        day = int(args[7])
        end_date = datetime(year,month,day)
    else:
        errmsg = 'Invalid number of date arguments (%d).' % date_args
        raise ValueError, errmsg
else:
    errmsg = 'Invalid number of date arguments (%d).' % date_args
    raise ValueError, errmsg

if end_date is None: past_date = start_date + ONE_DAY
else: past_date = end_date + ONE_DAY

factory = AppleGridFactory()
target_year = factory.getTargetYear(start_date)

# get the map directory path and the template for the map file name
map_dirpath = mapWorkingDir(target_year, variety.name, model.name, 'chill',
                            dataset, None, None, test_file)
filename_template = mapFilename('%s', variety.name, model.name, 'chill',
                                dataset, None, None, test_file)
filepath_template = map_dirpath + os.sep + filename_template

# get the map title template and initialize the map title
title_template = fromConfig('crops.apple.chill.maps.titles.accumulated')
title = title_template % { 'model':model.description, }

# get GDD map options
map_options = fromConfig('crops.apple.chill.maps.options.accumulated.attrs')

# get date indepenedent attributes and grids from the stage grid manager
manager = factory.getChillGridManager(target_year, 'r', test_file)
lats = manager.lats
lons = manager.lons

date = start_date
while date < past_date:
    map_options['title'] = title
    # date-specific map options
    map_options['date'] = date
    map_options['outputfile'] = filepath_template % asAcisQueryDate(date)

    # get GDD accumulations for the date and draw the map
    chill_grid = manager.getChill(model.name, dataset, date)
    chill_grid[N.where(chill_grid < 0.0)] = N.nan
    drawFilledContours(chill_grid, lats, lons, **map_options)

    date += ONE_DAY

