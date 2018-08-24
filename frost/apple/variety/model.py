
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from atmosci.utils.timeutils import asDatetimeDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AppleVarietyModelMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # properties derived from variety configuration
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _kill_levels_(self):
        return self.variety.kill_levels
    kill_levels = property(_kill_levels_)

    def _kill_temps_(self):
        return tuple(self.variety.kill_temps.attrvalues())
    kill_temps = property(_kill_temps_)

    def _min_chill_units_(self):
        return self.variety.min_chill_units
    min_chill_units = property(_min_chill_units_)

    def _phenology_(self):
        return tuple(self.variety.phenology.items())
    phenology = property(_phenology_)

    def _stages_(self):
        return self.variety.phenology._stages_()
    stages = property(_stages_)

    def _stage_thresholds_(self):
        return tuple(self.variety.phenology.attrvalues())
    stage_thresholds = property(_stage_thresholds_)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Growing degree day accumulation
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulateGdd(self, model_name, lo_gdd_th, hi_gdd_th, start_date,
                            accumulated_chill, daily_gdd):
        # need GDD accumulation and chill mask from previous day
        prev_day = start_date - ONE_DAY

        # start with chill mask from the previous day ... a mask is necessary
        # so that GDD accumulation will continue even after chill hours begin
        # to decline in later months of the season
        prev_mask =\
        self.getChillMask(model_name, lo_gdd_th, hi_gdd_th, prev_day)

        # allow accumulation wherever chill is above 
        # minimum chill hour threshold for variety
        above_min_chill = N.where(accumulated_chill >= self.min_chill_units)
        # chill accumulation is below min chill hour threshold at all nodes
        if len(above_min_chill[0]) == 0:
            return N.zeros_like(daily_gdd), N.zeros(daily_gdd.shape, dtype=bool)

        # chill accumulation is cumulative, so we need accumulated GDD for
        # the previous date
        if asDatetimeDate(start_date) > self.start_date:
            prev_gdd = self.getGdd(model_name, lo_gdd_th, hi_gdd_th, prev_day)
            prev_gdd = prev_gdd.astype(daily_gdd.dtype)
        else:
            prev_gdd = N.zeros_like(prev_mask.shape, dtype=daily_gdd.dtype)

        # accumulate GDD for this variety/model combination 
        accumulated_gdd = N.zeros_like(daily_gdd)
        if daily_gdd.ndim == 2:
            # adjust previous day's mask to include any additional nodes where
            # minimum chill units have been reached on the current date
            prev_mask[above_min_chill] = True
            indexes = N.where(prev_mask == True)
            # update accumulated GDD array with valid node from daily_gdd
            accumulated_gdd[indexes] = daily_gdd[indexes]
            # add previous accumulation 
            accumulated_gdd += prev_gdd

            return accumulated_gdd, prev_mask

        elif daily_gdd.ndim == 3:
            # create a 3D mask from the previous day's mask
            chill_mask = N.array([ prev_mask for i in range(daily_gdd.shape[0])],
                                   dtype=int)
            # adjust mask to include any additional dates/nodes where
            # minimum chill units have been reached
            chill_mask[above_min_chill] = True
            indexes = N.where(chill_mask == True)
            # insert input daily GDD only where new mask applies
            accumulated_gdd[indexes] = daily_gdd[indexes]
            # add the previous day's GDD accumlation to the first
            # day in the new accumulation
            accumulated_gdd[0] = prev_gdd + daily_gdd[0]
            # calculated the cumulative total GDD accumulated
            accumulated_gdd = N.cumsum(accumulated_gdd, axis=0)

            return accumulated_gdd, chill_mask

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Kill probability estimation
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateKill(self, stage_grid, mint, verbose=False):
        kill = N.zeros(mint.shape, dtype=int)
        kill[N.where(N.isnan(mint))] = -32768
        kill_probability = self.variety.kill_levels
        var_kill_temps = list(self.variety.kill_temps.attr_values)

        # loop thru each stage
        for stage, kill_temps_at_stage in enumerate(var_kill_temps, start=1):
            # loop thru kill temp at each level of kill for this stage
            for indx, kill_temp in enumerate(kill_temps_at_stage):
                # test for nodes where kill could occur
                indexes = N.where((stage_grid == stage) & (mint <= kill_temp))
                if verbose:
                    print '\n', stage, kill_probability[indx], len(indexes[0]), 'indexes'
                    print indexes

                # assign probability to each node where kill is possible
                if len(indexes[0]) > 0:
                    kill[indexes] = kill_probability[indx]

        return kill

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Phenological stage 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gddToStages(self, accumulated_gdd, verbose=False):
        """ determine phenological stage from accumulated GDD
        """
        thresholds = self.stage_thresholds
        # assume dormant stage
        stages = N.zeros(accumulated_gdd.shape, dtype=int)
        for indx, threshold in enumerate(thresholds, start=1):
            indexes = N.where(accumulated_gdd >= threshold)
            if verbose: print 'stage', indx, threshold, len(indexes[0])
            if len(indexes[0]) > 0: stages[indexes] = indx
        return stages

