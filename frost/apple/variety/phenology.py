
from collections import OrderedDict

from atmosci.utils.config import ConfigObject, OrderedConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Phenology(OrderedConfigObject):

    def __init__(self, parent=None, phenology=None):
        OrderedConfigObject.__init__(self, 'phenology', parent)

        if phenology is not None:
            for _key, _value in phenology.items():
                self.__dict__['__ATTRIBUTES__'][_key] = _value

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def copy(self, new_name=None, parent=None):
        if new_name is None: name = self.name
        else: name = new_name
        _copy = self._complete_copy_(Phenology())
        if parent is not None: # copying entire config tree
            parent.addChild(_copy)
        return _copy

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _stages_(self):
        return tuple(self.__dict__['__ATTRIBUTES__'].keys())
    stages = property(_stages_)

    def _stage_thresholds_(self):
        return tuple(self.__dict__['__ATTRIBUTES__'].values())
    stage_thresholds = property(_stage_thresholds_)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __len__(self):
        return len(self.stages)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleVariety(ConfigObject):

    def __init__(self, name, parent=None, phenology=None, kill_temps=None,
                       kill_levels=None, stage_name_map=None,
                       min_chill_units=None, description=None):
        ConfigObject.__init__(self, name, parent)

        if phenology is not None:
            self.set(phenology=Phenology(self, phenology))
        if kill_temps is not None:
            self.set(kill_temps=OrderedDict(kill_temps))
        if kill_levels is not None:
            self.set(kill_levels=kill_levels)
        if stage_name_map is not None:
            self.set(stage_name_map=OrderedDict(stage_name_map))
        if min_chill_units is not None:
            self.set(min_chill_units=min_chill_units)
        if description is not None:
            self.set(description=description)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def copy(self, new_name=None, parent=None):
        if new_name is None: name = self.name
        else: name = new_name
        _copy = self._complete_copy_(AppleVariety(name, None))
        if parent is not None: # copying entire config tree
            parent.addChild(_copy)
        return _copy

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _proper_name_(self, name):
        _name = name.replace('_', ' ').replace('(',' ').replace(')',' ')
        return _name.replace('  ', ' ').title()

    def _stages_(self):
        return self.phenology._stages_()
    stages = property(_stages_)

    def _stage_thresholds_(self):
        return self.phenology._stage_thresholds_()
    stage_thresholds = property(_stage_thresholds_)

