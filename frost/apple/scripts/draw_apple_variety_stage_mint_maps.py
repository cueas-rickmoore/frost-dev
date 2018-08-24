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

parser.add_option('-t', action='store', dest='temp_source', default='reported')
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

temp_source = options.temp_source
test_file = options.test_file
verbose = options.verbose

# apple variety config
variety = getAppleVariety(args[0])
# chill model
model = fromConfig('crops.apple.chill.%s.self' % args[1])

# get the date
date_args = len(args[3:])
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

factory = AppleGridFactory()
target_year = factory.getTargetYear(start_date)

# get the map directory path and the template for the map file name
map_dirpath = mapWorkingDir(target_year, variety.name, model_1.name,
                            'stage.mint', None, None, test_file)

filename_template = '%%s-Frost-Apple-%s-%s-%%s-Stage-%%s-Kill-Mint.png'
filename_template = filename_template % ( nameToFilepath(variety.name), 
                                          nameToFilepath(model.name) )
filepath = map_dirpath + os.sep + filename_template

title = '%s\n%%s Kill Temp at %%s Stage - mint\n%s' % ( variety.description,
                                                    model.descrption )
  
# apple variety grid manager
variety_manager = \
    factory.getVarietyGridManager(target_year, variety, 'r', test_file)
gdd_thresholds = variety_manager.gddThresholds(model_1.name)
lats = variety_manager.lats
lons = variety_manager.lons

# temperature grid manager
temp_manager = factory.getTempGridManager(target_year, 'r', test_file)
mint_dataset = '%s.mint' % temp_source

map_options = { 'area':'northeast', 'cmap':'jet', 'colorbar':True,
                'titleyoffset': 0.165, }

kill_levels = variety.kill_levels
kill_temps = variety.kill_temps.attr_list   

stage_names =\
tuple(fromConfig('crops.apple.variety.stage_name_map.attr_values'))

for lo_gdd_th, hi_gdd_th in gdd_thresholds:
    date = start_date
    while date <= end_date:
        map_options['date'] = date
        date_str = asAcisQueryDate(date)

        mint = temp_manager.getTemp(mint_dataset, date)
        stage_grid = \
            variety_manager.getStage(model.name, lo_gdd_th, hi_gdd_th, date)

        for stage, stage_name in enumerate(stage_names[1:], start=1):
            indexes = N.where(stage_grid == stage)
            if len(indexes[0]) > 0: 
                for indx, kill_level in enumerate(kill_levels):
                    percent = '%d%%' % kill_level
                    map_options['title'] = title % (percent, stage_name)
                    map_options['outputfile'] = \
                            filepath % (date_str, stage_name, percent)

                    diff = float(kill_temps[indx]) - mint
                    drawFilledContours(diff, lats, lons, **map_options)

        date += ONE_DAY

