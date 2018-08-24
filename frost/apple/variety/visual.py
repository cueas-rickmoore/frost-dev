
import os

import numpy as N

from atmosci.utils.timeutils import asAcisQueryDate

from frost.functions import fromConfig
from frost.apple.functions import mapWorkingDir, mapFilename, plotWorkingDir

from frost.visual.maps import hiResMap, finishMap
from frost.visual.maps import addScatterToMap, addMapText, addFigureText
from frost.visual.maps import drawBlankMap, drawFilledContours

from frost.apple.variety.grid import AppleVarietyGridManager
from frost.apple.visual import addModelText, drawNoDataMap

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleVarietyGridVisualizer(AppleVarietyGridManager):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initMapOptions(self, date, model, lo_gdd_th, hi_gdd_th, map_group,
                             map_type, title_key=None):
        # import map options from the config file
        config_path =\
        'crops.apple.%s.maps.options.%s.attrs' % (map_group, map_type)
        config_options = fromConfig(config_path)
        map_options = config_options.copy()
        map_options['date'] = date

        # set the map title
        if title_key is not None:
            #if lo_gdd_th is not None:
            #    # create threshold key for title
            #    thresholds = '%d<AVGT>%d' % (lo_gdd_th, hi_gdd_th)
            #    title = self.mapTitle(date, model, title_key, thresholds=thresholds)
            #else: title = self.mapTitle(date, model, title_key)
            title = self.mapTitle(date, model, title_key)
            map_options['title'] = title

        # set the map file path
        map_options['outputfile'] =\
        self.mapFilepath(date, model, map_group, map_type, None, None)
        return map_options

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapFilepath(self, date, model, map_group, map_type, lo_gdd_th,
                          hi_gdd_th, test_file=False):
        # get the map directory path and the template for the map file name
        map_dirpath = mapWorkingDir(self.target_year, self.variety.name,
                                    model.name, map_group, map_type, lo_gdd_th,
                                    hi_gdd_th, test_file)
        filename_template = mapFilename('%s', self.variety.name, model.name, 
                                         map_group, map_type, lo_gdd_th,
                                        hi_gdd_th, test_file)
        filepath_template = map_dirpath + os.sep + filename_template
        return filepath_template % asAcisQueryDate(date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def mapTitle(self, date, model, title_key, **kwargs):
        title_args = { 'variety':self.variety.description, }
        if len(kwargs) > 0: title_args.update(kwargs)

        # get the map title template and initialize the map title
        if '%' not in title_key:
            title_template =\
            fromConfig('crops.apple.variety.maps.titles.%s' % title_key)
            return title_template % title_args
        # a template was passed
        else: return title_key % title_args

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

    def drawChillMaskMap(self, date, model, lo_gdd_th, hi_gdd_th, verbose=False):
        lats = self.lats
        lons = self.lons
        # get initiaized map options from config file
        map_options = self.initMapOptions(date, model, None, None, 'variety',
                                          'mask', 'mask')
        var_config = fromConfig('crops.apple.variety')

        # get stage index for date and draw the map
        mask = self.getChillMask(model.name, lo_gdd_th, hi_gdd_th, date)
        indexes = N.where(mask == True)

        # kill is probable at one or more grid nodes
        if len(indexes[0]) > 0:

            options, _map_, map_fig, axes, xy_extremes, x, y, _grid_ = \
            hiResMap(mask, lats, lons, **map_options)
            del x, y, _grid_

            x,y = _map_(lons[indexes].flatten(), lats[indexes].flatten())
            fig1 = _map_.scatter(x, y, c='r', s=3, marker='^', linewidths=0)
            addModelText(map_fig, model, **map_options)
            finishMap(map_fig, axes, map_fig, **options)
            return options['outputfile']

        # no kill events - draw a blank map
        else:
            config = fromConfig('crops.apple.variety.maps.no_data.kill.attrs')
            return drawNoDataMap(lons, lats, config=config, model=model,
                                 **map_options)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawGDDMap(self, date, model, lo_gdd_th, hi_gdd_th, verbose=False):
        min_gdd = fromConfig('crops.apple.variety.maps.min_gdd_to_post')
        min_percent = fromConfig('crops.apple.variety.maps.min_percent_nodes')
        lats = self.lats
        lons = self.lons
        # get initiaized map options from config file
        map_options = self.initMapOptions(date, model, lo_gdd_th, lo_gdd_th,
                                          'variety', 'gdd', 'gdd')

        # get GDD accumulations for the date and draw the map
        gdd_grid = self.getGdd(model.name, lo_gdd_th, hi_gdd_th, date)
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
            addModelText(fig, model, **map_options)
            finishMap(fig, axes, fig1, **options)
            return options['outputfile']
        else:
            config = fromConfig('crops.apple.variety.maps.no_data.gdd.attrs')
            return drawNoDataMap(lons, lats, config=config, model=model,
                                 **map_options)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawKillMap(self, date, model, lo_gdd_th, hi_gdd_th, verbose=False):
        lats = self.lats
        lons = self.lons
        # get initiaized map options from config file
        map_options = self.initMapOptions(date, model, None, None, 'variety',
                                          'kill', 'kill')
        var_config = fromConfig('crops.apple.variety')

        # extract options required for plotting markers 
        marker_colors = map_options['markercolors']
        kill_probabilities = var_config.kill_probabilities

        # get stage index for date and draw the map
        kill = self.getKill(model.name, lo_gdd_th, hi_gdd_th, date)
        indexes = N.where(kill > 0)
        # kill is probable at one or more grid nodes
        if len(indexes[0]) > 0:
            options, _map_, map_fig, axes, xy_extremes, x, y, _grid_ = \
            hiResMap(kill, lats, lons, **map_options)
            del x, y, _grid_

            kill = kill[indexes].flatten()
            _lats_ = lats[indexes].flatten()
            _lons_ = lons[indexes].flatten()

            # draw a separate map layer for each probability
            for indx, probability in enumerate(kill_probabilities,start=1):
                prob_indexes = N.where(kill == probability)
                if len(prob_indexes[0]) > 0:
                    kill[prob_indexes] = indx

                    fig = addScatterToMap(options, _map_, map_fig, 
                                          kill[prob_indexes],
                                          _lats_[prob_indexes],
                                          _lons_[prob_indexes],
                                          markercolor=marker_colors[indx-1])
            addModelText(map_fig, model, **map_options)
            finishMap(map_fig, axes, map_fig, **options)
            return options['outputfile']

        # no kill events - draw a blank map
        else:
            config = fromConfig('crops.apple.variety.maps.no_data.kill.attrs')
            return drawNoDataMap(lons, lats, config=config, model=model,
                                 **map_options)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawStageMap(self, date, model, lo_gdd_th, hi_gdd_th, verbose=False):
        lats = self.lats
        lons = self.lons
        # get initiaized map options from config file
        map_options = self.initMapOptions(date, model, lo_gdd_th, lo_gdd_th,
                                  'variety', 'stage', 'stage')
        var_config = fromConfig('crops.apple.variety')

        # extract options required for plotting markers 
        marker_colors = map_options['markercolors']
        stage_name_map = var_config.stage_name_map

        # get stage index for date and draw the map
        stage_data = self.getStage(model.name, lo_gdd_th, hi_gdd_th, date)

        isfinite = N.where(N.isfinite(stage_data))
        if len(N.where(stage_data[isfinite] > 0)[0]) > 0:
            options, _map_, map_fig, axes, xy_extremes, x, y, _grid_ = \
            hiResMap(stage_data, lats, lons, **map_options)
            del x, y, _grid_

            _lats_ = lats[isfinite].flatten()
            _lons_ = lons[isfinite].flatten()
            stage_data = stage_data[isfinite].flatten()

            for stage in range(len(stage_name_map.attrs)):
                indexes = N.where(stage_data == stage)
                if len(indexes[0]) > 0:
                    fig = addScatterToMap(map_options, _map_, map_fig, 
                                          stage_data[indexes],
                                          _lats_[indexes],
                                          _lons_[indexes],
                                          markercolor=marker_colors[stage])
            addModelText(map_fig, model, **map_options)
            finishMap(map_fig, axes, map_fig, **options)
            return options['outputfile']
        else:
            config = fromConfig('crops.apple.variety.maps.no_data.stage.attrs')
            return drawNoDataMap(lons, lats, config=config, model=model,
                                 **map_options)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def drawStageContourMap(self, date, model, lo_gdd_th, hi_gdd_th,
                                  verbose=False):
        lats = self.lats
        lons = self.lons
        # get initiaized map options from config file
        map_options = self.initMapOptions(date, model, lo_gdd_th, lo_gdd_th,
                                  'variety', 'stage', 'stage')

        # get stage index for date and draw the map
        stage_grid = self.getStage(model.name, lo_gdd_th, hi_gdd_th, date)

        isfinite = N.where(N.isfinite(stage_grid))
        if len(N.where(stage_grid[isfinite] > 0)[0]) > 0:
            map_options['finish'] = False
            options, _map_, fig, axes, fig1, xy_extremes = \
            drawFilledContours(stage_grid, lats, lons, **map_options)
            addModelText(fig, model, **map_options)
            finishMap(fig, axes, fig1, **options)
            return options['outputfile']
        else:
            config = fromConfig('crops.apple.variety.maps.no_data.stage.attrs')
            return drawNoDataMap(lons, lats, config=config, model=model,
                                 **map_options)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # plotting methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def plotKillVsStageAtPoint(self, lon, lat, model, start_date, end_date,
                                     lo_gdd_th, hi_gdd_th, mint, 
                                     test_file=False, verbose=False):
        from dateutil.relativedelta import relativedelta
        from matplotlib import pyplot
        from matplotlib.ticker import Formatter

        # get the map directory path and the template for the map file name
        plot_dirpath = plotWorkingDir(self.target_year, self.variety.name,
                                      model.name, 'kill.at.stage', test_file)
        filename_template = '%s-Frost-Apple-%s-%%s-Kill-at-Stage-%s.png'
        filename_template = filename_template % (asAcisQueryDate(start_date),
                                                 self.variety.name,
                                                 model.name.title())
        filepath_template = plot_dirpath + os.sep + filename_template

        # get the map title template and initialize the map title
        title_template = '%s : %%s Kill at Stage\n%s\n\n%s\n%s'
        time_span = '%s thru %s' % (start_date.strftime('%B %d, %Y'),
                                    end_date.strftime('%B %d, %Y'))
        title_template = title_template % (self.variety.description,
                                           model.description, time_span,
                                           '%-7.3fW , %-6.3fN' % (lon,lat))

        # get date indepenedent attributes and grids
        y, x = self.indexOfClosestNode(lon, lat)
        start_indx = self.indexFromDate(start_date)
        end_indx = self.indexFromDate(end_date) + 1
        # turn start/end indexes into a list of dates
        days = [ day for day in range(1, (end_indx - start_indx)+1) ]

        # create a date formatter for the X axis
        class DateFormatter(Formatter):
            def __init__(self, start_date):
                self.start_date = start_date
            def __call__(self, x, pos=0):
                if pos == 0: return ''
                date = self.start_date + relativedelta(days=(x-1))
                return '%d/%d' % (date.month, date.day)
        dateFormatter = DateFormatter(start_date)

        # get stage at node for each day
        dataset = self.modelDatasetPath(model.name, lo_gdd_th, hi_gdd_th,
                                        'stage', 'index')
        stage_at_node = self.getDataset(dataset)[start_indx:end_indx, y, x]

        kill_levels = self.variety.kill_levels
        kill_temps = self.variety.kill_temps.attr_list   
        min_stage_temp = min(kill_temps[0][-1], N.nanmin(mint))
        stage_temps = [ kills for kills in kill_temps]
        stage_temps.insert(0, (min_stage_temp, min_stage_temp, min_stage_temp))

        var_config = fromConfig('crops.apple.variety')
        colors = var_config.maps.options.stage.colors
        stage_names = tuple(var_config.stage_name_map.attr_values)
        plot_options = var_config.plots.options.kill_at_stage
        mint_options = plot_options.mint.attrs
        stage_options = plot_options.stage.attrs

        # draw a plot for each kill level
        for indx, kill_level in enumerate(kill_levels):
            # initialize figure and GCA
            figure = pyplot.figure(figsize=(8,6),dpi=100)
            axis = figure.gca()

            # set X axis date limits before we draw anything
            pyplot.xlim(days[0],days[-1])

            # draw kill boundary for this kill level at each stage
            for stage, stage_kill in enumerate(kill_temps, start=1):
                kill_temp = stage_kill[indx]
                axis.plot([days[0],days[-1]], [kill_temp,kill_temp],
                           c=colors[stage], label=stage_names[stage])
   
            # draw a line showing the stage at each day
            stages = [stage_temps[stage][indx] for stage in stage_at_node]
            pyplot.plot(days, stages, **stage_options)
            # draw the mint overlay
            pyplot.plot(days, mint, **mint_options)

            # add X,Y axis labels, background grid and legend
            #axis.xaxis.set_major_locator = date_locator
            axis.xaxis.set_major_formatter(dateFormatter)
            #figure.autofmt_xdate()
            axis.set_ylabel('Temperature', fontsize=12)
            axis.grid(True)
            pyplot.legend(prop={'size':6}, fancybox=True, framealpha=0.5)

            # draw the axes
            pyplot.axes(axis)

            # post title
            kill_percent = '%d%%' % kill_level
            title = title_template % kill_percent
            pyplot.suptitle(title, fontsize=12)

            # save to output file
            output_filepath = filepath_template % kill_percent
            figure.savefig(output_filepath)
            print 'plot saved to', output_filepath

