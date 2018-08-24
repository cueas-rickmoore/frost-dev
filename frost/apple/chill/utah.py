
import numpy as N

from frost.apple.chill.accum import PointChillAccumulator
from frost.apple.chill.accum import PointsChillAccumulator
from frost.apple.chill.accum import GridChillAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

accumulators = { }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UtahChillMixin():
    """ Convert temperatures to chill units using Utah Chilling Unit
    Accumulation Model
    """

    def calcHourlyChillUnits(self, hourly_temps, debug=False):
        """Calculates the hourly chill for a sequence of days.

        'hourly_temps' is a Numpy array containing temperatures for 24
        hours on each day in the sequence. There is no restriction on 
        shape or layout of the input array as long as each node/item
        contains a temperature for one hour.

        Returns the hourly chill for each day in the sequence. The shape
        and layout of the returned array will be identical to that of
        the impout array.
        """
        # initialize the chill units array to all zeros ... saves significant
        # processing time when converting temps to chill factors
        hourly_chill = N.zeros_like(hourly_temps)
        # 0.0 for temp <= 1.4
        # 0.0 for 12.4 > temp <= 15.9

        # +0.5 for  1.4 > temp <= 2.4
        hourly_chill[N.where((hourly_temps>1.4) & (hourly_temps<=2.4))] = 0.5
        # +1.0 for  2.4 > temp <= 9.1
        hourly_chill[N.where((hourly_temps>2.4) & (hourly_temps<=9.1))] = 1.0
        # +0.5 for  9.1 > temp <= 12.4
        hourly_chill[N.where((hourly_temps>9.1) & (hourly_temps<=12.4))] = 0.5
        # -0.5 for 15.9 < temp <= 18.0
        hourly_chill[N.where((hourly_temps>15.9) & (hourly_temps<=18.0))] = -0.5
        # -1.0 for temp > 18.0
        hourly_chill[N.where(hourly_temps > 18)] = -1.0

        if debug: print '\nhourly chill units :\n', hourly_chill

        return hourly_chill


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UtahGridChillAccumulator(UtahChillMixin, GridChillAccumulator):
    """ Convert temperatures to chill factors using the North Carolina 
    Chilling Unit Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be a 2D
    array of [days, accumulated chill units by location]

    Value for constructor argument "daily_chill_units" must be a 2D
    array of [days, daily chill units by location]
    """
accumulators['grid'] = UtahGridChillAccumulator


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UtahPointChillAccumulator(UtahChillMixin, PointChillAccumulator):
    """ Convert temperatures to chill units using Utah Chilling Unit
    Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be a 2D
    array of [days, accumulated chill units by grid]

    Value for constructor argument "daily_chill_units" must be a 2D
    array of [days, daily chill units by grid]
    """
accumulators['point'] = UtahPointChillAccumulator


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UtahPointsChillAccumulator(UtahChillMixin, PointsChillAccumulator):
    """ Convert temperatures to chill factors using the North Carolina 
    Chilling Unit Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be a 2D
    array of [days, accumulated chill units by location]

    Value for constructor argument "daily_chill_units" must be a 2D
    array of [days, daily chill units by location]
    """
accumulators['points'] = UtahPointsChillAccumulator

