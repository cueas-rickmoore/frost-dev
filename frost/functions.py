
import os

from copy import deepcopy
from collections import OrderedDict
from datetime import date as datetime_date
from datetime import datetime as datetime_time

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from frost.config import CONFIG
CONFIG_OBJECT_CLASS = CONFIG.__class__

DOUBLE_SEPARATOR = '%s.%s' % (os.sep,os.sep)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def fromConfig(config_object_path):
    try:
        obj = eval('CONFIG.%s' % config_object_path)
    except KeyError as e:
        errmsg = 'full path = "%s"' % config_object_path
        e.args += (errmsg,)
        raise e
    return obj

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def nameToDirpath(name):
    _name = name.replace('_',' ').replace('-',' ').replace('.',' ')
    return os.path.normpath(_name.replace(' ',os.sep))

def nameToFilepath(name):
    _name = name.replace('.',' ').replace('_',' ')
    _name = _name.replace('(','').replace(')','')
    return _name.title().replace(' ','-').replace('--','-')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def seasonDate(target_year, month, day):
    if month < 7: return datetime_time(target_year, month, day)
    else: return datetime_time(target_year-1, month, day)

def targetDateSpan(date_or_year, crop=None, variety=None):
    if crop is not None:
        path = 'crops.%s' % crop 
        if variety is not None:
            path ='%s.variety.%s' % (path, varietyName(variety))
        config = fromConfig(path)
    else: config = fromConfig('default')
    if isinstance(date_or_year, (datetime_date, datetime_time)):
        target_year = _targetYearFromDate(date, config)
    else: target_year = date_or_year
    start_date = (target_year-1,) + config.start_day
    start_date = datetime_time(*start_date)
    end_date = (target_year,) + config.end_day
    end_date = datetime_time(*end_date)
    return start_date, end_date

def targetYearFromDate(date, crop=None, variety=None):
    if crop is not None:
        path = 'crops.%s' % crop 
        if variety is not None:
            path ='%s.variety.%s' % (path, varietyName(variety))
        config = fromConfig(path)
    else: config = fromConfig('default')
    return _targetYearFromDate(date, config)

def _targetYearFromDate(date, config):
    start_month = config.start_day[0]
    if date.month < start_month: return date.year
    elif date.month == start_month:
        if date.day < config.start_day[1]: return date.year
        else: return date.year + 1
    else: return date.year + 1

def timestamp(as_file_path=False):
    if as_file_path: return datetime_time.now().strftime('%Y%m%d-%H%M%S')
    else: return datetime_time.now().strftime('%Y-%m-%d %H:%M:%S')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def varietyName(variety):
    if isinstance(variety, CONFIG_OBJECT_CLASS): return variety.name
    elif isinstance(variety, basestring): return variety
    elif isinstance(variety, dict): return variety['name']
    else:
        raise TypeError, 'Unsupported type for "variety" argument.'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def buildLogDir(target_year, crop):
    log_dir = os.path.join(cropWorkingDir(target_year, crop, False), 'logs')
    if not os.path.exists(log_dir): os.makedirs(log_dir)
    return log_dir

def buildLogFilepath(target_year, crop, filename_template, pid=None):
    if pid is not None:
        key = '%s-%s' % (datetime_time.now().strftime('%Y-%m-%d'), str(pid))
    else: key = timestamp().replace(' ','-').replace(':','')
    log_filename = filename_template % key
    return os.path.join(buildLogDir(target_year, crop), log_filename)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def tempGridFilepath(target_year, test_dir=False):
    return os.path.join(tempWorkingDir(target_year, test_dir),
                        '%d_temperatures.h5' % target_year)

def tempPlotDir(target_year, temp_group, temp_type, plot_type, test_dir=False):
    temp_dir = os.path.join(gridWorkingDir(target_year, test_dir), 'temp')
    plot_dir = os.path.join(temp_dir, temp_group, temp_type, plot_type)
    if not os.path.exists(plot_dir): os.makedirs(plot_dir)
    return plot_dir

def tempWorkingDir(target_year, test_dir=False):
    temp_dir = os.path.join(gridWorkingDir(target_year, test_dir), 'temp')
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    return temp_dir

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def tempGridReader(target_year_or_date, test_file=False):
    from frost.temperature import FrostTempFileReader
    if isinstance(target_year_or_date, datetime_time):
        target_year = targetYearFromDate(target_year_or_date)
    else: target_year = target_year_or_date
    if test_file:
        filepath = tempGridFilePath(target_year, test_file)
        return FrostTempFileReader(target_year, filepath=filepath)
    else: return FrostTempFileReader(target_year)

def tempGridManager(target_year_or_date, mode='r', test_file=False):
    from frost.temperature import FrostTempFileManager
    if isinstance(target_year_or_date, datetime_time):
        target_year = targetYearFromDate(target_year_or_date)
    else: target_year = target_year_or_date
    if test_file:
        filepath = tTempGridFilePath(target_year, test_file)
        return FrostTempFileManager(target_year, mode, filepath=filepath)
    else: return FrostTempFileManager(target_year, mode)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def animationDir(target_year, crop, variety, test_dir=False):
    crop_dir = cropWorkingDir(target_year, crop, test_dir)
    animation_dir = os.path.join(crop_dir, 'animations')
    if not os.path.exists(animation_dir): os.makedirs(animation_dir)
    return animation_dir

def cropWorkingDir(target_year, crop, test_dir=False):
    crop_dir = os.path.join(gridWorkingDir(target_year), crop)
    if not os.path.exists(crop_dir): os.makedirs(crop_dir)
    return crop_dir

def gridWorkingDir(target_year, test_dir=False):
    working_dir = CONFIG.working_dir
    if test_dir: 
        working_dir = os.path.join(working_dir, 'test', str(target_year))
    else: working_dir = os.path.join(working_dir, 'grid', str(target_year))
    if not os.path.exists(working_dir): os.makedirs(working_dir)
    return working_dir

def varietyWorkingDir(target_year, crop, variety, test_dir=False):
    crop_dir = cropWorkingDir(target_year, crop, test_dir)
    variety_dir = os.path.join(crop_dir, varietyName(variety).lower())
    if not os.path.exists(variety_dir): os.makedirs(variety_dir)
    return variety_dir

def webAppsDir(target_year, crop):
    webapps_dir = os.path.join(CONFIG.webapps_dir, crop)
    if not os.path.exists(webapps_dir): os.makedirs(webapps_dir)
    return webapps_dir

