#!/Users/rem63/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import nameToFilepath
from frost.visual.maps import drawFilledContours

from frost.grape.factory import GrapeGridFactory
from frost.grape.functions import getGrapeVariety, plotWorkingDir

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store_true', dest='animate', default=False)
parser.add_option('-d', action='store', type='int', dest='delay', default=30)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

animate = options.animate
delay = options.delay
test_file = options.test_file
verbose = options.verbose

# apple variety config
variety = getGrapeVariety(args[0])

factory = GrapeGridFactory()

# get the date
date_args = len(args[1:])
if date_args == 1:
    target_year = int(args[1])
    start_date = datetime(target_year,1,1)
    end_date = datetime(target_year,5,15)
elif date_args >= 3:
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
    target_year = factory.getTargetYear(start_date)
else:
    errmsg = 'Invalid number of date arguments (%d).' % date_args
    raise ValueError, errmsg

if end_date is None: past_date = start_date + ONE_DAY
else: past_date = end_date + ONE_DAY

visualizer = factory.getVarietyVisualizer(target_year, variety, test_file)

date = start_date
while date < past_date:
    path = visualizer.drawHardinessMap(date, verbose)
    date += ONE_DAY
    print 'map saved to :', path
    sys.stdout.flush()

if animate:
    print 'creating animation'
    png_path = '*Hardiness-Map.png'
    template = '%d-Frost-Grape-%s-Hardiness-Map-animation.gif'
    anim_filename = template % (target_year, nameToFilepath(variety.name))
    anim_path = os.path.join(map_dirpath, anim_filename)
    os.chdir(map_dirpath)
    os.system('convert -delay %d %s -loop 0 %s' % (delay, png_path, anim_path))
    print 'animation complete', anim_path

