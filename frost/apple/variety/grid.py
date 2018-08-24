
import os

from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig
from frost.grid import FrostGridBuilderMixin

from frost.apple.functions import varietyFilepath, getAppleVariety
from frost.apple.functions import chillModelDescription
from frost.apple.grid import AppleGridFileManager, AppleGridFileReader

from frost.apple.variety.model import AppleVarietyModelMixin

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class VarietyGridAccessMixin:
    """ Apple variety data is stored in a hierarchical structure rooted
    in the Chill Model :

       Xxxxx - Chill Model Group
            LnnHnn - GDD Threshold Group
                gdd - GDD Accumulation Group
                    data - GDD Accumulation Dataset
                    provenance - GDD Accumulation Provenance Dataset
                stage - Phenological Stage
                    data - Phenological Stage Dataset
                    provenance - Phenological Stage Provenance Dataset
                kill - Kill Estimate Group
                    data - Kill Estimate Dataset
                    provenance - Kill Estimate Provenance Dataset
    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataFilepath(self, year, variety_name, test_file=False):
        return varietyFilepath(target_year, variety_name, test_file)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Model dataset and group access
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def getModelData(self, model_name, lo_gdd_th, hi_gdd_th, group, dataset,
                           start_date, end_date=None, **kwargs):
        full_path = self.modelDatasetPath(model_name, lo_gdd_th, hi_gdd_th,
                                          group, dataset)
        return self._getData(full_path, start_date, end_date, **kwargs)

    def getProvenance(self, model_name, lo_gdd_th, hi_gdd_th, group,
                           start_date, end_date=None):
        return self.getModelData(model_name, lo_gdd_th, hi_gdd_th, group,
                                 'provenance', start_date, end_date)

    def hasModelDataset(self, model_name, lo_gdd_th, hi_gdd_th, group,
                              dataset):
        full_path = self.modelDatasetPath(model_name, lo_gdd_th, hi_gdd_th,
                                          group, dataset)
        return self.hasDataset(full_path)

    def hasModelGroup(self, model_name, lo_gdd_th, hi_gdd_th, group):
        full_path = self.modelGroupPath(model_name, lo_gdd_th, hi_gdd_th,
                                        group)
        return self.hasGroup(full_path)

    def modelDatasetPath(self, model_name, lo_gdd_th, hi_gdd_th, group,
                               dataset):
        full_path = self.modelGroupPath(model_name, lo_gdd_th, hi_gdd_th,
                                        group)
        return '%s.%s' % (full_path, dataset)

    def modelDatasetShape(self, model_name, lo_gdd_th, hi_gdd_th, group, 
                                dataset):
        full_path = self.modelDatasetPath(model_name, lo_gdd_th, hi_gdd_th,
                                          group, dataset)
        return self.getDatasetShape(full_path)

    def modelGroupPath(self, model_name, lo_gdd_th, hi_gdd_th, group):
        full_path = self.thresholdGroupPath(model_name, lo_gdd_th, hi_gdd_th)
        return '%s.%s' % (full_path, group)

    def modelName(self, model_key): return self.properName(model_key)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # GDD threshold group access
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def gddThresholds(self, model_name):
        threshold_key = "%s.L" % self.modelName(model_name)
        gdd_thresholds  = [ ]
        for path in self._group_names:
            if path.startswith(threshold_key):
                names = path.split('.')
                if len(names) == 2:
                    low, high = names[1][1:].split('H')
                    gdd_thresholds.append( (int(low), int(high)) )
        return gdd_thresholds

    def hasThreshold(self, model_name, lo_gdd_th, hi_gdd_th):
        full_path = self.thresholdGroupPath(model_name, lo_gdd_th, hi_gdd_th)
        return full_path in self._group_names

    def thresholdGroupPath(self, model_name, lo_gdd_th, hi_gdd_th):
        return '%s.%s' % (self.modelName(model_name),
                          self.thresholdName(lo_gdd_th, hi_gdd_th))

    def thresholdName(self, lo_gdd_th, hi_gdd_th):
        return 'L%dH%d' % (lo_gdd_th, hi_gdd_th)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Growing degree day data acccess
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def getChillMask(self, model_name, lo_gdd_th, hi_gdd_th, start_date,
                           end_date=None):
        return self.getModelData(model_name, lo_gdd_th, hi_gdd_th, 'gdd',
                                 'chill_mask', start_date, end_date)

    def getGdd(self, model_name, lo_gdd_th, hi_gdd_th, start_date,
                     end_date=None, **kwargs):
        return self.getModelData(model_name, lo_gdd_th, hi_gdd_th, 'gdd',
                                 'accumulated', start_date, end_date, **kwargs)

    def getGddProvenance(self, model_name, lo_gdd_th, hi_gdd_th, start_date,
                               end_date=None):
        return self.getModelData(model_name, lo_gdd_th, hi_gdd_th, 'gdd',
                                 'provenance', start_date, end_date)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Kill data acccess
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def getKill(self, model_name, lo_gdd_th, hi_gdd_th, start_date,
                      end_date=None, **kwargs):
        return self.getModelData(model_name, lo_gdd_th, hi_gdd_th, 'kill',
                                 'level', start_date, end_date, **kwargs)

    def getKillProvenance(self, model_name, lo_gdd_th, hi_gdd_th, start_date,
                                end_date=None):
        return self.getModelData(model_name, lo_gdd_th, hi_gdd_th, 'kill',
                                 'provenance', start_date, end_date)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # Phenological stage access
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def getStage(self, model_name, lo_gdd_th, hi_gdd_th, start_date,
                       end_date=None, **kwargs):
        return self.getModelData(model_name, lo_gdd_th, hi_gdd_th, 'stage',
                                 'index', start_date, end_date, **kwargs)

    def getStageProvenance(self, model_name, lo_gdd_th, hi_gdd_th, start_date,
                                 end_date=None):
        return self.getModelData(model_name, lo_gdd_th, hi_gdd_th, 'stage',
                                 'provenance', start_date, end_date)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    @staticmethod
    def unpackGdd(raw_data):
        nan_indexes = N.where(raw_data < -32767)
        data = raw_data.astype(float)
        if len(nan_indexes[0]) > 0: data[nan_indexes] = N.nan
        return data


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleVarietyGridReader(AppleGridFileReader, VarietyGridAccessMixin,
                             AppleVarietyModelMixin):

    def __init__(self, target_year, variety, test_file=False,
                       **kwargs):
        filepath = kwargs.get('filepath', 
                              varietyFilepath(target_year, variety, test_file))
        AppleGridFileReader.__init__(self, target_year, filepath)

        if isinstance(variety, basestring):
            self.variety = getAppleVariety(variety)
        else: self.variety = variety

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        AppleGridFileReader._loadManagerAttributes_(self)
        # assign packer/unpacker for each gdd dataset
        ThisClass = self.__class__
        for dataset_path in self._dataset_names:
            if 'gdd' in dataset_path and not dataset_path.endswith('.provenance'):
                self._unpackers[dataset_path] = ThisClass.unpackGdd


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleVarietyGridManager(AppleGridFileManager, VarietyGridAccessMixin,
                              AppleVarietyModelMixin):

    def __init__(self, target_year, variety, mode='r', test_file=False,
                       **kwargs):
        if 'filepath' in kwargs: filepath = kwargs['filepath']
        else: filepath = varietyFilepath(target_year, variety, test_file)

        AppleGridFileManager.__init__(self, target_year, filepath, mode)

        if isinstance(variety, basestring):
            self.variety = getAppleVariety(variety)
        else: self.variety = variety

        self._loadProvenanceDependencies_()
        self.provenance.update(fromConfig('crops.apple.variety.provenance'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setThresholdAttrs(self, model_name, lo_gdd_th, hi_gdd_th, group=None,
                                dataset=None, **kwargs):
        if dataset is not None:
            dataset_path = self.modelDatasetPath(model_name, lo_gdd_th,
                                                 hi_gdd_th, group, dataset)
        elif group is not None:
            dataset_path = self.modelGroupPath(model_name, lo_gdd_th, hi_gdd_th,
                                               group)
        else:
            dataset_path = self.thresholdGroupPath(model_name, lo_gdd_th,
                                                   hi_gdd_th)
        self._setThresholdAttrs(dataset_path, model_name, lo_gdd_th, hi_gdd_th,
                                **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateGdd(self, model_name, lo_gdd_th, hi_gdd_th, accumulated,
                        chill_mask, start_date, **kwargs):
        # update accumulated GDD dataset
        full_path = self.modelDatasetPath(model_name, lo_gdd_th, hi_gdd_th,
                                          'gdd', 'accumulated')
        self.updateDataset(full_path, accumulated, start_date)
        # update chill mask dataset
        full_path = self.modelDatasetPath(model_name, lo_gdd_th, hi_gdd_th,
                                          'gdd', 'chill_mask')
        self.updateDataset(full_path, chill_mask, start_date)
        # update GDD provenance
        group_path = \
            self.modelGroupPath(model_name, lo_gdd_th, hi_gdd_th, 'gdd')
        self.updateProvenance(group_path, accumulated, start_date, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateKill(self, model_name, lo_gdd_th, hi_gdd_th, levels, start_date,
                         **kwargs):
        # update kill probability dataset
        full_path = self.modelDatasetPath(model_name, lo_gdd_th, hi_gdd_th,
                                          'kill', 'level')
        self.updateDataset(full_path, levels, start_date)
        # update kill provenance to correspond to data updates
        group_path = \
            self.modelGroupPath(model_name, lo_gdd_th, hi_gdd_th, 'kill')
        self.updateProvenance(group_path, levels, start_date, prov_key='kill',
                              **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateStage(self, model_name, lo_gdd_th, hi_gdd_th, stage_grid,
                          start_date, **kwargs):
        # update stage index dataset
        full_path = self.modelDatasetPath(model_name, lo_gdd_th, hi_gdd_th,
                                          'stage', 'index')
        self.updateDataset(full_path, stage_grid, start_date)
        # update stage provenance to correspond to data updates
        group_path = \
            self.modelGroupPath(model_name, lo_gdd_th, hi_gdd_th, 'stage')
        self.updateProvenance(group_path, stage_grid, start_date,
                              prov_key='stage', **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _loadProvenanceDependencies_(self):
        provenance = fromConfig('crops.apple.variety.provenance')

        # Kill provenance
        self.provenance.generators.kill = self._killProvenanceGenerator_
        self.provenance.empty.kill = provenance.empty.kill
        self.provenance.formats.kill = provenance.formats.kill
        self.provenance.names.kill = provenance.names.kill

        # Stage provenance
        self.provenance.generators.stage = self._stageProvenanceGenerator_
        self.provenance.empty.stage = provenance.empty.stage
        self.provenance.formats.stage = provenance.formats.stage
        self.provenance.names.stage = provenance.names.stage

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _killProvenanceGenerator_(self, date, timestamp, levels):
        # start with observation date and processing timestamp
        record = [asAcisQueryDate(date),]
        # add count for no kill
        record.append(len(N.where(levels == 0)[0]))
        # add counts for each kill temp
        for kill in self.kill_levels:
            record.append(len(N.where(levels == kill)[0]))
        record.append(timestamp)
        return tuple(record)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _stageProvenanceGenerator_(self, date, timestamp, stages):
        # start with observation date and processing timestamp
        record = [asAcisQueryDate(date),]
        # add count for each phenological stage
        for stage in range(len(self.stages)+1):
            record.append(len(N.where(stages == stage)[0]))
        record.append(timestamp)
        return tuple(record)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        AppleGridFileManager._loadManagerAttributes_(self)
        # assign packer/unpacker for each gdd dataset
        ThisClass = self.__class__
        for dataset_path in self._dataset_names:
            if 'gdd' in dataset_path and not dataset_path.endswith('.provenance'):
                self._packers[dataset_path] = ThisClass.packGdd
                self._unpackers[dataset_path] = ThisClass.unpackGdd

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    @staticmethod
    def packGdd(data):
        nan_indexes = N.where(N.isnan(data))
        packed = data.astype('<i2')
        if len(nan_indexes[0]) > 0: packed[nan_indexes] = -32768
        return packed


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleVarietyGridRepair(AppleVarietyGridManager, FrostGridBuilderMixin,
                              AppleVarietyModelMixin):

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _resolveThresholdAttrs(self, full_path, model_name, lo_gdd_th,
                                     hi_gdd_th, **kwargs):
        attrs = { 'chill_model' : chillModelDescription(model_name),
                  'lo_GDD_threshold' : lo_gdd_th,
                  'hi_GDD_threshold' : hi_gdd_th,
                }
        attrs.update(self._resolveDateAttributes(**kwargs))

        if full_path in self._dataset_names:
            if 'source' not in kwargs:
                kwargs['source'] = fromConfig('default.data_source')
            attrs.update(self._resolveGridSourceAttributes(**kwargs))
        return attrs

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _setThresholdAttrs(self, full_path, model_name, lo_gdd_th,
                                 hi_gdd_th, **kwargs):
        attrs = self._resolveThresholdAttrs(full_path, model_name, lo_gdd_th,
                                            hi_gdd_th, **kwargs)
        if full_path in self._dataset_names:
            self.setDatasetAttributes(full_path, **attrs)
        else: self.setGroupAttributes(full_path, **attrs)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleVarietyGridBuilder(AppleVarietyGridRepair):

    def __init__(self, variety,  start_date, end_date, lons, lats, models, 
                       gdd_thresholds, test_file=False, verbose=False,
                       **kwargs):
        """ Create a new, fully configured HDF5 file for a data belonging to 
        a particular apple variety.
        """
        target_year = self._builder_preinit(start_date, end_date)
        AppleVarietyGridRepair.__init__(self, target_year, variety, 'w',
                                         test_file, **kwargs)
        self._builder_postinit(lons, lats, **kwargs)

        # initialize the model groups and datasets
        for model_name in models:
            self.open('a')
            self._initModelGroup(model_name, verbose)
            self.close()
            for lo_gdd_th, hi_gdd_th in gdd_thresholds:
                self.open('a')
                self._initThresholdDatasets(model_name, lo_gdd_th, hi_gdd_th,
                                            verbose)
                self.close()

        # leave the builder open for writes
        self.open('a')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initGdd(self, model_name, lo_gdd_th, hi_gdd_th):
        # make sure GDD group exists for the model/low/high threshold combination
        if not self.hasModelGroup(model_name, lo_gdd_th, hi_gdd_th, 'gdd'):
            self._initGddGroup(model_name, lo_gdd_th, hi_gdd_th)
        else: self._initGddDatasets(model_name, lo_gdd_th, hi_gdd_th)

    def initKill(self, model_name, lo_gdd_th, hi_gdd_th):
        # make sure GDD group exists for the model/low/high threshold combination
        if not self.hasModelGroup(model_name, lo_gdd_th, hi_gdd_th, 'kill'):
            self._initKillGroup(model_name, lo_gdd_th, hi_gdd_th)
        else: self._initKillDatasets(model_name, lo_gdd_th, hi_gdd_th)

    def initStage(self, model_name, lo_gdd_th, hi_gdd_th):
        # make sure GDD group exists for the model/low/high threshold combination
        if not \
        self.hasModelGroup(model_name, lo_gdd_th, hi_gdd_th, 'stage'):
            self._initStageGroup(model_name, lo_gdd_th, hi_gdd_th)
        else: self._initStageDatasets(model_name, lo_gdd_th, hi_gdd_th)


    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # dataset initiailzation methods                                        #
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initModelGroup(self, model_name, verbose=False):
        group_name = self.modelGroupName(model_name)
        if group_name not in self._group_names:
            print 'creating', group_name, 'group'
            attributes = { 'chill_model' : self.modelName(model_name),
                           'start_date' : asAcisQueryDate(self.start_date),
                           'end_date' : asAcisQueryDate(self.end_date),
                           'description' : chillModelDescription(model_name),
                         }
            self.open('a')
            self.createGroup(self.modelGroupName(model_name), **attributes)
            self.close()
            self._registerModel(model_name)

    def _initThresholdGroup(self, model_name, lo_gdd_th, hi_gdd_th,
                                  verbose=False):
        # make sure that the model group exists
        self._initModelGroup(model_name)

        full_path = self.thresholdGroupPath(model_name, lo_gdd_th, hi_gdd_th)
        if full_path not in self._group_names:
            print 'creating', full_path, 'group'
            gdd_thresholds = '%dF =< AVGT <= %dF' % (lo_gdd_th, hi_gdd_th)
            description = 'Datasets where GDD is based on %s' % gdd_thresholds
            self.open('a')
            self.createGroup(full_path)
            self.close()
            self.open('a')
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description)
            self.close()

    def _initThresholdDatasets(self, model_name, lo_gdd_th, hi_gdd_th,
                                     verbose=False):
        # make sure that a group exists for this model/low/high combination
        if not self.hasThreshold(model_name, lo_gdd_th, hi_gdd_th):
            self._initThresholdGroup( model_name, lo_gdd_th, hi_gdd_th, verbose)

        # build the GDD group and datasets
        self._initGddGroup(model_name, lo_gdd_th, hi_gdd_th, verbose)

        # build the STAGE group and datasets
        self._initStageGroup(model_name, lo_gdd_th, hi_gdd_th, verbose)

        # build the KILL group and datasets
        self._initKillGroup(model_name, lo_gdd_th, hi_gdd_th, verbose)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initGddDatasets(self, model_name, lo_gdd_th, hi_gdd_th, verbose=False):
        """ Create the GDD datasets for model/thresholds combination
        only if they don't already exist.
        """
        num_days = (self.end_date - self.start_date).days + 1
        shape = (num_days,) + self.lons.shape
        chunks = (1,) + self.lons.shape

        # minimum chill unit threshold for variety/model combination
        path = 'crops.apple.chill.%s.accumulation_factor' % model_name
        min_chill_units = int(self.min_chill_units * fromConfig(path))

        # create the daily GDD accumulation dataset
        full_path = self.modelDatasetPath(model_name, lo_gdd_th, hi_gdd_th,
                                          'gdd', 'accumulated')
        if full_path not in self._dataset_names:
            print 'creating', full_path, 'dataset'
            data = N.full(shape, -32768, '<i2')
            self.open('a')
            self.createDataset(full_path, data, chunks=chunks,
                               compression='gzip')
            self.close()
            self.open('a')
            description = 'GDD accumulated since minimum chill units were accumulated'
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description, units='GDD',
                                    min_chill_units=min_chill_units)
            self.close()

        # create related chill mask
        full_path = full_path.replace('accumulated', 'chill_mask')
        if full_path not in self._dataset_names:
            print 'creating', full_path, 'dataset'
            description = 'Boolean grid where True = minimum chill units were accumulated.'

            self.open('a')
            self.createDataset(full_path, N.zeros(shape, dtype=bool),
                               chunks=chunks, compression='gzip')
            self.close()
            self.open('a')
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                   description=description,
                                   min_chill_units=min_chill_units)
            self.close()

        # create related provenance dataset
        full_path = full_path.replace('chill_mask', 'provenance')
        if full_path not in self._dataset_names:
            print 'creating', full_path, 'dataset'
            description = 'Daily GDD Processing Provenance'
            self.open('a')
            self._createEmptyProvenance(full_path, 'stats', verbose)
            self.close()
            self.open('a')
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description)
            self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initGddGroup(self, model_name, lo_gdd_th, hi_gdd_th, verbose=False):
        # if necessary, add a group for the model/low/high combination
        if not self.hasThreshold(model_name, lo_gdd_th, hi_gdd_th):
            self._initThresholdGroup(model_name, lo_gdd_th, hi_gdd_th)

        # make sure GDD group exists within the model/low/high group 
        full_path = self.modelGroupPath(model_name,lo_gdd_th,hi_gdd_th,'gdd')
        if full_path not in self._group_names:
            print 'creating', full_path, 'group'
            description = 'Accumlated GDD datasets'
            self.open('a')
            self.createGroup(full_path)
            self.close()
            self.open('a')
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description)
            self.close()

        # create the gdd datasets if they don't already exist
        self._initGddDatasets(model_name, lo_gdd_th, hi_gdd_th, verbose)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initKillDatasets(self, model_name, lo_gdd_th, hi_gdd_th,
                                verbose=False):
        num_days = (self.end_date - self.start_date).days + 1
        chunks = (1,) + self.lons.shape
        shape = (num_days,) + self.lons.shape
     
        # create the kill level dataset
        full_path = \
        self.modelDatasetPath(model_name, lo_gdd_th,hi_gdd_th, 'kill','level')
        if full_path not in self._dataset_names:
            print 'creating', full_path, 'dataset'
            description = 'Daily potential kill level'
            levels = { 'Level 0' : 'No kill potential', }
            for level, percent in enumerate(self.variety.kill_levels, start=1):
                key = 'Level %d' % level
                levels[key] = 'Potential for %d%% kill' % percent

            data = N.full(shape, -32768, '<i2')
            self.open('a')
            self.createDataset(full_path, data, chunks=chunks, 
                               compression='gzip')
            self.close()
            self.open('a')
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description)
            self.setDatasetAttributes(full_path, **levels)
            self.close()

        # create the kill provenance dataset
        full_path = full_path.replace('level', 'provenance')
        if full_path not in self._dataset_names:
            print 'creating', full_path, 'dataset'
            description = 'Kill processing provenance'
            self.open('a')
            self._createEmptyProvenance(full_path, 'kill', verbose)
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description)
            self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initKillGroup(self, model_name, lo_gdd_th, hi_gdd_th, verbose=False):
        # if necessary, add a group for the model/low/high combination
        if not self.hasThreshold(model_name, lo_gdd_th, hi_gdd_th):
            self._initThresholdGroup(model_name, lo_gdd_th, hi_gdd_th, verbose)

        # make sure kill group exists within the model/low/high group 
        full_path = self.modelGroupPath(model_name,lo_gdd_th,hi_gdd_th,'kill')
        if full_path not in self._group_names:
            if verbose: print 'creating', full_path
            description = 'Kill level datasets'

            self.open('a')
            self.createGroup(full_path, description=description)
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description)
            self.close()

        # make the kill datasets if they don't already exist
        self._initKillDatasets(model_name, lo_gdd_th, hi_gdd_th, verbose)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _initStageDatasets(self, model_name, lo_gdd_th, hi_gdd_th,
                                 verbose=False):
        chunks = (1,) + self.lons.shape
        num_days = (self.end_date - self.start_date).days + 1
        shape = (num_days,) + self.lons.shape

        # create the stage index dataset
        full_path =\
        self.modelDatasetPath(model_name, lo_gdd_th,hi_gdd_th, 'stage','index')
        if full_path not in self._dataset_names:
            print 'creating', full_path, 'dataset'
            description = 'Daily growth stage index'
            stages = { }
            stage_name_map =\
            fromConfig('crops.apple.variety.stage_name_map.attrs')
            for stage, stage_name in enumerate(stage_name_map.values()):
                stages['Stage %d' % stage] = stage_name

            data = N.full(shape, -32768, '<i2')
            self.open('a')
            self.createDataset(full_path, data, chunks=chunks,
                               compression='gzip')
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description)
            self.setDatasetAttributes(full_path, **stages)
            self.close()

        # create the stage provenance dataset
        full_path = full_path.replace('index', 'provenance')
        if full_path not in self._dataset_names:
            print 'creating', full_path, 'dataset'
            description = 'Stage index processing provenance'
            self.open('a')
            self._createEmptyProvenance(full_path, 'stage', verbose)
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th,
                                    hi_gdd_th, description=description)
            self.close()

    def _initStageGroup(self, model_name, lo_gdd_th, hi_gdd_th, verbose=False):
        # if necessary, add a group for the model/low/high combination
        if not self.hasThreshold(model_name, lo_gdd_th, hi_gdd_th):
            self._initThresholdGroup(model_name, lo_gdd_th, hi_gdd_th, verbose)

        # make sure kill group exists within the model/low/high group
        full_path = self.modelGroupPath(model_name,lo_gdd_th,hi_gdd_th,'stage')
        if full_path not in self._group_names:
            print 'creating', full_path, 'group'
            description = 'Growth stage datasets'
            self.open('a')
            self.createGroup(full_path, description=description)
            self._setThresholdAttrs(full_path, model_name, lo_gdd_th, hi_gdd_th,
                                    description=description)
            self.close()

        # make the stage datasets if they don't already exist
        self._initStageDatasets(model_name, lo_gdd_th, hi_gdd_th, verbose)

