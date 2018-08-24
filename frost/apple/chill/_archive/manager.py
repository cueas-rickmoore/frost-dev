
import os

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate
from atmosci.agg.gdd import GridGDDCalculator

from frost.functions import fromConfig
from frost.apple.functions import chillFilepath, chillModelDescription
from frost.apple.manager import AppleGridFileReader, AppleGridFileManager
from frost.apple.linvill.grid import temp3DGridToHourly, tempGridToHourly

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CHILL_DATA_ERR = "Missing data argument. AppleChillFileManager.estimateChill"
CHILL_DATA_ERR += " method argument list must include either 'hourly' or"
CHILL_DATA_ERR += " 'mint' and 'maxt'"

CHILL_DATE_ERR = "Missing date argument. AppleChillFileManager.estimateChill"
CHILL_DATE_ERR += " method requires 'date' (a single date) or 'dates'"
CHILL_DATE_ERR += " (a list of dates)"

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleChillMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataFilepath(self, target_year, test_file=False):
        return chillFilepath(target_year, test_file)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # chill model data access and storage methods                                 #
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def chillDatasetPath(self, model_name, dataset):
        group_name = self.modelGroupName(model_name)
        return '%s.%s' % (group_name, dataset)

    def chillDatasetShape(self, model_name, dataset):
        full_path = self.chillDatasetPath(model_name, dataset)
        return self.getDatasetShape(full_path)


    def gddAccumulationFactor(self, model_name):
        config_path ='crops.apple.chill.%s.accumulation_factor' % model_name
        return fromConfig(config_path)

    def chillModelExists(self, model_name):
        return self.groupExists(self.modelGroupName(model_name))
 
    def getChill(self, model_name, dataset, start_date, end_date=None):
        full_path = self.chillDatasetPath(model_name, dataset)
        return self._getDataByDate(full_path, start_date,end_date)
 
    def getChillProvenance(self, model_name, dataset, start_date,
                                 end_date=None):
        if dataset is not None:
            full_path =\
            self.chillDatasetPath(model_name, '%s_provenance' % dataset)
        else: full_path = self.chillDatasetPath(model_name, 'provenance')
        return self._getDataByDate(full_path, start_date, end_date)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Chill data access and estimation
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
            # mint not passed, need to access mint/maxt from current file
            if mint is None:
                if isinstance(date_arg, datetime): # date_arg is single date
                    maxt = self.getDataForDate('maxt', date_arg)
                    mint = self.getDataForDate('mint', date_arg)
                else: # date_arg contains a sequential list of dates
                    start = date_arg[0]
                    end = date_arg[-1]
                    maxt = self.getDataForDates('maxt', start, end)
                    mint = self.getDataForDates('mint', start, end)
            # mint was passed
            else:
                # maxt must be there too
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

        return daily, accumulated

    def thresholdGroupPath(self, lo_gdd_th, hi_gdd_th):
        return 'gdd.%s' % self.thresholdName(lo_gdd_th, hi_gdd_th)

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
    # Growing Degree Day data access and storage methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateGDD(self, lo_gdd_th, hi_gdd_th, mint, maxt, debug=False):
        gdd_calc = GridGDDCalculator(lo_gdd_th, hi_gdd_th)
        gdd = gdd_calc.estimateGDD(mint, maxt, debug)
        # make sure there are no GDD where they shouldn't be
        gdd[N.where(N.isnan(maxt))] = N.nan
        return gdd

    def getGdd(self, lo_gdd_th, hi_gdd_th, start_date, end_date=None):
        full_path = self.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'daily')
        return self._getDataByDate(full_path, start_date, end_date)

    def getGddProvenance(self, lo_gdd_th, hi_gdd_th, start_date, end_date=None):
        full_path = self.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'provenance')
        return self._getDataByDate(full_path, start_date, end_date)

    def gddDatasetPath(self, lo_gdd_th, hi_gdd_th, dataset):
        group_name = self.gddGroupName(lo_gdd_th, hi_gdd_th)
        return 'gdd.L%dH%d.%s' % (lo_gdd_th, hi_gdd_th, dataset)

    def gddGroupName(self, lo_gdd_th, hi_gdd_th):
        return 'gdd.L%dH%d' % (lo_gdd_th, hi_gdd_th)

    def gddThresholds(self):
        thresholds  = [ ]
        for group_name in self._group_names:
            if group_name.startswith('gdd.L'):
                names = group_name.split('.')
                if len(names) == 2:
                    low, high = names[1][1:].split('H')
                    thresholds.append( (int(low), int(high)) )
        return thresholds

    def hasThreshold(self, lo_gdd_th, hi_gdd_th):
        full_path = self.thresholdGroupPath(lo_gdd_th, hi_gdd_th)
        return full_path in self._group_names

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadChillFileAttributes_(self):
        AppleGridFileManager._loadManagerAttributes_(self)
        ThisClass = self.__class__
        for group_name in self._group_names:
            for dataset_path in self.getGroupHierarchy(group_name)[1:]:
                if dataset_path.split('.')[-1] in ('daily','accumulated'):
                    if 'gdd' in group_name:
                        self._packers[dataset_path] = ThisClass.packGdd
                        self._unpackers[dataset_path] = ThisClass.unpackGdd
                    else:
                        self._packers[dataset_path] = ThisClass.packChill
                        self._unpackers[dataset_path] = ThisClass.unpackChill

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _postInitAppleChill_(self, target_year, **kwargs):
        self.target_year = target_year

        self.chill_provenance_empty =\
             fromConfig('crops.apple.chill.provenance_empty')
        chill_provenance_type =\
             fromConfig('crops.apple.chill.provenance_type')
        self.chill_provenance_formats =\
             [item[1] for item in chill_provenance_type]
        self.chill_provenance_names =\
             [item[0] for item in chill_provenance_type]

        self.gdd_provenance_empty =\
             fromConfig('crops.apple.gdd_provenance_empty')
        gdd_provenance_type =\
             fromConfig('crops.apple.gdd_provenance_type')
        self.gdd_provenance_formats =\
             [item[1] for item in gdd_provenance_type]
        self.gdd_provenance_names =\
             [item[0] for item in gdd_provenance_type]

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # static methods for data packing and unpacking (serialization)
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    @staticmethod
    def packChill(data):
        nans = N.where(N.isnan(data))
        packed = (data * 10.).astype('<i2')
        if len(nans[0]) > 0: packed[nans] = -32768
        return packed

    @staticmethod
    def packGdd(data):
        nan_indexes = N.where(N.isnan(data))
        packed = data.astype('<i2')
        if len(nan_indexes[0]) > 0: packed[nan_indexes] = -32768
        return packed

    @staticmethod
    def unpackChill(raw_data):
        nans = N.where(raw_data < -32767)
        unpacked = raw_data.astype(float) / 10.
        if len(nans[0]) > 0: unpacked[nans] = N.nan
        return unpacked

    @staticmethod
    def unpackGdd(raw_data):
        nan_indexes = N.where(raw_data < -32767)
        unpacked = raw_data.astype(float)
        if len(nan_indexes[0]) > 0: unpacked[nan_indexes] = N.nan
        return unpacked


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleChillFileReader(AppleGridFileReader, AppleChillMixin):

    def __init__(self, target_year, test_file=False, **kwargs):
        if 'filepath' in kwargs:
            AppleGridFileReader.__init__(self, kwargs['filepath'])
        else:
            filepath = chillFilepath(target_year, test_file)
            AppleGridFileReader.__init__(self, filepath)

        self._postInitAppleChill_(target_year, **kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        """ Creates instance attributes specific to the content of the file
        to be managed.
        """
        # get superclass manager attributes
        AppleGridFileReader._loadManagerAttributes_(self)
        self._loadChillFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleChillFileManager(AppleGridFileManager, AppleChillMixin):

    def __init__(self, target_year, mode='r', test_file=False, **kwargs):
        if 'filepath' in kwargs:
            AppleGridFileManager.__init__(self, kwargs['filepath'], mode)
        else:
            filepath = chillFilepath(target_year, test_file)
            AppleGridFileManager.__init__(self, filepath, mode)

        self._postInitAppleChill_(target_year, **kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # chill model data update
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def updateChill(self, model_name, daily, accumulated, start_date, **kwargs):
        full_path = self.chillDatasetPath(model_name, 'accumulated')
        self.updateDataset(full_path, accumulated, start_date)
        full_path = self.chillDatasetPath(model_name, 'daily')
        self.updateDataset(full_path, daily, start_date)

        if daily.ndim == 2: num_days = 1
        else: num_days = daily.shape[0]
        indx = self.indexFromDate(start_date)
        end_index = indx + num_days
        timestamp = kwargs.get('processed', self.timestamp)

        records = [ ]
        for days in range(num_days):
            date = start_date + relativedelta(days=days)
            record = ( asAcisQueryDate(date), timestamp, int(N.nanmin(daily)),
                       int(N.nanmax(daily)), int(N.nanmean(daily)),
                       int(N.nanmin(accumulated)), int(N.nanmax(accumulated)),
                       int(N.nanmean(accumulated)) )
            records.append(record)

        provenance = N.rec.fromrecords(records, shape=(num_days,),
                                       formats=self.chill_provenance_formats,
                                       names=self.chill_provenance_names)
        full_path = self.chillDatasetPath(model_name, 'provenance')
        self._insertDataByIndex(full_path, provenance, indx, end_index)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Growing degree day update
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def updateGdd(self, lo_gdd_th, hi_gdd_th, data, start_date, **kwargs):
        full_path = self.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'daily')
        self.updateDataset(full_path, data, start_date)
        if data.ndim == 2: num_days = 1
        else: num_days = data.shape[0]
        indx = self.indexFromDate(start_date)
        end_index = indx + num_days
        timestamp = kwargs.get('processed', self.timestamp)

        records = [ ]
        for days in range(num_days):
            date = start_date + relativedelta(days=days)
            records.append( ( asAcisQueryDate(date), timestamp,
                              int(N.nanmin(data)), int(N.nanmax(data)), 
                              int(N.nanmean(data)) ) )

        provenance = N.rec.fromrecords(records, shape=(num_days,),
                                       formats=self.gdd_provenance_formats,
                                       names=self.gdd_provenance_names)
        full_path = self.gddDatasetPath(lo_gdd_th, hi_gdd_th, 'provenance')
        self._insertDataByIndex(full_path, provenance, indx, end_index)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        """ Creates instance attributes specific to the content of the file
        to be managed.
        """
        # get superclass manager attributes
        AppleGridFileManager._loadManagerAttributes_(self)
        self._loadChillFileAttributes_()

