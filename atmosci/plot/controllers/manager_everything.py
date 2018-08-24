
import matplotlib

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

prcp_colors = ('#660099','#A000C8','#1E3EFF','#00C8C8','#00DC00','#A0E632',
               '#E6DC32', '#E6AF2D','#F08228','#FF0000')

COLORS = { }
COLORS['normal'] = { }
#COLORS['normal']['low'] = ('#FFFFFF','#660099','#9966FF','#9999FF','#66CCFF',
COLORS['normal']['low'] = ('#DDDDDD','#FF00FF','#660099','#9966FF','#9999FF',
                           '#66CCFF','#3366FF','#0000FF','#006600','#00CC00',
                           '#99FF99', '#FFFF00','#F97900','#FF0000')
COLORS['normal']['medium'] = COLORS['normal']['low']
COLORS['normal']['high'] = COLORS['normal']['low']
COLORS['normal']['trace'] = COLORS['normal']['low']
COLORS['normal']['bias'] = ('#660099','#9966FF','#9999FF','#66CCFF','#3366FF',
                            '#0000FF','#DDDDDD','#006600','#00CC00','#99FF99',
                            '#FFFF00','#F97900','#FF0000')
COLORS['normal']['diff'] = COLORS['normal']['bias']

COLORS['extended'] = { }
COLORS['extended']['low'] = ('#DDDDDD','#FF00FF','#330066','#660099','#9966FF',
                             '#9999FF','#66CCFF','#3366FF','#0000FF','#006600',
                             '#00CC00','#99FF99','#FFFF00','#F97900','#FF0000',
                             '#990000')
COLORS['extended']['medium'] = COLORS['extended']['low']
COLORS['extended']['high'] = COLORS['extended']['low']
COLORS['extended']['trace'] = COLORS['extended']['low']
COLORS['extended']['diff'] = ('#FF00FF','#660099','#9966FF','#9999FF','#66CCFF',
                              '#3366FF','#0000FF','#DDDDDD','#006600','#00CC00',
                              '#99FF99','#FFFF00','#FFA500','#FF9790','#FF0000')
COLORS['extended']['bias'] = COLORS['extended']['diff']
COLORS['storms'] = ('#EEEEEE','#AAAAAA','#FF0000','#FF9900','#FFCC00','#FFFF00',
                    '#CCFF66','#66FF33','#33CC33','#009900','#009999','#00FFCC',
                    '#00CCFF','#0066FF','#0000FF','#000099','#660066','#9900CC',
                    '#CC33FF','#CC99FF',)

MMETERS = { }
MMETERS['normal'] = { }
MMETERS['normal']['trace'] = (0.001, 0.1, 1.0, 2.5, 5., 7.5, 10, 15., 20., 25., 30.,
                              40., 50.)
MMETERS['normal']['low'] = (0.001, 2.49, 6.4, 12.7, 19., 25.4, 38.1, 50.8, 63.5, 76.2,
                            88.9, 101.6, 127.)
MMETERS['normal']['medium'] = (0.001, 2.49, 12.7, 25.4, 50.8, 76.2, 101.6, 127., 152.4,
                               177.8, 203.2, 228.6, 254.)
MMETERS['normal']['high'] = (0.001, 25.4, 50.8, 101.6, 152.4, 203.2, 254., 317.5, 381.,
                             444.5, 508., 571.5, 635.)
MMETERS['normal']['diff'] = (-5., -2.5, -1., -0.5, -0.25, -0.1, 0.1, 0.25, 0.5,
                             1., 2.5, 5.)
MMETERS['normal']['bias'] = (-5., -2.5, -1., -0.5, -0.25, -0.1, 0.1, 0.25, 0.5,
                             1., 2.5, 5.)

MMETERS['extended'] = { }
MMETERS['extended']['trace'] = (0.001, 1.0, 2.5, 5., 7.5, 10, 15., 20., 25., 30.,
                                35., 40., 45., 50.)
MMETERS['extended']['low'] = (0.001, 2.49, 6.4, 12.7, 19., 25.4, 38.1, 50.8, 63.5,
                              76.2, 88.9, 101.6, 127., 190.5, 254.)
