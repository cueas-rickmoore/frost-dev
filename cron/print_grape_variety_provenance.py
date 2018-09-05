#! /Volumes/projects/venvs/frost/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asDatetime

from frost.grape.factory import GrapeGridFactory
from frost.grape.functions import getGrapeVariety

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DATA_FORMAT = '%s   % 6.2f   % 6.2f  % 6.2f  % 6.2f'
DATES = '%s thru %s'
DESCRIPTION = '%s Provenance'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-v', action='store_true', dest='verbose', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

verbose = options.verbose

# apple variety config
variety = getGrapeVariety(args[0])
group_name = args[1]
prov_dataset_name = '%s.provenance' % group_name

factory = GrapeGridFactory()

# get the date
date_args = args[2:]
num_date_args = len(date_args)
if num_date_args == 1:
    target_year = int(date_args[0])
    start_date = None
    end_date = None
elif num_date_args >= 3:
    year = int(date_args[0])
    month = int(date_args[1])
    day = int(date_args[2])
    start_date = datetime(year,month,day)
    if num_date_args == 3: end_date = None
    elif num_date_args == 4:
        end_date = start_date + relativedelta(days=int(date_args[3])-1)
    elif num_date_args == 6:
        year = int(date_args[3])
        month = int(date_args[4])
        day = int(date_args[5])
        end_date = datetime(year,month,day)
    else:
        errmsg = 'Invalid number of date arguments (%d).' % date_args
        raise ValueError, errmsg
    target_year = factory.getTargetYear(start_date)
else:
    errmsg = 'Invalid number of date arguments (%d).' % date_args
    raise ValueError, errmsg

reader = factory.getVarietyReader(target_year, variety)
description = reader.getGroupAttribute(group_name, 'description').title()

if start_date is None:
    start_date_str = reader.getDatasetAttribute(prov_dataset_name, 'start_date')
    start_date = asDatetime(start_date_str)
if end_date is None:
    last_date = reader.getDatasetAttribute(prov_dataset_name, 'last_valid_date')
    end_date = asDatetime(last_date)
print variety.description.center(44)

start_index, end_index = \
reader.indexesFromDates(prov_dataset_name, start_date, end_date)

provenance = reader.getDataset(prov_dataset_name)
names = provenance.dtype.names
print (DESCRIPTION % description).center(44)
print (DATES % (start_date_str, last_date)).center(44)
print '\n   %s        %s      %s     %s    diff' % names[:4]
print '==========   ======   ======   =====   ====='

for indx in range(start_index, end_index):
    date, xmin, xmax, xmean, xmedian, proc_date = provenance[indx]
    print DATA_FORMAT % (date, xmin, xmax, xmean, xmax-xmin)

reader.close()

