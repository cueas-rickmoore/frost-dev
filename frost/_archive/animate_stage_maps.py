#!/Users/rem63/venvs/frost/bin/python

import os, sys
from datetime import datetime

from frost.crops import crops
from frost.stage import MAP_FILEDIR
from frost.maps.stage import animateStageMaps

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from frost.config import config as CONFIG
APPLE = CONFIG.crops.apple.self

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('-z', action='store_true', dest='test_run', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# chill model 
model = args[0]
# apple variety config
variety = eval('APPLE.variety.%s' % args[1])

# map target dates
#start_date = datetime(int(args[2]), int(args[3]), int(args[4]))
#end_date = datetime(int(args[5]), int(args[6]), int(args[7]))
#animateStageMaps(model, variety, start_date, end_date)

dir_path = os.path.join(APPLE.map_dir, variety.parent.name, variety.name,
                        model)
png_path = os.path.join(dir_path, '*.png')
anim_path = os.path.join(dir_path, 'animation.gif')
os.system('convert -delay 30 %s -loop 0 %s' % (png_path, anim_path)

