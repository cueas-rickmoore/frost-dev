
ACCUMULATORS = { }

from frost.chill.dynamic.array import register
register(ACCUMULATORS)

from frost.chill.dynamic.grid import register
register(ACCUMULATORS)

from frost.chill.dynamic.point import register
register(ACCUMULATORS)

def register(registry):
    registry['dynamic'] = ACCUMULATORS
