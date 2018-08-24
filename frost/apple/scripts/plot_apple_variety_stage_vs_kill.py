#!/usr/bin/env python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
from matplotlib.ticker import Formatter

import numpy as N

from frost.functions import fromConfig
from frost.visual.maps import drawLabeledColorBar

from frost.apple.factory import AppleGridFactory
from frost.apple.functions import getAppleVariety

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

parser.add_option('-c', action='store', dest='coords', default="-76.5,42,45")
parser.add_option('-l', action='store', dest='location', default="Geneva, NY")
parser.add_option('-t', action='store', dest='temp_source', default='reported')
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-y', action='store_true', dest='test_file', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

temp_source = options.temp_source
test_file = options.test_file
# coordinates
ll = options.coords.split(',')
lon = float(ll[0].strip())
lat = float(ll[1].strip())
coords = (lon, lat)
location = options.location

# apple variety config
variety = getAppleVariety(args[0])
# chill model
model = fromConfig('crops.apple.chill.%s.self' % args[1])

# get the date span
year = int(args[2])
month = int(args[3])
day = int(args[4])
start_date = datetime(year,month,day)
if len(args) >=  8:
    year = int(args[5])
    month = int(args[6])
    day = int(args[7])
    end_date = datetime(year,month,day)
else: end_date = datetime.date.today() - relativedelta(days=1)

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

factory = AppleGridFactory()
target_year = factory.getTargetYear(start_date)

plot_options = \
fromConfig('crops.apple.variety.plots.options.hardiness_vs_temp').copy()
plot_options['coords'] = coords
plot_options['location'] = location
plot_options['variety'] = variety.description
temp_units = plot_options.temp_units

# initialize figure and GCA
figure = pyplot.figure(figsize=plot_options.figsize,dpi=100)
axis = figure.gca()

# read the reported mint for the current season
reader = factory.getTempGridReader(target_year)
# turn start/end dates into a list of date indexes
start, end = reader._indexesForDates('reported.mint', start_date, end_date)
days = N.array([ day for day in range(1, (end - start)+1) ])

# get minimum temperatures
mint = reader.getDateAtNode('reported.mint', lon, lat, start_date, end_date, 
                            units=temp_units)
reader.close()
# draw the mint line
pyplot.plot(days, mint, c='k', label='Minimum Temp')
ymax = N.nanmax(mint)
ymin = N.nanmin(mint)

# read the variety stage data
reader = factory.getVarietyGridReader(target_year, variety)
dataset_path = reader.modelDatasetPath('carolina', 45, 86, 'stage','index')
stage = reader.getDateAtNode(dataset_path, lon, lat, start_date, end_date)
reader.close()
del reader

# create arrays of kill temps for each kill level based on current stage
all_nans = N.empty(stage.shape, dtype=float)
all_nans.fill(N.nan)
kill_temps = [ all_nans.copy(), all_nans.copy(), all_nans ]

stages = [ ]
stage_indx = 0
for stage_key, kill_levels in variety.kill_temps.attrs.items():
    stage_indx += 1
    for indx, temp in enumerate(kill_levels):
        indexes = N.where(stage == stage_indx)
        if len(indexes[0]) > 0:
            kill_temps[indx][indexes] = float(temp)
            ymin = min(ymin, float(temp))
            ymax = max(ymax, float(temp))
        stages.append((stage_key, indexes))
del stage

# adjust ymin so the is room for a stage box for the first stage
ymin = ymin - 5.
ymax = ymax + 10.

# draw fill between min temp and curve for each stage
color_map = fromConfig('crops.apple.variety.stage_color_map')
prev_temp = None
for stage_key, indexes in stages:
    if prev_temp is not None:
        prev_indx = indexes[0][0] - 1
        ktemps = list(kill_temps[0][indexes])
        ktemps.insert(0, kill_temps[0][prev_indx])
        kt_days = list(days[indexes])
        kt_days.insert(0, days[prev_indx])
        base_temps = [ymin for day in range(len(indexes[0])+1)]
    else: # first stage on the plot
        ktemps = kill_temps[0][indexes]
        kt_days = days[indexes]
        base_temps = [ymin for indx in tuple(indexes[0])]
    prev_temp = ktemps[0]
    pyplot.fill_between(kt_days, ktemps, base_temps,
                        facecolor=color_map[stage_key], alpha=0.05)

# draw a line for each kill potential
axis.plot(days, kill_temps[0], c='b', label='10% Kill Potential')
axis.plot(days, kill_temps[1], c='orange', label='50% Kill Potential')
axis.plot(days, kill_temps[2], c='r', label='90% Kill Potential')

# set X axis date limits before we draw anything
pyplot.xlim(days[0],days[-1])
pyplot.ylim(ymin,ymax)
# add X,Y axis labels, background grid and legend
#axis.xaxis.set_major_locator = date_locator
axis.xaxis.set_major_formatter(DateFormatter(start_date))
axis.set_xlabel(plot_options.timeSpan(start_date, end_date), fontsize=12)
y_label_units = chr(176) +'F'
axis.set_ylabel('Temperature %s' % y_label_units.decode('latin1'), fontsize=12)
axis.grid(True)

# add a legend for the lines
pyplot.legend(prop={'size':10}, loc=2, fancybox=True, framealpha=0.5)
# add a color bar for the filled areas
print plot_options.attrs
drawLabeledColorBar(figure, figure, **plot_options.attrs)

# draw the axes
pyplot.axes(axis)

# post title
template = fromConfig('crops.apple.variety.plots.titles.hardiness_vs_temp')
pyplot.suptitle(template % plot_options, fontsize=12)
template = '%s-kill-potential-%s.%s.png'
plotpath = template % (variety.name, start_date.strftime('%m.%d'),
                       end_date.strftime('%m.%d'))
figure.savefig(plotpath)
print plotpath

"""
# save to output file
location = plot_options.location.replace(',','')
plot_options['location'] = location.replace(' ','')
plot_group = plot_options.plot_group % plot_options
plot_options['location'] = location.replace(' ','-')
plot_key = plot_options.plot_key % plot_options
plot_filepath = plotFilepath(end_date, variety, plot_group, plot_key, test_file)
figure.savefig(plot_filepath)
#print 'plot saved to', plot_filepath
"""
# turn annoying numpy warnings back on
warnings.resetwarnings()
