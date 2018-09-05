#! /Volumes/projects/venvs/frost/bin/python

from frost.factory import FrostGridFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = FrostGridFactory()

target_year = int(args[0])
dataset_path = args[1]
attribute = args[2]
new_value = args[3]

manager = factory.getTempGridManager(target_year, 'a')
manager.setDatasetAttribute(dataset_path, attribute, new_value)
manager.close()

manager.open('r')
print dataset_path, attribute, manager.datasetAttribute(dataset_path, attribute)
manager.close()

