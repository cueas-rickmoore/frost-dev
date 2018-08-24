
from dateutil.relativedelta import relativedelta

import numpy as N

from atmosci.utils.timeutils import asDatetime, asAcisQueryDate
from atmosci.utils.units import convertUnits

from frost.functions import fromConfig, tempGridFilepath
from frost.grid import FrostGridFileReader, FrostGridFileManager
from frost.grid import FrostGridBuilderMixin

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostTempMixin:

    def getTemp(self, temp_dataset_path, start_date, end_date=None, **kwargs):
        return self._getData(temp_dataset_path, start_date=start_date,
                             end_date=end_date, **kwargs)

    def getTempProvenance(self, temp_dataset_path, start_date, end_date=None):
        prov_dataset_path = temp_dataset_path + '_provenance'
        return self._getData(prov_dataset_path, start_date=start_date,
                             end_date=end_date)

    def tempDatasetPath(self, source, temp_dataset_name):
        return '%s.%s' % (source, temp_dataset_name)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostTempFileReader(FrostGridFileReader, FrostTempMixin):

    def __init__(self, target_year, **kwargs):
        filepath = kwargs.get('filepath',None)
        if filepath is None:
            filepath = tempGridFilepath(target_year)
        FrostGridFileReader.__init__(self, target_year, filepath)

        self.temp_descriptions = { 'maxt':'Daily maximum temperature',
                                   'mint':'Daily minimum temperature' }

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        FrostGridFileReader._loadManagerAttributes_(self)

        unpacker = fromConfig('unpackers.temp')
        for dataset_path in self._dataset_names:
            if not dataset_path.endswith('provenance'):
                if 'maxt' in dataset_path or 'mint' in dataset_path:
                    self._unpackers[dataset_path] = unpacker

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostTempFileManager(FrostGridFileManager, FrostTempMixin):

    def __init__(self, target_year, mode='r', **kwargs):
        filepath = kwargs.get('filepath',None)
        if filepath is None:
            filepath = tempGridFilepath(target_year)
        FrostGridFileManager.__init__(self, target_year, filepath, mode,
                                      kwargs.get('unpackers',None),
                                      kwargs.get('packers',None))

        self.temp_descriptions = { 'maxt':'Daily maximum temperature',
                                   'mint':'Daily minimum temperature' }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateTemp(self, temp_dataset_path, data, start_date, **kwargs):
        # update temperature value dataset
        self.updateDataset(temp_dataset_path, data, start_date, **kwargs)

        # update stage provenance to correspond to data updates
        timestamp = kwargs.get('downloaded',
                               kwargs.get('timestamp', self.timestamp))
        generator = self.provenance.generators['temp']

        if data.ndim == 3:
            records = [ ]
            for day in range(data.shape[0]):
                date = start_date + relativedelta(days=day)
                record = generator(date, timestamp, data[day])
                records.append(record)
        else:
            records = [generator(start_date, timestamp, data),]

        prov = N.rec.fromrecords(records, shape=(len(records),),
                                 formats=self.provenance.formats.temp,
                                 names=self.provenance.names.temp)
        prov_dataset_path = temp_dataset_path + '_provenance'
        self.insertByDate(prov_dataset_path, prov, start_date)


    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        FrostGridFileManager._loadManagerAttributes_(self)

        packer = fromConfig('packers.temp')
        unpacker = fromConfig('unpackers.temp')
        for dataset_path in self._dataset_names:
            if not dataset_path.endswith('provenance'):
                if 'maxt' in dataset_path or 'mint' in dataset_path:
                    self._packers[dataset_path] = packer
                    self._unpackers[dataset_path] = unpacker


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostTempFileRepair(FrostTempFileManager, FrostGridBuilderMixin):

    def _resolveTemperatureAttributes_(self, group, **kwargs):
        default = fromConfig('default')
        # setup the dataset attributes
        temp_attrs = self._resolveCommonAttributes(**kwargs)
        temp_attrs.update(self._resolveDateAttributes(**kwargs))
        temp_attrs['missing'] = kwargs.get('missing', default.missing.temp)
        temp_attrs['units'] = kwargs.get('units', 'F')

        if group == 'reported':
            # add attributes for observed temperature group
            kwargs['source'] = kwargs.get('reported', default.source.reported)
            temp_attrs.update(self._resolveGridSourceAttributes(**kwargs))
        elif group == 'forecast':
            # add attributes for forecast temperature group
            kwargs['source'] = kwargs.get('forecast', default.source.forecast)
            temp_attrs.update(self._resolveGridSourceAttributes(**kwargs))
            if 'ndfd' in kwargs['source'].lower():
                if temp_attrs['grid_type'] == 'unknown':
                    temp_attrs['grid_type'] = default.grid_type
                if temp_attrs['node_spacing'] == 'unknown':
                    temp_attrs['node_spacing'] = default.node_spacing

        return temp_attrs


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class FrostTempFileBuilder(FrostTempFileRepair):

    def __init__(self, start_date, end_date, lons, lats, test_file=False,
                       verbose=False, **kwargs):
        """ create a new, fully configured HDF5 file for temperature data.
        """
        target_year = self._builder_preinit(start_date, end_date)
        if verbose:
            print 'FrostTempFileBuilder.__init__', target_year, start_date, end_date
        FrostTempFileRepair.__init__(self, target_year, 'w', **kwargs)
        self._builder_postinit(lons, lats, **kwargs)

        # initialize the temperature datasets
        init_temps = kwargs.get('init_temps', True)
        if init_temps: self.initTempGroups(**kwargs)

        self.open('a')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initTempGroups(self, include_forecast=True, **kwargs):
        # create datasets for observed temperature group
        temp_attrs = \
            self._resolveTemperatureAttributes_('reported', **kwargs)
        self.initTempDatasets('reported', temp_attrs, **kwargs)

        # create datasets for forecast temperature group
        if include_forecast:
            temp_attrs = \
                self._resolveTemperatureAttributes_('forecast', **kwargs)
            self.initTempDatasets('forecast', temp_attrs, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initTempDatasets(self, group, temp_attrs, **kwargs):
        """ create empty temperature datasets
        """
        default = self.default
        group_description = '%s Temperatures' % group.title()

        # extract date attributes from inputs
        end_str = asAcisQueryDate(self.end_date)
        num_days = (self.end_date - self.start_date).days + 1
        start_str = asAcisQueryDate(self.start_date)

        # extract attributes used to create dataset
        chunks = kwargs.get('chunks', (1,) + self.lons.shape)
        compression = kwargs.get('compression','gzip')
        dtype = kwargs.get('dtype','<i2')
        shape = kwargs.get('shape', (num_days,) + self.lons.shape)
        verbose = kwargs.get('verbose',False)

        # create the group
        if group not in self._group_names:
            if verbose: print 'creating', group
            self.open('a')
            self.createGroup(group, description=group_description)
            self.close()

        # create the temprature datasets
        temp_datasets = kwargs.get('temp_datasets', default.temp_datasets)

        for key, name in temp_datasets:
            full_dataset_path = '%s.%s' % (group, key)
            if full_dataset_path in self._dataset_names: continue

            # creat emepty temperature dataset
            description = '%s %s temperature' % (name, group.title())
            if verbose: print '\nCreating empty %s dataset' % full_dataset_path
            self.open('a')
            self.createEmptyDataset(full_dataset_path, shape, dtype, 
                            temp_attrs['missing'], description=description,
                            chunks=chunks, compression=compression,
                                    )
            self.setDatasetAttributes(full_dataset_path, **temp_attrs)
            self.close()

            # create empty provenance dataset
            full_dataset_path = '%s_provenance' % full_dataset_path
            description = 'Provenance for %s' % description.lower()
            self.open('a')
            self._createEmptyProvenance(full_dataset_path, 'temp', description,
                                        verbose)
            self.close()

