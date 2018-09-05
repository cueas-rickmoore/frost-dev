#! /usr/bin/env python

import os, sys
import datetime

if len(sys.argv) > 1: year = int(sys.argv[1])
else:
    today = datetime.date.today()
    if today.month >= 9: year = today.year + 1
    else: year = today.year

SRC_TEMPLATE = '/Users/Shared/app_data/frost/grid/%d/apple/%s/%d-Frost-Apple-%s.h5'
DATA_TEMPLATE = '/Volumes/data/app_data/frost/grid/%d/apple/%s'
TRANSPORT_TEMPLATE = '/Volumes/Transport/data/app_data/frost/grid/%d/apple'
SOURCES = { 'chill':'Chill', 'empire':'Empire', 'mac_geneva':'Mac-Geneva', 'red_delicious':'Red-Delicious' }

TRANSPORT_DIRPATH = '/Volumes/Transport/data/app_data'

for source in SOURCES.keys():
    src_path = SRC_TEMPLATE % (year, source, year, SOURCES[source])
    data_path = DATA_TEMPLATE % (year,source)
    command = '/usr/bin/rsync -cgloprtuD rem63@tornado.nrcc.cornell.edu:%s %s' % (src_path, data_path)
    print command
    os.system(command)

    if os.path.exists(TRANSPORT_DIRPATH):
        transport_path = TRANSPORT_TEMPLATE % year
        command = '/usr/bin/rsync -cgloprtuD %s %s' % (data_path, transport_path)
        print command
        os.system(command)

