""" Python implementation of the grape hardiness model as presented in :

Ferguson J.C., M.M. Moyer, L.J. Mills, G. Hoogenboom and M. Keller (2013).
Modeling dormant bud cold hardiness and budbreak in 23 Vitis genotypes
reveals variation by region of origin. Am. J. Enol. Vitic. Research Article
dated December 10, 2013
doi: 10.5344/ajev.2013.13098
"""


import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

BAD_DIMENSION = '"%s" must be either a 2D or 3D numpy array.'
INCOMPATIBLE = 'Values of "%s" and "%s" arguments have incompatible dimensions'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GrapeModelMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Chill estimation
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulateChill(self, daily_chill, prev_chill=None):
        """ Create an accumlated chill grid from a daily chill grid and a
        grid containg chill for the previous day

        Arguments
        --------------------------------------------------------------------
        daily_chill : float, 2D or 3D grid - daily chill values
                      if 3D, time must be first dimension
        prev_chill  : float, 2D grid - accumulated chill on previous day

        Returns:
        --------------------------------------------------------------------
        float, grid containing cumulative chill. Dimensions will be the same
        as those of the daily_chill argument.
        """
        if prev_chill is None: return N.copy(daily_chill)
        elif prev_chill.ndim == 2: base_chill = prev_chill
        elif prev_chill.ndim == 3: base_chill = prev_chill[-1]
        else: # can only handle 2D and 3D arrays
            raise ValueError, BAD_DIMENSION % 'prev_chill'

        # 2D daily chill grid
        if daily_chill.ndim == 2: 
            return base_chill + daily_chill
        # 3D daily chill grid
        elif daily_chill.ndim == 3:
            accumulated = N.copy(daily_chill)
            accumulated[0] = base_chill + accumulated[0]
            return N.cumsum(accumulated, axis=0)
        else: # can only handle 2D and 3D arrays
            raise ValueError, BAD_DIMENSION % 'daily_chill'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dormancyBasedChill(self, average_temp, dormancy_stage):
        """ Calculate chill based on current dormancy stage at each node

        Arguments
        --------------------------------------------------------------------
        average_temp   : float, 2D or 3D grid - average temperatures at
                         each node. If 3D, time must be first dimension.
                         Temperatures MUST be in degrees Celsius.
        dormancy_stage : int, 2D or 3D grid - estimated dormancy stage
                         on previous day(s).
        Dimensions of average_temp and dormancy_stage grids must match.
        If grids are 3D, first dimension must be number of days.

        Returns:
        --------------------------------------------------------------------
        float, grid containing estimated chill at each node. Dimensions will
        match those of the average_temp grid.
        """
        chill_grid = N.zeros(average_temp.shape, dtype=float)
        chill_grid[N.where(N.isnan(average_temp))] = N.nan

        for stage in self.dormancy_stages:
            threshold = self.stage_thresholds[stage]
            ds_index = self.dormancyIndexFromStage(stage)
            indexes = N.where( (dormancy_stage == ds_index) &
                               (average_temp < threshold) )
            if len(indexes[0]) > 0:
                chill_grid[indexes] = average_temp[indexes] - threshold

        return chill_grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateChill(self, average_temp, threshold_temp):
        """ Estimate chill based on a single temperature threshold

        Arguments
        --------------------------------------------------------------------
        average_temp   : float, 2D or 3D grid - average temperatures at
                         each node. If 3D, time must be first dimension.
                         Temperatures MUST be in degrees Celsius.
                         If 3D, first dimension must be number of days.
        threshold_temp : float, scalar - temperature below which chilling
                         occurs.

        Returns:
        --------------------------------------------------------------------
        float, grid containg estimated chill at each node. Dimensions will
        match those of the average_temp argument.
        """
        chill_grid = N.zeros(average_temp.shape, dtype=float)
        chill_grid[N.where(N.isnan(average_temp))] = N.nan

        indexes = N.where(average_temp < threshold_temp)
        if len(indexes[0]) > 0:
            chill_grid[indexes] = average_temp[indexes] - threshold_temp

        return chill_grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Dormancy stage estimate methods
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dormancyStageFromChill(self, common_chill):
        """ Determine current dormancy stage from 10 degree GDD

        endo-dormancy : will not grow even under warm, favorable growing
                        conditions.
        eco-dormancy  : ready to grow but environmental conditions are
                        not favorable, usually too cold.
        """
        endo_indx = self.dormancyIndexFromStage('endo')
        eco_indx = self.dormancyIndexFromStage('eco')
        threshold = self.ecodormancy_threshold
        # initialize a new, empty dormancy grid and set to missing
        dormancy_grid = N.empty(common_chill.shape, dtype='<i2')
        dormancy_grid.fill(-32768)

        # eco-dormancy when GDD is LE threshold
        # YES it does seem backwards but it is the way the model works
        indexes = N.where(common_chill <= threshold)
        if len(indexes[0]) > 0: dormancy_grid[indexes] = eco_indx
        # endo-dormancy when GDD is GT threshold
        indexes = N.where(common_chill > threshold)
        if len(indexes[0]) > 0: dormancy_grid[indexes] = endo_indx

        return dormancy_grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Growing degree day estimation
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulateGDD(self, daily_gdd, dormancy_stage, prev_gdd=None):
        """ Create an accumlated GDD grid from a daily GDD grid, a dormancy
        stage grid and a grid containg GDD for the previous day

        Arguments
        --------------------------------------------------------------------
        daily_gdd      : float, 2D or 3D grid - daily gdd values
                         if 3D, time must be first dimension
        dormancy_stage : int, 2D or 3D grid - estimated dormancy stage
                         on previous day(s).
        prev_gdd       : float, 2D - accumulated gdd for day previous to
                         first day in daly_gdd and dormancy_stage grids.

        Dimensions of average_temp and dormancy_stage grids must match.
        If grids are 3D, first dimension must be number of days.

        Returns:
        --------------------------------------------------------------------
        float, grid containing cumulative gdd. Dimensions will be the same
        as those of the daily_gdd argument.
        """
        accumulated = N.copy(daily_gdd)
        # accumulation is possible only where plants are in ecodormancy stage
        eco_indx = self.dormancyIndexFromStage('eco')
        accumulated[N.where(dormancy_stage != eco_indx)] = 0.
        # no previous GDD accumlation, return daily_gdd adjusted for eco index
        if prev_gdd is None: return accumulated
        elif prev_gdd.ndim == 2: _prev_gdd_ = prev_gdd
        elif prev_gdd.ndim == 3: _prev_gdd_ = prev_gdd[-1]
        else: # only handles 2D and 3D arrays
            raise ValueError, BAD_DIMENSION % 'prev_gdd'

        # 2D accumulation grid
        if accumulated.ndim == 2: return accumulated + _prev_gdd_
        # 3D accumulation grid
        elif accumulated.ndim == 3:
            accumulated[0] = accumulated[0] + _prev_gdd_
            return N.cumsum(accumulated, axis=0)
        else: # only handles 2D and 3D arrays
            raise ValueError, BAD_DIMENSION % 'daily_gdd'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dormancyBasedGDD(self, average_temp, dormancy_stage):
        """ Calclate GDD based on current dormancy stage at each node

        Arguments
        --------------------------------------------------------------------
        average_temp   : float, 2D or 3D grid - average temperatures at
                         each node. If 3D, time must be first dimension.
                         Temperatures MUST be in degrees Celsius.
        dormancy_stage : int, 2D or 3D grid - estimated dormancy stage
                         on previous day(s).

        Dimensions of average_temp and dormancy_stage grids must match.
        If grids are 3D, first dimension must be number of days.

        Returns:
        --------------------------------------------------------------------
        float, grid containg estimated GDD at each node. Dimensions will
        match those of the average_temp grid.
        """
        gdd_grid = N.zeros(average_temp.shape, dtype=float)

        for stage in self.dormancy_stages:
            threshold = self.stage_thresholds[stage]
            ds_index = self.dormancyIndexFromStage(stage)
            indexes = N.where( (dormancy_stage == ds_index) &
                               (average_temp > threshold) )
            if len(indexes[0]) > 0:
                gdd_grid[indexes] = average_temp[indexes] - threshold

        gdd_grid[N.where(N.isnan(average_temp))] = N.nan
        return gdd_grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Hardiness estimation method
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateHardiness(self, dormancy_stage, prev_daily_chill,
                                prev_accum_chill, prev_daily_gdd, 
                                prev_hardiness=None):
        """Estimate hardiness temperature a day or sequence of days.
        Hardiness temperature for each day is based on dormancy stage
        plus chill and GDD from previous days.

        Required Arguments
        --------------------------------------------------------------------
        dormancy_stage   : int, grid - estimated dormancy stage
        prev_daily_chill : float, grid - daily dormancy-based chill 
        prev_accum_chill : float, grid - accumulated dormancy-based chill 
        prev_daily_gdd   : float, grid - daily dormancy-based GDD

        Grids for dormancy stage, chill and gdd must all have the same
        dimensions. If 2D grids are passed, they must contain data for
        the previous day and a single day's output grids will be
        estimated.

        If 3D grids are used, the first dimension must be number of days.
        Day 0 must be the day prior to the first day to be estimated and
        the last day will be the day prior to the last day to be estimated.
        For example: if the dates to be estimated span 1/1/2012 thru 1/31/2012,
        the 3D previous day grids must span 12/31/2011 thru 1/30/2012.

        "Optional" Arguments
        --------------------------------------------------------------------
        prev_hardiness : float, 2D grid - estimated hardiness for the day 
                         previous to the first day to be estimated. If None,
                         an array will be created using the appropriate
                         initial hardiness for the variety being managed.
                         WARNING: using None will only result in an
                         accurate estimate on the very first day of the
                         season. Therefore, prev_hardiness is only
                         optional for hardiness estimates on the first
                         day of the season.

        Returns
        --------------------------------------------------------------------
        float, grid : estimated acclimation factors
        float, grid : estimated deacclimation factors
        float, grid : estimated hardiness temperatures

        Dimensions of the output grids will the same as those of the input
        temperature, dormancy, and chill input grids.
        """
        if dormancy_stage.ndim == 2:
            if prev_daily_chill.ndim != 2:
                raise ValueError, INCOMPATIBLE % ('dormancy_stage','prev_daily_chill')
            if prev_accum_chill.ndim != 2:
                raise ValueError, INCOMPATIBLE % ('dormancy_stage','prev_accum_chill')
            if prev_daily_gdd.ndim != 2:
                raise ValueError, INCOMPATIBLE % ('dormancy_stage','prev_daily_gdd')
        elif dormancy_stage.ndim == 3:
            if prev_daily_chill.ndim != 3:
                raise ValueError, INCOMPATIBLE % ('dormancy_stage','prev_daily_chill')
            if prev_accum_chill.ndim != 3:
                raise ValueError, INCOMPATIBLE % ('dormancy_stage','prev_accum_chill')
            if prev_daily_gdd.ndim != 3:
                raise ValueError, INCOMPATIBLE % ('dormancy_stage','prev_daily_gdd')
        else: # only handles 2D and 3D arrays
            raise ValueError, BAD_DIMENSION % 'dormancy_stage'

        variety = self.variety

        # previous haridness temperature may be unknown on first day of season
        if prev_hardiness is None:
            if prev_daily_chill.ndim == 2:
                prev_hardiness = N.empty(prev_daily_chill.shape)
                nan_indexes = N.where(N.isnan(prev_daily_chill))
            else:
                prev_hardiness = N.empty(prev_daily_chill.shape[1:])
                nan_indexes = N.where(N.isnan(prev_daily_chill[0]))
            # fill empty grid with the appropriate initial hardiness temp
            prev_hardiness.fill(variety.hardiness.init)
            prev_hardiness[nan_indexes] = N.nan

        acclimation_rate = variety.acclimation_rate.attributes
        deacclimation_rate = variety.deacclimation_rate.attributes
        hard_max = variety.hardiness.max
        hard_min = variety.hardiness.min 
        theta = variety.theta

        if dormancy_stage.ndim == 2: # process 2D input arrays
            acclimation, deacclimation, hardiness = \
            self.estimateHardinessForDay(dormancy_stage, prev_daily_chill,
                 prev_accum_chill, prev_daily_gdd, prev_hardiness, hard_min, 
                 hard_max, theta, acclimation_rate, deacclimation_rate)

        else: # process 3D input arrays
            _prev_hardiness_ = prev_hardiness
            # create 3D grids to hold daily estimates
            acclimation = N.zeros(prev_daily_chill.shape, dtype=float)
            deacclimation = N.zeros(prev_daily_chill.shape, dtype=float)
            hardiness = N.zeros(prev_daily_chill.shape, dtype=float)

            # loop through days ... num days == dormancy_stage.shape[0]
            for day in range(dormancy_stage.shape[0]):
                acclimation_day, deacclimation_day, _hardiness_ = \
                self.estimateHardinessForDay(dormancy_stage[day],
                     prev_daily_chill[day], prev_accum_chill[day], 
                     prev_daily_gdd[day], _prev_hardiness_, hard_min,
                     hard_max, theta, acclimation_rate, deacclimation_rate)
                acclimation[day] = acclimation_day
                deacclimation[day] = deacclimation_day
                hardiness[day] = _hardiness_
                _prev_hardiness_ = _hardiness_

        return hardiness, acclimation, deacclimation

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateHardinessForDay(self, dormancy_stage, prev_day_chill,
                                prev_accum_chill, prev_day_gdd, prev_hardiness,
                                hard_min, hard_max, theta, acclimation_rate,
                                deacclimation_rate):
        """Estimate hardiness temperature a single day.

        Required Arguments
        --------------------------------------------------------------------
        dormancy_stage   : int, 2D grid - estimated dormancy stage
        prev_daily_chill : float, 2D grid - daily dormancy-based chill 
        prev_accum_chill : float, 2D grid - accumulated dormancy-based chill 
        prev_daily_gdd   : float, 2D grid - daily dormancy-based GDD
        prev_hardiness   : float, 2D grid - estimated hardiness
        hard_max         : float, scalar - maximum hardiness for variety
        hard_min         : float, scalar - minimum hardiness for variety
        acclim_rate      : float, scalar - acclimation rate for variety
        deacclim_rate    : float, scalar - deacclimation rate for variety

        All input grids must all have the same dimensions and contain data
        for the day previous to the one being estimated.

        Returns
        --------------------------------------------------------------------
        float, 2D grid : estimated acclimation factors
        float, 2D grid : estimated deacclimation factors
        float, 2D grid : estimated hardiness temperatures

        Dimensions of the output grids will be the same as the input grids.
        """
        hard_range = hard_min - hard_max
        
        # initialize acclimation grids to zero
        acclimation = N.zeros(prev_day_chill.shape, dtype=float)
        deacclimation = N.zeros(prev_day_chill.shape, dtype=float)

        # acclimation factors used to calculate accilmation/deacclimation
        acclim_factor = 1 - ((hard_min - prev_hardiness) / hard_range)
        deacclim_factor = \
            1 - ((prev_hardiness - hard_max) / hard_range)**theta

        # acclimation/deacclimation rates vary according to dormacy stage
        for stage in self.dormancy_stages:
            ds_index = self.dormancyIndexFromStage(stage)

            # calculate acclimation at all nodes in current dormancy stage
            indexes = N.where(dormancy_stage == ds_index)

            if len(indexes[0]) > 0:
                acclim = acclim_factor[indexes] * acclimation_rate[stage]
                acclimation[indexes] = prev_day_chill[indexes] * acclim

            # deacclimation is only calculated for nodes where chill is
            # less than zero AND the node is in the current dormancy stage
            indexes = N.where( (dormancy_stage == ds_index) &
                               (prev_accum_chill < 0) )
            if len(indexes[0]) > 0:
                deacclim = deacclim_factor[indexes] * deacclimation_rate[stage]
                deacclimation[indexes] = prev_day_gdd[indexes] * deacclim

        # hardiness temperature is based on hardiness of previous day and
        # the net acclimation factor
        hardiness = prev_hardiness + (acclimation + deacclimation)

        # YEA, this next stuff looks bogus but the model uses negative
        # numbers for limits with "max" being a more negative number
        # than "min", so it works.
        # e.g for Concord grapes, hard_max = -29.5 and hard_min = -2.5 
        # ... go figure ???
        hardiness[hardiness <= hard_max] = hard_max
        hardiness[hardiness > hard_min] = hard_min

        # mask all nodes that were masked (N.nan) on input
        nan_indexes = N.where(N.isnan(prev_day_chill))
        acclimation[nan_indexes] = N.nan
        deacclimation[nan_indexes] = N.nan
        hardiness[nan_indexes] = N.nan

        return acclimation, deacclimation, hardiness

GrapeModelMethods = GrapeModelMixin
