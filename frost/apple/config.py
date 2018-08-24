
from collections import OrderedDict
from datetime import datetime

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PROVENANCE_RECORD_TYPE = ( ('obs_date', '|S10'), ('processed', '|S20'), )
GDD_PROVENANCE_STATS = ( ('min','<i2'), ('max','<i2'), ('avg', '<i2') )

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

APPLE = ConfigObject('apple', None, 'animation.start')

APPLE.end_day = (6,30)
APPLE.start_day = (9,1)

APPLE.gdd_thresholds = ((43,86),)
APPLE.gdd_provenance_empty = ('', '', -32768, -32768, -32768)
APPLE.gdd_provenance_type = PROVENANCE_RECORD_TYPE + GDD_PROVENANCE_STATS

APPLE.animation.start.chill = (9,15)
APPLE.animation.start.gdd = (2,1)
APPLE.animation.start.stage = (2,1)
APPLE.animation.start.kill = (2,1)

from frost.apple.chill.config import CHILL
APPLE.addChild(CHILL)

from frost.apple.variety.config import VARIETY, VARIETIES
APPLE.addChild(VARIETY)
APPLE.addChild(VARIETIES)

