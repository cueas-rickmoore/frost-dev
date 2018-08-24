#! /Users/rem63/venvs/frost/bin/python

import os, sys
from copy import copy
import subprocess, shlex

from datetime import datetime
from dateutil.relativedelta import relativedelta

from atmosci.utils.report import Reporter

from frost.functions import buildLogFilepath, fromConfig, targetYearFromDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

GRAPE = fromConfig('crops.grape')

#APP = os.path.splitext(os.path.split(__file__)[1])[0].upper().replace('_',' ')
APP = os.path.split(sys.argv[0])[1] + ' ' + ' '.join(sys.argv[1:])
#PID = os.getpid()
PID = 'PID %d' % os.getpid()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#CRON_SCRIPT_DIR = '/Users/rrem63/venvs/frost/cron'
CRON_SCRIPT_DIR = os.path.split(os.path.abspath(sys.argv[0]))[0]
ONE_DAY = relativedelta(days=1)
PYTHON_EXECUTABLE = sys.executable

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

AS_MSG = 'ACTIVE SCRIPT : %s %s'
CALL_MSG = 'called %s for %s'
FAILURE = '%s for %s failed with return code %d'
IP_MSG = 'INITIATE PROCESS : %s %s for %s'
SUCCESS = 'COMPLETED : %s for %s'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DummyProcess(object):

    def __init__(self):
        self.returncode = 0

    def poll(self): pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ProcessServer(object):

    PROCESS_INIT_METHODS = {}

    def __init__(self, reporter, season_start, download_temps, build_grids,
                       draw_plots, publish_maps, plot_days, plot_coords,
                       debug=False, test_run=False):
        self.active_script = None
        self.debug = debug
        self.plot_days = plot_days
        self.plot_location = ' -c %s' % plot_coords
        self.relative_plot_days = relativedelta(days=plot_days)
        self.reporter = reporter
        self.season_start = season_start
        self.target_year = targetYearFromDate(season_start)
        self.test_run = test_run

        varieties = list(GRAPE.varieties.build)
        varieties.reverse()

        scripts = [ ]
        for variety in varieties:
            if publish_maps:
               scripts.append( ('publish_graphics', variety) )
               scripts.append( ('animate', (variety, 'hardiness.temp')) )
               scripts.append( ('animate', (variety, 'kill.potential')) )
            if draw_plots:
               scripts.append( ('map_hard_temp', variety) )
               scripts.append( ('map_kill_potential', variety) )
               scripts.append( ('plot_hard_temp', variety) )
            if build_grids:
               scripts.append( ('build_dormancy', variety) )
               scripts.append( ('build_hardiness', variety) )
        if download_temps: scripts.append( ('download_temp', None) )
        self.all_scripts = tuple(scripts)
        if debug: print 'all scripts', self.all_scripts

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def run(self, date):
        self.frost_date = date
        self.frost_date_arg = date.strftime('%Y %m %d')
        self.frost_date_str = date.strftime('%B %d, %Y')
        self.temp_date = date + ONE_DAY
        self.process_queue = list(self.all_scripts)

        debug = self.debug
        keep_on_trucking = True
        active_process = None

        while keep_on_trucking:
            # service active process
            if active_process is not None:
                active_process.poll()
                retcode = active_process.returncode
                if retcode is not None:
                    active_process =\
                        self.completeProcess(active_process, retcode)
                    if active_process is None:

                        msg = 'Completed grape daily build for'
                        print msg, self.frost_date.strftime('%B %d, %Y')
                        keep_on_trucking = False
            else:
                process = self.nextProcess()
                if debug: print 'next script :', process
                active_process = self.initiateProcess(process)

        self.reporter.logEvent('BUILD SERVER EXITING')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def completeProcess(self, active_process, retcode):
        reporter = self.reporter
        if retcode <= 0:
            msg = SUCCESS % (self.active_script, self.frost_date_str)
            reporter.logEvent(msg)
        else:
            errmsg = \
            FAILURE % (self.active_script, self.frost_date_str, retcode)
            reporter.logError(errmsg)
            reporter.reportError(errmsg)
            exit()

        next_process = self.nextProcess()
        if next_process is not None:
            return self.initiateProcess(next_process)
        return None

    def initiateProcess(self, process):
        if process is not None:
            self.active_process = process
            script, args = process
            initProcess = self.PROCESS_INIT_METHODS[script]
            if args is None: return initProcess(self)
            elif isinstance(args, tuple): return initProcess(self, *args)
            else: return initProcess(self, args)
        else: return None

    def nextProcess(self):
        if self.process_queue:
            return self.process_queue.pop()
        return None

    def runSubprocess(self, script, args):
        self.reporter.logEvent(AS_MSG % (script,args))
        command = [PYTHON_EXECUTABLE, os.path.join(CRON_SCRIPT_DIR, script)]
        command.extend(args.split())
        if self.debug: print 'command :', command
        self.active_script = script
        return subprocess.Popen(command, shell=False, env=os.environ)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initiateBuildDormancyGrids(self, variety_name):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateBuildDormancyGrids', date
            msg = CALL_MSG % ('initiateBuildDormancyGrids', date)
            self.reporter.logInfo(msg)
        if self.test_run:
            return DummyProcess()
        script = 'build_grape_dormancy_grids.py'
        args = '%s %s' % (variety_name, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['build_dormancy'] = initiateBuildDormancyGrids

    def initiateBuildHardinessGrids(self, variety_name):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateBuildHardinessGrids', variety_name, date
            msg = CALL_MSG % ('initiateBuildHardinessGrids', date)
            self.reporter.logInfo(msg)
        if self.test_run: return DummyProcess()
        script = 'build_grape_hardiness_grids.py'
        args = '%s %s' % (variety_name, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['build_hardiness'] = initiateBuildHardinessGrids

    def initiateMapAnimation(self, variety, map_key):
        if self.debug:
            print '\ninitiateMapAnimation', variety,  map_key
            self.reporter.logInfo(CALL_MSG % ('initiateMapAnimation',
                                              self.frost_date_str))
        #if self.test_run or self.frost_date < self.animation_dates[map_key]:
        #    return DummyProcess()
        script = 'animate_grape_maps.py'
        args = '%d %s %s' % (self.target_year, variety, map_key)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['animate'] = initiateMapAnimation

    def initiateMapHardinessTemps(self, variety_name):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateMapHardinessTemps', variety_name, date
            msg = CALL_MSG % ('initiateMapHardinessTemps', date)
            self.reporter.logInfo(msg)
        if self.test_run: return DummyProcess()

        script = 'draw_grape_hardiness_maps.py'
        args = '%s' % variety_name
        args += ' %s' % self.frost_date_arg
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['map_hard_temp'] = initiateMapHardinessTemps

    def initiateMapKillPotential(self, variety_name):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateMapKillPotential', variety_name, date
            msg = CALL_MSG % ('initiateMapKillPotential', date)
            self.reporter.logInfo(msg)
        if self.test_run: return DummyProcess()

        script = 'draw_grape_variety_kill_maps.py'
        args = '%s' % variety_name
        args += ' %s' % self.frost_date_arg
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['map_kill_potential'] = initiateMapKillPotential

    def initiatePlotHardinessTemps(self, variety_name):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiatePlotHardinessTemps', variety_name, date
            msg = CALL_MSG % ('initiatePlotHardinessTemps', date)
            self.reporter.logInfo(msg)
        if self.test_run: return DummyProcess()

        # test that enough days have elapsed to draw a reasonable plot
        if (self.frost_date - self.season_start).days < self.plot_days: 
            return DummyProcess() # not enough days

        script = 'plot_grape_hardiness_vs_temp.py'
        args = '%s' % variety_name
        plot_start_date = self.frost_date - self.relative_plot_days
        args += plot_start_date.strftime(' %Y %m %d')
        args += ' %s' % self.frost_date_arg
        args += self.plot_location
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['plot_hard_temp'] = initiatePlotHardinessTemps

    def initiatePublishGraphics(self, variety_name):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiatePublishGraphics', variety_name, date
            self.reporter.logInfo(CALL_MSG % ('initiatePublishGraphics', date))
        if self.test_run: return DummyProcess()
        script = 'publish_grape_graphics.py'
        args = '%s %s' % (variety_name, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['publish_graphics'] = initiatePublishGraphics

    def initiateTempDownload(self):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateTempDownload', date
            self.reporter.logInfo(CALL_MSG % ('initiateTempDownload', date))
        if self.test_run: return DummyProcess()
        script = 'download_latest_temp_grids.py'
        args = self.temp_date.strftime('%Y %m %d')
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['download_temp'] = initiateTempDownload

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser = OptionParser(usage="usage: %prog [year month day] [options]")
parser.add_option('--da', action='store', type='int', dest='days_ago',
                  default=1, help='start building N days ago')
parser.add_option('--nd', action='store', type='int', dest='num_days',
                  default=1, help='number of days to build')
parser.add_option('--mrt', action='store', type='string', dest='max_run_time',
                  default=None)
parser.add_option('--pc', action='store', type='string', dest='plot_coords',
                  default='-76.5,42.45')
parser.add_option('--pd', action='store', type='int', dest='plot_days',
                  default=30)

parser.add_option('-b', action='store_false', dest='build_grids', default=True)
parser.add_option('-d', action='store_false', dest='draw_plots', default=True)
parser.add_option('-l', action='store', type='string', dest='log_filepath',
                  default=None,
                  help='path to alternate file to be used for logging')
parser.add_option('-p', action='store_true', dest='publish_maps', default=False)
parser.add_option('-t', action='store_false', dest='download_temps',
                  default=True)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

build_grids = options.build_grids
download_temps = options.download_temps
draw_plots = options.draw_plots
num_days = options.num_days
plot_days = options.plot_days
plot_coords = options.plot_coords
publish_maps = options.publish_maps

debug = options.debug
test_run = options.test_run
if test_run: debug = True
if options.max_run_time is not None:
    max_run_time = options.max_run_time
    if max_run_time[-1] == ':':
        max_run_hours = int(max_run_time[:-1])
        max_run_minutes = 0
    elif max_run_time[0] == ':':
        max_run_hours = 0
        max_run_minutes = int(max_run_time[1:])
    else:
        colon = max_run_time.find(':')
        if colon > 0:
            max_run_hours = int(max_run_time[:colon])
            max_run_minutes = int(max_run_time[colon+1:])
        else:
            max_run_hours = int(max_run_time)
            max_run_minutes = 0
    max_run_time = relativedelta(hours=max_run_hours,
                                 minutes=max_run_minutes)
    quit_time = datetime.now() + max_run_time
    if debug: print 'server quit time', quit_time
else:
    quit_time = None

end_date = None
target_year = None

num_date_args = len(args)
if num_date_args == 0:
    start_date = datetime.now() - relativedelta(days=options.days_ago)
    target_year = targetYearFromDate(start_date)
elif num_date_args == 1:
    target_year = int(args[0])
    start_date = datetime(target_year-1, *GRAPE.start_day)
    end_date = datetime(target_year, *GRAPE.end_day)
    if end_date > datetime.now():
        end_date = datetime.now() - ONE_DAY
elif num_date_args in (3,6):
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime(year,month,day)
    if num_date_args == 6:
        year = int(args[3])
        month = int(args[4])
        day = int(args[5])
        end_date = datetime(year,month,day)
else:
    print sys.argv
    errmsg = 'Invalid number of date arguments (%d).' % num_date_args
    raise ValueError, errmsg

if end_date is None:
    if num_days == 1: end_date = start_date
    else: end_date = start_date + relativedelta(days=num_days-1)

if target_year is None: target_year = targetYearFromDate(start_date)
season_start = datetime(target_year-1, *GRAPE.start_day)

log_filepath = options.log_filepath
if log_filepath is None:
    log_filepath = buildLogFilepath(target_year, 'grape',
                                    '%s-grape-daily-build.log', os.getpid())
reporter = Reporter(PID, log_filepath)

if download_temps or build_grids or draw_plots: 
    process_server = ProcessServer(reporter, season_start, download_temps,
                                   build_grids, draw_plots, publish_maps,
                                   plot_days, plot_coords, debug, test_run)

    date = start_date
    while date <= end_date:
        # do not start new date after quit time
        if quit_time is None or datetime.now() < quit_time:
            process_server.run(date)
        else:
            reason = 'time limit exceeded'
            exit()
        date += ONE_DAY

elif publish_maps:
    process_server = ProcessServer(reporter, season_start, False, False,
                                   False, True, plot_days, plot_coords,
                                   debug, test_run)
    process_server.run(end_date)

reporter.logInfo('Processing ended gracefully')

