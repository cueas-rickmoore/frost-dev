
import numpy as N

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

datasets = ConfigObject('datasets', None)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# datasets contains configuration parameters that MUST be set for each dataset
#
# description : detailed description of dataset
# raw_data : used to specify how the raw data is stored
#            type : type of storage-specific 
#, units, missing , frequency, interval)
#            frequency : observation frequency (time span e.g.'hour','day',etc.)
#            interval : number of time spans per data value
# serial_type : used to specify output data transforms for extracting data from 
#               hdf5 files via getSerialData() of HDF5DataFileManager an it's
#               subclasses : expressed as tuple (dtype, units, missing values)
# tsvar_type : used for extracting data using UCAN interface:
#              expressed as tuple (dtype, missing, units, tsv name, tsv units)
#              generated data datasets do not have tsvar_type
# units : used expressed as tuple (hdf5 type, hdf5 units, script type, script units)
# value_type : used to convey character and limits of observed data values
#              expressed as tuple (data character, min reasonable value,
#                                  max reasonable value, data precision)
#              variability : continuos = data contains continuous decimal
#                                        values
#                            discrete = data contains whole integer numbers
#                            direction = data expresse angles from 0 to 360
#              precision : the number of decimal places to use when
#                          comparing values (use 0 for discrete types
#                          or to require integer directions)
#
# generated datasets have the following paramaters :
#
# dependencies : tuple of names of datasets used to generate data
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# precipitation (pcpn)
datasets.pcpn = { 'description' : 'Precipitation',
        'raw_data' : { 'type':'i2', 'units':'in*100', 'missing':-32768,
                       'frequency':'day', 'interval':1 },
        'serialized' : { 'type':float, 'units':'in', 'missing':N.inf },
        'value_type' : { 'variability':'continuous', 'min_valid':0,
                         'max_valid':26., 'precision':3},
        }

# temperature (temp)
# extremes from lowest ever in Midwest to highest ever in Death Valley
datasets.temp = {
        'description' : 'Temperature',
        'sensor'      : 'Temperature',
        'raw_type'    : ('i2', 'F*10', -32768, 'hour', 1),
        'serial_type' : (float, 'F', N.inf),
        'tsvar_type'  : (float, N.inf),
        'units'       : (int, 'F', float, 'degF'),
        'value_type'  : ('linear', -50., 130., 1),
        }

