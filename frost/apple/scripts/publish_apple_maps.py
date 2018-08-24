#! /Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from frost.functions import targetYearFromDate

from frost.apple.functions import animationFilepath, copyMapFileToWeb
from frost.apple.functions import mapFilepath

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PUBLISHED = 'Published %s for %s to %s'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
test_file = options.test_file

# args[0] = 'chill' or variety name
model = args[1]

# get the date
if len(args) > 2:
    year = int(args[2])
    month = int(args[3])
    day = int(args[4])
    date = datetime(year,month,day)
else:
    date = datetime.now() - ONE_DAY
date_str = date.strftime('%B %d, %Y')
target_year = targetYearFromDate(date)

if args[0] == 'chill':
    # publish accumulated chill map
    src_filepath = mapFilepath(date, None, model, 'chill', 'accumulated')
    if os.path.exists(src_filepath):
        web_filepath = \
        copyMapFileToWeb(src_filepath, date, None, model, 'chill', 'accumulated')
        print PUBLISHED % ('Accumulated Chill map', date_str, web_filepath)

    # publish chill animation
    src_filepath = \
    animationFilepath(target_year, None, model, 'chill', 'accumulated')
    if os.path.exists(src_filepath):
        web_filepath = copyMapFileToWeb(src_filepath, date, None, model,
                                        'chill', 'accumulated', 'web_anim')
        print PUBLISHED % ('Accumulated Chill animation', date_str,
                           web_filepath)
else:
    # publish variety maps 
    variety = args[0]
    #lo_gdd_th, hi_gdd_th = fromConfig('crops.apple.gdd_thresholds')[0]
    lo_gdd_th = hi_gdd_th = None

    # publish variety accumulated GDD map
    src_filepath = \
    mapFilepath(date, variety, model, 'variety', 'gdd', lo_gdd_th, hi_gdd_th)
    if os.path.exists(src_filepath):
        web_filepath = \
        copyMapFileToWeb(src_filepath, date, variety, model, 'variety', 'gdd')
        print PUBLISHED % ('%s GDD map' % variety, date_str, web_filepath)

    # publish GDD animation
    src_filepath = animationFilepath(target_year, variety, model, 'variety',
                                     'gdd', lo_gdd_th, hi_gdd_th)
    if os.path.exists(src_filepath):
        web_filepath = copyMapFileToWeb(src_filepath, date, variety, model,
                                        'variety', 'gdd', 'web_anim')
        print PUBLISHED % ('%s GDD animation' % variety, date_str, web_filepath)

    # publish variety phenological stage map
    src_filepath = \
    mapFilepath(date, variety, model, 'variety', 'stage', lo_gdd_th, hi_gdd_th)
    if os.path.exists(src_filepath):
        web_filepath = \
        copyMapFileToWeb(src_filepath, date, variety, model, 'variety', 'stage')
        print PUBLISHED % ('%s Stage map' % variety, date_str, web_filepath)

    # publish stage animation
    src_filepath = animationFilepath(target_year, variety, model, 'variety', 
                                     'stage', lo_gdd_th, hi_gdd_th)
    if os.path.exists(src_filepath):
        web_filepath = copyMapFileToWeb(src_filepath, date, variety, model,
                                        'variety', 'stage', 'web_anim')
        print PUBLISHED % ('%s Stage animation' % variety, date_str, web_filepath)

    # publish variety kill probablity map
    src_filepath = \
    mapFilepath(date, variety, model, 'variety', 'kill', lo_gdd_th, hi_gdd_th)
    if os.path.exists(src_filepath):
        web_filepath = \
        copyMapFileToWeb(src_filepath, date, variety, model, 'variety', 'kill')
        print PUBLISHED % ('%s Kill map' % variety, date_str, web_filepath)

    # publish kill animation
    src_filepath = animationFilepath(target_year, variety, model, 'variety',
                                     'kill', lo_gdd_th, hi_gdd_th)
    if os.path.exists(src_filepath):
        web_filepath = copyMapFileToWeb(src_filepath, date, variety, model,
                                        'variety', 'kill', 'web_anim')
        print PUBLISHED % ('%s Kill animation' % variety, date_str, web_filepath)

