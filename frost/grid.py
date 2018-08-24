
from datetime import datetime

from dateutil.relativedelta import relativedelta

import numpy as N

from atmosci.hdf5.manager import Hdf5DateGridFileReader
from atmosci.hdf5.manager import Hdf5DateGridFileManager

from atmosci.utils.timeutils import asDatetime, asAcisQueryDate
from atmosci.utils.units import convertUnits

from frost.functions import fromConfig, targetYearFromDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostGridMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDatasetUnits(self, dataset_path):
        attrs = self.getDatasetAttributes(dataset_path)
        return attrs.get('units', None)

    def properName(self, name):
        _name = name.replace('_', ' ').replace('(','').replace(')','')
        return _name.title()

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _getData(self, dataset_path, start_date, end_date=None, **kwargs):
        if end_date is None or end_date == start_date:
            return self.getDataForDate(dataset_path, start_date, **kwargs)
        return self.getDateSlice(dataset_path, start_date, end_date, **kwargs)

    def _postUnpack(self, dataset_path, data, **kwargs):
        to_units = kwargs.get('units', None)
        if to_units is not None:
            from_units = self.getDatasetUnits(dataset_path)
            if from_units is not None:
                if '*' in from_units: from_units = from_units.split('*')[0]
                data = convertUnits(data, from_units, to_units)
        return data

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _preInitFrost_(self, target_year):
        self.target_year = target_year
        self._packers = { }
        self._unpackers = { }

    def _postInitFrost_(self):
        self.default = fromConfig('default')
        self.node_search_radius = self.default.node_search_radius

    def _loadFrostFileAttributes_(self):
        attrs = self.getFileAttributes()
        if not hasattr(self, 'target_year'):
            self.target_year = attrs.get('target_year', None)
            if self.target_year is not None:
                self.target_year = int(self.target_year)
            elif self.end_date is not None:
                self.target_year = targetYearFromDate(self.end_date)

        for attr_name, attr_value in attrs.items():
            if attr_name not in ('start_date', 'end_date', 'target_year'):
                self.__dict__[attr_name] = attr_value
        if self.hasDataset('lon'):
            self.__dict__['acis_grid'] = \
                self.getDatasetAttribute('lon', 'acis_grid')
        else: self.__dict__['acis_grid'] = None


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostGridFileReader(FrostGridMixin, Hdf5DateGridFileReader):

    def __init__(self, target_year, filepath):

        self._preInitFrost_(target_year)
        Hdf5DateGridFileReader.__init__(self, filepath)
        self._postInitFrost_()

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        Hdf5DateGridFileReader._loadManagerAttributes_(self)
        self._loadFrostFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostGridFileManager(FrostGridMixin, Hdf5DateGridFileManager):

    def __init__(self, target_year, filepath, mode='r', unpackers=None,
                       packers=None):

        self._preInitFrost_(target_year)
        Hdf5DateGridFileManager.__init__(self, filepath, mode)
        self._postInitFrost_()

        self.provenance = fromConfig('provenance')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateDataset(self, dataset_path, data, start_date, **kwargs):
        errmsg =  'invalid dataset path "%s"' % dataset_path
        self.insertByDate(dataset_path, data, start_date, **kwargs)
        self._setLastValidDate(dataset_path, start_date, data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # provenance update methods used by multiple data types
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateProvenance(self, group_path, data, start_date, verbose=False,
                               **kwargs):
        """ Creates the provenance dataset based on statistics from the
        data grid. 

        Useful at any level, but primarily designed to be called from each
        group's update convenience method.

        Arguments
        --------------------------------------------------------------------
        group_path : string - the full path to one of the data groups
        data       : 2D or 3D grid - data to be used to calculated provenance
                     statistics If 3D, first dimension must be number of days.
        start_date : datetime, scalar - date of provenance entry. If input 
                     data is 3D, it is the first date and separate entries
                     will be made for each day.
        dataset_name : string - name of a dataset group.
        """
        prov_path = kwargs.get('prov_path','%s.provenance' % group_path)
        start_index = self.indexFromDate(prov_path, start_date)

        timestamp = kwargs.get('timestamp', self.timestamp)
        prov_key = kwargs.get('prov_key', 'stats')
        generateProvenance = self.provenance.generators[prov_key]

        if data.ndim == 2:
            records = [generateProvenance(start_date, timestamp, data),]
            num_days = 1
        else:
            num_days = data.shape[0]
            records = [ ]
            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                records.append(generateProvenance(date, timestamp, data[day]))
                if verbose: print date, records[-1]

        provenance = N.rec.fromrecords(records, shape=(num_days,),
                           formats=self.provenance.formats[prov_key],
                           names=self.provenance.names[prov_key])

        end_index = start_index + num_days
        dataset = self.getDataset(prov_path)
        dataset[start_index:end_index] = provenance
        self._setLastValidDate(prov_path, start_date, data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateAccumulateProvenance(self, group_path, daily, accumulated,
                                         start_date, verbose=False, **kwargs):
        """ Creates the provenance dataset for groups that track statistics 
        for both daily and accumulated data grids. 

        Useful at any level, but primarily designed to be called from each
        group's update convenience method.

        Arguments
        --------------------------------------------------------------------
        group_path  : string - the full path to one of the file's data groups
        daily       : float, 2D or 3D grid - daily data values.
                      If 3D, time must be first dimension
        accumulated : float, 2D or 3D grid - accumulated data values
                      If 3D, time must be first dimension
        start_date  : datetime, scalar - date of provenance entry. If input 
                      data is 3D, it is the first date and separate entries
                      will be made for each day.
        """
        # update provenance to correspond to data updates
        prov_path = kwargs.get('prov_path','%s.provenance' % group_path)
        start_index = self.indexFromDate(prov_path, start_date)

        timestamp = kwargs.get('timestamp', self.timestamp)
        prov_key = kwargs.get('prov_key', 'accum')
        generateProvenance = self.provenance.generators[prov_key]

        if daily.ndim == 2:
            records = [ generateProvenance(start_date, timestamp, daily,
                                           accumulated), ]
            num_days = 1
        else:
            num_days = daily.shape[0]
            records = [ ]
            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                record = generateProvenance(date, timestamp, daily[day],
                                            accumulated[day])
                records.append(record)
                if verbose: print date, records[-1]
        end_date = start_date + relativedelta(days=num_days)

        provenance = N.rec.fromrecords(records, shape=(num_days,),
                           formats=self.provenance.formats[prov_key],
                           names=self.provenance.names[prov_key])
        
        end_index = start_index + num_days
        dataset = self.getDataset(prov_path)
        dataset[start_index:end_index] = provenance
        self._setLastValidDate(prov_path, start_date, daily)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _prePack(self, dataset_path, data, **kwargs):
        from_units = kwargs.get('units', None)
        if from_units is not None:
            to_units = self.getDatasetUnits(dataset_path)
            if to_units is not None:
                if '*' in to_units: to_units = to_units.split('*')[0]
            data = convertUnits(data, from_units, to_units)
        return data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _setLastValidDate(self, dataset_path, start_date, data):
        if data.ndim == 2: num_days = 1
        else: num_days = data.shape[0]
        end_date = start_date + relativedelta(days=num_days-1)
        last_date_str = \
        self.getDatasetAttribute(dataset_path, 'last_valid_date', None)
        if isinstance(end_date, datetime):
            end_is_later = end_date > asDatetime(last_date_str)
        else: end_is_later = asDatetime(end_date) > asDatetime(last_date_str)
        if last_date_str is None or end_is_later:
            self.setDatasetAttribute(dataset_path, 'last_valid_date',
                                     end_date.strftime('%Y-%m-%d'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _loadManagerAttributes_(self):
        Hdf5DateGridFileManager._loadManagerAttributes_(self)
        self._loadFrostFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostGridBuilderMixin:

    def _builder_preinit(self, start_date, end_date):
        self._access_authority = ('r','a', 'w')
        self.start_date = start_date
        self.end_date = end_date
        return targetYearFromDate(start_date)

    def _builder_postinit(self, lons, lats, **kwargs):
        self._initFileAttributes(**kwargs)
        self.close()
        # cache the lon/lat grids
        self._initLonLatDatasets(lons, lats, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _createEmptyProvenance(self, dataset_path, prov_key, description,
                                     verbose=False):
        end_date = self.end_date
        end_str = asAcisQueryDate(end_date)
        start_date = self.start_date
        start_str = asAcisQueryDate(start_date)
        num_days = (end_date - start_date).days + 1

        empty_record = self.provenance.empty[prov_key]
        formats = self.provenance.formats[prov_key]
        names = self.provenance.names[prov_key]

        if names[0] in ('date','obs_date'):
            record_tail = empty_record[1:]
            records = [ ]
            for day in range(num_days):
                date = start_date + relativedelta(days=day)
                record = (asAcisQueryDate(date),) + record_tail
                records.append(record)
        else: records = [empty_record for day in range(num_days)]

        if verbose:
            print '\ncreating empty provenance for', prov_key
            print 'names', formats
            print 'formats', formats
            print 'empty record', empty_record
            print 'record  0', records[0]
            print 'record -1', records[-1], '\n'

        empty = N.rec.fromrecords(records, shape=(num_days,), formats=formats,
                                  names=names)
        self.createDataset(dataset_path, empty, raw=True)
        self.setDatasetAttributes(dataset_path, start_date=start_str,
                                  end_date=end_str, description=description)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initLonLatDatasets(self, lons, lats, **kwargs):
        attrs = self._resolveCommonAttributes(**kwargs)
        attrs.update(self._resolveGridSourceAttributes(**kwargs))

        # capture longitude/latitude limits of input grids
        min_lon = N.nanmin(lons)
        max_lon = N.nanmax(lons)
        min_lat = N.nanmin(lats)
        max_lat = N.nanmax(lats)

        self.open('a')
        attrs['description'] = 'Degrees West Longitude'
        attrs['max'] = max_lon
        attrs['min'] = min_lon
        self.createDataset('lon', lons, dtype=float, raw=True)
        self.setDatasetAttributes('lon', **attrs)
        self.lons = lons

        attrs['description'] = 'Degrees North Latitude',
        attrs['max'] = max_lat
        attrs['min'] = min_lat
        self.createDataset('lat', lats, dtype=float, raw=True)
        self.setDatasetAttributes('lat', **attrs)
        self.lats = lats

        self.setFileAttributes(min_lon=min_lon, max_lon=max_lon,
                               min_lat=min_lat, max_lat=max_lat)
        self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initFileAttributes(self, **kwargs):
        _kwargs_ = self._validateKwargs(kwargs)
        end_str = asAcisQueryDate(self.end_date)
        start_str = asAcisQueryDate(self.start_date)
        created = kwargs.get('created', self.timestamp)
        bbox = kwargs.get('data_bbox', None)
        if bbox is None: bbox = fromConfig('default.bbox.data')

        self.open('a')
        self.setFileAttributes(created=created, target_year=self.target_year,
                               start_date=start_str, end_date=end_str,
                               data_bbox=bbox)
        self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveCommonAttributes(self, **kwargs):
        default = fromConfig('default')
        if 'created' in kwargs: attrs = { 'created' : kwargs['created'] }
        else: attrs = { }
        # source based attributes
        source = kwargs.get('source', default.data_source)
        if 'acis' in source.lower():
            attrs['grid_type'] = kwargs.get('grid_type', default.grid_type)
            attrs['node_spacing'] = \
                 kwargs.get('node_spacing', default.node_spacing)
        else:
            attrs['grid_type'] = kwargs.get('grid_type', 'unknown')
            attrs['node_spacing'] = kwargs.get('node_spacing', 'unknown')
        return attrs
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveDateAttributes(self, **kwargs):
        end = kwargs.get('end_date', asAcisQueryDate(self.end_date))
        if isinstance(end, datetime): end = asAcisQueryDate(end)
        start = kwargs.get('start_date', asAcisQueryDate(self.start_date))
        if isinstance(start, datetime): start = asAcisQueryDate(start)
        return { 'start_date':start, 'end_date':end }

    def _setDateAttributes(self, dataset_path, **kwargs):
        date_attrs = self._resolveDateAttributes(**kwargs)
        self.setDatasetAttributes(dataset_path, **date_attrs)
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _resolveGridSourceAttributes(self, **kwargs):
        default = fromConfig('default')
        source = kwargs.get('source', default.data_source)
        attrs = { 'source':source, }
        if 'acis' in source.lower():
            attrs['acis_grid'] = kwargs.get('acis_grid', default.acis_grid)
        return attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _validateKwargs(self, kwargs):
        default = fromConfig('default')
        if 'acis_grid' not in kwargs: kwargs['acis_grid'] = default.acis_grid
        if 'search_bbox' not in kwargs:
            if 'bbox' in kwargs: 
                 kwargs['search_bbox'] = kwargs['bbox']
                 del kwargs['bbox']
            else: kwargs['search_bbox'] = default.bbox.data
        if 'node_spacing' not in kwargs:
            kwargs['node_spacing'] = default.node_spacing
        if 'source' not in kwargs: kwargs['source'] = default.source
        return kwargs

