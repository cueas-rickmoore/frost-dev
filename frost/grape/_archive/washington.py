
import os, sys

import numpy as N

from frost.functions import fromConfig

# This code is based on: "Modeling Dormant Bud Cold Hardiness and Budbreak
# in 23 Vitis Genotypes Reveals Variation by Region of Origin"
# John C. Ferguson, Michelle M. Moyer, Lynn J. Mills, Gerrit Hoogenboom
# and Markus Keller
# Am. J. Enol. Vitic December 2013 ajev.2013.13098
# doi: 10.5344/ajev.2013.13098


def GDD_Calc(tmean_in,thres):   
        if tmean_in>thres:
                GDD=tmean_in-thres
        else:
                GDD = 0 
        return GDD

def Chill_DD_Calc(tmean_in,thres):

        if tmean_in<thres:
                Chill_DD = tmean_in-thres
        else:
                Chill_DD = 0
        return Chill_DD


##GDD PHENOLOGY ACCUMULATIONS

Hc_init = -10.3
Hc_min = -1.2
Hc_max = -25.1

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


Hc_range = Hc_min - Hc_max
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

# Hc_min was taken as the hardiness of green growing tissues (4th-leaf stage):
# -1.2°C for all V. vinifera cultivars and -2.5°C for V. labruscana cultivars

# grapevine bud cold hardiness (Hc) used in model
#              Vitis           Vitis
# Cultivar   vinifera      lambruscana
# Woolly bud   -3.4          -9.2
# Budbreak     -2.2          -6.4
# 1st leaf     -2.0          -4.5
# 2nd leaf     -1.7          -3.9
# 4th leaf     -1.2          -2.5


#infile = 'hardiness_temp_input.txt'

#ifile = N.genfromtxt(infile,dtype=None,delimiter="\t")

#day_mon = ifile['f0']
#yr_strt_end = ifile['f1']
#jul_date = ifile['f2']
#location = ifile['f3']
#t_mean = ifile['f4']
#t_max = ifile['f5']
#t_min = ifile['f6']
#obs_hc = ifile['f7']

year = 2014
start_date = (year-1,10,01)   ### need to start chill computation in previous October   
end_date = (year,06,30)
        
start_date_str = str(start_date[0])+'-%02d'%(start_date[1])+'-%02d'%(start_date[2])
        
end_date_str= str(end_date[0])+'-%02d'%(end_date[1])+'-%02d'%(end_date[2])
        
input_dict = {"sid":"304174","sdate":start_date_str,"edate":end_date_str,"elems":"maxt,mint,avgt","meta":"ll"}  
params = urllib.urlencode({'params':json.dumps(input_dict)})
req = urllib2.Request('http://data.rcc-acis.org/StnData', params, {'Accept':'application/json'})
response = urllib2.urlopen(req)
data_vals = json.loads(response.read())

        
data_array = N.array(data_vals['data'])
t_max=data_array[:,1]
t_min=data_array[:,2]
t_mean=data_array[:,3]  

t_max[t_max.astype(str)=='M']=N.nan
t_min[t_min.astype(str)=='M']=N.nan     
t_mean[t_mean.astype(str)=='M']=N.nan   
        
t_max=t_max.astype(float)
t_min=t_min.astype(float)
t_mean=t_mean.astype(float)

t_max[t_max<-100] = N.nan
t_min[t_min<-100] = N.nan
t_mean[t_mean<-100] = N.nan

t_max=(t_max-32.)*5./9.
t_min=(t_min-32.)*5./9.
t_mean=(t_mean-32.)*5./9.

date=data_array[:,0]
date = date.astype(str)

deacclim = []
acclim = []
model_Hc = []

DD_chilling_sum = [0,]
DD_10_sum = [0,]
DD_heating_sum = []

for day in range(len(t_mean)):

        DD_heating = GDD_Calc(t_mean[day],T_thres_dorm[period])

        DD_chilling = Chill_DD_Calc(t_mean[day],T_thres_dorm[period])
        DD_10 = Chill_DD_Calc(t_mean[day],10.)

        
        deacclim.append(DD_heating * deacclim_rate[period] * (1 - ((model_Hc_yest - Hc_max) / Hc_range)**theta))
        if DD_chilling_sum[day] == 0:deacclim[-1] = 0

        acclim.append(DD_chilling * acclim_rate[period] * (1 - (Hc_min - model_Hc_yest) / Hc_range))

        model_Hc.append(model_Hc_yest + (acclim[-1] + deacclim[-1]))

        if model_Hc[-1] <= Hc_max: model_Hc[-1] = Hc_max
        if model_Hc[-1] > Hc_min: model_Hc[-1] = Hc_min

        DD_chilling_sum.append(DD_chilling_sum[-1]+DD_chilling)
        DD_10_sum.append(DD_10_sum[-1]+DD_10)

        if period == 1:
                DD_heating_sum.append(DD_heating_sum[-1]+DD_heating)
        else:
                DD_heating_sum.append(0)

        if DD_10_sum[day] <= dorm_bound: period = 1

        if Hc_min == -1.2:    ## assume vinifera with budbreak at -2.2
                if model_Hc_yest < -2.2:
                        if model_Hc >= -2.2:
                                budbreak= date[day]
                                end_hardy= model_Hc[day]

        if Hc_min == -2.5:    ## assume labrusca with budbreak at -6.4
                if model_Hc_yest < -6.4:
                        if model_Hc >= -6.4:
                                budbreak= jul_date[day]      
                                end_hardy= model_Hc[day]
        
        model_Hc_yest=model_Hc[day]

        
duh


GDD_CH45 = N.where(CH_45_sum>accum_thresh_45,GDD,0)
