#! /Volumes/projects/venvs/frost/bin/python

import os, sys
from copy import copy
import subprocess, shlex

from datetime import datetime
from dateutil.relativedelta import relativedelta

from atmosci.utils.report import Reporter

from frost.functions import fromConfig, buildLogFilepath 
from frost.functions import seasonDate, targetYearFromDate, targetDateSpan

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#APP = os.path.splitext(os.path.split(__file__)[1])[0].upper().replace('_',' ')
APP = os.path.split(sys.argv[0])[1] + ' ' + ' '.join(sys.argv[1:])
#PID = os.getpid()
PID = 'PID %d' % os.getpid()

APPLE = fromConfig('crops.apple')

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

    def __init__(self, target_year, reporter, download_temps, build_grids,
                       draw_maps, publish_maps, debug=False, test_run=False):
        self.active_script = None
        self.debug = debug
        self.reporter = reporter
        self.target_year = target_year
        self.test_run = test_run

        animation_dates = { }
        for map_type, day in APPLE.animation.start.attr_items:
            animation_dates[map_type] = seasonDate(target_year, *day)
        self.animation_dates = animation_dates

        chill_models = APPLE.chill.models
        varieties = APPLE.varieties.build

        scripts = [ ]
        for variety in varieties:
            if publish_maps:
                scripts.append( ('publish_maps', (variety, 'carolina')) )
                scripts.append( ('animate', (variety, 'carolina', 'kill')) )
                scripts.append( ('animate', (variety, 'carolina', 'stage')) )
                scripts.append( ('animate', (variety, 'carolina', 'gdd')) )
            for model in chill_models:
                if draw_maps:
                    scripts.append( ('kill_map', (variety, model)) )
                    scripts.append( ('stage_map', (variety, model)) )
                    scripts.append( ('gdd_map', (variety, model)) )
                if build_grids:
                    scripts.append( ('build_stage', (variety,)) )
        if publish_maps:
            scripts.append( ('publish_maps', ('chill', 'carolina')) )
            scripts.append( ('animate', (None, 'carolina', 'chill')) )
        if draw_maps:
            for model in chill_models:
                scripts.append( ('chill_map', (model,)) )
        if build_grids: scripts.append( ('build_chill', ()) )
        if download_temps: scripts.append( ('download_temp', ()) )
        self.all_scripts = tuple(scripts)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def run(self, date):
        debug = self.debug
        self.frost_date = date
        self.frost_date_arg = date.strftime('%Y %m %d')
        self.frost_date_str = date.strftime('%B %d, %Y')
        #self.temp_date = date + ONE_DAY
        self.temp_date = self.frost_date
        self.temp_date_str = self.frost_date_str
        self.process_queue = list(self.all_scripts)
        if debug:
            print '\nrun process queue', self.frost_date_arg,
            print self.process_queue

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

                        msg = 'Completed apple daily build for'
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
        date_str = self.frost_date_str
        if retcode <= 0:
            reporter.logEvent(SUCCESS % (self.active_script, date_str))
        else:
            errmsg = FAILURE % (self.active_script, date_str, retcode)
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
            initProcess = self.PROCESS_INIT_METHODS[process[0]]
            args = process[1]
            if args: return initProcess(self, *args)
            else: return initProcess(self)
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

    def initiateBuildChillGrids(self):
        if self.debug:
            print '\ninitiateBuildChillGrids', date
            self.reporter.logInfo(CALL_MSG % ('initiateBuildChillGrids', date))
        if self.test_run:
            return DummyProcess()
        script = 'build_apple_chill_grids.py'
        args = '%s' % self.frost_date_arg
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['build_chill'] = initiateBuildChillGrids

    def initiateBuildStageGrids(self, variety):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateBuildStageGrids', variety, date
            self.reporter.logInfo(CALL_MSG % ('initiateBuildStageGrids', date))
        if self.test_run: return DummyProcess()
        script = 'build_apple_stage_grids.py'
        args = '%s %s' % (variety, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['build_stage'] = initiateBuildStageGrids

    def initiateDrawChillMaps(self, model):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateDrawChillMaps', model, date
            self.reporter.logInfo(CALL_MSG % ('initiateDrawChillMaps', date))
        if self.test_run: return DummyProcess()
        script = 'draw_apple_chill_maps.py'
        args = '%s %s' %  (model, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['chill_map'] = initiateDrawChillMaps

    def initiateDrawGDDMaps(self, variety, model):
        if self.debug:
            date = self.frost_date_str
            print '\initiateDrawGDDMaps',date
            self.reporter.logInfo(CALL_MSG % ('initiateDrawGDDMaps', date))
        if self.test_run: return DummyProcess()
        script = 'draw_apple_variety_gdd_maps.py'
        args = '%s %s %s' % (variety, model, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['gdd_map'] = initiateDrawGDDMaps

    def initiateDrawKillMaps(self, variety, model):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateDrawKillMaps',date
            self.reporter.logInfo(CALL_MSG % ('initiateDrawKillMaps', date))
        if self.test_run: return DummyProcess()
        script = 'draw_apple_variety_kill_maps.py'
        args = '%s %s %s' % (variety, model, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['kill_map'] = initiateDrawKillMaps

    def initiateDrawStageMaps(self, variety, model):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiateDrawStageMaps', variety, date
            self.reporter.logInfo(CALL_MSG % ('initiateDrawStageMaps', date))
        if self.test_run: return DummyProcess()
        script = 'draw_apple_variety_stage_maps.py'
        args = '%s %s %s' % (variety, model, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['stage_map'] = initiateDrawStageMaps

    def initiateMapAnimation(self, variety, model, map_key):
        if self.debug:
            print '\ninitiateMapAnimation', variety,  model, map_key
            self.reporter.logInfo(CALL_MSG % ('initiateMapAnimation',
                                              self.frost_date_str))
        if self.test_run or self.frost_date < self.animation_dates[map_key]:
            return DummyProcess()
        script = 'animate_apple_maps.py'
        if map_key =='chill': args = '%d %s chill' % (self.target_year, model)
        else: args = '%d %s %s %s' % (self.target_year, model, map_key, variety)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['animate'] = initiateMapAnimation

    def initiatePublishMaps(self, variety_or_chill, model):
        if self.debug:
            date = self.frost_date_str
            print '\ninitiatePublishMaps', variety_or_chill, date
            self.reporter.logInfo(CALL_MSG % ('initiatePublishMaps', date))
        if self.test_run: return DummyProcess()
        script = 'publish_apple_maps.py'
        args = '%s %s %s' % (variety_or_chill, model, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['publish_maps'] = initiatePublishMaps

    def initiateTempDownload(self):
        if self.debug:
            date = self.temp_date_str
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

parser.add_option('-b', action='store_false', dest='build_grids', default=True)
parser.add_option('-d', action='store_false', dest='draw_maps', default=True)
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
days_ago = options.days_ago
download_temps = options.download_temps
draw_maps = options.draw_maps
num_days = options.num_days
if draw_maps:
    publish_maps = options.publish_maps
else: publish_maps = False

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
num_date_args = len(args)
if num_date_args == 0:
    #start_date = datetime.now() - relativedelta(days=days_ago)
    start_date = datetime.now()
elif num_date_args in (3,4,5,6):
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime(year,month,day)
    if num_date_args == 4:
        day = int(args[3])
        end_date = datetime(year,month,day)
    elif num_date_args == 5:
        month = int(args[3])
        day = int(args[4])
        end_date = datetime(year,month,day)
    elif num_date_args == 6:
        year = int(args[3])
        month = int(args[4])
        day = int(args[5])
        end_date = datetime(year,month,day)
else:
    print sys.argv
    errmsg = 'Invalid number of date arguments (%d).' % num_date_args
    raise ValueError, errmsg
target_year = targetYearFromDate(start_date, 'apple')
season_start, season_end = targetDateSpan(target_year, 'apple')

if start_date > season_end: sys.exit(0)
if end_date is None:
    end_date = start_date + relativedelta(days=num_days-1)
if end_date <= season_start: sys.exit(0)
if start_date < season_start: start_date = season_start

log_filepath = options.log_filepath
if log_filepath is None:
    log_filepath = buildLogFilepath(targetYearFromDate(start_date), 'apple',
                                    '%s-apple-daily-build.log', os.getpid())
reporter = Reporter(PID, log_filepath)
process_server = ProcessServer(target_year, reporter, download_temps,
                               build_grids, draw_maps, False, debug, test_run)

if download_temps or build_grids or draw_maps:
    date = start_date
    while date <= end_date:
        # do not start new date after quit time
        if quit_time is None or datetime.now() < quit_time:
            process_server.run(date)
        else:
            reason = 'time limit exceeded'
            exit()
        date += ONE_DAY

if publish_maps:
    process_server = ProcessServer(target_year, reporter, False, False, False,
                                   True, debug, test_run)
    process_server.run(end_date)

reporter.logInfo('Processing ended gracefully')

