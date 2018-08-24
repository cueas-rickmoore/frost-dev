#!/Users/rem63/venvs/frost/bin/python
""" utility to run the several scripts in sequence
"""
import os, sys, shlex
import subprocess

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SCRIPTS = ( 
           'draw_grape_hardiness_histogram.py cab_franc %s -a',
           'draw_grape_hardiness_histogram.py chard %s -a',
           'draw_grape_hardiness_histogram.py concord %s -a',
           'draw_grape_hardiness_histogram.py lemberger %s -a',
           'draw_grape_hardiness_histogram.py malbac %s -a',
           'draw_grape_hardiness_histogram.py merlot %s -a',
           'draw_grape_hardiness_histogram.py pin_gris %s -a',
           'draw_grape_hardiness_histogram.py reisling %s -a',
           'draw_grape_hardiness_histogram.py sauv_blanc %s -a',
           'draw_grape_hardiness_histogram.py syrah %s -a',
          )

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-s', action='store', type='string', dest='script_dir',
                  default=None, help="alternate script directory")

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

target_year = args[0]

if options.script_dir is not None:
    script_dir = os.path.normpath(options.script_dir)
else:
    script_dir = os.path.split(os.path.abspath(__file__))[0]

for script in SCRIPTS:
    command = script_dir + os.sep + script % target_year
    print '\n\n==>', command
    sys.stdout.flush()
    result = subprocess.call(shlex.split(command))
    if result != 0 :
        print 'ERROR : script failed ...', result
        sys.stdout.flush()

