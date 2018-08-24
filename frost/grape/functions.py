
import os

from atmosci.utils.timeutils import asAcisQueryDate, asDatetime

from frost.functions import animationDir, cropWorkingDir, varietyWorkingDir
from frost.functions import nameToDirpath, nameToFilepath, varietyName
from frost.functions import fromConfig, targetYearFromDate, webAppsDir

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DEFAULT_FILE_CHUNK = 16*1024

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getGrapeVariety(variety_name):
    return fromConfig('crops.grape.varieties.%s' % variety_name)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def animationFilename(target_year, variety, map_key, test_path=False):
    params = { }
    params['variety'] = nameToFilepath(variety.description)
    params['anim_key'] = nameToFilepath(map_key)
    if isinstance(target_year, basestring): params['year'] = target_year
    else: params['year'] = str(target_year)
    template = fromConfig('crops.grape.filenames.anim.variety')
    return template % params

def animationFilepath(target_year, variety, map_key, test_path=False):
    anim_dir = \
    mapWorkingDir(target_year, variety, map_key.split('.')[0], test_path)
    #anim_dir = animationDir(target_year, 'grape', variety, test_path)
    filename = animationFilename(target_year, variety, map_key, test_path)
    return os.path.join(anim_dir, filename)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def mapFilename(date, variety, map_key, map_type=None, test_path=False):
    params = { 'variety' : nameToFilepath(variety.description), }
    if isinstance(date, basestring): params['date_str'] = date
    else: params['date_str'] = asAcisQueryDate(date)

    if map_type is None and '.' in map_key:
        map_group, map_type = map_key.split('.')
    else: map_group = map_key

    if map_type == 'gdd':
        params['map_key'] = '%s-GDD' % nameToFilepath(map_group)
    else:
        params['map_key'] = '%s-%s' % ( nameToFilepath(map_group),
                                        nameToFilepath(map_type) )
    template = fromConfig('crops.grape.filenames.maps.variety')

    return template % params

def mapFilepath(date, variety, map_key, map_type=None, test_path=False):
    map_dir = mapWorkingDir(date, variety, map_key, map_type, test_path)
    filename = mapFilename(date, variety, map_key, map_type, test_path)
    return os.path.join(map_dir, filename)

def mapWorkingDir(date, variety, map_key, map_type=None, test_path=False):
    if '.' in map_key: map_group = map_key.split('.')[0]
    else: map_group = map_key
    target_year = targetYearFromDate(asDatetime(date))
    variety_dir = varietyWorkingDir(target_year, 'grape', variety, test_path)
    working_dir =  os.path.join(variety_dir, 'maps', nameToDirpath(map_group))
    if not os.path.exists(working_dir): os.makedirs(working_dir)
    return working_dir

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def plotFilename(date, variety, plot_key, test_path=False):
    params = { 'variety' : nameToFilepath(variety.description),
               'plot_key' : plot_key }
    if isinstance(date, basestring): params['date_str'] = date
    else: params['date_str'] = asAcisQueryDate(date)
    return fromConfig('crops.grape.filenames.plots.variety') % params

def plotFilepath(date, variety, plot_group, plot_key, test_path=False):
    filename = plotFilename(date, variety, plot_key, test_path)
    working_dir = plotWorkingDir(date, variety, plot_group, test_path)
    return os.path.join(working_dir, filename)

def plotWorkingDir(date, variety, plot_group, test_path=False):
    target_year = targetYearFromDate(asDatetime(date))
    variety_dir = varietyWorkingDir(target_year, 'grape', variety, test_path)
    working_dir = os.path.join(variety_dir, 'plots', plot_group)
    if not os.path.exists(working_dir): os.makedirs(working_dir)
    return working_dir

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def varietyFilename(target_year, variety):
    template = fromConfig('crops.grape.filenames.data.variety')
    if isinstance(variety, basestring):
        return template % (int(target_year), nameToFilepath(variety))
    else: return template % (int(target_year), nameToFilepath(variety.name))

def varietyFilepath(target_year, variety, test_path=False):
    variety_dir = varietyWorkingDir(target_year, 'grape', variety, test_path)
    filename = varietyFilename(target_year, variety)
    return os.path.join(variety_dir, filename)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def copyGraphicsFile(src_filepath, dest_filepath,
                     chunk_size=DEFAULT_FILE_CHUNK):
    src_file = open(src_filepath, 'rb') 
    dest_file = open(dest_filepath, 'wb')
    chunk = src_file.read(chunk_size)
    while chunk:
        dest_file.write(chunk)
        chunk = src_file.read(chunk_size)
    dest_file.close()
    src_file.close()
    return dest_filepath

def publishWebGraphic(graphic_type, src_filepath, date, variety, graphic_key,
                      chunk_size=DEFAULT_FILE_CHUNK):
    ext = os.path.splitext(src_filepath)[1]
    if graphic_type == 'map':
        dest_filepath = \
        webGraphicFilepath(date, variety, graphic_key, ext, True)
    elif graphic_type == 'plot':
        dest_filepath = \
        webGraphicFilepath(date, variety, graphic_key, ext, False)
    elif graphic_type == 'anim':
        dest_filepath = \
        webGraphicFilepath(date, variety, graphic_key, ext, True)
    return copyGraphicsFile(src_filepath, dest_filepath, chunk_size)

def webGraphicFilename(date, variety, graphic_key, ext, parse_keywords=True):
    params = { 'variety': nameToFilepath(variety.description), 'ext': ext }
    if isinstance(date, basestring): params['date_str'] = date
    else: params['date_str'] = asAcisQueryDate(date)

    template = fromConfig('crops.grape.filenames.web_graphic.variety')
    if parse_keywords: params['keywords'] = nameToFilepath(graphic_key)
    else: params['keywords'] = graphic_key
    return template % params

def webGraphicFilepath(date, variety, graphic_key, ext, parse_keywords=True):
    target_year = targetYearFromDate(asDatetime(date))
    graphics_dir = webGraphicsDir(target_year, variety)
    filename = \
    webGraphicFilename(date, variety, graphic_key, ext, parse_keywords)
    return os.path.join(graphics_dir, filename)

def webGraphicsDir(target_year, variety):
    graphics_dir = os.path.join(webAppsDir(target_year, 'grape'),
                                varietyName(variety).lower())
    if not os.path.exists(graphics_dir): os.makedirs(graphics_dir)
    return graphics_dir

