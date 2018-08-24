
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

INVALID_TYPE = 'Invalid data type for "%s" attribute. Must be a list.'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ChillingUnitAccumulator(object):
    """Base Chilling Unit Accumulator
    """

    def __init__(self, accumulated_chill=None, daily_chill_units=None):

        self._accumulated_chill = accumulated_chill
        self._daily_chill = daily_chill_units

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, hourly_temps, debug=False):
        """Executes the complete accumulation stack :
            1. calls 'calcHourlyChillUnits' method with 'hourly_temps'
            2. calls 'calcDailyChillUnits' method with output from 1
               and extends cached daily chill array with the results
            3. calls 'accumulate' method with output from 2 and extends
               cached accumulated chill array with the results

        Returns a tuple with daily chill calculated by 'calcDailyChillUnits'
        method and accumulated chill calculated by 'accumulate' method.
        """
        daily_chill = self.calcDailyChillUnits(
                      self.calcHourlyChillUnits(hourly_temps, debug))
        if self._daily_chill is not None:
            self._daily_chill = N.vstack((self._daily_chill, daily_chill))
        else: self._daily_chill = daily_chill

        accumulated = self.accumulate(daily_chill, debug)
        if self._accumulated_chill is not None:
            self._accumulated_chill = N.vstack((self._accumulated_chill,
                                               accumulated))
        else: self._accumulated_chill = accumulated

        return daily_chill, accumulated

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulate(self, daily_chill_units):
        """Calculates the accumulated chill for a sequence of days.

        'daily_chill_units' is a Numpy array containing chill units
        for a sequence of days. The shape of the array is dependent
        on the requirements of the subclass impementation.

        Returns the accumulated chill thru each day in the sequence. The
        shape of the returned array is dependent on the requirements of
        the subclass implementation.
        """
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcDailyChillUnits(self, hourly_chill_units, debug=False):
        """Calculates the daily chill for a sequence of days.

        'hourly_chill_units' is a Numpy array containing chill units
        for 24 hours on each day in the sequence. The array shape is
        dependent on the requirements of the subclass's impementation.

        Returns the daily chill for each day in the sequence. The shape
        of the returned array is dependent on the requirements of the
        subclass implementation.
        """
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcHourlyChillUnits(self, hourly_temps, debug=False):
        """Calculates the hourly chill for a sequence of days.

        'hourly_temps' is a Numpy array containing temperatures for 24
        hours on each day in the sequence. The shape of the array is
        dependent on the requirements of the subclass's impementation.

        Returns the hourly chill for each day in the sequence. The shape
        of the returned array is dependent on the requirements of the
        subclass implementation.
        """
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAccumulatedChill(self):
        """Returns the cached sequence of accumulated chill totals

        The format of the returned Numpy array is dependent on the 
        requirements of the subclass implementation.
        """
        return self._accumulated_chill

    def getDailyChillUnits(self):
        """ Returns the cached daily chill totals.

        The format of the returned Numpy array is dependent on the 
        requirements of the subclass implementation.
        """
        return self._daily_chill

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _previouslyAccumulated(self):
        """Returns the accumulated chill total at the end of the cached
        sequence. The format of the returned array is dependent on the
        requirements of the subclass implementation.
        """
        raise NotImplementedError


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PointChillAccumulator(ChillingUnitAccumulator):
    """ Base Chilling Unit Accumulation for a single point location
    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulate(self, daily_chill_units, debug=False):
        """ Calculate the cumulative chill at a single location over a
        sequence of days.

        'daily_chill_units' is a 1D Numpy array containing chill units
        for a sequence of days at a sinlge point.

        Returns a 1D numpy array containing the accumulated chill thru
        each day in the sequence.
        """
        accumulated = self._previouslyAccumulated()

        for chill_units in daily_chill_units:
            if chill_units > 0 and accumulated < 0: accumulated = chill_units
            else: accumulated = accumulated + chill_units

        return accumulated

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcDailyChillUnits(self, hourly_chill_units, debug=False):
        """Calculates the daily chill for a sequence of days.

        'hourly_chill_units' is a 2D Numpy array containing chill units
        for 24 hours on each day in the sequence. The expected layout
        is [days, 24 hours] yeilding an N x 24 array.

        Returns a 1D Numpy array containing the total chill for each
        day in the sequence.
        """
        chill_units = list(N.nansum(hourly_chill_units, axis=1))
        if debug:
            print '\ndaily chill units\n', chill_units
        return chill_units

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAccumulatedChill(self):
        """Returns the cached sequence of accumulated chill totals as a
        1D Numpy array.
        """
        return ChillingUnitAccumulator.getAccumulatedChill(self)

    def getDailyChillUnits(self):
        """ Returns the cached daily chill totals as a 1D Numpy array.
        """
        return ChillingUnitAccumulator.getDailyChillUnits(self)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _previouslyAccumulated(self):
        """Returns the accumulated chill total at the end of the cached
        sequence as an integer.
        """
        if self._accumulated_chill is None: return 0
        else: return self._accumulated_chill[-1]


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PointsChillAccumulator(PointChillAccumulator):
    """ Base Chilling Unit Accumulation for multiple point locations that
    NOT on a regular 2D grid.
    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulate(self, daily_chill_units, debug=False):
        """ Calculate the cumulative chill at a multiple locations over
        a sequence of days.

        'daily_chill_units' is a 2D Numpy array containing chill units
        for a sequence of days at multiple points. The expected layout
        is [locations, days]. The number of days must be the same for
        all locations.

        Returns a 2D numpy array containing the accumulated chill thru
        each day in the sequence at each location. The layout of the
        returned array is [locations, days].
        """
        accumulated = self._previouslyAccumulated(daily_chill_units.shape[0])

        # for efficiency, swap axes to [days, locations]
        daily_chill_units = N.swapaxes(daily_chill_units,0,1)

        for day in range(daily_chill_units.shape[0]):
            chill_units = daily_chill_units[day]
            self._daily_chill.append(chill_units)

            zero_out = N.where((chill_units > 0) & (accumulated < 0))
            if len(zero_out[0]) > 0: accumulated[reset] = 0
            accumulated = accumulated + chill_units

            if debug:
                print '\nday %02d\nchill units' % day
                print chill_units
                print 'accumulated :\n', accumulated

            # save the daily and accumulated chill units to the cache
            self._accumulated_chill.append(accumulated)

        # total chill hours by location
        return accumulated

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcDailyChillUnits(self, hourly_chill_units, debug=False):
        """Calculates the daily chill for a sequence of days at
        multiple locations.

        'hourly_chill_units' is a 3D Numpy array containing chill units
        for 24 hours on each day in the sequence.The expected layout is 
        [locations, days, 24 hours]. The number of days must be the same
        for all locations.

        Returns a 2D Numpy array containing the total chill for each day
        in the sequence at each location. The layout of the returned
        array is [locations, days].
        """
        chill_units = N.nansum(hourly_chill_units, axis=2)
        if debug:
            print '\ndaily chill units\n', chill_units
        # exit array is [locations, days]
        return chill_units

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _previouslyAccumulated(self, num_locations):
        """Returns a 2D Numpy array containing the accumulated chill total
        for each location at the end of the cached sequence. The layout is
        [1, location totals]
        """
        if self._accumulated_chill is None:
            return N.zeros((num_locations,), dtype=float)
        else: return self._accumulated_chill[-1]


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GridChillAccumulator(PointsChillAccumulator):
    """ Base Chilling Unit Accumulation for grids of locations
    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulate(self, daily_chill_units, debug=False):
        """ Value for argument "daily_chill_units" must be a 3D array with
        axes = [days, 2D daily chill units grid]
        """
        """ Calculate the cumulative chill over a 2D grid for a sequence 
        of days.

        'daily_chill_units' is a 3D Numpy array containing chill units
        for a grid over sequence of days. The expected array layout is
        [days, x, y].

        Returns a 3D numpy array containing the accumulated chill thru
        each day in the sequence at each grid node. The layout of the
        returned array is [days, x, y].
        """
        # get an empty accumulation array of the correct shape
        if len(daily_chill_units.shape) == 2:
            accumulation = self._previouslyAccumulated(daily_chill_units.shape)
            accumulated = N.empty((1,) + daily_chill_units.shape,
                                  dtype=daily_chill_units.dtype)
            num_days = 1
        else:
            accumulation = self._previouslyAccumulated(daily_chill_units.shape[1:])
            accumulated = N.empty_like(daily_chill_units)
            num_days = daily_chill_units.shape[0]

        for day in range(num_days):
            chill_units = daily_chill_units[day]
            zero_out = N.where((chill_units > 0) & (accumulation < 0))
            if len(zero_out[0]) > 0: accumulation[zero_out] = 0
            accumulation = accumulation + chill_units
            # save the daily and accumulated chill units to the cache
            accumulated[day] = accumulation

            if debug:
                print '\nday %02d\nchill units' % day
                print chill_units
                print 'accumulation :\n', accumulation

        # total chill hours grid
        return accumulated

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcDailyChillUnits(self, hourly_chill_units, debug=False):
        """ Value for argument "hourly_chill_units" must be a 3D array
        with axes = [days, hourly chill units grid]
        """
        """Calculates the daily chill over a 2D grid for a sequence of
        days.

        'hourly_chill_units' is a 4D Numpy array containing chill units
        for 24 hours on each day in the sequence. The expected layout is 
        [days, x, y, 24 hours].

        Returns a 3D Numpy array containing the total chill for each day
        in the sequence at each grid node. The layout of the returned
        array is [days, x, y].
        """
        if len(hourly_chill_units.shape) == 4:
            chill_units = N.nansum(hourly_chill_units, axis=1)
        else:
            chill_units = N.empty((1,) + hourly_chill_units.shape[1:],
                                  dtype=hourly_chill_units.dtype)
            chill_units[0] = N.nansum(hourly_chill_units, axis=0)
        if debug:
            print '\nhourly chill shape', hourly_chill_units.shape
            print 'daily chill shape', chill_units.shape
            print 'daily chill grid\n', chill_units
    
        # exit array is [locations, days]
        return chill_units

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _previouslyAccumulated(self, grid_shape):
        """Returns a 3D Numpy array containing the accumulated chill total
        for the grid at the end of the cached sequence. The layout is
        [1, ,x ,y].
        """
        if self._accumulated_chill is None:
            return N.zeros((1,) + grid_shape, dtype=float)
        else: return self._accumulated_chill[-1]

