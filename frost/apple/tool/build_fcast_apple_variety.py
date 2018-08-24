#! /usr/bin/env python

import os, sys
from copy import deepcopy
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)

import numpy as N

from atmosci.hdf5.dategrid import Hdf5DateGridFileManager, \
                                  Hdf5DateGridFileReader
from atmosci.utils.options import stringToTuple
from atmosci.utils.timeutils import DateIterator, asDatetime
from atmosci.utils.timeutils import daysInYear, lastDayOfMonth

from frost.functions import fromConfig
from frost.apple.functions import getAppleVariety
from frost.apple.variety.grid import AppleVarietyGridManager

from frost.apple.tool.factory import AppleToolFactory
from frost.apple.tool.copyfile import copyHdf5DategridFile


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-d', action='store_true', dest='is_dev_build',
                        default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

is_dev_build = options.is_dev_build
verbose = options.verbose
debug = options.debug or verbose

today = datetime.date.today()
fcast_year = today.year

factory = AppleToolFactory()
region = factory.region()
source = factory.source()

# TODO
# TODO need to handle cases where forecast spans end of year into next year
# TODOL43H86.gddi
if len(args) == 1:
    variety = getAppleVariety(args[0])
    target_year, season_start, season_end = factory.seasonDates(today)
    if today < season_start or today > season_end:
        # quietly exit when outside season ... useful when in cron
        if exit_quitely: os.exit(0)
        errmsg = "Taday's date is not within season limits. Try passing the"
        errmsg += "%s target year as an argument on the command line."
        raise ValueError, errmsg
else:
    target_year, season_start, season_end = factory.seasonDates(int(args[0]))
    variety = getAppleVariety(args[1])

season_dates = {'start_date':season_start.strftime('%Y-%m-%d'),
                'end_date':season_end.strftime('%Y-%m-%d'),
               }

# root directory is possibly different for development and production cases
if is_dev_build:
    frost_filepath = factory.devFilepath('frost', target_year, region,
                                          source, variety, 'variety')
    chill_filepath = factory.devFilepath('tool', target_year, region,
                                         source, 'chill')
    temps_filepath = factory.devFilepath('tool', target_year, region,
                                         source, 'temps', 'tempext')
    tool_filepath = factory.devFilepath('tool', target_year, region,
                                        source, variety, 'variety')
else:
    frost_filepath = factory.toolFilepath('frost', target_year, region,
                                          source, variety, 'variety')
    chill_filepath = factory.toolFilepath('tool', target_year, region,
                                          source, 'chill')
    temps_filepath = factory.toolFilepath('tool', target_year, region,
                                          source, 'temps', 'tempext')
    tool_filepath = factory.toolFilepath('tool', target_year, region,
                                         source, variety, 'variety')
if os.path.exists(tool_filepath): os.remove(tool_filepath)

# set parameters for copy function
exclusions = ('Utah','Utah.L43H86', 'Utah.L43H86.gdd',
              'Utah.L43H86.gdd.accumulated', 'Utah.L43H86.gdd.chill_mask',
              'Utah.L43H86.gdd.provenance',
              'Utah.L43H86.kill', 'Utah.L43H86.kill.level',
              'Utah.L43H86.kill.provenance',
              'Utah.L43H86.stage', 'Utah.L43H86.stage.index',
              'Utah.L43H86.stage.provenance',
             )

datasets = {'lat': factory.tool.datasets.lat.attrs,
            'lon': factory.tool.datasets.lon.attrs,
           }
data_attrs = factory.tool.datasets.data.attrs
datasets['lat'].update(data_attrs)
datasets['lon'].update(data_attrs)
datasets['Carolina.L43H86.gdd.accumulated'] = deepcopy(data_attrs)
datasets['Carolina.L43H86.gdd.chill_mask'] = deepcopy(data_attrs)
datasets['Carolina.L43H86.stage.index'] = deepcopy(data_attrs)
datasets['Carolina.L43H86.kill.level'] = deepcopy(data_attrs)

time_attrs = factory.tool.datasets.time.attrs
datasets['Carolina.L43H86.gdd.accumulated'].update(time_attrs)
datasets['Carolina.L43H86.gdd.chill_mask'].update(time_attrs)
datasets['Carolina.L43H86.stage.index'].update(time_attrs)
datasets['Carolina.L43H86.kill.level'].update(time_attrs)

prov_attrs = factory.tool.datasets.provenance.attrs
datasets['Carolina.L43H86.gdd.provenance'] = deepcopy(prov_attrs)
datasets['Carolina.L43H86.stage.provenance'] = deepcopy(prov_attrs)
datasets['Carolina.L43H86.kill.provenance'] = deepcopy(prov_attrs)

