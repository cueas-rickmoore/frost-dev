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

# variety
variety = getGrapeVariety(args[0])
variety_path = nameToFilepath(variety.name)

# full dataset path
full_dataset_path = args[1]
# actually need individual parts of dataset path
path_list = full_dataset_path.split('.')
data_group = data_group = path_list[0]
dataset_name = path_list[-1]
if data_group == 'chill':
    group_path = '.'.join(path_list[:-1]
    title_key = ' '.join([name.title() for name in path_list.reverse()])
else:
    group_path = data_group
    title_key = dataset_name.title()

# get the date
date_args = len(args[2:])
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

if end_date is None: past_date = start_date + ONE_DAY
else: past_date = end_date + ONE_DAY

factory = GrapeGridFactory()
target_year = factory.getTargetYear(start_date)

# get the map directory path and the template for the map file name
map_dirpath = \
    plotWorkingDir(target_year, variety, title_key, 'histograms', test_file)

template = '%%s-Frost-Grape-%s-%s-Histogram.png'
template = template % (variety_path, title_key.replace(' ','-'))
filepath_template = map_dirpath + os.sep + template

title = u"%s - Hardiness Temperature" % variety.description

manager = factory.getVarietyManager(target_year, variety, 'r', test_file)
lats = manager.lats
lons = manager.lons

# contour bounds in degrees F (~ -26.1 to -1.1 C)
bins = [-15. + (n * 2.5) for n in range(20)]
# extended range for a few varieties 
if manager.hardiness.max < -26.25: # this is degrees C
    bins = [ -22.5, -20., -17.5 ] + bins

from matplotlib import pyplot
date = start_date
while date < past_date:
    hard_temp = manager.getHardiness(date, units='F')

    figure = pyplot.figure()
    axis = figure.add_subplot(111)
    pyplot.xlim(bins[0], bins[-1])
    pyplot.ylim(0, 100000)
    axis.hist(hard_temp.flatten(), bins, normed=False, histtype='bar', rwidth=0.8)

    pyplot.suptitle(title, fontsize=12)
    pyplot.title(date.strftime('%B %d, %Y'), fontsize=12)

    output_filepath = filepath % asAcisQueryDate(date)
    figure.savefig(output_filepath)
    print 'plot saved to', output_filepath
    # need this stop Matplotlib from keeping each plot in figure memory
    pyplot.close()
    date += ONE_DAY

if animate:
    print 'creating animation'
    title_key = title_key.replace(' ','-'))
    png_path = '%s-%s-Histogram.png' % (variety_path, title_key)
    template = '%d-Frost-Grape-%s-%s-Histogram-animation.gif'
    anim_filename = template % (target_year, nameToFilepath(variety.name))
    anim_path = os.path.join(map_dirpath, anim_filename)
    os.chdir(map_dirpath)
    os.system('convert -delay %d %s -loop 0 %s' % (delay, png_path, anim_path))
    print 'animation complete', anim_path

