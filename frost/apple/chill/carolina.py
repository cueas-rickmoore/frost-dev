
import numpy as N

from frost.apple.chill.accum import PointChillAccumulator
from frost.apple.chill.accum import PointsChillAccumulator
from frost.apple.chill.accum import GridChillAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

accumulators = { }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class  CarolinaChillMixin():
    """ Convert temperatures to chill units using Carolina Chilling Unit
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
        # 0.0 for temp <= 1.5
        # 0.0 for 16.4 > temp <= 18.9

        # +0.5 for  1.5 > temp <= 7.1
        hourly_chill[N.where((hourly_temps>1.5) & (hourly_temps<=7.1))] = 0.5
        # +1.0 for  7.1 > temp <= 12.9
        hourly_chill[N.where((hourly_temps>7.1) & (hourly_temps<=12.9))] = 1.0
        # +0.5 for  12.9 > temp <= 16.4
        hourly_chill[N.where((hourly_temps>12.9) & (hourly_temps<=16.4))] = 0.5
        # -0.5 for 18.9 < temp <= 20.6
        hourly_chill[N.where((hourly_temps>18.9) & (hourly_temps<=20.6))] = -0.5
        # -1.0 for 20.6 < temp <= 22
        hourly_chill[N.where((hourly_temps>20.6) & (hourly_temps<=22))] = -1.0
        # -1.5 for 22 < temp <= 23.2
        hourly_chill[N.where((hourly_temps>22) & (hourly_temps<=23.2))] = -1.5
        # -2.0 for temp > 23.2
        hourly_chill[N.where(hourly_temps > 23.2)] = -2.0
        
        if debug: print '\nhourly chill units :\n', hourly_chill

        return hourly_chill

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class CarolinaGridChillAccumulator(CarolinaChillMixin, GridChillAccumulator):
    """ Convert temperatures to chill factors using the North Carolina 
    Chilling Unit Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be a 2D
    array of [days, accumulated chill units by grid]

    Value for constructor argument "daily_chill_units" must be a 2D
    array of [days, daily chill units by grid]
    """
accumulators['grid'] = CarolinaGridChillAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class CarolinaPointChillAccumulator(CarolinaChillMixin, PointChillAccumulator):
    """Convert temperatures to chill units using the North Carolina
    Chilling Unit Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be an
    array of total accumulated chill units per day

    Value for constructor argument "daily_chill_units" must be an array
    array chill units per day
    """
accumulators['point'] = CarolinaPointChillAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class CarolinaPointsChillAccumulator(CarolinaChillMixin,
                                     PointsChillAccumulator):
    """ Convert temperatures to chill factors using the North Carolina 
    Chilling Unit Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be a 2D
    array of [days, accumulated chill units by location]

    Value for constructor argument "daily_chill_units" must be a 2D
    array of [days, daily chill units by location]
    """
accumulators['points'] = CarolinaPointsChillAccumulator

