
import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

try:
    import simplejson as json
except ImportError:
    import json

import numpy as N

from atmosci.acis.griddata import AcisGridDataClient
from atmosci.utils.timeutils import asDatetime, asAcisQueryDate
from atmosci.utils.timeutils import timeSpanToIntervals

from frost.functions import fromConfig, targetYearFromDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostDataFactory(object):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def properName(self, name):
        _name = name.replace('_', ' ').replace('(','').replace(')','')
        return _name.title()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def datesFromDateSpan(self, start_date, end_date=None):
        if end_date is None: return (start_date,)
        else: return timeSpanToIntervals(start_date, end_date, 'day', 1)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getTargetDateSpan(self, year_or_start_date, crop=None, variety=None):
        if crop is not None:
            path = 'crops.%s' % crop 
            if variety is not None:
                if isinstance(variety, basestring):
                    path ='%s.variety.%s' % (path, variety)
                else: path ='%s.variety.%s' % (path, variety.name)
        else: path = 'default'
        config = fromConfig(path)

        if isinstance(year_or_start_date, int):
            target_year = year_or_start_date
            start_date = (target_year-1,) + default.start_day
            end_date = (target_year,) + default.end_day
        elif isinstance(year_or_start_date, (tuple,list)):
            _date = datetime.datetime(*year_or_start_date)
            start_date, end_date = self._targetSpanFromDate(_date, config)
        elif isinstance(year_or_start_date, (datetime.datetime,datetime.date)):
            _date = year_or_start_date
            start_date, end_date = self._targetSpanFromDate(_date, config)
        else:
            errmsg = "Invalid type for 'year_or_start_date' argument : %s"
            raise TypeError, errmsg % type(year_or_start_date)

        return datetime.datetime(*start_date), datetime.datetime(*end_date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getTargetYear(self, date, crop=None, variety=None):
        return targetYearFromDate(date, crop=None, variety=None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _targetSpanFromDate(self, _date, config):
        # target_year same year as _date.year
        if _date.month < config.start_day[0]:
            start_date = (_date.year-1,) + config.start_day
            end_date = (_date.year,) + config.end_day
            return start_date, end_date
        # target_year potentially the same as _date.year
        if _date.month == config.start_day[0] \
        and _date.day < config.start_day[1]: # target_year same as _date.year
            start_date = (_date.year-1,) + config.start_day
            end_date = (_date.year,) + config.end_day
            return start_date, end_date
        # target_year not the same as _date.year
        start_date = (_date.year,) + default.start_day
        end_date = (_date.year+1,) + default.end_day
        return start_date, end_date

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostGridFactory(FrostDataFactory):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAcisGridData(self, elems, start_date, end_date=None, meta=None,
                              bbox=None, grid=None, debug=False):
        if bbox is None: bbox = fromConfig('default.bbox.data')
        if grid is None: grid = fromConfig('default.acis_grid')
        query = '{"grid":"%d","bbox":"%s"' % (grid, bbox)
        _start_date = asAcisQueryDate(start_date)
        if end_date is not None:
            _end_date = asAcisQueryDate(end_date)
            query += ',"sdate":"%s","edate":"%s"' % (_start_date, _end_date)
        else:
            query += ',"date":"%s"' % _start_date

        if isinstance(elems, basestring):
            if ',' in elems: _elems = elems.split(',')
            else: _elems = elems
        if isinstance(_elems, (list,tuple)):
            _elems_ = [ ]
            for name in _elems:
                _elems_.append('{"name":"%s"}' % name)
            query += ',"elems":[%s]' % ','.join(_elems_)
        else: query += ',"elems":"%s"' % _elems

        if isinstance(meta, basestring): query += ',"meta":"%s"' % meta
        elif isinstance(meta, (list,tuple)):
            query += ',"meta":"%s"' % ','.join(meta)

        query += '}'
        if debug: print 'factory.getAcisGridData :\n', query

        client = AcisGridDataClient(debug=debug)
        # returns python dict { 'meta' = { "lat" : grid, 'lon' : grid }
        #                       'data' = [ [date string, mint_grid] ]
        query_result = json.loads(client.query(query)[0])

        return self.unpackQueryResults(query_result, _elems, meta)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def unpackQueryResults(self, query_result, elems, meta):
        # unpack the grids
        if isinstance(elems, basestring): _elems = elems.split(',')
        else: _elems = elems
        data = [ ]
        for result in query_result['data']:
            date = [asDatetime(result[0]),]
            for indx, grid in enumerate(result[1:]):
                elem_name = _elems[indx]
                date.append(self.unpackGrid(elem_name, grid))
            data.append(date)

        if len(data) > 1:
            # convert list of (date, elem, ...) tuples to date tuple,
            # and a data tuple for each element
            data = zip(*data)
            # convert data tuples to arrays
            for indx, grid in enumerate(data[1:],start=1):
                data[indx] = N.array(grid)
        else:
            date = data[0][0]
            data = [grid for grid in data[0][1:]]
            data.insert(0,(date,))

        data_dict = { 'dates': data[0], }
        for indx, elem_name in enumerate(_elems, start=1):
            data_dict[elem_name] = data[indx]

        if meta is not None:
            meta_dict = query_result['meta']
            if 'elev' in meta_dict:
                meta_dict['elev'] = self.unpackGrid('elev', meta_dict['elev'])
            if 'lat' in meta_dict:
                meta_dict['lat'] = self.unpackGrid('lat', meta_dict['lat'])
                meta_dict['lon'] = self.unpackGrid('lon', meta_dict['lon'])
            data_dict.update(meta_dict)

        return data_dict

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def unpackGrid(self, elem, grid):
        if 'M' in grid:
            grid = N.array(grid)
            grid[N.where(grid=='M')] = -999
            grid = grid.astype(float)
        else: grid = N.array(grid, float)
        grid[grid<-998] = N.nan
        return grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getTempGridFilePath(self, target_year, test_file=False):
        from frost.functions import tempGridFilepath
        return tempGridFilepath(target_year, test_file)

    def getTempGridReader(self, target_year, test_file=False):
        from frost.functions import tempGridReader
        return tempGridReader(target_year, test_file)

    def getTempGridManager(self, target_year, mode='r', test_file=False):
        from frost.functions import tempGridManager
        return tempGridManager(target_year, mode, test_file)

    def newTempGridManager(self, target_year, data_bbox=None, test_file=False,
                                 verbose=False, **kwargs):
        from frost.temperature import FrostTempFileBuilder
        start_date, end_date = self.getTargetDateSpan(target_year)
        end_date += ONE_DAY
        if verbose:
            print 'newTempGridManager', target_year, data_bbox
            print 'newTempGridManager dates', start_date, end_date
        grid_number = fromConfig('default.acis_grid')
        data = self.getAcisGridData('mint', start_date, None, 'll', data_bbox,
                                    grid_number)
        if test_file:
            filepath = self.getTempGridFilePath(target_year, test_file)
            return FrostTempFileBuilder(start_date, end_date, data['lon'],
                                data['lat'], test_file, verbose,
                                filepath=filepath, data_bbox=data_bbox,
                                acis_grid=grid_number, **kwargs)
        else:
            return FrostTempFileBuilder(start_date, end_date, data['lon'],
                                data['lat'], test_file, verbose, 
                                data_bbox=data_bbox, acis_grid=grid_number,
                                **kwargs)

