
import os

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.functions import animationDir, cropWorkingDir, fromConfig
from frost.functions import nameToFilepath, targetYearFromDate
from frost.functions import varietyName, varietyWorkingDir, webAppsDir

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DEFAULT_FILE_CHUNK = 16*1024

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def animationFilename(target_year, variety, model_name, map_group, map_type,
                      lo_gdd_th=None, hi_gdd_th=None, test_path=False):
    params = { 'model' : nameToFilepath(model_name), }

    if isinstance(target_year, basestring): params['date_str'] = target_year
    else: params['date_str'] = str(target_year)

    if variety is not None:
        template = fromConfig('crops.apple.filenames.animation.variety')
        params['variety'] = nameToFilepath(varietyName(variety))
    else:
        template = fromConfig('crops.apple.filenames.animation.%s' % map_group)

    if map_type == 'gdd': params['map_type'] = 'GDD'
    else: params['map_type'] = nameToFilepath(map_type)

    return template % params

def animationFilepath(target_year, variety, model_name, map_group, map_type,
                      lo_gdd_th=None, hi_gdd_th=None, test_path=False):
    anim_dir = animationDir(target_year, 'apple', variety, test_path)
    filename = animationFilename(target_year, variety, model_name, map_group,
                                 map_type, lo_gdd_th, hi_gdd_th, test_path)
    return os.path.join(anim_dir, filename)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def chillWorkingDir(target_year, test_dir=False):
    crop_dir = cropWorkingDir(target_year, 'apple', test_dir)
    chill_dir = os.path.join(crop_dir, 'chill')
    if not os.path.exists(chill_dir): os.makedirs(chill_dir)
    return chill_dir

def chillFilepath(target_year, test_path=False):
    chill_dir = chillWorkingDir(target_year, test_path)
    template = fromConfig('crops.apple.filenames.data.chill')
    filename = template % int(target_year)
    return os.path.join(chill_dir, filename)

def chillModelDescription(model_name):
    return fromConfig('crops.apple.chill.%s.description' % model_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def gddThresholdName(lo_gdd_th, hi_gdd_th):
    return 'L%dH%d' % (lo_gdd_th, hi_gdd_th)

def getAppleVariety(variety_name):
    return fromConfig('crops.apple.varieties.%s' % variety_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def mapFilename(date, variety, model_name, map_group, map_type,
                lo_gdd_th=None, hi_gdd_th=None, test_path=False):
    params = { 'model' : nameToFilepath(model_name), }

    if isinstance(date, basestring): params['date_str'] = date
    else: params['date_str'] = asAcisQueryDate(date)

    if variety is not None:
        template = fromConfig('crops.apple.filenames.maps.variety')
        params['variety'] = nameToFilepath(varietyName(variety))
    else:
        template = fromConfig('crops.apple.filenames.maps.%s' % map_group)

    if map_type == 'gdd': params['map_type'] = 'GDD'
    else: params['map_type'] = nameToFilepath(map_type)

    if lo_gdd_th is not None:
        params['thresholds'] = gddThresholdName(lo_gdd_th, hi_gdd_th)

    return template % params

def mapFilepath(date, variety, model_name, map_group, map_type,
                lo_gdd_th=None, hi_gdd_th=None, test_path=False):
    target_year = targetYearFromDate(asDatetime(date))
    map_dir = mapWorkingDir(target_year, variety, model_name, map_group,
                            map_type, lo_gdd_th, hi_gdd_th, test_path)
    filename = mapFilename(date, variety, model_name, map_group, map_type,
                           lo_gdd_th, hi_gdd_th, test_path)
    return os.path.join(map_dir, filename)

def mapWorkingDir(target_year, variety, model_name, map_group, map_type,
                  lo_gdd_th=None, hi_gdd_th=None, test_path=False):
    if variety is None: # used for chill maps, etc.
        working_dir = cropWorkingDir(target_year, 'apple', test_path)
        map_dir = os.path.join(working_dir, map_group, map_type, model_name)
    else:
        model_dir = modelWorkingDir(target_year, variety, model_name,
                                    test_path)
        if lo_gdd_th is not None:
            thresholds = gddThresholdName(lo_gdd_th, hi_gdd_th)
            model_dir = os.path.join(model_dir, thresholds)
        map_dir = os.path.join(model_dir, map_type)
    if not os.path.exists(map_dir): os.makedirs(map_dir)
    return map_dir

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def modelWorkingDir(target_year, variety, model_name, test_path=False):
    working_dir = varietyWorkingDir(target_year, 'apple', variety,
                                    test_path)
    model_dir = os.path.join(working_dir, model_name)
    if not os.path.exists(model_dir): os.makedirs(model_dir)
    return model_dir

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def plotWorkingDir(target_year, variety, model_name, plot_key,
                   test_path=False):
    model_dir = modelWorkingDir(target_year, variety, model_name,
                                test_path)
    plot_dir = os.path.join(working_dir, plot_key)
    if not os.path.exists(plot_dir): os.makedirs(plot_dir)
    return plot_dir

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def varietyFilepath(target_year, variety, test_path=False):
    variety_dir = varietyWorkingDir(target_year, 'apple', variety,
                                    test_path)
    template = fromConfig('crops.apple.filenames.data.variety')
    filename = \
    template % (int(target_year), nameToFilepath(varietyName(variety)))
    return os.path.join(variety_dir, filename)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def copyMapFileToWeb(src_filepath, date, variety, model_name, map_group,
                     map_type, config_key='web_maps', 
                     chunk_size=DEFAULT_FILE_CHUNK):
    dest_filepath = webMapFilepath(date, variety, model_name, map_group,
                                   map_type, config_key)
    src_file = open(src_filepath, 'rb') 
    dest_file = open(dest_filepath, 'wb')
    chunk = src_file.read(chunk_size)
    while chunk:
        dest_file.write(chunk)
        chunk = src_file.read(chunk_size)
    dest_file.close()
    src_file.close()
    return dest_filepath

def publishMapForWeb(date, variety, model_name, map_group, map_type,
                     chunk_size=DEFAULT_FILE_CHUNK):
    src_filepath = mapFilepath(date, variety, model_name, map_group, map_type)
    return copyMapFileToWeb(src_filepath, date, variety, model_name, map_group,
                            map_type, chunk_size)

def webMapFilename(date, variety, model_name, map_group, map_type,
                   config_key='web_maps'):
    params = { 'model' : nameToFilepath(model_name), }

    if isinstance(date, basestring): params['date_str'] = date
    else: params['date_str'] = asAcisQueryDate(date)

    if variety is not None:
        template = fromConfig('crops.apple.filenames.%s.variety' % config_key)
        params['variety'] = nameToFilepath(varietyName(variety))
    else:
        template = \
        fromConfig('crops.apple.filenames.%s.%s' % (config_key, map_group))
    params['map_type'] = nameToFilepath(map_type)
    return template % params

def webMapFilepath(date, variety, model_name, map_group, map_type,
                   config_key='web_maps'):
    target_year = targetYearFromDate(asDatetime(date))
    webmaps_dir = webMapsDir(target_year, variety)
    filename = \
    webMapFilename(date, variety, model_name, map_group, map_type, config_key)
    return os.path.join(webmaps_dir, filename)

def webMapsDir(target_year, variety):
    webmaps_dir = webAppsDir(target_year, 'apple')
    if variety is not None:
        webmaps_dir = os.path.join(webmaps_dir, varietyName(variety).lower())
    if not os.path.exists(webmaps_dir): os.makedirs(webmaps_dir)
    return webmaps_dir

