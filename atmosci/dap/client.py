
import os, sys
from httplib2 import FailedToDecompressContent

import pydap.client

import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BaseDapClient(object):

    def __init__(self, server_url):
        self.server_url = server_url

        self.connection = None
        self.connection = None
        self.dataset_names = ()
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataset(self, dataset_name):
        if self.hasDataset(dataset_name):
            return self.connection[dataset_name]
        else:
            errmsg ='DAP connection has no dataset named %s'
            return KeyError, errmsg % dataset_name

    def hasDataset(self, dataset_name):
        return dataset_name in self.dataset_names

    def listDatasets(self):
        return self.dataset_names

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def connect(self, target=None):
        self._connect(self._genConnectionUrl(target))

    def closeConnection(self):
        self.connection = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _connect(self, connection_url):
        if self.connection_url != connection_url:
            self.closeConnection()
            self.connection = pydap.client.open_url(connection_url)
            self.connection_url = connection_url
            keys = list(self.connection.keys())
            leys.sort()
            self.dataset_names = tuple(keys)

    def _genConnectionUrl(self, target=None):
        if target is not None:
            if target[0] == '/': return self.server_url + target
            else: return '%s/%s' % (self.server_url, target)
        else: self.server_url

