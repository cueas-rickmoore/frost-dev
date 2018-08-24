
import math
from datetime import datetime

import numpy as N

def tempRangeToHourly(date, min_1, max_t, min_2):
    from scipy.interpolate import splrep

    splrep(range(3), N.array((min_1, max_t, min_2)))
    return 
    #from scipy.interpolate import UnivariateSpline
    #points_per_knot = 12
    #knot_intervals = range(3)
    #spline_intervals = range((knot_intervals[-1] * points_per_knot) + 1)
    #factor = 1. / 12.
    #spline_knots = tuple([indx*factor for indx in spline_intervals])
    #last_knot = len(spline_knots)
    #spline = UnivariateSpline(knot_intervals, N.array((min_1, max_t, min_2)),
    #                          s=0)
    #return spline(spline_knots)

if __name__ == '__main__':
    import os, sys
    filepath = os.path.abspath(sys.argv[1])
    data = eval(open(filepath,'r').read())
    dates = data['Date']
    mints = data['MinTemperature']
    print 'mints', mints
    maxts = data['MaxTemperature']
    print 'maxts', maxts
    for indx, date in enumerate(dates):
        if indx > 0:
            print '\n', date
            print  mints[indx-1], maxts[indx], mints[indx]
            _date_ = tuple([int(x) for x in date.split('-')])
            temps =\
            tempRangeToHourly(_date_, mints[indx-1], maxts[indx], mints[indx])
            print temps

