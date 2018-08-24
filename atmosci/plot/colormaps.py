
import copy
import string
from cStringIO import StringIO

import numpy as N
import matplotlib
from matplotlib import pyplot

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CMAP_NAMES = [cmap for cmap in matplotlib.cm.datad if not cmap.endswith('_r')]
def ignore_case_compare(string1, string2):
    return cmp(string1.lower(), string2.lower())
CMAP_NAMES.sort(ignore_case_compare)

from .customcmaps import CUSTOM_COLORMAPS

DEFAULT_COLORMAP = 'jet'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from .htmlcolors import htmlColorName2Hex

def isHexColor(_string):
    if _string[0] != '#': return False
    for char in _string[1:]:
        if char not in string.hexdigits: return False
    return True

def hex2MplColors(hex_colors):
    mpl_colors = [ ]
    for hex_color in hex_colors:
        mpl_colors.append(matplotlib.colors.hex2color(hex_color))
    return tuple(mpl_colors)

def getColorSet(cmap_name, num_colors):
    return matplotlib.cm.get_cmap(cmap_name, num_colors)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ColormapManager:

    def __init__(self, colormaps={ }):
        self._builtin_cmap_names = tuple(CMAP_NAMES)
        self._builtin_cmap_dict = { }
        for name in self._builtin_cmap_names:
            self._builtin_cmap_dict[name.lower()] = name
        self._builtin_lower_names = tuple(self._builtin_cmap_dict.keys())
        self._custom_cmaps = copy.deepcopy(CUSTOM_COLORMAPS)
        self._custom_cmap_names = tuple(self._custom_cmaps.keys())
        discrete_names = [ ]
        for name, cmap in self._custom_cmaps.items():
            if type(cmap) == 'dict' and 'bounds' in cmap:
                discrete_names.append(name)
        self._discrete_cmap_names = tuple(name) 

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def addColormap(self, cmap_name, colors, bounds=None):
        if name in self._builtin_cmap_names or\
           name in self._builtin_lower_names:
            raise KeyError, "'%s' is a reserved colormap name." % cmap_name
        if name in self._custom_cmap_names:
            raise KeyError, "Colormap '%s' already exists." % cmap_name

        cmap = { 'colors' : colors }
        self._custom_cmaps[name] = cmap
        self._custom_cmap_names = tuple(self._custom_cmaps.keys())
        if bounds is not None:
            self._custom_cmaps[name]['bounds'] = bounds
            self._discrete_cmap_names =\
                 tuple([name for name in self._custom_cmap_names
                             if 'bounds' in self._custom_cmaps[name]])

    def getColormap(self, colors):
        return matplotlib.colors.ListedColormap(self.getMplColors(colors))

    def getColormapByName(self, cmap_name):
        if cmap_name in self._custom_cmap_names:
            cmap_spec = self._custom_cmap[cmap_name]
            if 'bounds' in cmap_spec:
                return self.getDiscreteColormap(cmap_spec['colors'],
                                                cmap_spec['bounds'])
            return self.getColormap(cmap_spec['colors'])
        else:
            if cmap_name.islower():
                cmap_name = self._builtin_cmap_dict.get(cmap_name, cmap_name)
            if cmap_name in self._builtin_cmap_names:
                return matplotlib.cm.get_cmap(cmap_name)

        raise KeyError, "Colormap '%s' does not exist." % cmap_name

    def getDiscreteColormap(self, colors_or_cmap, boundaries):
        if isinstance(colors_or_cmap,(tuple,list)):
            cmap = self.getColormap(colors_or_cmap)
            num_colors = len(colors_or_cmap)
            if num_colors != len(boundaries)-1:
                raise ValueError, "In discrete colormaps, the number of " +\
                                  "colors must egual the number of intervals."
        elif isinstance(colors_or_cmap, matplotlib.colors.Colormap):
            cmap = colors_or_cmap
            num_colors = colors_or_cmap.N
        elif isinstance(colors_or_cmap, basestring):
            cmap = self.getColormapByName(colors_or_cmap)
            if cmap == None:
                raise ValueError, "Invalid value for 'color_or_cmap'."
            num_colors = cmap.N
        else:
            raise ValueError, "Unsupported value type for 'color_or_cmap'."

        norm_bounds = matplotlib.colors.BoundaryNorm(boundaries, num_colors)
        return cmap, norm_bounds

    def getMplColors(self, colors):
        mpl_colors = [ ]
        for color in colors:
            if isHexColor(color):
                mpl_colors.append(matplotlib.colors.hex2color(color))
            else:
                hex_color = htmlColorName2Hex(color)
                if hex_color is not None:
                    mpl_colors.append(matplotlib.colors.hex2color(hex_color))
                else:
                    raise ValueError, "Invalid color in list 'colors'."
        return mpl_colors

    def isDiscreteColormap(self, cmap_name):
        if cmap_name in self._discrete_cmap_names: return True
        return False

    def listColormaps(self, format='python'):
        return self._builtin_cmap_names

    def removeColormap(self, cmap_name):
        if name in self._custom_cmap_names:
            del self._custom_cmaps[cmap_name]
        else:
            if name in self._builtin_cmap_names:
                raise KeyError, "'%s' is a reserved colormap name." % cmap_name
            raise KeyError, "Colormap '%s' does not exist." % cmap_name

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawColormaps(self, cmap_names=None):
        if cmap_names is None:
            cmap_names = self.listColormaps()
        spacing = N.outer(N.ones(10), N.arange(0,1,0.01))
        figure = pyplot.figure(figsize=(8,16))
        pyplot.subplots_adjust(top=1.0, bottom=0.05, left=0.05, right=0.8,
                               hspace=0.25)
        num_subplots = len(cmap_names)+1
        for indx, name in enumerate(cmap_names):
            axes = pyplot.subplot(num_subplots, 1, indx+1)
            pyplot.axis('off')
            pyplot.imshow(spacing, aspect='auto', cmap=self.getColormap(name),
                          origin='lower')
            pyplot.title(name, x=1.025, y=0.0, fontsize=12,
                         horizontalalignment='left', verticalalignment='center')
        return figure

    def displayColormaps(self, facecolor='gray', format='PNG'):
        figure = self.drawColormaps()
        image_buffer = StringIO()
        figure.savefig(image_buffer, facecolor=facecolor, format=format)
        image = image_buffer.getvalue()
        image_buffer.close()
        return image

    def saveColormaps(self, filepath, facecolor='gray', format='PNG'):
        figure = self.drawColormaps()
        figure.savefig(filepath, facecolor=facecolor, format=format)

