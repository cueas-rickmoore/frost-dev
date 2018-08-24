
from frost.functions import fromConfig
from frost.grid import FrostGridFileReader, FrostGridFileManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleGridFileMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Chill model and GDD threshold methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hasModel(self, model_name):
        return self.modelGroupName(model_name) in self.file_chill_models

    def modelName(self, model_name):
        return self.properName(model_name).replace(' ','_')
    modelGroupName = modelName

    def thresholdName(self, low_threshold, high_threshold):
        return 'L%dH%d' % (low_threshold, high_threshold)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _modelsInFile(self):
        return [ name for name in self._group_names
                      if name.lower() in self.apple_chill_models ]

    def _registerModel(self, model_name):
        self.file_chill_models.append(self.properName(model_name))

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadAppleFileAttributes_(self):
        self.apple_chill_models = fromConfig('crops.apple.chill.models')
        self.file_chill_models = self._modelsInFile()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleGridFileReader(FrostGridFileReader, AppleGridFileMixin):

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        """ Creates instance attributes specific to the content of the file
        to be managed.
        """
        # get superclass manager attributes
        FrostGridFileReader._loadManagerAttributes_(self)
        self._loadAppleFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleGridFileManager(FrostGridFileManager, AppleGridFileMixin):

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        """ Creates instance attributes specific to the content of the file
        to be managed.
        """
        # get superclass manager attributes
        FrostGridFileManager._loadManagerAttributes_(self)
        self._loadAppleFileAttributes_()

