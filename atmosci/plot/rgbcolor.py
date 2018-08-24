
import re
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

HEX_COLOR = re.compile("\A#[a-fA-F0-9]{6}\Z")

LUMINANCE_MULTIPLIERS = { 'luminosity' : N.array((0.2126,0.7152,0.0722)),
                          'brightness' : N.array((0.299,0.587,0.114)),
                          'television' : N.array((0.241,0.691,0.068)),
                        }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def hex2rgb(hex_color_string):
    """ Convert a hex color string to the corresponding RGB color tuple
    where each value is type<float> in the range 0.0 to 1.0
    """
    if not isinstance(hex_color_string, basestring):
        raise TypeError, '"color_string"  must be type<str>'
    if HEX_COLOR.match(hex_color_string) is None:
        errmsg = '"%s is an invalid hex color definition'
        raise ValueError, errmsg % hex_color_string
    rgb = [int(hex_value, 16)/255.0 for hex_value in (s[1:3], s[3:5], s[5:7])]
    return tuple(rgb)

def rgb2hex(rgb_color):
    """ Convert a RGB color tuple to the corresponding hex color string,
    Note: the individual RGB values must be type<float> in the range
    0.0 to 1.0
    """
    if not isinstance(rgb_color, (list,tuple)):
        errmsg = '"rgb_color" must be either type<tuple> or type<list>'
        raise TypeError, errmsg
    if type(rgb_color[0]) != float:
        raise TypeError, '"rgb_color" values must be type<float>'
    hex_ints = [round(value*255) for value in rgb_color]
    return '#%02x%02x%02x' % hex_ints

def rgb2luminance(rgb_color, algorithm='objective'):
    multiplers = LUMINANCE_MULTIPLIERS[algorithm]
    if algorithm == 'television':
        rgb_squared = [value**2 for value in rgb_color]
        return math.sqrt((multiplers * rgb_squared).sum())
    else:
        return (multiplers * rgb_color).sum()

