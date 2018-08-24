#! /usr/bin/env python

import os, sys
import datetime
ONE_DAY = datetime.timedelta(days=1)

from atmosci.hdf5.dategrid import Hdf5DateGridFileManager
from atmosci.hdf5.dategrid import Hdf5DateGridFileReader

from frost.temperature import FrostTempFileManager
from frost.apple.tool.factory import AppleToolFactory
from frost.apple.tool.copyfile import copyHdf5DategridFile


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-d', action='store_true', dest='is_dev_build',
                        default=False)
parser.add_option('-f', action='store_false', dest='forecast', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

add_forecast = options.forecast
debug = options.debug
is_dev_build = options.is_dev_build
verbose = options.verbose or debug

today = datetime.date.today()
fcast_year = today.year

factory = AppleToolFactory()
region = factory.region()
source = factory.source()

# TODO
# TODO need to handle cases where forecast spans end of year into next year
# TODO
if len(args) == 1:
    target_year, season_start, season_end = factory.seasonDates(int(args[0]))
else:
    target_year, season_start, season_end = factory.seasonDates(today)
    if today < season_start or today > season_end:
        # quietly exit when outside season ... useful when in cron
        if exit_quitely: os.exit(0)
        errmsg = "Taday's date is not within season limits. Try passing the"
        errmsg += "%s target year as an argument on the command line."
        raise ValueError, errmsg
num_days = (season_end - season_start).days + 1

season_dates = {'start_date':season_start.strftime('%Y-%m-%d'),
                'end_date':season_end.strftime('%Y-%m-%d'),
               }

# TODO
# TODO need to handle cases where forecast spans end of year into next year
# TODO
# root directory is possibly different for development and production cases
if is_dev_build:
    frost_filepath = factory.devFilepath('frost', target_year, region,
                                          source, 'temp', 'tempext')
    shared_filepath = factory.devFilepath('shared', fcast_year, region,
                                          source, 'temps', 'tempext')
    tool_filepath = factory.devFilepath('tool', target_year, region,
                                        source, 'temps', 'tempext')
else:
    frost_filepath = factory.toolFilepath('frost', target_year, region,
                                          source, 'temp', 'tempext')
    shared_filepath = factory.toolFilepath('shared', fcast_year, region,
                                           source, 'temps', 'tempext')
    tool_filepath = factory.toolFilepath('tool', target_year, region,
                                         source, 'temps', 'tempext')

# copy temperatire file from Frost daily build to tool build dirctory
if os.path.exists(tool_filepath): os.remove(tool_filepath)

# setup file copy paramaeters
exclusions = ('forecast','forecast.maxt','forecast.maxt_provenance',
                         'forecast.mint','forecast.mint_provenance')
datasets = {'lat': factory.tool.datasets.lat.attrs,
            'lon': factory.tool.datasets.lon.attrs,
            'reported.maxt': {'description':'Maximum Temperture',},
            'reported.mint': {'description':'Minimum Temperture',},
           }
data_attrs = factory.tool.datasets.data.attrs
datasets['lat'].update(data_attrs)
datasets['lon'].update(data_attrs)
datasets['reported.maxt'].update(data_attrs)
datasets['reported.mint'].update(data_attrs)
# time attributes used by date grid handlers to access data by date
time_attrs = factory.tool.datasets.time.attrs
datasets['reported.maxt'].update(time_attrs)
datasets['reported.mint'].update(time_attrs)
# time attributes used by date grid handlers to access provenance by date
provenance_attrs = factory.tool.datasets.provenance.attrs

# copy frost temperature file to frapple build directory
reader = Hdf5DateGridFileReader(frost_filepath)
season_dates['last_valid_date'] = \
             reader.datasetAttribute('reported.maxt', 'last_valid_date')
season_dates['last_obs_date'] = season_dates['last_valid_date'] 
print 'Copying : ', reader.filepath
manager = Hdf5DateGridFileManager(tool_filepath, mode='a')
print 'To : ', manager.filepath
copyHdf5DategridFile(reader, manager, factory.tool.fileattrs.attrs, datasets,
                     exclusions)
del reader
manager.open('a')
manager.move('reported','temps')
manager.close()

# copy forecast tempratures to the build file
if add_forecast:
    fcast_reader = factory.sourceFileReader(source, fcast_year, region,
                                            'temps', filepath=shared_filepath)
    fcast_end = fcast_reader.dateAttribute('temps.maxt', 'fcast_end_date')
    if fcast_end <= today:
        fcast_reader.close()
        exit()
    print('Reading forecast from : %(shared)s' % {"shared":shared_filepath,})
    fcast_start = fcast_reader.dateAttribute('temps.maxt', 'fcast_start_date')
    if fcast_start < today: fcast_start = today

    # TODO
    # TODO need to handle cases where forecast spans end of year into next year
    # TODO
    print('Adding forecast to tool file')
    season_dates['fcast_end_date'] = fcast_end.strftime("%Y-%m-%d")
    season_dates['fcast_start_date'] = fcast_start.strftime("%Y-%m-%d")
    season_dates['last_obs_date'] = \
                 fcast_reader.datasetAttribute('temps.maxt', 'last_obs_date')
    season_dates['last_valid_date'] = season_dates['fcast_end_date']

    # create a file manager for the tool tempratures file
    manager = \
        FrostTempFileManager(target_year, mode='a', filepath=tool_filepath)
    frost_end_date = manager.dateAttribute('temps.maxt','last_valid_date')
    manager.close()
    slice_start = frost_end_date + ONE_DAY
    slice_datetime = \
        datetime.datetime(slice_start.year, slice_start.month, slice_start.day)

    for extreme in ('maxt','mint'):
        # add forecast temps (and any missing days prior to forecast)
        # TODO
        # TODO need handle case where forecast spans end of year into next year
        # TODO
        dataset_name = 'temps.%s' % extreme
        data = fcast_reader.dateSlice(dataset_name, slice_start, fcast_end)
        if debug:
            print 'updateTemp for', dataset_name
            print '    slice :', slice_start, ':', slice_datetime
            print data
        manager.open('a')
        manager.updateTemp(dataset_name, data, slice_datetime)
        manager.close()
        manager.open('a')
        manager.setDatasetAttributes(dataset_name, **season_dates)
        dataset_name += '_provenance'
        manager.setDatasetAttributes(dataset_name, **season_dates)
        manager.setDatasetAttributes(dataset_name, **provenance_attrs)
        manager.close()
    fcast_reader.close()

print 'Key dates for new file :'
for key in season_dates.keys():
    print('    %s = %s' % (key, season_dates[key]))

