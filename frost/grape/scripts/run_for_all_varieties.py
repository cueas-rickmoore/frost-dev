#!/Users/rem63/venvs/frost/bin/python
""" utility to run the several scripts in sequence
"""
import os, sys, shlex
import subprocess

from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-s', action='store', type='string', dest='script_dir',
                  default=None, help="alternate script directory")

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if options.script_dir is not None:
    script_dir = os.path.normpath(options.script_dir)
else:
    script_dir = os.path.split(os.path.abspath(__file__))[0]
script = os.path.join(script_dir, args[0])

command_template = "%s %%s %s" % (script, ' '.join(args[1:]))

for variety in fromConfig('crops.grape.varieties.build'):
    command = command_template % variety
    print '\n\n==>', command
    sys.stdout.flush()
    result = subprocess.call(shlex.split(command))
    if result != 0 :
        print 'ERROR : script failed ...', result
        sys.stdout.flush()

