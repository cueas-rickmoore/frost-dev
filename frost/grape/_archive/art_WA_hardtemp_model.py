import numpy as np
import math
def CH45_modelnp(temp_in):
	chill_out = np.array(temp_in.shape)
	chill_out=np.where((temp_in>0)&(temp_in<7.2),1,0)
	
	return chill_out
	
def CH45_model(temp_hr):
	if temp > 0 and temp < 7.2:
		chill_out = 1
	else:
		chill_out = 0
		
	return chill_out

def CHUtah_model(temp_in):

	if temp <= 1.4:
		chill_out = 0
	elif temp >1.4 and temp <= 2.4:
		chill_out = 0.5
	elif temp > 2.4 and temp <=9.1:
		chill_out = 1
	elif temp >9.1 and temp <=12.4:
		chill_out = 0.5
	elif temp >12.4 and temp <=15.9:
		chill_out =0
	elif temp >15.9 and temp <=18.0:
		chill_out = -0.5
	elif temp >18.0:
		chill_out = -1	

def CHUtah_modelnp(temp_in):
#	chill_out = np.empty(temp_in.shape)
#	chill_out[:]=np.NaN
#	for dy in range(len(temp_in)):
#		for hr in range(len(temp_in[dy])):
#			if temp_in[dy][hr] <= 1.4:
#				chill_out[dy][hr] = 0.0
#			elif temp_in[dy][hr] >1.4 and temp_in[dy][hr] <= 2.4:
#				chill_out[dy][hr] = 0.5
#			elif temp_in[dy][hr] > 2.4 and temp_in[dy][hr] <=9.1:
#				chill_out[dy][hr] = 1.0
#			elif temp_in[dy][hr] >9.1 and temp_in[dy][hr] <=12.4:
#				chill_out[dy][hr] = 0.5
#			elif temp_in[dy][hr] >12.4 and temp_in[dy][hr] <=15.9:
#				chill_out[dy][hr] =0.0
#			elif temp_in[dy][hr] >15.9 and temp_in[dy][hr] <=18.0:
#				chill_out[dy][hr] = -0.5
#			elif temp_in[dy][hr] >18.0:
#				chill_out[dy][hr] = -1.0

	chill_lt14 = np.zeros(temp_in.shape)
	chill_14_24 = np.zeros(temp_in.shape)
	chill_24_91 = np.zeros(temp_in.shape)
	chill_91_124 = np.zeros(temp_in.shape)
	chill_124_159 = np.zeros(temp_in.shape)
	chill_159_18 = np.zeros(temp_in.shape)
	chill_gt18 = np.zeros(temp_in.shape)
	
	###chill_lt14 while by default just be zeros as will chill_124_159 since these temp ranges do not accumulate chill
	chill_14_24 = np.where((temp_in>1.4) & (temp_in<=2.4),0.5,0)
	chill_24_91 = np.where((temp_in>2.4) & (temp_in<=9.1),1.0,0)
	chill_91_124 = np.where((temp_in>9.1) & (temp_in<=12.4),0.5,0)
	chill_159_18 = np.where((temp_in>15.9) & (temp_in<=18.0),-0.5,0)
	chill_gt18 = np.where(temp_in>18,-1.0,0)
	
	chill_out = chill_14_24 + chill_24_91 + chill_91_124 + chill_159_18 + chill_gt18
	
	return chill_out

def CHDynamic_model(temp,intere_last,t):
	
	e0 = 4.15E+03
	e1 = 1.29E+04
	a0 = 1.40E+05
	a1 = 2.57E+18
	slp = 1.6
	tetmlt = 277
	aa = 5.43E-14    # a0/a1
	ee = 8.74E+03     # e1-e0	
	
	tempK = temp+273    #convert to K

	flmprt = slp*tetmlt*(tempK-tetmlt)/tempK
	
	sr = math.exp(flmprt)
	
	xi = sr/(1+sr)
	xs = aa*exp(ee/tempK)

	ak1 = a1*exp(-e1/tempK)
	
	
	if t ==0:   #This is a new start= 
		Inter_s = 0.00
	elif intere_last < 1:
		Inter_s = intere_last
	else:
		Inter_s = intere_last*(1-xi)
	
	Inter_e = xs - (xs-Inter_s)*exp(-ak1)
	
	if t ==0:   #This is a new start= 
		delt = 0.00
	elif Inter_e < 1:
		delt = 0
	else:
		delt = xi*Inter_e
		
	return delt,Inter_e
	
