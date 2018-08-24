#!/Users/rem63/venvs/frost/bin/python

import os, sys
from datetime import datetime

import numpy as N

from frost.linvill import getInterpolator
from frost.chill import getAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('--lat', action='store', type='float', dest='lat',
                  default=42.48) # default is Ithaca Airport
parser.add_option('--maxt', action='store', type='float', dest='maxt',
                  default=70)
parser.add_option('--mint', action='store', type='float', dest='mint',
                  default=10)

parser.add_option('-d', action='store', type='int', dest='num_days',
                  default=1)

parser.add_option('-g', action='store_true', dest='test_grid', default=False)
parser.add_option('-m', action='store_true', dest='test_multipoint',
                   default=False)
parser.add_option('-p', action='store_true', dest='test_point', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

separator = '*' * 72

model = args[0]

if len(args) == 4:
    date = (int(args[1]), int(args[2]), int(args[3]))
else: date = datetime.now()

lat = float(options.lat)
maxt = float(options.maxt)
mint = float(options.mint)
num_days = options.num_days

interpolate = getInterpolator('point')
hourly = interpolate(date, lat, mint, maxt, 'F', debug=True)

if options.test_point:
    print '\npoint interpolator'
    print separator
    print '\nhourly temps', hourly
    days = N.array([hourly for day in range(num_days)], dtype=float)
    
    if model in ('threshold',):
        accumulator =\
        getAccumulator('threshold', 'point')(None, None, 0, 45, 'F', 'C')
    else: accumulator = getAccumulator(model, 'point')()
    accumulated_chill_hours = accumulator(days, debug=True)

    print '\nchill unts by day :\n', accumulator.getDailyChillUnits()
    print '\naccumulated by day :\n', accumulator.getAccumulatedChillUnits()
    print '\ntotal accumulated :\n', accumulated_chill_hours

if options.test_multipoint:
    lat_array = N.array([lat for i in range(10)], dtype=float)
    maxt_array = N.array([maxt for i in range(10)], dtype=float)
    mint_array = N.array([mint for i in range(10)], dtype=float)

    print '\narray interpolator'
    print 'latitide\n', lat_array
    print separator

    print '\nhourly temps\n', hourly
    daily = N.array([hourly for day in range(num_days)], dtype=float)
    locations = N.array([daily for location in range(10)], dtype=float)

    if model in ('threshold',):
        accumulator =\
        getAccumulator('threshold', 'points')(None, None, 0, 45, 'F', 'C')
    else: accumulator = getAccumulator(model, 'points')()
    accumulated_chill_hours = accumulator(locations, debug=True)

    print '\nchill unts by day :\n', accumulator.getDailyChillUnits()
    print '\naccumulated by day :\n', accumulator.getAccumulatedChillUnits()
    print '\ntotal accumulated :\n', accumulated_chill_hours

if options.test_grid:
    row = [lat for i in range(4)]
    lat_grid = N.array( [row for i in range(4)], dtype=float )

    row = [maxt for i in range(4)]
    maxt_grid = N.array( [row for i in range(4)], dtype=float )

    row = [mint for i in range(4)]
    mint_grid = N.array( [row for i in range(4)], dtype=float )

    print '\ngrid interpolator'
    print separator
    interpolate = getInterpolator('grid')
    hourly = interpolate(date, lat_grid, mint_grid, maxt_grid, 'F', debug=True)
    print '\nhourly @ node[0,0]'
    print hourly[:,0,0]
    print '\nhourly @ node[-1,-1]'
    print hourly[:,-1,-1]
    days = N.array([hourly for day in range(num_days)], dtype=float)

    if model in ('threshold',):
        accumulator =\
        getAccumulator('threshold', 'grid')(None, None, 0, 45, 'F', 'C')
    else: accumulator = getAccumulator(model, 'grid')()
    accumulated_chill_hours = accumulator(days, debug=True)

    print '\nchill unts by day :\n', accumulator.getDailyChillUnits()
    print '\naccumulated by day :\n', accumulator.getAccumulatedChillUnits()
    print '\ntotal accumulated :\n', accumulated_chill_hours

