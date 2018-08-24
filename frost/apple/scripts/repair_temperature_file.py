#!/Users/rem63/venvs/frost/bin/python

import os, sys
import warnings

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from frost.functions import fromConfig
from frost.temperature import FrostTempFileRepair

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-f', action='store_true',  dest='forecast', default=True)
parser.add_option('-r', action='store_true',  dest='reported', default=True)
parser.add_option('-v', action='store_true',  dest='verbose', default=False)
parser.add_option('-z', action='store_true',  dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

fix_forecast = options.forecast
fix_reported = options.reported
test_file = options.test_file
verbose = options.verbose

target_year = int(args[0])

default = fromConfig('default')

manager = FrostTempFileRepair(target_year, 'a')

# observed temperature datasets
if fix_reported:
    old_attrs = manager.getDatasetAttributes('reported.maxt')
    if 'acis_grid' in old_attrs: del old_attrs['acis_grid']
    del old_attrs['units']
    del old_attrs['node_spacing']
    del old_attrs['missing']
    new_attrs = \
    manager._resolveTemperatureAttributes_('reported', **old_attrs)
    new_attrs['description'] = old_attrs['description']
    if 'updated' in old_attrs: new_attrs['updated'] = old_attrs['updated']
    manager.setDatasetAttributes('reported.maxt', **new_attrs)

    old_attrs = manager.getDatasetAttributes('reported.mint')
    if 'acis_grid' in old_attrs: del old_attrs['acis_grid']
    del old_attrs['units']
    del old_attrs['node_spacing']
    del old_attrs['missing']
    new_attrs = \
    manager._resolveTemperatureAttributes_('reported', **old_attrs)
    new_attrs['description'] = old_attrs['description']
    if 'updated' in old_attrs: new_attrs['updated'] = old_attrs['updated']
    manager.setDatasetAttributes('reported.mint', **new_attrs)

# update forecast datasets
if fix_forecast:
    old_attrs = manager.getDatasetAttributes('forecast.maxt')
    if 'acis_grid' in old_attrs: del old_attrs['acis_grid']
    del old_attrs['units']
    del old_attrs['node_spacing']
    del old_attrs['missing']
    new_attrs = \
    manager._resolveTemperatureAttributes_('forecast', **old_attrs)
    new_attrs['description'] = old_attrs['description']
    if 'updated' in old_attrs: new_attrs['updated'] = old_attrs['updated']
    manager.setDatasetAttributes('forecast.maxt', **new_attrs)

    old_attrs = manager.getDatasetAttributes('forecast.mint')
    if 'acis_grid' in old_attrs: del old_attrs['acis_grid']
    del old_attrs['units']
    del old_attrs['node_spacing']
    del old_attrs['missing']
    new_attrs = \
    manager._resolveTemperatureAttributes_('forecast', **old_attrs)
    new_attrs['description'] = old_attrs['description']
    if 'updated' in old_attrs: new_attrs['updated'] = old_attrs['updated']
    manager.setDatasetAttributes('forecast.mint', **new_attrs)

manager.close()

