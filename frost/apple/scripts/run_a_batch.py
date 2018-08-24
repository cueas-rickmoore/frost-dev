#! /Users/rem63/venvs/nrcc/bin/python
""" utility to run the same script on datasets from several consecutive days
... useful for repairing small errors such as bad or mis-spelled values
of dataset tributes.
"""
import os, sys, shlex
import subprocess
from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SCRIPT_DIR = os.path.split(os.path.abspath(__file__))[0]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-i', action='store', type='int', dest='batch_interval',
                  default=15, help="number of days per script call")
parser.add_option('-s', action='store', type='string', dest='script_dir',
                  default=SCRIPT_DIR, help="alternate script directory")
parser.add_option('-v', action='store_true', dest='verbose', default=False)

parser.add_option('--optional', action='store', type='string',
                  dest='optional_args', default=None,
                  help="opitional script arguments")
parser.add_option('--required', action='store', type='string',
                  dest='required_args', default=None,
                  help="required script arguments")


options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

batch_interval = relativedelta(days=options.batch_interval-1)
optional_args = options.optional_args
required_args = options.required_args
script_dir = options.script_dir
verbose = options.verbose

script_name = args[0]
if not script_name.endswith('.py'): script_name += '.py'
script_path = os.path.join(script_dir, script_name)

num_args = len(args[1:])
if num_args == 1:
    target_year = int(args[1])
    start_date = datetime(target_year-1,
                          *fromConfig('crops.apple.start_day'))
    end_date = datetime(target_year, *fromConfig('crops.apple.end_day'))
elif num_args == 2:
    year = int(args[1])
    month = int(args[2])
    start_date = datetime(year,month,1)
    last_day = lastDayOfMonth(year, month)
    end_date = datetime(year, month, last_day)
elif num_args in (3,4,6):
    year = int(args[1])
    month = int(args[2])
    day = int(args[3])
    start_date = datetime(year,month,day)
    if num_args == 3:
        end_date += batch_interval
    elif num_args == 4:
        end_date = start_date + relativedelta(days=int(args[4])-1)
    elif num_args == 6:
        year = int(args[4])
        month = int(args[5])
        day = int(args[6])
        end_date = datetime(year,month,day)
else:
    print sys.argv
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise SyntaxError, errmsg

if required_args is None: script = script_path
else: script = '%s %s' % (script_path, required_args)
if optional_args is None: script_template = '%s %%s %%s' % script
else: script_template = '%s %%s %%s %s' % (script, optional_args)
if verbose: script_template += ' -v'

date = start_date
while date <= end_date:
    start = date.strftime('%Y %m %d')
    end = date + batch_interval
    if end > end_date: end = end_date
    end = end.strftime('%Y %m %d')
    command = script_template % (start, end)
    print '==>', command
    sys.stdout.flush()
    result = subprocess.call(shlex.split(command))
    if result != 0 :
        print 'ERROR : script failed ...', result
        sys.stdout.flush()

    date += batch_interval + ONE_DAY

