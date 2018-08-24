#!/Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig, nameToFilepath
from frost.visual.maps import drawFilledContours

from frost.apple.functions import varietyWorkingDir, getAppleVariety
from frost.apple.factory import AppleGridFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-m', action='store', type='string', dest='map_type',
                  default='accumulated')
parser.add_option('-y', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

map_type = options.map_type
test_file = options.test_file

# apple variety config
variety = getAppleVariety(args[0])
# chill models
model_1 = fromConfig('crops.apple.chill.%s.self' % args[1])
model_2 = fromConfig('crops.apple.chill.%s.self' % args[2])

# get the date
date_args = len(args[3:])
if date_args >= 3:
    year = int(args[3])
    month = int(args[4])
    day = int(args[5])
    start_date = datetime(year,month,day)
    if date_args == 3: end_date = None
    elif date_args == 4:
        end_date = start_date + relativedelta(days=int(args[6])-1)
    elif date_args == 6:
        year = int(args[6])
        month = int(args[7])
        day = int(args[8])
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
map_dirpath = varietyWorkingDir(target_year, variety.name, test_file)
map_dirpath = os.path.join(map_dirpath, model_1.name, 'chill.diff')

filename_template = '%%s-Frost-Apple-%s-%s-%s-Chill-Diff.png'
filename_template = filename_template % ( nameToFilepath(variety.name), 
                                          nameToFilepath(model_1.name), 
                                          nameToFilepath(model_2.name) )
filepath_template = map_dirpath + os.sep + filename_template

# get GDD map options
map_options = fromConfig('crops.apple.chill.maps.options.accumulated.attrs')
map_options['titleyoffset'] = 0.165
del map_options['contourbounds']
title = '%s\nAccumulated Chill Difference\n%s - %s' % ( variety.description,
                                                        model_1.name.title(),
                                                        model_2.name.title())

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
    chill_grid_1 = manager.getChill(model_1.name, 'accumulated', date)
    chill_grid_1[N.where(chill_grid_1 < 0.0)] = N.nan
    print 'grid 1', N.nanmin(chill_grid_1), N.nanmax(chill_grid_1)
    chill_grid_2 = manager.getChill(model_2.name, 'accumulated', date)
    chill_grid_2[N.where(chill_grid_2 < 0.0)] = N.nan
    print 'grid 2', N.nanmin(chill_grid_2), N.nanmax(chill_grid_2)

    chill_grid = chill_grid_1 - chill_grid_2
    print N.nanmin(chill_grid), N.nanmax(chill_grid)
    drawFilledContours(chill_grid, lats, lons, **map_options)

    date += ONE_DAY

