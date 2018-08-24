
import os

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig
from frost.grid import FrostGridBuilderMixin

from frost.grape.grid import GrapeVarietyFileManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GrapeVarietyFileBuilder(FrostGridBuilderMixin, GrapeVarietyFileManager):

    def __init__(self, variety, start_date, end_date, lons, lats,
                       test_file=False, verbose=False, **kwargs):
        """ Create a new, fully configured HDF5 file for a data belonging to 
        a particular grape variety.
        """
        target_year = self._builder_preinit(start_date, end_date)
        GrapeVarietyFileManager.__init__(self, target_year, variety, 'w',
                                         test_file, **kwargs)
        self._builder_postinit(lons, lats, **kwargs)

        # initialize the model datasets
        self.initChillGroups(verbose)
        self.initGddGroup(verbose)
        self.initDormancyGroup(verbose)
        self.initAcclimationGroup(verbose)
        self.initDeacclimationGroup(verbose)
        self.initHardinessGroup(verbose)

        # leave the new instance open for appends
        self.open('a')

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #
    # group/dataset initialization methods
    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def initAcclimationGroup(self, verbose=False):
        """ Initialize acclimation group and datasets in a new file.

        WARNING : DO NOT USE IN AN FILE THAT ALREADY HAS THESE DATASETS !!!
                  IT WILL FAIL AND THE FILE MAY BECOME HOPELESSLY CORRUPTED.
        """
        rates = ( 'endo=%-4.2f' % self.variety.acclimation_rate.endo,
                  'eco=%-4.2f' % self.variety.acclimation_rate.eco )
        group = fromConfig('crops.grape.groups.acclimation')
        attrs = dict(group.datasets.factor.attributes)
        attrs['acclimation_rates'] = ', '.join(rates)
        self._initModelDatasets('acclimation', (('factor', attrs),),
                                group.description, verbose=verbose,
                                prov_key='stats')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initDeacclimationGroup(self, verbose=False):
        """ Initialize deacclimation group and datasets in a new file.

        WARNING : DO NOT USE IN AN FILE THAT ALREADY HAS THESE DATASETS !!!
                  IT WILL FAIL AND THE FILE MAY BECOME HOPELESSLY CORRUPTED.
        """
        rates = ( 'endo=%-4.2f' % self.variety.deacclimation_rate.endo,
                  'eco=%-4.2f' % self.variety.deacclimation_rate.eco )
        group = fromConfig('crops.grape.groups.deacclimation')
        attrs = dict(group.datasets.factor.attributes)
        attrs['deacclimation_rates'] = ', '.join(rates)
        self._initModelDatasets('deacclimation', (('factor', attrs),),
                                group.description, verbose=verbose,
                                prov_key='stats')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initChillGroups(self, verbose=False, chill_groups=None):
        """ Initialize chill groups and datasets in a new file.

        WARNING : DO NOT USE IN AN FILE THAT ALREADY HAS THESE DATASETS !!!
                  IT WILL FAIL AND THE FILE MAY BECOME HOPELESSLY CORRUPTED.
        """
        getThresholdString = fromConfig('crops.grape.chill.getThresholdString')

        if chill_groups is None:
            chill_groups = fromConfig('crops.grape.groups.chill')

        # create the chill master group
        if 'chill' not in self._group_names:
            if verbose: print 'creating chill group'
            description='Container for chill data groups'
            self.open('a')
            self.createGroup('chill', description=description)
            self.close()

        for chill_type in chill_groups.children:
            datasets = [ ]
            th_key, th_value = getThresholdString(chill_type.name, self.variety)
            for dataset in chill_type.datasets.children:
                attrs = dict(dataset.attributes)
                attrs[th_key] = th_value
                datasets.append((dataset.name, attrs))
            group_name = self.chillGroupPath(chill_type.name)
            self._initModelDatasets(group_name, tuple(datasets),
                           chill_type.description, verbose=verbose,
                           prov_key='accum')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initDormancyGroup(self, verbose=False):
        """ Initialize dormancy stage group and datasets in a new file.

        WARNING : DO NOT USE IN AN FILE THAT ALREADY HAS THESE DATASETS !!!
                  IT WILL FAIL AND THE FILE MAY BECOME HOPELESSLY CORRUPTED.
        """
        group = fromConfig('crops.grape.groups.dormancy')
        attrs = dict(group.datasets.stage.attributes)
        self._initModelDatasets('dormancy', (('stage',attrs),),
                                group.description, verbose=verbose)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initGddGroup(self, verbose=False):
        """ Initialize growing degree days group and datasets in a new file.

        WARNING : DO NOT USE IN AN FILE THAT ALREADY HAS THESE DATASETS !!!
                  IT WILL FAIL AND THE FILE MAY BECOME HOPELESSLY CORRUPTED.
        """
        thresholds = ('endodormancy=%-4.2f' % self.stage_thresholds.endo,
                      'ecodormancy=%-4.2f' % self.stage_thresholds.eco)
        group = fromConfig('crops.grape.groups.gdd')

        datasets = [ ]
        for dataset in group.datasets.children:
            attrs = dict(dataset.attributes)
            attrs['gdd_threshold_temps'] = ', '.join(thresholds)
            datasets.append((dataset.name, attrs))

        self._initModelDatasets('gdd', tuple(datasets), group.description,
                                verbose=verbose, prov_key='accum')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initHardinessGroup(self, verbose=False):
        """ Initialize hardiness group and datasets in a new file.

        WARNING : DO NOT USE IN AN FILE THAT ALREADY HAS THESE DATASETS !!!
                  IT WILL FAIL AND THE FILE MAY BECOME HOPELESSLY CORRUPTED.
        """
        group = fromConfig('crops.grape.groups.hardiness')
        attrs = dict(group.datasets.temp.attributes)
        self._initModelDatasets('hardiness', (('temp',attrs),),
                                group.description, verbose=verbose, 
                                prov_key='stats')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initModelDatasets(self, group, datasets, group_description,
                                 verbose=False, **kwargs):
        """ Does the "heavy lifting" to initialize a group and it's datasets
        in a new file. Be careful, this method is primarily meant to be
        called by the group-sepcific methods above.

        WARNING : DO NOT USE IN AN FILE THAT ALREADY HAS THE GROUP OR
                  IT'SDATASETS !!! IT WILL FAIL AND THE FILE MAY BECOME
                  HOPELESSLY CORRUPTED.
        """
        default = fromConfig('default')
        num_days = (self.end_date - self.start_date).days + 1

        chunks = kwargs.get('chunks', (1,) + self.lons.shape)
        compression = kwargs.get('compression',default.compression)
        shape = kwargs.get('shape', (num_days,) + self.lons.shape)
        verbose = kwargs.get('verbose',False)

        # date attributes
        date_attrs = { 'start_date' : asAcisQueryDate(self.start_date),
                       'end_date' : asAcisQueryDate(self.end_date),
                     }

        # create the group
        if group not in self._group_names:
            if verbose: print 'creating', group
            self.open('a')
            self.createGroup(group, description=group_description)
            self.setGroupAttributes(group, **date_attrs)
            self.close()

        # create datasets
        for dataset_name, ds_attrs in datasets:
            #ds_attrs = dict(ds_attrs)
            full_dataset_path = self.modelDatasetPath(group, dataset_name)
            if full_dataset_path not in self._dataset_names:
                if verbose: print 'creating', full_dataset_path
                ds_attrs.update(date_attrs)
                if 'node_spacing' not in ds_attrs:
                    ds_attrs['node_spacing'] = '5 km'
                self.open('a')
                self.createEmptyDataset(full_dataset_path, shape,
                                ds_attrs['dtype'], ds_attrs['missing'],
                                chunks=chunks, compression=compression,
                                description=ds_attrs['description'])
                del ds_attrs['dtype'], ds_attrs['description']
                self.setDatasetAttributes(full_dataset_path, **ds_attrs)
                self.close()

        # create the chill provenance dataset
        prov_path = self.modelDatasetPath(group, 'provenance')
        if prov_path not in self._dataset_names:
            if verbose: print 'creating', prov_path
            prov_key = kwargs.get('prov_key', group)
            prov_description = kwargs.get('prov_description',None)
            if prov_description is None:
                prov_description = \
                    '%s processing provenance' % group_description.lower()

            self.open('a')
            self._createEmptyProvenance(prov_path, prov_key, prov_description,
                                        verbose)
            self.close()

