#!/Users/rem63/venvs/frost/bin/python

from frost.functions import fromConfig
from frost.apple.functions import chillModelDescription, getAppleVariety
from frost.apple.variety.grid import AppleVarietyGridRepair

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DEFAULTS = fromConfig('default')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def repairGroup(manager, group_path, chill_model):
    old_attrs = manager.getGroupAttributes(group_path)
    if 'high_GDD_threshold' in old_attrs:
        manager.deleteGroupAttribute(group_path, 'high_GDD_threshold')
    if 'hi_GDD_threshold' in old_attrs:
        manager.deleteGroupAttribute(group_path, 'hi_GDD_threshold')
    if 'low_GDD_threshold' in old_attrs:
        manager.deleteGroupAttribute(group_path, 'low_GDD_threshold')
    if 'lo_GDD_threshold' in old_attrs:
        manager.deleteGroupAttribute(group_path, 'lo_GDD_threshold')
    manager.setGroupAttributes(group_path, lo_gdd_threshold=45,
                               hi_gdd_threshold=86, chill_model=chill_model)

def repairModelDataset(manager, group_path, dataset, chill_model, missing=None):
    dataset_path = '%s.%s' % (group_path, dataset)
    old_attrs = manager.getDatasetAttributes(dataset_path)
    if 'high_GDD_threshold' in old_attrs:
        manager.deleteDatasetAttribute(dataset_path, 'high_GDD_threshold')
    if 'hi_GDD_threshold' in old_attrs:
        manager.deleteDatasetAttribute(dataset_path, 'hi_GDD_threshold')
    if 'low_GDD_threshold' in old_attrs:
        manager.deleteDatasetAttribute(dataset_path, 'low_GDD_threshold')
    if 'lo_GDD_threshold' in old_attrs:
        manager.deleteDatasetAttribute(dataset_path, 'lo_GDD_threshold')
    if 'acis_grid' in old_attrs:
        manager.deleteDatasetAttribute(dataset_path, 'acis_grid')
    if 'source' in old_attrs:
        manager.deleteDatasetAttribute(dataset_path, 'source')

    attrs = { 'chill_model' : chill_model, }
    if missing is not None: attrs['missing'] = missing
    attrs['hi_gdd_threshold'] = 86
    attrs['lo_gdd_threshold'] = 45
    if not dataset_path.endswith('.provenance'):
        attrs['grid_type'] = DEFAULTS.grid_type
        attrs['node_spacing'] = DEFAULTS.node_spacing
    manager.setDatasetAttributes(dataset_path, **attrs)

def repairModel(manager, model, options):
    _model = model.title()
    thresh_group = '%s.L45H86' % _model
    chill_model = chillModelDescription(model)
    repairGroup(manager, thresh_group, chill_model)

    if options.gdd:
        group_path = '%s.gdd' % thresh_group 
        repairGroup(manager, group_path, chill_model)
        repairModelDataset(manager, group_path, 'accumulated', chill_model,
                           missing=-32768)
        repairModelDataset(manager, group_path, 'chill_mask', chill_model)
        repairModelDataset(manager, group_path, 'provenance', chill_model)

    if options.kill:
        group_path = '%s.kill' % thresh_group 
        repairGroup(manager, group_path, chill_model)
        repairModelDataset(manager, group_path, 'level', chill_model,
                           missing=-999)
        repairModelDataset(manager, group_path, 'provenance', chill_model)

    if options.stage:
        group_path = '%s.stage' % thresh_group 
        repairGroup(manager, group_path, chill_model)
        repairModelDataset(manager, group_path, 'index', chill_model,
                           missing=-999)
        repairModelDataset(manager, group_path, 'provenance', chill_model)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-c', action='store_false', dest='carolina', default=True)
parser.add_option('-g', action='store_false', dest='gdd', default=True)
parser.add_option('-k', action='store_false', dest='kill', default=True)
parser.add_option('-s', action='store_false', dest='stage', default=True)
parser.add_option('-u', action='store_false', dest='utah', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='test_file', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

repair_carolina = options.carolina
repair_utah = options.utah
test_file = options.test_file
verbose = options.verbose

target_year = int(args[0])
variety = getAppleVariety(args[1])

manager = AppleVarietyGridRepair(target_year, variety, 'a')

if repair_carolina:
    repairModel(manager, 'carolina', options)
    manager.close()
if repair_utah:
    manager.open(mode='a')
    repairModel(manager, 'utah', options)
    manager.close()

attrs = { 'grid_type':DEFAULTS.grid_type,
          'node_spacing':DEFAULTS.node_spacing }
manager.open(mode='a')
manager.setDatasetAttributes('lat', **attrs)
manager.setDatasetAttributes('lon', **attrs)
manager.close()

