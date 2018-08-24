#!/Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from frost.functions import fromConfig
from frost.apple.chill.grid import AppleChillGridRepair

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def repairModelDataset(manager, model, dataset_name):
    dataset_path = '%s.%s' % (model.title(), dataset_name)
    old_attrs = manager.getDatasetAttributes(dataset_path)
    if 'acis_grid' in old_attrs: del old_attrs['acis_grid']
    if 'missing' in old_attrs: del old_attrs['missing']
    if 'node_spacing' in old_attrs: del old_attrs['node_spacing']
    if 'units' in old_attrs: del old_attrs['units']
    new_attrs = \
    manager._resolveChillDatasetAttributes_(model, dataset_name, **old_attrs)
    new_attrs['description'] = old_attrs['description']
    if 'updated' in old_attrs: new_attrs['updated'] = old_attrs['updated']
    manager.setDatasetAttributes(dataset_path, **new_attrs)

def repairModel(manager, model):
    repairModelDataset(manager, model, 'daily')
    repairModelDataset(manager, model, 'accumulated')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-c', action='store_false', dest='carolina', default=True)
parser.add_option('-g', action='store_false', dest='gdd', default=True)
parser.add_option('-u', action='store_false', dest='utah', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

repair_carolina = options.carolina
repair_gdd = options.gdd
repair_utah = options.utah
test_file = options.test_file
verbose = options.verbose

target_year = int(args[0])

default = fromConfig('default')

manager = AppleChillGridRepair(target_year, 'a')

if repair_carolina:
    repairModel(manager, 'carolina')
    manager.close()
if repair_utah:
    manager.open(mode='a')
    repairModel(manager, 'utah')
    manager.close()
if repair_gdd:
    manager.open(mode='a')
    old_attrs = manager.getDatasetAttributes('gdd.L45H86.daily')
    if 'acis_grid' in old_attrs:
        manager.deleteDatasetAttribute('gdd.L45H86.daily', 'acis_grid')
    manager.close()
    manager.open(mode='a')
    manager.setDatasetAttribute('gdd.L45H86.daily', 'node_spacing',
                                fromConfig('default.node_spacing'))

manager.close()

