#!/Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig, nameToFilepath
from frost.visual.maps import drawFilledContours

from frost.apple.functions import mapWorkingDir
from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getAppleVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

test_file = options.test_file
verbose = options.verbose

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
map_dirpath = mapWorkingDir(target_year, variety.name, model_1.name,
                            'stage.diff', None, None, test_file)

filename_template = '%%s-Frost-Apple-%s-%s-%s-Stage-Diff.png'
filename_template = filename_template % ( nameToFilepath(variety.name), 
                                          nameToFilepath(model_1.name), 
                                          nameToFilepath(model_2.name) )
filepath_template = map_dirpath + os.sep + filename_template

title = '%s\nPhenological Stage Difference\n%s - %s' % ( variety.description,
                                                         model_1.name.title(),
                                                         model_2.name.title() )

manager = factory.getVarietyGridManager(target_year,variety.name,'r',test_file)
gdd_thresholds = manager.gddThresholds(model_1.name)
lats = manager.lats
lons = manager.lons

map_options = { 'area':'northeast', 'cmap':'jet', 'colorbar':True,
                'titleyoffset': 0.165, }

for lo_gdd_th, hi_gdd_th in gdd_thresholds:
    date = start_date
    while date < past_date:
        map_options['title'] = title
        # date-specific map options
        map_options['date'] = date
        map_options['outputfile'] = filepath_template % asAcisQueryDate(date)

        # get GDD accumulations for the date and draw the map
        stage_grid_1 = \
                manager.getStage(model_1.name, lo_gdd_th, hi_gdd_th, date)
        stage_grid_2 = \
                manager.getStage(model_2.name, lo_gdd_th, hi_gdd_th, date)

        stage_grid = stage_grid_1 - stage_grid_2
        drawFilledContours(stage_grid, lats, lons, **map_options)

        date += ONE_DAY

