#!/Users/rem63/venvs/frost/bin/python

import os, sys

from frost.functions import tempPlotDir

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TEMP_NAMES = { 'mint':'Minimum', 'maxt':'Maximum', 'avgt':'Average' }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('-d', action='store', type='int', dest='delay', default=30)
parser.add_option('-z', action='store_true', dest='test_path', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

delay = options.delay
test_path = options.test_path

target_year = int(args[0])
temp_path = args[1]
temp_group, temp_type = temp_path.split('.')
plot_type = args[2]
strings = (temp_group.title(), temp_type.title(), plot_type[:-1].title())

working_dir = tempPlotDir(target_year, temp_group, temp_type, plot_type)
png_path = '*-Frost-%s-%s-%s.png' % strings
anim_filename = '%d-Frost-%s-%s-%s-animation.gif' % ((target_year,) + strings)
anim_path = os.path.join(working_dir, anim_filename)
os.chdir(working_dir)
os.system('convert -delay %d %s -loop 0 %s' % (delay, png_path, anim_path))

