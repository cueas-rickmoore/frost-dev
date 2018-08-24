#! /Volumes/projects/venvs/frost/bin/python

import os, sys
from copy import copy
import subprocess, shlex

from datetime import datetime
from dateutil.relativedelta import relativedelta

from atmosci.utils.report import Reporter

from frost.functions import fromConfig, targetDateSpan, targetYearFromDate
from frost.functions import buildLogFilepath, nameToFilepath

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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

    def __init__(self, reporter, variety_name, build_grids, draw_maps,
                       debug=False, test_run=False):
        self.active_script = None
        self.debug = debug
        self.reporter = reporter
        self.test_run = test_run

        chill_models = fromConfig('crops.apple.chill.models')

        scripts = [ ]
        for model in chill_models:
            if draw_maps:
                scripts.append( ('kill_map', (variety_name, model)) )
                scripts.append( ('stage_map', (variety_name, model)) )
                scripts.append( ('gdd_map', (variety_name, model)) )
            if build_grids:
                scripts.append( ('build_stage', (variety_name,)) )
        self.all_scripts = tuple(scripts)
        if debug: print 'all scripts', self.all_scripts

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def run(self, date):
        self.frost_date = date
        self.frost_date_arg = date.strftime('%Y %m %d')
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

                        msg = 'Completed apple variety build for'
                        print msg, self.frost_date.strftime('%B %d, %Y')
                        sys.stdout.flush()
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
            reporter.logEvent(SUCCESS % (self.active_script, date))
        else:
            errmsg = FAILURE % (self.active_script, date, retcode)
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

    def initiateBuildStageGrids(self, variety_name):
        if self.debug:
            date = self.frost_date.strftime('%B %d, %Y')
            print '\ninitiateBuildStageGrids', variety_name, date
            self.reporter.logInfo(CALL_MSG % ('initiateBuildStageGrids', date))
        if self.test_run: return DummyProcess()
        script = 'build_apple_stage_grids.py'
        args = '%s %s' % (variety_name, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['build_stage'] = initiateBuildStageGrids

    def initiateDrawGDDMaps(self, variety_name, model):
        if self.debug:
            date = self.frost_date.strftime('%B %d, %Y')
            print '\initiateDrawGDDMaps',date
            self.reporter.logInfo(CALL_MSG % ('initiateDrawGDDMaps', date))
        if self.test_run: return DummyProcess()
        script = 'draw_apple_variety_gdd_maps.py'
        args = '%s %s %s' % (variety_name, model, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['gdd_map'] = initiateDrawGDDMaps

    def initiateDrawKillMaps(self, variety_name, model):
        if self.debug:
            date = self.frost_date.strftime('%B %d, %Y')
            print '\ninitiateDrawKillMaps',date
            self.reporter.logInfo(CALL_MSG % ('initiateDrawKillMaps', date))
        if self.test_run: return DummyProcess()
        script = 'draw_apple_variety_kill_maps.py'
        args = '%s %s %s' % (variety_name, model, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['kill_map'] = initiateDrawKillMaps

    def initiateDrawStageMaps(self, variety_name, model):
        if self.debug:
            date = self.frost_date.strftime('%B %d, %Y')
            print '\ninitiateDrawStageMaps', variety_name, date
            self.reporter.logInfo(CALL_MSG % ('initiateDrawStageMaps', date))
        if self.test_run: return DummyProcess()
        script = 'draw_apple_variety_stage_maps.py'
        args = '%s %s %s' % (variety_name, model, self.frost_date_arg)
        if self.debug: args += ' -z'
        return self.runSubprocess(script, args)
    PROCESS_INIT_METHODS['stage_map'] = initiateDrawStageMaps


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser = OptionParser(usage="usage: %prog [year month day] [options]")
parser.add_option('--da', action='store', type='int', dest='days_ago',
                  default=1, help='build for a day N days ago')
parser.add_option('--mrt', action='store', type='string', dest='max_run_time',
                  default=None)

parser.add_option('-b', action='store_false', dest='build_grids', default=True)
parser.add_option('-l', action='store', type='string', dest='log_filepath',
                  default=None,
                  help='path to alternate file to be used for logging')
parser.add_option('-m', action='store_false', dest='draw_maps', default=True)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

build_grids = options.build_grids
draw_maps = options.draw_maps

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

variety = args[0]

if len(args) == 2 : # target year is only argument
    start_date, end_date = targetDateSpan(int(args[1]))
elif len(args) > 2: # start date specified
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    start_date = datetime(year,month,day)
    if len(args) > 4: # end date specified
        year = int(args[4])
        month = int(args[5])
        day = int(args[6])
        end_date = datetime(year,month,day)
    else: end_date = start_date
else:
    start_date = datetime.now() - relativedelta(days=options.days_ago)
    end_date = start_date

log_filepath = options.log_filepath
if log_filepath is None:
    log_filename = '%%s-apple-variety-%s-build.log' % nameToFilepath(variety)
    log_filepath = buildLogFilepath(targetYearFromDate(start_date), 'apple',
                                    log_filename, os.getpid())
reporter = Reporter(PID, log_filepath)
process_server = ProcessServer(reporter, variety, build_grids, draw_maps,
                               debug, test_run)

date = start_date
while date <= end_date:
    # do not start new date after quit time
    if quit_time is None or datetime.now() < quit_time:
        process_server.run(date)
    else:
        reason = 'time limit exceeded'
        exit()
    date += ONE_DAY

reporter.logInfo('Processing ended gracefully')

