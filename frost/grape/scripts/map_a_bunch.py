#!/Users/rem63/venvs/frost/bin/python
""" utility to run the several scripts in sequence
"""
import os, sys, shlex
import subprocess

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SCRIPTS = (
            'draw_grape_kill_maps.py cab_franc reported %s -a',
            'draw_grape_kill_maps.py chard reported %s -a',
            'draw_grape_kill_maps.py concord reported %s -a',
            'draw_grape_kill_maps.py lemberger reported %s -a',
            'draw_grape_kill_maps.py malbac reported %s -a',
            'draw_grape_kill_maps.py merlot reported %s -a',
            'draw_grape_kill_maps.py pin_gris reported %s -a',
            'draw_grape_kill_maps.py riesling reported %s -a',
            'draw_grape_kill_maps.py sauv_blanc reported %s -a',
            'draw_grape_kill_maps.py syrah reported %s -a',

            'draw_grape_hardiness_maps.py cab_franc %s -a',
            'draw_grape_hardiness_maps.py chard %s -a',
            'draw_grape_hardiness_maps.py concord %s -a',
            'draw_grape_hardiness_maps.py lemberger %s -a',
            'draw_grape_hardiness_maps.py malbac %s -a',
            'draw_grape_hardiness_maps.py merlot %s -a',
            'draw_grape_hardiness_maps.py pin_gris %s -a',
            'draw_grape_hardiness_maps.py riesling %s -a',
            'draw_grape_hardiness_maps.py sauv_blanc %s -a',
            'draw_grape_hardiness_maps.py syrah %s -a',
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

