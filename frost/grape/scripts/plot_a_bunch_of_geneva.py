#!/Users/rem63/venvs/frost/bin/python
""" utility to run the several scripts in sequence
"""
import os, sys, shlex
import subprocess

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-s', action='store', type='string', dest='script_dir',
                  default=None, help="alternate script directory")

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

script = 'plot_grape_hardiness_vs_temp.py'

if options.script_dir is not None:
    script_dir = os.path.normpath(options.script_dir)
else:
    script_dir = os.path.split(os.path.abspath(__file__))[0]

variety = args[0]

year = int(args[1])
month = int(args[2])
day = int(args[3])
start_date = datetime(year,month,day)
year = int(args[4])
month = int(args[5])
day = int(args[6])
end_date = datetime(year,month,day)

date = start_date
while date <= end_date:
    first_date = date - relativedelta(days=30)
    command = script_dir + os.sep + script
    command += ' %s %s' % (variety, first_date.strftime('%Y %m %d'))
    command += ' %s' % date.strftime('%Y %m %d')
    print '\n==>', command
    sys.stdout.flush()
    result = subprocess.call(shlex.split(command))
    if result != 0 :
        print 'ERROR : script failed ...', result
        sys.stdout.flush()
    date += ONE_DAY

