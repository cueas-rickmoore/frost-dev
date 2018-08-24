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

# get the map directory path and the template for the map file name
plot_dirpath = \
    plotWorkingDir(target_year, variety, 'hardiness', 'histograms', test_file)

filename_template = '%%s-Frost-Grape-%s-Hardiness-Temp-Histogram.png'
filename_template = filename_template % nameToFilepath(variety.name) 
filepath = plot_dirpath + os.sep + filename_template

title = u"%s : Hardiness Temperature" % variety.description

manager = factory.getVarietyManager(target_year, variety, 'r', test_file)
lats = manager.lats
lons = manager.lons

# contour bounds in degrees F (~ -26.1 to -1.1 C)
#bins = [-15. + (n * 2.5) for n in range(20)]
bins = [-30. + (n * 1.25) for n in range(49)]
# extended range for a few varieties 
#if manager.hardiness.max < -26.25: # this is degrees C
#    bins = [ -22.5, -20., -17.5 ] + bins

from matplotlib import pyplot
date = start_date
while date < past_date:
    hard_temp = manager.getHardiness(date, units='F')

    figure = pyplot.figure()
    axis = figure.add_subplot(111)
    pyplot.xlim(bins[0], bins[-1])
    pyplot.ylim(0, 40000)
    axis.hist(hard_temp.flatten(), bins, normed=False, histtype='bar', rwidth=0.8)

    axis.set_ylabel('Number of Nodes', fontsize=10)
    label_units = chr(176) +'F'
    axis.set_xlabel('Temperature %s' % label_units.decode('latin1'), fontsize=10)
    axis.grid(True)

    pyplot.suptitle(title, fontsize=14)
    pyplot.title(date.strftime('%B %d, %Y'), fontsize=12)

    output_filepath = filepath % asAcisQueryDate(date)
    figure.savefig(output_filepath)
    print 'completed', output_filepath
    # need this stop Matplotlib from keeping each plot in figure memory
    pyplot.close()
    date += ONE_DAY
    sys.stdout.flush()

if animate:
    print 'creating animation'
    png_path = '*Hardiness-Temp-Histogram.png'
    template = '%d-Frost-Grape-%s-Hardiness-Temp-Histogram-animation.gif'
    anim_filename = template % (target_year, nameToFilepath(variety.name))
    anim_path = os.path.join(plot_dirpath, anim_filename)
    os.chdir(plot_dirpath)
    os.system('convert -delay %d %s -loop 0 %s' % (delay, png_path, anim_path))
    print 'animation complete', anim_path