MMETERS['extended']['medium'] = (0.001, 2.49, 12.7, 25.4, 50.8, 76.2, 101.6, 127.,
                                 152.4, 177.8, 203.2, 228.6, 254., 317.5, 381.)
MMETERS['extended']['high'] = (0.001, 25.4, 50.8, 76.2, 101.6, 127., 152.4, 203.2,
                               254., 304.8, 355.6, 396.4, 447.2, 508., 635.)
#MMETERS['extended']['diff'] = (-20., -10., -5., -2.5, -1., -0.5, -0.1, 0.1, 0.5,
#                               1., 2.5, 5., 10., 20.)
MMETERS['extended']['diff'] = (-20., -17.5, -15., -10., -5., -2.5, -1.0, 1., 2.5, 5., 10., 15.,
                              17.5, 20.)
MMETERS['extended']['bias'] = (-5., -2.5, -1., -0.5, -0.25, -0.1, -0.01, 0.01,
                               0.1, 0.25, 0.5, 1., 2.5, 5.)

INCHES = { }
INCHES['normal'] = { }
INCHES['normal']['trace'] = (0.001, 0.025, 0.05, 0.075, .10, .15, .2, .25, .3, .35, .4, .5, 1.)
INCHES['normal']['low'] = (0.001, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3., 3.5, 4., 5.)
INCHES['normal']['medium'] = (0.001, 0.1, 0.5, 1., 2., 3., 4., 5., 6., 7., 8., 9., 10.)
INCHES['normal']['high'] = (0.001, 0.5, 1., 2., 4., 6., 8, 10., 12.5, 15., 17.5, 20., 22.5, 25.)
INCHES['normal']['diff'] = (-5., -2.5, -1., -0.5, -0.25, -0.1, 0.1, 0.25, 0.5, 1., 2.5, 5.)
INCHES['normal']['bias'] = (-5., -2.5, -1., -0.5, -0.25, -0.1, 0.1, 0.25, 0.5, 1., 2.5, 5.)

INCHES['extended'] = { }
INCHES['extended']['trace'] = (0.01, 0.025, 0.05, 0.075, .10, .15, .2, .25, .3, .35, .4, .5, .75, 1.0, 1.25)
INCHES['extended']['low'] = (0.01, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3., 3.5, 4., 5., 7.5, 10.)
INCHES['extended']['medium'] = (0.01, 0.1, 0.5, 1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 12.5, 15.)
INCHES['extended']['high'] = (0.01, 1., 2., 3., 4., 5., 6., 8, 10., 12., 14., 16., 18., 20., 25.)
INCHES['extended']['diff'] = (-20.,-5., -2.5, -1., -0.5, -0.25, -0.1, 0.1, 0.25, 0.5,
                              1., 2.5, 5.,20.)
INCHES['extended']['bias'] = (-5., -2.5, -1., -0.5, -0.25, -0.1, -0.01, 0.01, 0.1, 0.25, 0.5,
                              1., 2.5, 5.)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

temp_colors = ('#660099','#A000C8','#1E3EFF','#00C8C8','#00DC00','#A0E632',
               '#E6DC32','#E6AF2D','#F08228','#FF0000')

elev_colors = ('#FFFFFF','#A000C8','#1E3EFF','#00C8C8','#00DC00','#A0E632',
               '#E6DC32','#E6AF2D','#F08228','#FF0000')

more_colors = ('#999999',
               '#660099','#A000C8','#00C8C8','#0099FF','#1E3EFF','#009900',
               #'#660099','#A000C8','#00C8C8','#0099FF','#1E3EFF','#DDDDDD',
               '#00DC00','#A0E632','#E6DC32','#E6AF2D','#F08228','#FF0000')
#               '#000000')


ELEVATIONS = [ {} for indx in range(6) ]
ELEVATIONS[-1] = { 'discrete' : (-1000.,-1.,0.,1.,25.,50.,100.,250.,500.,750.,
                                  1000.) ,
                  'ticks' : (-1.,0.,1.,25.,50.,100.,250.,500.,750.) }