def CHDynamic_modelnp(temp_in):

	e0 = 4.15E+03
	e1 = 1.29E+04
	a0 = 1.40E+05
	a1 = 2.57E+18
	slp = 1.6
	tetmlt = 277.	
	aa = 5.43E-14    # a0/a1
	ee = 8.74E+03     # e1-e0

	delt=np.empty(temp_in.shape)
	delt[:]=np.NaN

	tempK = temp_in+273    #convert to K

	flmprt = slp*tetmlt*(tempK-tetmlt)/tempK

	sr = np.exp(flmprt)

	xi = sr/(1+sr)
	xs = aa*np.exp(ee/tempK)

	ak1 = a1*np.exp(-e1/tempK)

	for dy in range(len(temp_in)):
		for hr in range (len(temp_in[dy])):
			if dy == 0 and hr == 0:
				Inter_s=0.0
				intere_last = 0.7
			elif intere_last < 1:
				Inter_s = intere_last
				
			else:
				Inter_s = intere_last*(1-xi[dy][hr])			

			Inter_e = xs[dy][hr] - (xs[dy][hr]-Inter_s)*math.exp(-ak1[dy][hr])
			intere_last = Inter_e
		
			if dy==0 and hr == 0:
				delt[dy][hr]=0
			elif Inter_e < 1:
				delt[dy][hr]=0
			else:
				delt[dy][hr] = xi[dy][hr]*Inter_e

	return delt

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

## FINAL PROGRAM TO GENERATE GDD DATES LAST TEMP DATES FROST RISK FOR CURRENT AND FUTURE PERIODS BASED ON GCM OUTPUT. 
## RUNS USING THE OUTPUT FROM fit_harm_clim_mod2_ithaca.py
import csv
import scipy
from scipy import stats
import numpy as np
from numpy.linalg import inv, cholesky

import rpy2.rpy_classic as rpy
rpy.set_default_mode(rpy.NO_CONVERSION)

from mx import DateTime
import os, sys, urllib, urllib2

try :
	import json 
except ImportError:
	import simplejson as json


##GDD PHENOLOGY ACCUMULATIONS
Phenology_dict = {'stip':102,'gtip': 147,'ghalf':203,'cluster':258,'pink':325,'bloom':422,'petalfall':518}
last_cold_temps = [12,16,20,24,28,32]
kill_temps = {'stip':(11,5,0),'gtip':(19,10,4),'ghalf':(22,17,11),'cluster':(25,21,18),'pink':(27,26,24),'bloom':(28,26,25),'petalfall':(29,27.1,26.6)}

Hc_init = -10.3
Hc_min = -1.2
Hc_max = -25.1

T_thres_dorm = [13.0,5.0]
deacclim_rate = [0.08,0.10]

theta = 7.
acclim_rate = [0.12,0.10]

dorm_bound = -700.

