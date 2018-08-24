import os

from setuptools import setup, find_packages
from distutils.extension import Extension
import numpy

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

BUILD_DIR = os.path.dirname(__file__)

def getVersion():
    return open(os.path.join(BUILD_DIR,'frost','version.txt')).read().strip()

def read(*filepath):
    return open(os.path.join(BUILD_DIR, *filepath)).read()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PKG_PATH = os.path.normpath(os.getcwd())
PACKAGES = find_packages(exclude=('*._archive', '*._Archive',))
DATA_PACKAGES = [ 'scripts',
                  os.path.join('apple','scripts'),
                  os.path.join('grape','scripts'),
                ]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # "

dist = setup(name='frost', version=getVersion(),
             description='Frost Damage Eatimation',
             author='Rick Moore',
             packages=PACKAGES,
             package_data={ 'nrcc' : DATA_PACKAGES },
           )