ELEVATIONS[0] = { 'discrete' : (-1000.,.01,50.,100.,200.,300.,400.,500.,600.,
                                700.,1000.) ,
                  'ticks' : (.01,50.,100.,200.,300.,400.,500.,600.,700.) }
ELEVATIONS[1] = { 'discrete' : (-100.,0.1,100.,200.,400.,600.,800.,1000.,1100.,
                                1200.,1300.,1400.,1500.,2000.) ,
                  'ticks' : (0.1,100.,200.,400.,600.,800.,1000.,1100.,1200.,
                             1300.,1400.,1500.) }
ELEVATIONS[2] = { 'discrete' : (-100.,0.1,100.,200.,400.,600.,800.,1000.,1250.,
                                1500.,1750., 2000.,2500.,5000.) ,
                  'ticks' : (0.1,100.,200.,400.,600.,800.,1000.,1250.,1500.,
                             1750.,2000.,2500.) }
ELEVATIONS[3] = { 'discrete' : (-100.,250.,500.,750.,1000.,1250.,1500.,1750.,
                              2000.,2250.,2500.,2750.,3000.,6000.) ,
                  'ticks' : (250.,500.,750.,1000.,1250.,1500.,1750.,2000.,
                             2250.,2500.,2750.,3000.) }
ELEVATIONS[4] = { 'discrete' : (-100.,250.,500.,750.,1000.,1250.,1500.,1750.,
                              2000.,2500.,3000.,4000.,5000.,10000.) ,
                  'ticks' : (250.,500.,750.,1000.,1250.,1500.,1750.,2000.,
                             2500.,3000.,4000.,5000.) }
