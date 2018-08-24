
from frost.functions import fromConfig
from frost.grid import FrostGridFileReader, FrostGridFileManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleGridReaderMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Chill model and GDD threshold methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hasModel(self, model_name):
        return self.modelGroupName(model_name) in self.file_chill_models

    def modelName(self, model_name):
        return self.properName(model_name).replace(' ','_')
    modelGroupName = modelName

    def thresholdName(self, low_threshold, high_threshold):
        return 'L%dH%d' % (low_threshold, high_threshold)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getTemp(self, temp_type, start_date, end_date=None):
        return self._getDataByDate(temp_type, start_date, end_date)

    def getTempProvenance(self, temp_type, start_date, end_date=None):
        dataset_name = '%s_provenance' % temp_type
        return self._getDataByDate(dataset_name, start_date, end_date)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _modelsInFile(self):
        return [ name for name in self._group_names
                      if name.lower() in self.apple_chill_models ]

    def _registerModel(self, model_name):
        self.file_chill_models.append(self.properName(model_name))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleGridfileReader(AppleGridReaderMixin, FrostGridFileReader):

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        self.apple_chill_models = fromConfig('crops.apple.chill.models')
        FrostGridFileReader._loadManagerAttributes_(self)
        self.file_chill_models = self._modelsInFile()
        unpackTemps = fromConfig('unpackers.temp')
        self._unpackers['maxt'] = unpackTemps
        self._unpackers['mint'] = unpackTemps

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleGridFileManager(AppleGridReaderMixin, FrostGridFileManager):

    def updateTemp(self, temp_type, data, start_date, **kwargs):
        # update temperature value dataset
        self.updateDataset(temp_type, data, start_date)
        # update stage provenance to correspond to data updates
        self._updateTempProvenance_(temp_type, start_date, data, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _updateTempProvenance_(self, temp_type, start_date, data, **kwargs):
        timestamp = kwargs.get('processed', self.timestamp)
        start_index = self.indexFromDate(start_date)
        generator = provenance.generator['temp']

        if data.ndim == 3:
            records = [ ]
            for day in range(data.shape[0]):
                date = start_date + relativedelta(days=day)
                record = generator(date, timestamp, data, source)
                records.append(record)
            end_index = start_index + data.shape[0]
        else:
            records = [generator(date, timestamp, data, source),]
            end_index = None

        prov = N.rec.fromrecords(records, shape=(len(records),),
                                 formats=self.temp_provenance_formats,
                                 names=self.temp_provenance_names)
        dataset_name = '%s_provenance' % temp_type
        self._insertDataByIndex(dataset_name, prov, start_index, end_index)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        self.apple_chill_models = fromConfig('crops.apple.chill.models')
        FrostGridFileManager._loadManagerAttributes_(self)
        self.file_chill_models = self._modelsInFile()
        packTemps = fromConfig('packers.temp')
        self._packers['maxt'] = packTemps
        self._packers['mint'] = packTemps
        unpackTemps = fromConfig('unpackers.temp')
        self._unpackers['maxt'] = unpackTemps
        self._unpackers['mint'] = unpackTemps

