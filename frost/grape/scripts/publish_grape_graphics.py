#! /Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from frost.functions import targetYearFromDate

from frost.grape.functions import getGrapeVariety, publishWebGraphic
from frost.grape.functions import animationFilepath, mapFilepath, plotFilepath

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PUBLISHED = 'Published %s for %s to :\n%s'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
test_file = options.test_file

variety = getGrapeVariety(args[0])
vardesc = variety.description

# get the date
if len(args) > 1:
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    date = datetime(year,month,day)
else:
    date = datetime.now() - ONE_DAY
date_str = date.strftime('%B %d, %Y')
target_year = targetYearFromDate(date)

# publish variety hardiness temp map
src_filepath = mapFilepath(date, variety, 'hardiness.temp')
if os.path.exists(src_filepath):
    web_filepath = \
    publishWebGraphic('map', src_filepath, date, variety, 'hardiness.temp')
    print PUBLISHED % ('%s Hardiness map' % vardesc, date_str, web_filepath)

# publish hardiness animation
src_filepath = animationFilepath(target_year, variety, 'hardiness.temp')
if os.path.exists(src_filepath):
    web_filepath = \
    publishWebGraphic('anim', src_filepath, date, variety, 'hardiness.temp')
    print PUBLISHED % ('%s Hardiness animation' % vardesc,date_str,web_filepath)

# publish variety kill probablity map
src_filepath = mapFilepath(date, variety, 'kill.potential')
if os.path.exists(src_filepath):
    web_filepath = \
    publishWebGraphic('map', src_filepath, date, variety, 'kill.potential')
    print PUBLISHED % ('%s Kill map' % vardesc, date_str, web_filepath)

# publish kill animation
src_filepath = animationFilepath(target_year, variety, 'kill.potential')
if os.path.exists(src_filepath):
    web_filepath = \
    publishWebGraphic('anim', src_filepath, date, variety, 'kill.potential')
    print PUBLISHED % ('%s Kill animation' % vardesc, date_str, web_filepath)

# publish kill vs temp graph
plot_group = 'kill.@.GenevaNY'
plot_key = 'Kill-vs-Temp-@-Geneva-NY'
src_filepath = plotFilepath(date, variety, plot_group, plot_key)
if os.path.exists(src_filepath):
    web_filepath = \
    publishWebGraphic('plot', src_filepath, date, variety, plot_key)
    plot_descrip = '%s %s plot' % (vardesc, plot_key)
    print PUBLISHED % (plot_descrip, date_str, web_filepath)

