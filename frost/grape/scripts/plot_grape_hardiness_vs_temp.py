#!/Users/rem63/venvs/frost/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
from matplotlib.ticker import Formatter

from frost.functions import fromConfig

from frost.grape.factory import GrapeGridFactory
from frost.grape.functions import getGrapeVariety, plotFilepath

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# create a date formatter for the X axis
class DateFormatter(Formatter):
    def __init__(self, start_date):
        self.start_date = start_date
    def __call__(self, x, pos=0):
        if pos == 0: return ''
        date = self.start_date + relativedelta(days=(x-1))
        return '%d/%d' % (date.month, date.day)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-c', action='store', dest='coords', default=None)
parser.add_option('-l', action='store', dest='location', default=None)
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = GrapeGridFactory()

test_file = options.test_file

# grape variety config
variety = getGrapeVariety(args[0])

# get the date span
date_args = args[1:]
num_date_args = len(date_args)
if num_date_args == 1: 
    target_year = int(date_args[0])
    start_date, end_date = factory.getTargetDateSpan(target_year)
elif num_date_args >= 3 :
    year = int(date_args[0])
    month = int(date_args[1])
    day = int(date_args[2])
    if num_date_args == 3:
        start_date = datetime(year,month,day)
        end_date = start_date
    elif num_date_args == 4:
        end_date = datetime(year,month,day)
        start_date = end_date - relativedelta(days=int(date_args[3])-1)
        print date_args[3], start_date, end_date
    elif num_date_args == 6:
        start_date = datetime(year,month,day)
        year = int(date_args[3])
        month = int(date_args[4])
        day = int(date_args[5])
        end_date = datetime(year,month,day)
    else:
        errmsg = 'Invalid number of date arguments : %d' % num_date_args
        raise ValueError, errmsg
    target_year = factory.getTargetYear(start_date)

# get the variety and temperature managers
variety_reader = factory.getVarietyReader(target_year, variety, test_file)
temp_reader = factory.getTempGridReader(target_year, test_file)

# get default plot options from configuration
plot_options = fromConfig('crops.grape.plots.options.hardiness_vs_temp').copy()
plot_options['variety'] = variety.description
temp_units = plot_options.temp_units

# apply overrides from input options (if any)
if options.location is None:
    target_lon, target_lat = plot_options.coords
else:
    plot_options.location = options.location
    if options.coords is not None:
        ll = options.coords.split(',')
        target_lon = float(ll[0].strip())
        target_lat = float(ll[1].strip())
        plot_options.coords = (target_lon, target_lat)
    else:
        errmsg = \
        'Both -c and -l options are required when requesting a custom location.'
        raise ValueError, errmsg

# indexes for grid node and date bounds
y, x = variety_reader.indexOfClosestNode(target_lon, target_lat)
start_indx, end_indx = \
variety_reader.indexesFromDates('hardiness.temp', start_date, end_date)
# turn start/end indexes into a list of dates
days = [ day for day in range(1, (end_indx - start_indx)+1) ]

# initialize figure and GCA
figure = pyplot.figure(figsize=plot_options.figsize,dpi=100)
axis = figure.gca()
# set X axis date limits before we draw anything
pyplot.xlim(days[0],days[-1])
pyplot.ylim(*plot_options.temp_limits)

# draw the temp overlays
maxt = temp_reader.getDateAtNode('reported.maxt', target_lon, target_lat,
                                   start_date, end_date, units='F')
mint = temp_reader.getDateAtNode('reported.mint', target_lon, target_lat,
                                   start_date, end_date, units='F')

pyplot.fill_between(days, maxt, mint, facecolor='b', alpha=0.2)
pyplot.plot(days, maxt, c='b', label='Max Temp')
pyplot.plot(days, mint, c='b', label='Min Temp')
del maxt, mint

# draw a line showing the hardiness at each day
y, x = variety_reader.ll2index(target_lon, target_lat)
start, end = \
variety_reader._indexesForDates('hardiness.temp', start_date, end_date)
hardiness = variety_reader.getDataset('hardiness.temp')

hardiness = variety_reader.getDateAtNode('hardiness.temp', target_lon,
                           target_lat, start_date, end_date, units='F')
axis.plot(days, hardiness, c='r', label='Hardiness')
del hardiness

# add X,Y axis labels, background grid and legend
#axis.xaxis.set_major_locator = date_locator
axis.xaxis.set_major_formatter(DateFormatter(start_date))
#figure.autofmt_xdate()
axis.set_xlabel('Date', fontsize=12)
y_label_units = chr(176) +'F'
axis.set_ylabel('Temperature %s' % y_label_units.decode('latin1'), fontsize=12)
axis.grid(True)
pyplot.legend(prop={'size':10}, fancybox=True, framealpha=0.5)

# draw the axes
pyplot.axes(axis)

# post title
template = fromConfig('crops.grape.plots.titles.hardiness_vs_temp')
pyplot.suptitle(template % plot_options, fontsize=12)
pyplot.title(plot_options.timeSpan(start_date, end_date), fontsize=12)

# save to output file
location = plot_options.location.replace(',','')
plot_options['location'] = location.replace(' ','')
plot_group = plot_options.plot_group % plot_options
plot_options['location'] = location.replace(' ','-')
plot_key = plot_options.plot_key % plot_options
plot_filepath = plotFilepath(end_date, variety, plot_group, plot_key, test_file)
figure.savefig(plot_filepath)
print 'plot saved to', plot_filepath

