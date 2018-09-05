#! /usr/bin/env python

import os, sys
import datetime

if len(sys.argv) > 1: year = int(sys.argv[1])
else:
    today = datetime.date.today()
    if today.month >= 9: year = today.year + 1
    else: year = today.year

SRC_TEMPLATE = '/Users/Shared/app_data/frost/grid/%d/grape/%s/%d-Frost-Grape-%s.h5'
DATA_TEMPLATE = '/Volumes/data/app_data/frost/grid/%d/grape/%s'
TRANSPORT_TEMPLATE = '/Volumes/Transport/data/app_data/frost/grid/%d/grape'
VARIETIES = { 'cab_franc':'Cab-Franc', 'concord':'Concord', 'riesling':'Riesling' }

TRANSPORT_DIRPATH = '/Volumes/Transport/data/app_data'

for variety in ['cab_franc', 'concord', 'riesling']:
    source = (year,variety,year,VARIETIES[variety])
    paths = ( SRC_TEMPLATE % source, DATA_TEMPLATE % (year,variety) )
    command = '/usr/bin/rsync -cgloprtuD rem63@tornado.nrcc.cornell.edu:%s %s' % paths
    print command
    os.system(command)

    if os.path.exists(TRANSPORT_DIRPATH):
        paths = ( DATA_TEMPLATE % (year,variety), TRANSPORT_TEMPLATE % year )
        command = '/usr/bin/rsync -cgloprtuD %s %s' % paths
        print command
        os.system(command)