# get last valid from from frost's variety file
frost_reader = Hdf5DateGridFileReader(frost_filepath)
last_valid_date = frost_reader.dateAttribute('Carolina.L43H86.gdd.accumulated',
                                             'last_valid_date')
# start date for this build is one day after last valid date
start_date = last_valid_date + ONE_DAY
start_datetime = asDatetime(start_date)
frost_reader.close()

# get mint and key dates
temps_reader = Hdf5DateGridFileReader(temps_filepath)
end_date = temps_reader.dateAttribute('temps.mint', 'last_valid_date')
mint = temps_reader.dateSlice('temps.mint', start_date, end_date)
temps_reader.close()
del temps_reader

# create a chill file reader
chill_reader = Hdf5DateGridFileReader(chill_filepath)
# key dates MUST match the chill grids, not the copied variety file
temps_dates = chill_reader.dateAttributes('Carolina.accumulated')
chill_reader.close()
date_attrs = {'last_obs_date':temps_dates['last_obs_date'],
              'last_valid_date':temps_dates['last_valid_date'],
              'fcast_start_date':temps_dates['fcast_start_date'],
              'fcast_end_date':temps_dates['fcast_end_date'],
             }
# add key dates to each dataset's attributes
datasets['Carolina.L43H86.gdd.accumulated'].update(date_attrs)
datasets['Carolina.L43H86.gdd.chill_mask'].update(date_attrs)
datasets['Carolina.L43H86.gdd.provenance'].update(date_attrs)
datasets['Carolina.L43H86.stage.index'].update(date_attrs)
datasets['Carolina.L43H86.stage.provenance'].update(date_attrs)
datasets['Carolina.L43H86.kill.level'].update(date_attrs)
datasets['Carolina.L43H86.kill.provenance'].update(date_attrs)

print 'Copying : ', frost_reader.filepath
frost_reader.open()
builder = Hdf5DateGridFileManager(tool_filepath, mode='a')
print 'To : ', builder.filepath
copyHdf5DategridFile(frost_reader, builder, factory.tool.fileattrs.attrs,
                     datasets, exclusions, debug)
builder.close()
frost_reader.close()
del frost_reader, builder

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# update the stage grids with 6-day forecast
manager = AppleVarietyGridManager(target_year, variety, mode='a',
                                  filepath=tool_filepath)
chill_reader.open()
for model in factory.tool.project.models:
    proper_name = manager.properName(model)
    # get the Chill accumulation
    dataset_path = '%s.accumulated' % model.title()
    end_date = chill_reader.dateAttribute(dataset_path, 'fcast_end_date')
    accumulated_chill = \
        chill_reader.dateSlice(dataset_path, start_date, end_date)
    #  loop trough all GDD thresholds
    for lo_gdd, hi_gdd in factory.tool.project.gdd_thresholds:
        # get daily GDD from the chill grid file
        dataset_path = 'gdd.L%dH%d.daily' % (lo_gdd, hi_gdd)
        daily_gdd = chill_reader.dateSlice(dataset_path, start_date, end_date)

        # calculuate accumulated GDD from daily gdd
        # let manager get accumulated GDD for previous day
        manager.open('a')
        accumulated_gdd, chill_mask = \
        manager.accumulateGdd(model, lo_gdd, hi_gdd, start_date,
                              accumulated_chill, daily_gdd)
        manager.updateGdd(model, lo_gdd, hi_gdd, accumulated_gdd, chill_mask,
                          start_datetime)
        manager.close()
        # no longer need grid for daily GDD
        del daily_gdd

        # generate stage grid from accumulated GDD
        stage_grid = manager.gddToStages(accumulated_gdd)
        manager.open('a')
        manager.updateStage(model, lo_gdd, hi_gdd, stage_grid, start_datetime)
        manager.close()
        # no longer need grid for accumulated GDD
        del accumulated_gdd

        # estimate kill probability from stages and predicted mint
        kill_grid = manager.estimateKill(stage_grid, mint)
        manager.open('a')
        manager.updateKill(model, lo_gdd, hi_gdd, kill_grid, start_datetime)
        manager.close()
        # no longer need stage or kill grids
        del stage_grid, kill_grid

# set attributes needed by atmosci.hdf5.dategrid and apple frost tool
#for dataset_path, attributes in datasets.items():
#    manager.open('a')
#    manager.setDatasetAttributes(dataset_path, **attributes)
#    manager.close()

# turn annoying numpy warnings back on
warnings.resetwarnings()

