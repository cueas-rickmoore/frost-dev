
import numpy as N

from frost.apple.chill.accum import GridChillAccumulator
from frost.apple.chill.accum import PointChillAccumulator
from frost.apple.chill.accum import PointsChillAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

FIVE_NINTHS = 5. / 9.
NINE_FIFTHS = 9. / 5.

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

accumulators = { }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ThresholdAccumulatorMixin():
    """ convert temperatures to chill factors using 45 degree Chilling Unit
    Accumulation Model
    """

    def __init__(self, accumulated_chill=None, daily_chill_units=None,
                       low_threshold=0, high_threshold=45, threshold_units='F',
                       hourly_temp_units='F'):
        """
        Value for constructor argument "accumulated_chill_units" must be a 1D
        array of days

        Value for constructor argument "daily_chill_units" must be a 1D
        array of days

        "low_threshold" is minimum temperature at which accumulation occurs.
        Default is 0 degrees.

        "high_threshold" is maximum temperature at which accumulation occurs.
        Default is 45 degrees

        "threshold_units" is the units (degress F or C) of the threshold
        temperatures. Default is degrees F

        "hourly_temp_units" is the units (degress F or C) of the temperatues
        in the hourly temperature array used to calculated chill units.
        Default is degrees F
        """
        self.accumulated_chill = accumulated_chil
        self.daily_chill_units = daily_chill_units

        self.low_threshold = self._convertTempUnits(float(low_threshold),
                                                    threshold_units, 'C')
        self.high_threshold = self._convertTempUnits(float(high_threshold),
                                                     threshold_units, 'C')
        self.hourly_temp_units = hourly_temp_units

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

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
        _hourly_temps = self._convertTempUnits(hourly_temps,
                                               self.hourly_temp_units, 'C')
        if debug:
            thresholds = self.low_threshold, self.high_threshold
            print '\nlower,upper chill temp thresholds :', thresholds

        # chill units are either zero or one
        hourly_chill_units = N.zeros(_hourly_temps.shape, dtype=float)
        hourly_chill_units[N.where((_hourly_temps > self.low_threshold) &
                                   (_hourly_temps < self.high_threshold))] = 1
        if debug:
            print '\nhourly chill units :\n', hourly_chill_units

        return hourly_chill_units

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _convertTempUnits(self, temps, from_units, to_units):
        if from_units == 'F' and to_units == 'C':
            return (temps - 32)  * FIVE_NINTHS
        elif from_units == 'C' and to_units == 'F':
            return (temps * NINE_FIFTHS) + 32.
        else: return temps

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GridThresholdChillAccumulator(ThresholdAccumulatorMixin, 
                                    GridChillAccumulator):
    """ Convert temperatures to chill factors using min/max degree Chilling
    Unit Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be a 2D
    array of [days, accumulated chill units by grid]

    Value for constructor argument "daily_chill_units" must be a 2D
    array of [days, daily total chill units by grid]

    Constructor argument "low_threshold" is minimum temperature at which
    accumulation occurs. Default is 0 degrees.

    Constructor argument "high_threshold" is maximum temperature at which
    accumulation occurs. Default is 45 degrees.

    Constructor argument "threshold_units" is the units (degress F or C)
    of the threshold temperatures. Default is degrees F

    Constructor argument "hourly_temp_units" is the units (degress F or C)
    of the temperatues in the hourly temperature array used to calculated
    chill units. Default is degrees F
    """

accumulators['grid'] = GridThresholdChillAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PointThresholdChillAccumulator(ThresholdAccumulatorMixin, 
                                     PointChillAccumulator):
    """ Convert temperatures to chill factors using min/max degree Chilling
    Unit Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be an
    array of total accumulated chill units per day

    Value for constructor argument "daily_chill_units" must be an array
    array chill units per day

    Constructor argument "low_threshold" is minimum temperature at which
    accumulation occurs. Default is 0 degrees.

    Constructor argument "high_threshold" is maximum temperature at which
    accumulation occurs. Default is 45 degrees.

    Constructor argument "threshold_units" is the units (degress F or C)
    of the threshold temperatures. Default is degrees F

    Constructor argument "hourly_temp_units" is the units (degress F or C)
    of the temperatues in the hourly temperature array used to calculated
    chill units. Default is degrees F
    """

accumulators['point'] = PointThresholdChillAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PointsThresholdChillAccumulator(ThresholdAccumulatorMixin, 
                                      PointsChillAccumulator):
    """ Convert temperatures to chill factors using min/max degree Chilling
    Unit Accumulation Model

    Value for constructor argument "accumulated_chill_units" must be a 2D
    array of [days, accumulated chill units by grid]

    Value for constructor argument "daily_chill_units" must be a 2D
    array of [days, daily total chill units by grid]

    Constructor argument "low_threshold" is minimum temperature at which
    accumulation occurs. Default is 0 degrees.

    Constructor argument "high_threshold" is maximum temperature at which
    accumulation occurs. Default is 45 degrees.

    Constructor argument "threshold_units" is the units (degress F or C)
    of the threshold temperatures. Default is degrees F

    Constructor argument "hourly_temp_units" is the units (degress F or C)
    of the temperatues in the hourly temperature array used to calculated
    chill units. Default is degrees F
    """

accumulators['points'] = PointsThresholdChillAccumulator

