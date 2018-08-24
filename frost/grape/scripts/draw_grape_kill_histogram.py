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

# station search criteria
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

test_file = options.test_file
verbose = options.verbose

# apple variety config
variety = getGrapeVariety(args[0])
# temperature source
temp_source = args[1]
temp_path = '%s.mint' % temp_source

factory = GrapeGridFactory()

# get the date
date_args = len(args[2:])
if date_args == 1:
    target_year = int(args[2])
    start_date = datetime(target_year,1,1)
    end_date = datetime(target_year,5,15)
elif date_args >= 3:
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
    target_year = factory.getTargetYear(start_date)
else:
    errmsg = 'Invalid number of date arguments (%d).' % date_args
    raise ValueError, errmsg

if end_date is None: past_date = start_date + ONE_DAY
else: past_date = end_date + ONE_DAY

# get the map directory path and the template for the map file name
plot_dirpath = \
    plotWorkingDir(target_year, variety, 'kill', 'histograms', test_file)

filename_template = '%%s-Frost-Grape-%s-Kill-Histogram.png'
filename_template = filename_template % nameToFilepath(variety.name) 
filepath = plot_dirpath + os.sep + filename_template

title = u"%s Grape - Kill Severity" % variety.description

# grape variety manager for hardiness and lats/lons
variety_manager = \
    factory.getVarietyManager(target_year, variety, 'r', test_file)
lats = variety_manager.lats
lons = variety_manager.lons

# temp manager for mint
temp_manager = factory.getTempGridManager(target_year, 'r', test_file)

# bin bounds in degrees F (~ -30. to 10 C)
bins = [-30. + (n * 2.) for n in range(21)]

from matplotlib import pyplot
date = start_date
while date < past_date:
    hard_temp = variety_manager.getHardiness(date, units='F')
    min_temp = temp_manager.getTemp(temp_path, date, units='F')
    temp_diff = hard_temp - min_temp
    #temp_diff = min_temp - hard_temp

    figure = pyplot.figure()
    axis = figure.add_subplot(111)
    pyplot.xlim(bins[0], bins[-1])
    pyplot.ylim(0, 100000)
    axis.hist(temp_diff.flatten(), bins, normed=False, histtype='bar', rwidth=0.8)

    pyplot.suptitle(title, fontsize=12)
    pyplot.title(date.strftime('%B %d, %Y'), fontsize=12)

    output_filepath = filepath % asAcisQueryDate(date)
    figure.savefig(output_filepath)
    print 'plot saved to', output_filepath
    # need this stop Matplotlib from keeping each plot in figure memory
    pyplot.close()
    date += ONE_DAY
    sys.stdout.flush()

if animate:
    print 'creating animation'
    png_path = '*Kill-Histogram.png'
    template = '%d-Frost-Grape-%s-Kill-Histogram-animation.gif'
    anim_filename = template % (target_year, nameToFilepath(variety.name))
    anim_path = os.path.join(plot_dirpath, anim_filename)
    os.chdir(plot_dirpath)
    os.system('convert -delay %d %s -loop 0 %s' % (delay, png_path, anim_path))
    print 'animation complete', anim_path

