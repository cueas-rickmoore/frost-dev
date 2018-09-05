#! /Volumes/projects/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig, nameToFilepath
from frost.visual.maps import drawFilledContours, finishMap

from frost.apple.functions import getAppleVariety, mapWorkingDir, mapFilename
from frost.apple.factory import AppleGridFactory
from frost.apple.visual import addModelText, drawNoDataMap

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-d', action='store', type='string', dest='dataset',
                  default='accumulated')
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

dataset = options.dataset
debug = options.debug
map_type = 'chill.%s' % dataset
test_file = options.test_file
chill_config = fromConfig('crops.apple.chill')
maps_config = chill_config.maps
min_chill = maps_config.min_chill_to_post
min_percent = maps_config.min_percent_nodes

# chill model
if not args[0].isdigit():
    models = (chill_config[args[0]],)
    date_indx = 1
else:
    models = chill_config.getActiveModels()
    date_indx = 0

# get the date
date_args = args[date_indx:]
num_date_args = len(date_args)
if num_date_args >= 3:
    year = int(date_args[0])
    month = int(date_args[1])
    day = int(date_args[2])
    start_date = datetime(year,month,day)
    if num_date_args == 3: end_date = None
    elif num_date_args == 4:
        end_date = start_date + relativedelta(days=int(date_args[3])-1)
    elif num_date_args == 6:
        year = int(date_args[3])
        month = int(date_args[4])
        day = int(date_args[5])
        end_date = datetime(year,month,day)
    else:
        errmsg = 'Invalid number of date arguments (%d).' % date_args
        raise ValueError, errmsg
else:
    errmsg = 'Invalid number of date arguments (%d).' % date_args
    raise ValueError, errmsg

if end_date is None: end_date = start_date

factory = AppleGridFactory()
target_year = factory.getTargetYear(start_date)

# get the map title
title = maps_config.titles.accumulated

# get GDD map options
map_options = maps_config.options.accumulated.attrs
no_data = maps_config.no_data.accumulated.attrs

# get date indepenedent attributes and grids from the stage grid manager
manager = factory.getChillGridManager(target_year, 'r', test_file)
lats = manager.lats
lons = manager.lons

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

for model in models:
    # get the map directory path and the template for the map file name
    map_dirpath = mapWorkingDir(target_year, None, model.name, 'chill',
                                dataset, None, None, test_file)
    filename_template = mapFilename('%s', None, model.name, 'chill',
                                    dataset, None, None, test_file)
    filepath_template = map_dirpath + os.sep + filename_template

    date = start_date
    while date <= end_date:
        map_options['title'] = title
        # date-specific map options
        map_options['date'] = date
        map_options['outputfile'] = filepath_template % asAcisQueryDate(date)

        # get GDD accumulations for the date and draw the map
        chill_grid = manager.getChill(model.name, 'accumulated', date)

        finite = N.where(N.isfinite(chill_grid))
        num_finite = float(len(finite[0]))
        if num_finite > 0:
            num_ge_min = float(len(N.where(chill_grid[finite] >= min_chill)[0]))
            if num_ge_min > 0 and (num_ge_min / num_finite) > min_percent:
                chill_grid[chill_grid < 100.] = N.nan
                options, _map_, fig, axes, fig1, xy_extremes = \
                drawFilledContours(chill_grid, lats, lons, finish=False,
                                   **map_options)
                addModelText(fig, model, **map_options)
                finishMap(fig, axes, fig1, **options)
                path = options['outputfile']
            else:
                path = drawNoDataMap(lons, lats, config=no_data, model=model,
                                     **map_options)
            print 'completed', path
        else:
            print 'All data missing for', date.strftime('%Y-%m-%d')

        date += ONE_DAY

# turn annoying numpy warnings back on
warnings.resetwarnings()