ELEVATIONS[5] = { 'discrete' : (0.,1000.,1500.,2000.,2500.,3000.,3500., 4000.,
                                5000.,6000.,7000.,8000.,9000.,15000.) ,
                  'ticks' : (1000.,1500.,2000.,2500.,3000.,3500.,4000.,5000.,
                             6000.,7000.,8000.,9000.) }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if set_ticks:
    if len(tick_specs) == 2:
        ticks = [ ]
        tick = tick_specs[0]
        per_tick = tick_specs[1]
        while tick < data_max:
            ticks.append(round(tick))
            tick += per_tick
        num_ticks = len(ticks)
        color_incr = 1. / num_ticks
        print num_ticks, color_incr, ticks
        discrete = [ticks[0]-per_tick,] + ticks + [ticks[-1]+per_tick,]
        colors = [matplotlib.cm.jet(indx*color_incr)
                  for indx in range(num_ticks)]
    elif len(tick_specs) > 2:
        ticks = tick_specs
        discrete = (-1.,) + ticks + (200.,)
        if len(ticks) < 12:
            raise ValueError, 'ticks must be specified as a list with 12 values'
    else:
        if units == 'in':
            TICKS= INCHES
            max_discrete = 100.
        else:
            TICKS = MMETERS
            max_discrete = 1000.
        if diff:
            if extended_range:
                colors = COLORS['extended']['diff']
                ticks = TICKS['extended']['diff']
            else:
                colors = COLORS['normal']['diff']
                ticks = TICKS['normal']['diff']
            discrete = (-200.,) + ticks + (200.,)

        elif bias:
            if extended_range:
                colors = COLORS['extended']['diff']
                ticks = TICKS['extended']['diff']
            else:
                colors = COLORS['normal']['diff']
                ticks = TICKS['normal']['diff']
            discrete = (-200.,) + ticks + (200.,)

        else:
            if extended_range:
                if trace_range:
                    colors = COLORS['extended']['trace']
                    ticks = TICKS['extended']['trace']
                else:
                    half_way = ( TICKS['extended']['high'][-1] +
                                 TICKS['extended']['medium'][-1] ) / 2.0
                    if data_max > half_way:
                        colors = COLORS['extended']['high']
                        ticks = TICKS['extended']['high']
                    else:
                        half_way = ( TICKS['extended']['medium'][-1] +
                                     TICKS['extended']['low'][-1] ) / 2.0
                        if data_max > half_way:
                            colors = COLORS['extended']['medium']
                            ticks = TICKS['extended']['medium']
                        else:
                            half_way = ( TICKS['extended']['low'][-1] +
                                         TICKS['extended']['trace'][-1] ) / 2.0
                            if data_max > half_way:
                                colors = COLORS['extended']['low']
                                ticks = TICKS['extended']['low']
                            else:
                                colors = COLORS['extended']['low']
                                ticks = TICKS['extended']['trace']
            else:
                if trace_range:
                    colors = COLORS['normal']['trace']
                    ticks = TICKS['normal']['trace']
                else:
                    half_way = ( TICKS['normal']['high'][-1] +
                                 TICKS['normal']['medium'][-1] ) / 2.0
                    if data_max > half_way:
                        colors = COLORS['normal']['high']
                        ticks = TICKS['normal']['high']
                    else:
                        half_way = ( TICKS['normal']['medium'][-1] +
                                     TICKS['normal']['low'][-1] ) / 2.0
                        if data_max > half_way:
                            colors = COLORS['normal']['medium']
                            ticks = TICKS['normal']['medium']
                        else:
                            half_way = TICKS['normal']['trace'][-1] * 2.
                            if data_max > half_way:
                                colors = COLORS['normal']['low']
                                ticks = TICKS['normal']['low']
                            else:
                                colors = COLORS['normal']['low']
                                ticks = TICKS['normal']['trace']

            #discrete = (-1.,) + ticks + (200.,)
            #ticks = (0.1,) + ticks[1:] 
            discrete = (-0.00001,) + ticks + (max_discrete,)

    if plot_infinite_nodes:
        colors = colors + ('#000000',)
        discrete = discrete + (9999.,)
    if plot_nan_nodes:
        colors = ('#555555',) + colors
        discrete = (-32000.,) + discrete

    cmap = matplotlib.colors.ListedColormap(colors)
    norm = matplotlib.colors.BoundaryNorm(discrete,len(colors))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

   ticks = [first_tick+(tick*per_tick) for tick in range(num_ticks)]
    if units == 'K':
        discrete = [-250.,] + ticks + [350.,]
    elif units == 'F':
        discrete = [-32.,] + ticks + [130.,]
    elif units == 'm':
        discrete = [-30.,] + ticks + [7500.,]
    elif units == 'ft':
        discrete = [-100.,] + ticks + [22000.,]
    else:
        extreme = 20.*per_tick
        discrete = [ticks[0] - extreme,] + ticks + [ticks[-1] + extreme,]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if set_ticks:
    if extended_colors:
        num_ticks = len(more_colors) - 1
    else:
        num_ticks = len(temp_colors) - 1

    if diff_or_bias:
        if 'elev' in data_key:
            discrete = (-1000.,-500.,-200.,-100.,-50.,-20.,-10.,10.,20.,50.,
                         100.,200.,500.,1000.)
            ticks = (-500.,-200.,-100.,-50.,-20.,-10.,10.,20.,50.,100.,
                      200.,500.)
        else:
            if data_max > 40:
                if data_min > -5:
                    ticks = (-1.,0.,1.,2.5,5.,10.,20.,30.,40.)
                elif data_min > -15:
                    ticks = (-5.,-2.5,0.,2.5,5.,10.,20.,30.,40.)
                elif data_min > -30:
                    ticks = (-20.,-10.,-5.,0.,5.,10.,20.,30.,40.)
                discrete = list(ticks)
                discrete.insert(0,-100.)
                discrete.append(100.)
            elif data_max > 20:
                if data_min > -5:
                    ticks = (-2.5,-1.,0.,1.,2.5,5.,10.,15.,20.)
                elif data_min > -15:
                    ticks = (-10.,-5.,-2.5,0.,2.5,5.,10.,15.,20.)
                elif data_min > -30:
                    ticks = (-20.,-15.,-10.,-5.,0.,5.,10.,15.,20.)
                discrete = list(ticks)
                discrete.insert(0,-100.)
                discrete.append(100.)
            elif data_max > 10:
                if data_min > -5:
                    ticks = (-2.5,-1.,0.,1.,2.5,5.,7.5,10.,12.5)
                elif data_min > -15:
                    ticks = (-12.5,-10.,-7.5,-5.,-2.5,0.,2.5,5.,7.5)
                elif data_min > -30:
                    ticks = (-20.,-15.,-12.5,-10.,-7.5,-5.,0.,5.,7.5)
                discrete = list(ticks)
                discrete.insert(0,-100.)
                discrete.append(100.)
            elif data_max < 1:
                if data_min > -10:
                    ticks = (-10.,-8.,-6.,-5.,-4.,-3.,-2.,-1.,0.)
                elif data_min > -15:
                    ticks = (-12.5,-10.,-8.,-6.,-4.,-3.,-2.,-1.,0.)
                elif data_min > -30:
                    ticks = (-25.,-20.,-15.,-12.5,-10.,-7.5,-5.,-2.5,0.)
                discrete = list(ticks)
                discrete.insert(0,-100.)
                discrete.append(100.)
            elif data_min < -40:
                if data_max <= 10.:
                    ticks = (-40.,-30.,-20.,-10.,-5.,-1,0.,1.,5.)
                elif data_max < 20.:
                    ticks = (-40.,-30.,-20.,-10.,-5.,0.,5.,10.,15.)
                else:
                    ticks = (-40.,-30.,-20.,-10.,0.,10.,20.,30.,40.)
                discrete = list(ticks)
                discrete.insert(0,-100.)
                discrete.append(100.)
            else:
                discrete = (-50.,-10.,-5.,-1.,0.,1.,2.5,5.,7.,10.,50.)
                ticks = (-10.,-5.,-1.,0.,1.,2.5,5.,7.,10.)
    elif 'elev' in data_key:
        ticks, discrete = getTicksFromArgs(args, num_ticks, data_min, data_max,
                                           units, False)
        if ticks is None:
            discrete = ELEVATIONS[options.elevations]['discrete']
            ticks = ELEVATIONS[options.elevations]['ticks']
    elif 'lapse' in data_key:
        discrete = (-10., -1., -0.1, -0.05, -0.03, -0.02, -0.01, 0.01, 0.02,
                    0.03, 0.05, 0.1, 1., 10.)
        ticks = (-1., -0.1, -0.05, -0.03, -0.02, -0.01, 0.01, 0.02, 0.03, 0.05,
                 0.1, 1.)
    elif 'mask' not in data_key:
        ticks, discrete = getTicksFromArgs(args, num_ticks, data_min, data_max,
                                           units, True)
    elif data_key in ('lon','lat'):
        ticks = calculateTicks(int(data_min+0.5)+1, int(data_max-0.5)-1, 12)
        discrete = ticks
        discrete.insert(0,int(data_min-3.))
        discrete.append(int(data_max+3.))

    if 'elev' in data_key:
        if extended_colors or diff_or_bias or options.elevations > 0:
            cmap = matplotlib.colors.ListedColormap(more_colors)
            norm = matplotlib.colors.BoundaryNorm(discrete, len(discrete)-1)
        else:
            cmap = matplotlib.colors.ListedColormap(elev_colors)
            norm = matplotlib.colors.BoundaryNorm(discrete, len(elev_colors))
    elif 'lapse' in data_key:
        cmap = matplotlib.colors.ListedColormap(more_colors)
        norm = matplotlib.colors.BoundaryNorm(discrete, len(discrete)-1)
    elif 'mask' in data_key:
        colors = ('#FFFFFF','#666666','#CCCCFF','#FFFFFF')
        cmap = matplotlib.colors.ListedColormap(colors)
        ticks = (0.,1.)
        discrete = (-1000000.,0.,1.,1000000.)
        norm = matplotlib.colors.BoundaryNorm(discrete,len(colors))
    else:
        if extended_colors:
            cmap = matplotlib.colors.ListedColormap(more_colors)
            norm = matplotlib.colors.BoundaryNorm(discrete,len(more_colors))
        else:
            cmap = matplotlib.colors.ListedColormap(temp_colors)
            norm = matplotlib.colors.BoundaryNorm(discrete,len(temp_colors))

