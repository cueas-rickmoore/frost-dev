
import matplotlib

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from .standards import STANDARD_COLORS

COLOR_SETS = { 10 : ('#DDDDDD',) + STANDARD_COLORS[10][1:],
               12 : ('#DDDDDD',) + STANDARD_COLORS[12][1:],
               14 : ('#DDDDDD',) + STANDARD_COLORS[14][1:],
             }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TICK_SETS = { }
TICK_SETS[500] = { 
    10 : (-1.,0.,1.,25.,50.,100.,200.,300.,400.,500.),
    12 : (-1.,0.,1.,50.,100.,150.,200.,250.,300.,350.,400.,500.),
    14 : (-5.,-1.,0.,1.,50.,100.,150.,200.,250.,300.,350.,400.,450.,500.),
    }
TICK_SETS[1000] = { 
    10 : (-1.,0.,1.,50.,100.,200.,400.,600.,800.,1000.),
    12 : (-1.,0.,1.,50.,100.,200.,300.,400.,500.,600.,800.,1000.),
    12 : (-1.,0.,1.,50.,100.,200.,300.,400.,500.,600.,700.,800.,900.,1000.),
    }
TICK_SETS[1500] = {
    10 : (0.1,100.,200.,400.,600.,800.,1000.,1200.,1400.,1500.),
    12 : (0.1,100.,200.,400.,600.,800.,1000.,1100.,1200.,1300.,1400.,1500.),
    12 : (0.1,100.,200.,400.,600.,700.,800.,900.,1000.,1100.,1200.,1300.,1400.,
          1500.),
    }
TICK_SETS[2000] = {
    10 : (0.1,250.,500.,750.,1000.,1200.,1400.,1600.,1800.,2000.),
    12 : (0.1,250.,500.,750.,1000.,1200.,1400.,1600.,1700.,1800.,1900.,2000.),
    14 : (0.1,250.,500.,750.,1000.,1200.,1300.,1400.,1500.,1600.,1700.,1800.,
          1900.,2000.),
    }
TICK_SETS[3000] = { 
    10 : (0.1,500.,1000.,1250.,1500.,1750.,2000.,2250.,2500.,2750.,3000.),
    12 : (0.1,500.,1000.,1500.,1750.,2000.,2250.,2500.,2600.,2700.,2800.,
          3000.),
    14 : (0.1,500.,1000.,1500.,2000.,2100.,2200.,2300.,2400.,2500.,2600.,2700.,
          2800.,3000.),
    }
TICK_SETS[5000] = {
    10 : (0.1,500.,1000.,1500.,2000.,2500.,3000.,3500.,4000.,5000.),
    12 : (0.1,500.,1000.,1500.,2000.,2500.,3000.,3500.,4000.,4300.,4600.,5000.),
    14 : (0.1,500.,1000.,1500.,2000.,2300.,2600.,3000.,3300.,3600.,4000.,4300.,
          4600.,5000.),
    }
TICK_SETS[10000] = {
    10 : (0.1,1000.,2000.,3000.,4000.,5000.,6000.,7000.,8000.,9000.)
    12 : (0.1,1000.,2000.,3000.,4000.,5000.,6000.,7000.,7500.,8000.,8500.,9000.)
    14 : (0.1,1000.,2000.,3000.,4000.,5000.,5500.,6000.,6500.,7000.,7500.,8000.,
          8500.,9000.)
    }

TICK_EXTREMES = (-500.,100000.)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ElevationPlotController(object):

    def getColors(self, num_colors):
        try: colors = COLOR_SETS[num_colors]
        except: colors = COLOR_SETS['default']
        return colors

    def getTicks(self, num_ticks):
        return TICK_SETS[num_ticks]

    def getMappedColors(num_ticks):
        colors = self.getColors(num_ticks)
        cmap = matplotlib.colors.ListedColormap(colors)
        low_end, high_end = TICK_EXTREMES
        discrete = (low_end,) + self.getTicks(num_ticks) + (high_end,)
        norm = matplotlib.colors.BoundaryNorm(discrete,len(colors))
        return cmap, norm

    def getMappedColors(num_ticks):
        colors = self.getColors(num_ticks)
        cmap = matplotlib.colors.ListedColormap(colors)
        low_end, high_end = TICK_EXTREMES
        discrete = (low_end,) + self.getTicks(num_ticks) + (high_end,)
        norm = matplotlib.colors.BoundaryNorm(discrete,len(colors))
        return cmap, norm

