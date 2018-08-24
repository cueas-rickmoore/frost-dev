#!/Users/rem63/venvs/frost/bin/python

import os, sys
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate
from frost.functions import fromConfig

from frost.apple.factory import AppleGridFactory
from frost.apple.functions import plotWorkingDir

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-t', action='store', dest='temp_source', default='reported')
parser.add_option('-p', action='store', dest='point', default="-76.5,42,45")
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

temp_source = options.temp_source
test_file = options.test_file
# coordinates
ll = options.point.split(',')
target_lon = float(ll[0].strip())
target_lat = float(ll[1].strip())

# apple variety config
variety = fromConfig('crops.apple.variety.%s.self' % args[0])
# chill model
model = fromConfig('crops.apple.chill.%s.self' % args[1])

# get the date span
year = int(args[2])
month = int(args[3])
day = int(args[4])
start_date = datetime(year,month,day)
year = int(args[5])
month = int(args[6])
day = int(args[7])
end_date = datetime(year,month,day)

factory = AppleGridFactory()
target_year = factory.getTargetYear(start_date)

# get the map directory path and the template for the map file name
plot_dirpath = plotWorkingDir(target_year, variety.name, model.name,
                              'kill.at.stage', test_file)
filename_template = '%s-Frost-Apple-%s-Stage-vs-Kill-%%d.png'
filename_template = filename_template % (asAcisQueryDate(start_date),
                                         model.name.title())
filepath_template = plot_dirpath + os.sep + filename_template

# get the map title template and initialize the map title
title_template = '%s : %%s Kill at Stage\n%s\n%s'
time_span = '%s thru %s' % (start_date.strftime('%B %d, %Y'),
                            end_date.strftime('%B %d, %Y'))
title_template = title_template % (variety.description, model.description,
                                   time_span)

# get date indepenedent attributes and grids from the variety manager
variety_manager = factory.getVarietyGridManager(target_year,variety.name,'r',test_file)
gdd_thresholds = variety_manager.gddThresholds(model.name)
lo_gdd_th, hi_gdd_th = gdd_thresholds[0]

y, x = variety_manager.indexOfClosestNode(target_lon, target_lat)
print target_lon, y, target_lat, x
start_indx = variety_manager.indexFromDate(start_date)
end_indx = variety_manager.indexFromDate(end_date) + 1
days = range((end_indx - start_indx))

# get data for time span
#dataset_path = manager.modelDatasetPath(model.name, lo_gdd_th, hi_gdd_th,
#                                        'stage', 'index')
#stage_data = manager.getDataset(dataset_path)[start_indx:end_indx, y, x]
#print stage_data

#dataset_path = manager.modelDatasetPath(model.name, lo_gdd_th, hi_gdd_th,
#                                        'kill', 'level')
#kill_data = manager.getDataset(dataset_path)[sdate_indx:edate_indx, y, x]

# temperature grid manager
temp_manager = factory.getTempGridManager(target_year, 'r', test_file)
mint_dataset = '%s.mint' % temp_source
mint = temp_manager.getDataset(mint_dataset)[start_indx:end_indx, y, x]

kill_levels = variety.kill_levels
kill_temps = variety.kill_temps.attr_list
colors = ('blue','yellow','red')

for level in (0,1,2):
    # initialize figure
    figure = pyplot.figure(figsize=(8,6),dpi=100)
    axis = figure.gca(projection='3d')
    #axis.azim = 45

    for stage, stage_kill in enumerate(kill_temps):
        kill_temp = stage_kill[level]
        #diffs = mint - kill_temp

        axis.plot([stage,stage],[0,days[-1]],[kill_temp,kill_temp], c='r')
        x = [stage for day in days]
        axis.plot(x, days, mint, c='b')

    #axis.set_xlabel('Longitude', fontsize=20)
    #axis.set_ylabel('Latitude', fontsize=20)
    axis.grid(True)

    #ax_pos = axis.get_position()
    #l,b,w,h = ax_pos.bounds
    #color_axis = pyplot.axes([l+w, b, 0.025, h])

    #pyplot.axes(axis)

    kill_level = kill_levels[level]
    title = title_template % ('%sd%%' % kill_level)
    pyplot.suptitle(title, fontsize=12)

    output_filepath = filepath_template % kill_level
    figure.savefig(output_filepath)
    print 'plot saved to', output_filepath


