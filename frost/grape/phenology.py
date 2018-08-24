
from collections import OrderedDict

from atmosci.utils.config import ConfigObject, OrderedConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Phenology(OrderedConfigObject):

    def __init__(self, parent=None, cultivar=None, phenology=None):
        OrderedConfigObject.__init__(self, 'phenology', parent)

        self.__dict__['cultivar'] = cultivar
        if phenology is not None:
            for _key, _value in phenology.items():
                self.__dict__['__ATTRIBUTES__'][_key] = _value

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def copy(self, new_name=None, parent=None):
        if new_name is None: name = self.name
        else: name = new_name
        _copy = Phenology(parent, self.cultivar, None)
        _copy = self._complete_copy_(_copy)
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

class GrapeVariety(ConfigObject):

    def __init__(self, name, parent, description=None, cultivar=None,
                       phenology=None, hardiness=None, 
                       ecodormancy_threshold=None, acclimation_rate=None,
                       deacclimation_rate=None, stage_thresholds=None,
                       theta=None):

        ConfigObject.__init__(self, name, parent)
        self.__dict__['proper_name'] = description

        if description is not None:
            self.set(description=description)
        if phenology is not None:
            self.set(phenology=Phenology(self, cultivar, phenology))
        if ecodormancy_threshold is not None:
            self.set(ecodormancy_threshold=ecodormancy_threshold)
        if hardiness is not None:
            self.set(hardiness=hardiness)
        if acclimation_rate is not None:
            self.set(acclimation_rate=acclimation_rate)
        if deacclimation_rate is not None:
            self.set(deacclimation_rate=deacclimation_rate)
        if stage_thresholds is not None:
            self.set(stage_thresholds=stage_thresholds)
        if theta is not None:
            self.set(theta=theta)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def copy(self, new_name=None, parent=None):
        if new_name is None: name = self.name
        else: name = new_name
        _copy = self._complete_copy_(GrapeVariety(name, None))
        if parent is not None: # copying entire config tree
            parent.addChild(_copy)
        return _copy

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _proper_name_(self, name):
        return name

