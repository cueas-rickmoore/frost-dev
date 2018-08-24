
import os

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig
from frost.grape.functions import mapFilename, mapFilepath, mapWorkingDir
from frost.grape.functions import plotWorkingDir

from frost.visual.maps import hiResMap, finishMap, mapInit
from frost.visual.maps import addScatterToMap, addMapText, addFigureText
from frost.visual.maps import drawBlankMap, drawFilledContours

from frost.grape.grid import GrapeVarietyFileReader

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GrapeVarietyGridVisualizer(GrapeVarietyFileReader):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initMapOptions(self, date, data_group, subgroup, title_key=None):
        # import map options from the config file
        config_path = 'crops.grape.maps.options.%s.attrs' % data_group
        config_options = fromConfig(config_path)
        map_options = config_options.copy()
        map_options['date'] = date

        # set the map title
        if title_key is not None:
            title = self.mapTitle(date, title_key)
            map_options['title'] = title

        # set the map file path
        map_options['outputfile'] = \
        mapFilepath(date, self.variety, data_group, subgroup)
        return map_options

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapTitle(self, date, title_key, **kwargs):
        title_args = { 'variety':self.variety.description, }
        if kwargs: title_args.update(kwargs)

        # get the map title template and initialize the map title
        title_template = fromConfig('crops.grape.maps.titles.%s' % title_key)
        return title_template % title_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # mapping methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def addTitleText(self, fig, title, **map_options):
        options = { 'backgroundcolor':text_options.get('title_bgcolor','white'),
                    'color':text_options.get('title_fgcolor','black'),
                    'fontsize':text_options.get('title_fontsize',12),
                    'ha':text_options.get('title_ha','right'),
                    'va':text_options.get('title_va','center'),
                    'zorder':text_options.get('title_zorder',20),
                  }
        x = text_options.get('title_x',0.875)
        y = tet_options.get('title_y',0.3)

        fig_text = fig.text(x, y, title, **options)
        fig_text.set_bbox({'alpha':0})

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawGDDMap(self, date, verbose=False):
        min_gdd = fromConfig('crops.grape.maps.min_gdd_to_post')
        min_percent = fromConfig('crops.grape.maps.min_percent_nodes')
        lats = self.lats
        lons = self.lons
        # get initiaized map options from config file
        map_options = self.initMapOptions(date,
                                          'variety', 'gdd', 'gdd')

        # get GDD accumulations for the date and draw the map
        gdd_grid = self.getGdd(model.name, date)
        gdd_grid[N.where(gdd_grid < 0.99)] = N.nan

        finite = N.where(N.isfinite(gdd_grid))
        num_finite = len(finite[0])
        if num_finite > 0:
            num_ge_min = float(len(N.where(gdd_grid[finite] >= min_gdd)[0]))
            draw_contours = (num_ge_min / num_finite) > min_percent
        else: draw_contours = False
        if draw_contours:
            map_options['finish'] = False
            options, _map_, fig, axes, fig1, xy_extremes = \
            drawFilledContours(gdd_grid, lats, lons, **map_options)
            addModelText(fig, **map_options)
            finishMap(fig, axes, fig1, **options)
            return options['outputfile']
        else:
            config = fromConfig('crops.grape.maps.no_data.gdd.attrs')
            return drawNoDataMap(lons, lats, config=config, model=model,
                                 **map_options)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawHardinessMap(self, date, verbose=False):
        # get initiaized map options from config file
        map_options = self.initMapOptions(date, 'hardiness', 'temp')

        map_options['outputfile'] = \
        mapFilepath(date, self.variety, 'hardiness', 'temp')

        units = chr(176)+'F'
        map_options['title'] = \
        self.mapTitle(date, 'hardiness', units=units.decode('latin1'))

        hard_temp = self.getHardiness(date, units='F')
        drawFilledContours(hard_temp, self.lats, self.lons, **map_options)
        return map_options['outputfile']

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawKillMap(self, date, mint, verbose=False):
        if self.temp_reader is None:
            from frost.functions import tempGridReader
            self.temp_reader = tempGridReader(date)

        lats = self.lats
        lons = self.lons
        # get initiaized map options from config file
        map_options = self.initMapOptions(date, 'kill', 'potential')
        map_options['title'] = self.mapTitle(date, 'kill')

        # extract options required for plotting markers 
        marker_colors = map_options['markercolors']

        # get hardines temp and min temp for the date
        hardiness = self.getHardiness(date, units='F')
        mint = self.temp_reader.getTemp('reported.mint', date, units='F')

        # we need number of degrees mint is below hardiness temp.
        # In order to guarantee that we don't have one negative value
        # and one positive value, we need to adjust the grids so that
        # all values in each of them are above zero
        # using 1000. might be overkill, but it is guaranteed safe
        hardiness += 1000.
        mint += 1000.
        diff = hardiness - mint

        indexes = N.where(diff >= 0)
        # there is potential kill at one or more grid nodes
        if len(indexes[0]) > 0:
            options, _map_, map_fig, axes, xy_extremes, x, y, _grid_ = \
            hiResMap(diff, lats, lons, **map_options)
            del x, y, _grid_

            diff = diff[indexes].flatten()
            _lats_ = lats[indexes].flatten()
            _lons_ = lons[indexes].flatten()

            # draw a separate map layer for each potential
            for indx, where_clause in enumerate(map_options['where_potential']):
                prob_indexes = eval('N.where(%s)' % where_clause)
                if len(prob_indexes[0]) > 0:
                    diff[prob_indexes] = indx
                    fig = addScatterToMap(options, _map_, map_fig, 
                                          diff[prob_indexes],
                                          _lats_[prob_indexes],
                                          _lons_[prob_indexes],
                                          markercolor=marker_colors[indx])

            finishMap(map_fig, axes, map_fig, **options)
            return options['outputfile']

        # no kill events - draw a blank map
        else:
            return self.drawNoDataMap('kill', **map_options)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawNoDataMap(self, map_key, **options):
        from frost.visual.maps import mapSetup

        no_data = fromConfig('crops.grape.maps.no_data.%s.attrs' % map_key)
        options.update(no_data)

        map_options, _basemap_, map_fig, axes, xy_extremes = \
        mapSetup(options, self.lats, self.lons)

        if 'contourbounds' in options:
            from frost.visual import resolveColorMapOptions
            x_min = xy_extremes[0]
            x = N.array( [ [x_min, x_min+1.0], [x_min, x_min+1.0 ] ] )
            y_min = xy_extremes[2]
            y = N.array( [ [y_min, y_min], [y_min+1.0, y_min+1.0 ] ] )
            zero = N.array( [ [0.0, 0.0], [0.0, 0.0] ] )

            cmap_options = resolveColorMapOptions(**map_options)
            fig1 = _basemap_.contourf(x, y, zero, options['contourbounds'],
                                     **cmap_options)
            finishMap(map_fig, axes, fig1, **map_options)

        else: finishMap(map_fig, axes, map_fig, **map_options)

        return map_options['outputfile']

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # plotting methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def plotHardinessVsTempAtPoint(self, start_date, end_date, test_path=False,
                                         verbose=False):
        from dateutil.relativedelta import relativedelta
        from matplotlib import pyplot
        from matplotlib.ticker import Formatter

        # create a date formatter for the X axis
        class DateFormatter(Formatter):
            def __init__(self, start_date):
                self.start_date = start_date
            def __call__(self, x, pos=0):
                if pos == 0: return ''
                date = self.start_date + relativedelta(days=(x-1))
                return '%d/%d' % (date.month, date.day)
        dateFormatter = DateFormatter(start_date)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _postInitGrape_(self, target_year, variety, **kwargs):
        GrapeVarietyFileReader._postInitGrape_(self, target_year, variety,
                                                     **kwargs)
        self.temp_reader = kwargs.get('temp_reader', None)

