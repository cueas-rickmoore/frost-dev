
from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.agg.gdd import GridGDDCalculator

from frost.functions import fromConfig

from frost.apple.linvill.grid import temp3DGridToHourly, tempGridToHourly

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CHILL_DATA_ERR = "Missing data argument. AppleChillFileManager.estimateChill"
CHILL_DATA_ERR += " method argument list must include either 'hourly' or"
CHILL_DATA_ERR += " both 'mint' and 'maxt'"

CHILL_DATE_ERR = "Missing date argument. AppleChillFileManager.estimateChill"
CHILL_DATE_ERR += " method requires 'date' (a single date) or 'dates'"
CHILL_DATE_ERR += " (a list of dates)"

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleChillModelMixin:

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Chill estimation
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def chillCalculator(self, model_name, previous_accumulated=None,
                              previous_daily=None):
        config_path = 'crops.apple.chill.%s.accumulators.grid' % model_name
        Klass = fromConfig(config_path)
        return Klass(previous_accumulated, previous_daily)

    def chillDate(self, model_name):
        model_group = self.properName(model_name)
        return self._hdf5_file[model_group].attrs.get('chill_date', None)

    def chillThresholdDate(self, model_name, chill_threshold):
        days = self.chillThresholdIndex(model_name, chill_threshold)
        if days is None: return None
        else: return self.start_date + relativedelta(days=days)

    def chillThresholdIndex(self, model_name, chill_threshold):
        dataset_name = self.chillDatasetPath(model_name, 'accumulated')
        indexes = N.where(self.getData(dataset_name) >= chill_threshold)
        if len(indexes[0] > 0): return indexes[0].min()
        return None

    def estimateChill(self, model_name, **kwargs):
        """ estimate daily chill units and cumulative chill accumulation
        """
        debug = kwargs.get('debug', False)

        # look through possible date conbinations
        date_arg = kwargs.get('date', kwargs.get('dates', None))

        # not a single date or list of dates, look for start/end date
        if date_arg is None:
            start_date = kwargs.get('start_date', None)
            if start_date is None:
                raise KeyError, CHILL_DATE_ERR
            end_date = kwargs.get('end_date', None)
            if end_date is None:
                raise KeyError, CHILL_DATE_ERR
            # convert start/ end date into the list of dates that Linvill needs
            num_days = (end_date - start_date).days + 1
            date_arg = [ start_date + relativedelta(days=days)
                         for days in range(num_days) ]

        # may pass hourly temps when they are known
        hourly_temps = kwargs.get('hourly',None)
        if hourly_temps is None:
            # hourly temps were not passed ... need to iterpolate from mint/maxt
            mint = kwargs.get('mint', None)
            if mint is None:
                raise KeyError, CHILL_DATA_ERR
            maxt = kwargs.get('maxt', None)
            if maxt is None:
                raise KeyError, CHILL_DATA_ERR
            # get temperature units, default to Fahrenheit
            units = kwargs.get('units','F')

            # interpolate hourly temps from mint/maxt wit Linvill algorithm
            hourly_temps = self.linvill(date_arg, mint, maxt, units, debug)

        # set previous acummulation to zero - need 3D array even for 1 day
        previous = N.zeros((1,) + self.lats.shape, dtype=float)
        # attempt to override with actual previous day's accumulation
        if isinstance(date_arg, datetime): date = date_arg
        else: date = date_arg[0]
        if self.start_date is not None and date > self.start_date:
            previous[0] = self.getChill(model_name, 'accumulated',
                                        start_date=date-ONE_DAY)

        # create an instance of the chill accumulator class
        chill = self.chillCalculator(model_name, previous, None)
        # calculate daily chill units
        daily = chill.calcDailyChillUnits(
                chill.calcHourlyChillUnits(hourly_temps, debug) , debug)

        # calculate daily accumulations
        accumulated = chill.accumulate(daily)

        if daily.shape[0] == 1: return daily[0], accumulated[0]
        else: return daily, accumulated

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Linvill hourly temperature interpolation model
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def linvill(self, dates, mint, maxt, units='F', debug=False):
        """ interpolate hourly temperatures from mint,maxt using the 
        Linvill equations
        """
        if len(mint.shape) == 2:
            if isinstance(dates, (tuple,list)): date = dates[0]
            else: date = dates
            return tempGridToHourly(date, self.lats, mint, maxt, units, debug)
        elif len(mint.shape) == 3:
            return temp3DGridToHourly(dates, self.lats, mint, maxt, units, debug)
        else:
            errmsg = "Unsupported grid shape %s for 'mint'/'maxt'."
            errmsg += " Only 2D and 3D arrays are valid."
            raise ValueError, errmsg % str(mint.shape)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Growing Degree Day  estimation
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateGDD(self, lo_gdd_th, hi_gdd_th, mint, maxt, debug=False):
        gdd_calc = GridGDDCalculator(lo_gdd_th, hi_gdd_th)
        gdd = gdd_calc.estimateGDD(mint, maxt, debug)
        # make sure there are no GDD where they shouldn't be
        gdd[N.where(N.isnan(maxt))] = N.nan
        return gdd

    def gddAccumulationFactor(self, model_name):
        config_path ='crops.apple.chill.%s.accumulation_factor' % model_name
        return fromConfig(config_path)

