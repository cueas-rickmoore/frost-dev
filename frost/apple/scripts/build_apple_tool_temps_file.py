#! /Volumes/projects/venvs/frost/bin/python

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
exit_quietly = not debug
is_dev_build = options.is_dev_build
verbose = options.verbose or debug

today = datetime.date.today()
last_usable_obs = today - ONE_DAY
last_usable_obs_str = last_usable_obs.strftime('%Y-%m-%d')

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
        if exit_quietly: sys.exit(0)
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
if reader.datasetHasAttribute('reported.maxt', 'last_valid_date'):
   last_valid_date = reader.datasetAttribute('reported.maxt', 'last_valid_date')
   last_valid = datetime.date(*tuple([int(d) for d in last_valid_date.split('-')]))

   if last_valid > last_usable_obs:
       season_dates['last_obs_date'] = last_usable_obs_str
       season_dates['last_valid_date'] = last_usable_obs_str
   else:
       season_dates['last_obs_date'] = last_valid_date
       season_dates['last_valid_date'] = last_valid_date

print 'Copying : ', reader.filepath
manager = Hdf5DateGridFileManager(tool_filepath, mode='a')
print 'To : ', manager.filepath
copyHdf5DategridFile(reader, manager, factory.tool.fileattrs.attrs, datasets,
                     exclusions)
del reader

manager.open('a')
manager.move('reported','temps')
if 'last_obs_date' in season_dates:
    manager.setDatasetAttribute('temps.maxt', 'last_obs_date', season_dates['last_obs_date'])
    manager.setDatasetAttribute('temps.mint', 'last_obs_date', season_dates['last_obs_date'])
if 'last_valid_date' in season_dates:
    manager.setDatasetAttribute('temps.maxt', 'last_valid_date', season_dates['last_valid_date'])
    manager.setDatasetAttribute('temps.mint', 'last_valid_date', season_dates['last_valid_date'])
manager.close()

# copy forecast tempratures to the build file
if add_forecast:
    fcast_reader = factory.sourceFileReader(source, fcast_year, region,
                                            'temps', filepath=shared_filepath)
    print('Reading forecast from : %(shared)s' % {"shared":shared_filepath,})
    last_obs = fcast_reader.dateAttribute('temps.maxt', 'last_obs_date')
    fcast_end = fcast_reader.dateAttribute('temps.maxt', 'fcast_end_date', None)
    if fcast_end is None or fcast_end < season_start:
        fcast_reader.close()
        if verbose:
            if fcast_end is None:
                print 'FILE ERROR: ', factory.filepath
                print 'DATE MISSING: "fcast_end_date" not specified in "temsp.maxt"'
            elif fcast_end < season_start:
                msg = 'TOO EARLY: forecast end (%s) is before season start (%s)'
                print msg % (fcast_end.strftime("%Y-%m-%d"),
                             season_start.strftime("%Y-%m-%d"))
        os.exit()
    if fcast_end > season_end: fcast_end = season_end

    fcast_start = fcast_reader.dateAttribute('temps.maxt', 'fcast_start_date', None)
    if fcast_start is None or fcast_start >= season_end:
        fcast_reader.close()
        if verbose:
            if fcast_start is None:
                print 'FILE ERROR: ', factory.filepath
                print 'DATE MISSING: "fcast_start_date" not specified in "temps.maxt"'
            elif fcast_start >= season_end:
                msg = 'TOO LATE: forecast start (%s) is after season end (%s)'
                print msg % (fcast_start.strftime("%Y-%m-%d"),
                             season_end.strftime("%Y-%m-%d"))
        os.exit()
    if fcast_start <= last_obs:
        fcast_start = last_obs + ONE_DAY
        if verbose:
            msg = 'ADJUSTING: forecast start (%s) is before last observation (%s)'
            print msg % (fcast_start.strftime("%Y-%m-%d"), last_obs.strftime("%Y-%m-%d"))

    # TODO
    # TODO need to handle cases where forecast spans end of year into next year
    # TODO
    print('Adding forecast to tool file')
    season_dates['fcast_end_date'] = fcast_end.strftime("%Y-%m-%d")
    season_dates['fcast_start_date'] = fcast_start.strftime("%Y-%m-%d")
    season_dates['last_obs_date'] = last_obs.strftime("%Y-%m-%d")
    season_dates['last_valid_date'] = season_dates['fcast_end_date']

    # create a file manager for the tool tempratures file
    manager = \
        FrostTempFileManager(target_year, mode='a', filepath=tool_filepath)
    frost_end_date = manager.dateAttribute('temps.maxt','last_valid_date')
    manager.close()
    # this should only happen on the first day when file is empty
    if frost_end_date is None: exit(0)

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

