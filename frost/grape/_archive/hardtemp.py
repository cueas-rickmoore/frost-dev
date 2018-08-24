
import os, sys

import numpy as N

from frost.functions import fromConfig

# This code is based on: "Modeling Dormant Bud Cold Hardiness and Budbreak
# in 23 Vitis Genotypes Reveals Variation by Region of Origin"
# John C. Ferguson, Michelle M. Moyer, Lynn J. Mills, Gerrit Hoogenboom
# and Markus Keller
# Am. J. Enol. Vitic December 2013 ajev.2013.13098
# doi: 10.5344/ajev.2013.13098


##GDD PHENOLOGY ACCUMULATIONS

Hc_init = -10.3
hard_min = -1.2
hard_max = -25.1

T_thres_dorm = [13.0,5.0]
deacclim_rate = [0.08,0.10]

theta = 7.
acclim_rate = [0.12,0.10]

dorm_bound = -700.


# Cold hardiness (Hc) ... the ability to tolerate freezing temperatures
# Hc is a dynamic trait that is acquired in response to shortening photoperiod
# and declining temperature in late fall or early winter.
#
# hardiness:init -> the Hc of endodormant buds in late summer or early fall
# after the shoots have formed brown periderm but before the subsequent,
# temperature-driven cold acclimation process in late fall and early winter.
#
# hc:min -> the least cold-hardy condition or minimum hardiness allowable
# set to the hardiness of green growing tissues (4th-leaf stage): -1.2°C
# for all V. vinifera cultivars and -2.5°C for V. labruscana cultivars

# theta -> exponent that varies by genotype. Permits the model to better
# capture the accelerated deacclimation observed just before budbreak.

# dormancy_boundary -> chilling degree days (DDc) required for dormancy
# release. Defines the transition of buds from endo- to ecodormancy.

# Transition from paradormancy to endodormancy is a prerequisite for the
# subsequent acquisition of full Hc. Temperature-driven acclimation /
# deacclimation cycles continue until the changes # leading up to budbreak
# render the deacclimation process irreversible. 

# measures low-temperature exotherms (LTE) and high-temperature exotherms
# (HTE). An LTE corresponds to the (lethal) temperature at which supercooled
# intracellular water freezes in # an organ. The Hc is expressed as LT50,
# which is the lethal temperature for 50% of buds tested. An HTE indicates
# the freezing of extracellular water, which occurs at higher temperatures
# and is usually not lethal, although it induces cellular dehydration.


hard_range = hard_min - hard_max
model_Hc_yest = Hc_init

period = 0

# This dynamic thermal-time model predicts bud hardiness using genotype-specific coefficients
# (e.g., minimum and maximum hardiness, acclimation and deacclimation rates, ecodormancy boundary,
# etc.), with daily mean temperature as the single input variable.
# endo-dormancy : plant will not grow even under good, warm, growing conditions.
# eco-dormancy : plant is ready to grow but environmental conditions aren't right, usually too cold.

# Model has several limitations, including the low number of genotypes that were parameterized
# and relatively poor predictive performance during late winter/early spring, when buds are
# deacclimating. 

# hard_min was taken as the hardiness of green growing tissues (4th-leaf stage):
# -1.2°C for all V. vinifera cultivars and -2.5°C for V. labruscana cultivars

# grapevine bud cold hardiness (Hc) used in model
#              Vitis           Vitis
# Cultivar   vinifera      lambruscana
# Woolly bud   -3.4          -9.2
# Budbreak     -2.2          -6.4
# 1st leaf     -2.0          -4.5
# 2nd leaf     -1.7          -3.9
# 4th leaf     -1.2          -2.5



year = 2014
start_date = (year-1,10,01)   ### need to start chill computation in previous October   
end_date = (year,06,30)
        

t_max=(t_max-32.)*5./9.
t_min=(t_min-32.)*5./9.
t_mean=(t_mean-32.)*5./9.

date=data_array[:,0]
date = date.astype(str)

deacclim = []
acclim = []
model_Hc = []

chill_grid_sum = [0,]
DD_10_sum = [0,]
gdd_grid_sum = []





