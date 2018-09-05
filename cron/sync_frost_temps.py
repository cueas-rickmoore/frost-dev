#! /usr/bin/env python

import os, sys
import datetime

if len(sys.argv) > 1: year = int(sys.argv[1])
else:
    today = datetime.date.today()
    if today.month >= 9: year = today.year + 1
    else: year = today.year
    
data_dirpath = '/Volumes/data/app_data/frost/grid/%d/temp' % year
src_dirpath = '/Users/Shared/app_data/frost/grid/%d/temp' % year
temp_filename = '%d_temperatures.h5' % year

paths = (os.path.join(src_dirpath, temp_filename), data_dirpath)
command = '/usr/bin/rsync -cgloprtuD rem63@tornado.nrcc.cornell.edu:%s %s' % paths
print command
os.system(command)

transport_dirpath = '/Volumes/Transport/data/app_data'
if os.path.exists(transport_dirpath):
    transport_temp_dirpath = '%s/frost/grid/%d/temp' % (transport_dirpath, year)
    paths = (os.path.join(data_dirpath, temp_filename), transport_temp_dirpath)
    command = '/usr/bin/rsync -cgloprtuD %s %s' % paths
    print command
    os.system(command)