Variety_input_dict = {'Barbera':{'Hardiness_init':-10.1,'Hardiness_min':-1.2,'Hardiness_max':-23.5,'T_thresholds_endo_eco':[15.0,3.0],'DormancyBoundary':-700,'Acclim_rate_endo_eco':[0.06,0.02],'Deacclim_rate_endo_eco':[0.10,0.08],'Theta_val':7},
'Cabernet franc':{'Hardiness_init':-9.9,'Hardiness_min':-1.2,'Hardiness_max':-25.4,'T_thresholds_endo_eco':[13.0,4.0],'DormancyBoundary':-500,'Acclim_rate_endo_eco':[0.12,0.10],'Deacclim_rate_endo_eco':[0.04,0.10],'Theta_val':7},
'Cabernet Sauvignon':{'Hardiness_init':-10.3,'Hardiness_min':-1.2,'Hardiness_max':-25.1,'T_thresholds_endo_eco':[13.0,5.0],'DormancyBoundary':-700,'Acclim_rate_endo_eco':[0.12,0.10],'Deacclim_rate_endo_eco':[0.08,0.10],'Theta_val':7},
'Chardonnay':{'Hardiness_init':-11.8,'Hardiness_min':-1.2,'Hardiness_max':-25.7,'T_thresholds_endo_eco':[14.0,3.0],'DormancyBoundary':-600,'Acclim_rate_endo_eco':[0.10,0.02],'Deacclim_rate_endo_eco':[0.10,0.08],'Theta_val':7},
'Chenin blanc':{'Hardiness_init':-12.1,'Hardiness_min':-1.2,'Hardiness_max':-24.1,'T_thresholds_endo_eco':[14.0,4.0],'DormancyBoundary':-700,'Acclim_rate_endo_eco':[0.10,0.02],'Deacclim_rate_endo_eco':[0.04,0.10],'Theta_val':7},
'Concord':{'Hardiness_init':-12.8,'Hardiness_min':-2.5,'Hardiness_max':-29.5,'T_thresholds_endo_eco':[13.0,3.0	],'DormancyBoundary':-600,'Acclim_rate_endo_eco':[0.12,0.10],'Deacclim_rate_endo_eco':[0.02,0.10],'Theta_val':3},
'Dolcetto':{'Hardiness_init':-10.1,'Hardiness_min':-1.2,'Hardiness_max':-23.2,'T_thresholds_endo_eco':[12.0,4.0],'DormancyBoundary':-600,'Acclim_rate_endo_eco':[0.16,0.10],'Deacclim_rate_endo_eco':[0.10,0.12],'Theta_val':3},
'Gewurztraminer':{'Hardiness_init':-11.6,'Hardiness_min':-1.2,'Hardiness_max':-24.9,'T_thresholds_endo_eco':[13.0,6.0],'DormancyBoundary':-400,'Acclim_rate_endo_eco':[0.12,0.02],'Deacclim_rate_endo_eco':[0.06,0.18],'Theta_val':5},
'Grenache':{'Hardiness_init':-10.0,'Hardiness_min':-1.2,'Hardiness_max':-22.7,'T_thresholds_endo_eco':[12.0,3.0],'DormancyBoundary':-500,'Acclim_rate_endo_eco':[0.16,0.10],'Deacclim_rate_endo_eco':[0.02,0.06],'Theta_val':5},
'Lemberger':{'Hardiness_init':-13.0,'Hardiness_min':-1.2,'Hardiness_max':-25.6,'T_thresholds_endo_eco':[13.0,5.0],'DormancyBoundary':-800,'Acclim_rate_endo_eco':[0.10,0.10],'Deacclim_rate_endo_eco':[0.02,0.18],'Theta_val':7},
'Malbec':{'Hardiness_init':-11.5,'Hardiness_min':-1.2,'Hardiness_max':-25.1,'T_thresholds_endo_eco':[14.0,4.0],'DormancyBoundary':-400,'Acclim_rate_endo_eco':[0.10,0.08],'Deacclim_rate_endo_eco':[0.06,0.08],'Theta_val':7},
'Merlot':{'Hardiness_init':-10.3,'Hardiness_min':-1.2,'Hardiness_max':-25.0,'T_thresholds_endo_eco':[13.0,5.0],'DormancyBoundary':-500,'Acclim_rate_endo_eco':[0.10,0.02],'Deacclim_rate_endo_eco':[0.04,0.10],'Theta_val':7},
'Mourvedre':{'Hardiness_init':-9.5,'Hardiness_min':-1.2,'Hardiness_max':-22.1,'T_thresholds_endo_eco':[13.0,6.0],'DormancyBoundary':-600,'Acclim_rate_endo_eco':[0.12,0.06],'Deacclim_rate_endo_eco':[0.08,0.14],'Theta_val':5},
'Nebbiolo':{'Hardiness_init':-11.1,'Hardiness_min':-1.2,'Hardiness_max':-24.4,'T_thresholds_endo_eco':[11.0,3.0],'DormancyBoundary':-700,'Acclim_rate_endo_eco':[0.16,0.02],'Deacclim_rate_endo_eco':[0.02,0.10],'Theta_val':3},
'Pinot gris':{'Hardiness_init':-12.0,'Hardiness_min':-1.2,'Hardiness_max':-24.1,'T_thresholds_endo_eco':[13.0,6.0],'DormancyBoundary':-400,'Acclim_rate_endo_eco':[0.12,0.02],'Deacclim_rate_endo_eco':[0.02,0.20],'Theta_val':3},
'Riesling':{'Hardiness_init':-12.6,'Hardiness_min':-1.2,'Hardiness_max':-26.1,'T_thresholds_endo_eco':[12.0,5.0],'DormancyBoundary':-700,'Acclim_rate_endo_eco':[0.14,0.10],'Deacclim_rate_endo_eco':[0.02,0.12],'Theta_val':7},
'Sangiovese':{'Hardiness_init':-10.7,'Hardiness_min':-1.2,'Hardiness_max':-21.9,'T_thresholds_endo_eco':[11.0,3.0],'DormancyBoundary':-700,'Acclim_rate_endo_eco':[0.14,0.02],'Deacclim_rate_endo_eco':[0.02,0.06],'Theta_val':7},
'Sauvignon blanc':{'Hardiness_init':-10.6,'Hardiness_min':-1.2,'Hardiness_max':-24.9,'T_thresholds_endo_eco':[14.0,5.0],'DormancyBoundary':-300,'Acclim_rate_endo_eco':[0.08,0.10],'Deacclim_rate_endo_eco':[0.06,0.12],'Theta_val':7},
'Semillon':{'Hardiness_init':-10.4,'Hardiness_min':-1.2,'Hardiness_max':-22.4,'T_thresholds_endo_eco':[13.0,7.0],'DormancyBoundary':-300,'Acclim_rate_endo_eco':[0.10,0.02],'Deacclim_rate_endo_eco':[0.08,0.20],'Theta_val':5},
'Sunbelt':{'Hardiness_init':-11.8,'Hardiness_min':-2.5,'Hardiness_max':-29.1,'T_thresholds_endo_eco':[14.0,3.0],'DormancyBoundary':-400,'Acclim_rate_endo_eco':[0.10,0.10],'Deacclim_rate_endo_eco':[0.06,0.12],'Theta_val':1.5},
'Syrah':{'Hardiness_init':-10.3,'Hardiness_min':-1.2,'Hardiness_max':-24.2,'T_thresholds_endo_eco':[14.0,4.0],'DormancyBoundary':-700,'Acclim_rate_endo_eco':[0.08,0.04],'Deacclim_rate_endo_eco':[0.06,0.08],'Theta_val':7},
'Viognier':{'Hardiness_init':-11.2,'Hardiness_min':-1.2,'Hardiness_max':-24.0,'T_thresholds_endo_eco':[14.0,5.0],'DormancyBoundary':-300,'Acclim_rate_endo_eco':[0.10,0.10],'Deacclim_rate_endo_eco':[0.08,0.10],'Theta_val':7},
'Zinfandel':{'Hardiness_init':-10.4,'Hardiness_min':-1.2,'Hardiness_max':-24.4,'T_thresholds_endo_eco':[12.0,3.0],'DormancyBoundary':-500,'Acclim_rate_endo_eco':[0.16,0.10],'Deacclim_rate_endo_eco':[0.02,0.06],'Theta_val':7}}

Hc_range = Hc_min - Hc_max
model_Hc_yest = Hc_init

period = 0

#infile = 'hardiness_temp_input.txt'

#ifile = np.genfromtxt(infile,dtype=None,delimiter="\t")

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
print DateTime.now(),'BEFORE ACIS CALL'
params = urllib.urlencode({'params':json.dumps(input_dict)})
req = urllib2.Request('http://data.rcc-acis.org/StnData', params, {'Accept':'application/json'})
response = urllib2.urlopen(req)
data_vals = json.loads(response.read())

print DateTime.now(),'AFTER ACIS CALL'
	
data_array = np.array(data_vals['data'])
t_max=data_array[:,1]
t_min=data_array[:,2]
t_mean=data_array[:,3]	

t_max[t_max.astype(str)=='M']=np.nan
t_min[t_min.astype(str)=='M']=np.nan	
t_mean[t_mean.astype(str)=='M']=np.nan	
	
t_max=t_max.astype(float)
t_min=t_min.astype(float)
t_mean=t_mean.astype(float)

t_max[t_max<-100] = np.nan
t_min[t_min<-100] = np.nan
t_mean[t_mean<-100] = np.nan

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


GDD_CH45 = np.where(CH_45_sum>accum_thresh_45,GDD,0)
