#! /Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.agg.linvill.grid import Linvill3DGridModel
from atmosci.utils.timeutils import lastDayOfMonth

from frost.apple.factory import AppleGridFactory
from frost.apple.linvill.grid import temp3DGridToHourly

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-v', action='store_true', dest='verbose', default=False)
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

verbose = options.verbose
factory = AppleGridFactory()

num_args = len(args)
if num_args == 0:
    start_date = datetime.now() - ONE_DAY
    end_date = None
elif num_args == 2:
    year = int(args[0])
    month = int(args[1])
    start_date = datetime(year,month,1)
    end_date = datetime(year, month, lastDayOfMonth(year, month))
elif num_args in (3,4,6):
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime(year,month,day)
    if num_args == 3: end_date = None
    elif num_args == 4:
        end_date = start_date + relativedelta(days=int(args[3])-1)
    elif num_args == 6:
        year = int(args[3])
        month = int(args[4])
        day = int(args[5])
        end_date = datetime(year,month,day)
else:
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise SyntaxError, errmsg

# target year is the year that we want to predict frost damage
target_year = factory.getTargetYear(start_date)
dates = factory.datesFromDateSpan(start_date, end_date)

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# get maxt/mint from temperature file
reader = factory.getTempGridReader(target_year)
if end_date is None:
    maxt = reader.getTemp('reported.maxt', start_date, None)
    mint = reader.getTemp('reported.mint', start_date, None)
else:
    maxt = reader.getTemp('reported.maxt', start_date, end_date)
    mint = reader.getTemp('reported.mint', start_date, end_date)
lats = reader.lats
reader.close()
del reader

# some versions of HDF5 return a 3D array even if only one day is requested
if maxt.ndim == 3 and maxt.shape[0] == 1:
    maxt = maxt[0]
    mint = mint[0]
maxt_nan_indexes = N.where(N.isnan(maxt))

# interpolate hourly temperatures from mint,maxt using Linvill algorithm
print 'running agg version'
agg_model = Linvill3DGridModel()
agg_hourly = agg_model.tempGridToHourly(start_date, lats, mint, maxt, 'F')
print agg_hourly.shape
print agg_hourly[0,:,120:125,190:192]

print 'running frost version'
frost_hourly = temp3DGridToHourly(dates, lats, mint, maxt, 'F')
print frost_hourly.shape
print frost_hourly[0,:,120:125,190:192]


# turn annoying numpy warnings back on
warnings.resetwarnings()