from frost.functions import fromConfig

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HardinessTemperatureModel(object):

    def __init__(self, variety_name):
        variety = fromConfig('crops.grape.variety.%s.self' % variety.name)
        # cache the configuration so we don't do config lookups for every call
        self.acclimation = variety.acclimation
        self.deacclimation = variety.deacclimation
        self.ecodormancy_threshold = variety.ecodormancy_threshold
        self.hardiness = variety.hardiness
        self.temp_thresholds = variety.temp_thresholds
        self.theta = variety.theta

        parent = variety.parent
        self.dormancy_states = parent.dormancy_states
        self.dormancyIndexFromState = parent.dormancyIndexFromState
        self.dormancyStateFromIndex = parent.dormancyStateFromIndex

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dormancyState(self, chill_10_grid):
        """ determine current dormancy state from 10 degree GDD

        endo-dormancy : will not grow even under warm, favorable growing
                        conditions.
        eco-dormancy : ready to grow but environmental conditions are
                       not favorable, usually too cold.
        """
        endo = self.dormancyIndexFromState('endo')
        eco = self.dormancyIndexFromState('eco')
        # initialize a new, empty dormancy grid and set to missing
        dormancy_grid = N.empty(dd_10_grid.shape, dtype='<i2')
        dormancy_grid.fill(-999)

        # eco-dormancy when GDD is LE threshold
        # YES it does seem backwards but it is the way the model works
        indexes = N.where(chill_10_grid <= self.ecodormancy_threshold)
        if len(indexes[0]) > 0: dormancy_grid[indexes] = eco
        # endo-dormancy when GDD is GT threshold
        indexes = N.where(chill_10_grid > self.ecodormancy_threshold)
        if len(indexes[0]) > 0: dormancy_grid[indexes] = endo

        return dormancy_grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dormancyChill(self, avgt_grid, dormancy_state_grid):
        """ calclate GDD based on current dormancy state at each node
        """
        chill_grid = N.zeros(avgt_grid.shape, dtype=float)

        for state in self.dormancy_states:
            threshold = self.temp_thresholds[state]
            ds_index = self.dormancyIndexFromState(state)
            indexes = N.where( (dormancy_state_grid == ds_index) &
                               (avgt_grid < threshold) )
            if len(indexes[0]) > 0:
                chill_grid[indexes] = avgt_grid[indexes] - threshold

        return chill_grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dormancyGDD(self, avgt_grid, dormancy_state_grid):
        """ calclate GDD based on current dormancy state at each node
        and the temperature threshold for that dormancy state
        """
        gdd_grid = N.zeros(avgt_grid.shape, dtype=float)

        for state in self.dormancy_states:
            threshold = self.temp_thresholds[state]
            ds_index = self.dormancyIndexFromState(state)
            indexes = N.where( (dormancy_state_grid == ds_index) &
                               (avgt_grid > threshold) )
            if len(indexes[0]) > 0:
                gdd_grid[indexes] = avgt_grid[indexes] - threshold

        return gdd_grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateChill(self, avgt_grid, threshold_tmep):
        """ estimate Growing Degree Days based on a single temperature
        threshold
        """
        chill_grid = N.zeros(avgt_grid.shape, dtype=float)
        indexes = N.where(avgt_grid < threshold_temp)
        if len(indexes[0]) > 0:
            chill_grid[indexes] = avgt_grid[indexes] - threshold_temp
        return chill_grid

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateHardiness(self, avgt_grid, prev_hardiness=None):
        """ Run all steps in the model in their proper sequence
        """
        # Transition of buds from endo- to eco-dormancy, is calculated using
        # a threshold temperature common to all genotypes (10°C). makes the
        # fixed Tth,c used for chilling requirements independent of the
        # estimated Tth used for acclimation and deacclimation
        chill_10_grid = self.estimateChill(avgt_grid, 10.)
        dormancy_state_grid = self.dormancyState(chill_10_grid)

        # Calculate dormancy-dependent chill and growing degree days
        chill_grid = self.dormancyChill(avgt_grid, dormancy_state_grid)
        gdd_grid = self.dormancyGDD(avgt_grid, dormancy_state_grid)

        if gdd_grid.ndim == 2:
            hardiness, acclimation, deacclimation =\
            self.hardiness(gdd_grid, chill_grid, dormancy_state_grid,
                           prev_hardiness)
        else:
            num_days = gdd.shape[0]
            acclimation = N.zeros(gdd_grid.shape)
            deacclimation = N.zeros(gdd_grid.shape)
            hardiness = N.zeros(gdd_grid.shape)

            for day in range(num_days):
                hardy, acclim, deacclim =\
                self.hardiness(gdd_grid, chill_grid, dormancy_state_grid,
                               prev_hardiness)
                acclimation[day] = acclim
                deacclimation[day] = deacclim
                hardiness[day] = hardy
                prev_hardiness = hardy

        return (chill_grid, chill_10_grid, gdd_grid, hardiness, acclimation,
                deacclimation, dormancy_state_grid)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hardiness(self, gdd_grid, chill_grid, dormancy_state_grid,
                        prev_hardiness=None):
        hard_max = self.hardiness.max
        hard_min = self.hardiness.min 
        hard_range = hard_min - hard_max 

        acclimation = N.zeros(gdd_grid.shape, dtype=float)
        acclim_factor = 1 - ((prev_hardiness - hard_max) / hard_range)**theta
        
        deacclimation = N.zeros(gdd_grid.shape, dtype=float)
        deacclim_factor = 1 - ((hard_min - prev_hardiness) / hard_range)

        for state in self.dormancy_states:
            acc_rate = self.acclimation[state]
            deacc_rate = self.deacclimation[state]

            ds_index = self.dormancyIndexFromState(state)
            indexes = N.where(dormancy_state_grid == ds_index)
            if len(indexes[0]) > 0:
                deacclim[indexes] = gdd_grid[indexes] * deacclim_rate * deacclim_factor
                acclim[indexes] = chill_grid[indexes] * acclim_rate[state] * acclim_factor

                if chill_grid_sum[day] == 0: deacclim[-1] = 0


        model_Hc.append(model_Hc_yest + (acclim[-1] + deacclim[-1]))

        if model_Hc[-1] <= hard_max: model_Hc[-1] = hard_max
        if model_Hc[-1] > hard_min: model_Hc[-1] = hard_min

        chill_grid_sum.append(chill_grid_sum[-1]+chill_grid)
        DD_10_sum.append(DD_10_sum[-1]+DD_10)

        if period == 1:
                gdd_grid_sum.append(gdd_grid_sum[-1]+gdd_grid)
        else:
                gdd_grid_sum.append(0)

        if DD_10_sum[day] <= dorm_bound: period = 1
        model_Hc_yest=model_Hc[day]

    def estimateBudBreak(self, date, hardiness):
        if hard_min == -1.2:    ## assume vinifera with budbreak at -2.2
                if model_Hc_yest < -2.2:
                        if model_Hc >= -2.2:
                                budbreak = date
                                end_hardy = hardiness[day]

        if hard_min == -2.5:    ## assume labrusca with budbreak at -6.4
                if model_Hc_yest < -6.4:
                        if model_Hc >= -6.4:
                                budbreak = date
                                end_hardy = hardiness[day]
        

        
duh


GDD_CH45 = N.where(CH_45_sum>accum_thresh_45,GDD,0)
