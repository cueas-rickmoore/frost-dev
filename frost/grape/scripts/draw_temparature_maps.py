#! /Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.factory import FrostGridFactory
from frost.functions import fromConfig, nameToFilepath, tempPlotDir

from frost.visual.maps import plot_bound, drawFilledContours

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TEMP_NAMES = { 'mint':'Minimum', 'maxt':'Maximum', 'avgt':'Average' }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-u', action='store', type='string', dest='units',
                  default='F')
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

test_file = options.test_file
units = options.units
verbose = options.verbose

temp_path = args[0]
temp_group, temp_type = temp_path.split('.')

# get the date
date_args = len(args[1:])
if date_args >= 3:
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    start_date = datetime(year,month,day)
    if date_args == 3: end_date = None
    elif date_args == 4:
        end_date = start_date + relativedelta(days=int(args[4])-1)
    elif date_args == 6:
        year = int(args[4])
        month = int(args[5])
        day = int(args[6])
        end_date = datetime(year,month,day)
    else:
        errmsg = 'Invalid number of date arguments (%d).' % date_args
        raise ValueError, errmsg
else:
    errmsg = 'Invalid number of date arguments (%d).' % date_args
    raise ValueError, errmsg

factory = FrostGridFactory()
target_year = factory.getTargetYear(start_date)

# create the map filepath template
template = '%%s-Frost-%s-%s-Map.png' % (temp_group.title(), temp_type.title())
map_dirpath = tempPlotDir(target_year, temp_group, temp_type, 'maps')
map_filepath = map_dirpath + os.sep + template

# create the map title tmplate
title_units = chr(176) + units
title = u"%s Temperature\n%%-.f < %s > %%-.F" % ( TEMP_NAMES[temp_type],
                                                  title_units.decode('latin1') )

# get temp manager and lot, lon data
manager = factory.getTempGridManager(target_year, 'r', test_file)
lats = manager.lats
lons = manager.lons

map_options = { 'area':'northeast', 'titleyoffset': 0.165, #'apply_mask':False,
                'cmap':'jet', 'colorbar':True, }

temp = manager.getTemp(temp_path, start_date, end_date, units=units)

if end_date is None:
    map_options['autobounds'] = True
    map_options['date'] = start_date
    map_options['title'] = title
    map_options['outputfile'] = map_filepath % asAcisQueryDate(start_date)

    drawFilledContours(temp, lats, lons, **map_options)
else:
    map_options['contourbounds'] = plot_bound(temp, 20)

    num_days = (end_date - start_date).days + 1
    for day in range(num_days):
        date = start_date + relativedelta(days=day)
        map_options['date'] = date
        map_options['outputfile'] = map_filepath % asAcisQueryDate(date)

        day_temps = temp[day]
        map_options['title'] = title % (N.nanmin(day_temps),N.nanmax(day_temps))
        drawFilledContours(day_temps, lats, lons, **map_options)

