import numpy as N
import math

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def CH45_model(temp_in):
    """ convert temperatures to chill factors using 45 degree Chilling Unit
    Accumulation Model

        argument:
            temp_in = hourly temperature in degress C
                      dimensions = (days by hours per day)
        returns:
            array of chiil factors equal in size to temp_in array
    """
    # initialize array to all zeros ... saves processing time when converting
    # temps to chill factors
    chill = N.zeros(temp_in.shape, dtype=float)
    # chill factor is either zero or one
    chill[N.where((temp_in > 0) & (temp_in < 7.2))] = 1

    return chill

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def CHUtah_model(temp_in):
    """ convert temperatures to chill factors using Utah Chilling Unit
    Accumulation Model

        argument:
            temp_in = hourly temperature in degress C
                      dimensions = (days by hours per day)
        returns:
            array of chiil factors equal in size to temp_in array
    """
    start = datetime.now()

    # initialize array to all zeros ... saves processing time when converting
    # temps to chill factors
    chill = N.zeros(temp_in.shape, dtype=float)
    #  0.0 for temp <= 1.4
    # +0.5 for  1.4 < temp <= 2.4
    chill[N.where((temp_in>1.4) & (temp_in<=2.4))] - 0.5
    # +1.0 for  2.4 < temp <= 9.1
    chill[N.where((temp_in>2.4) & (temp_in<=9.1))] = 1.0
    # +0.5 for  9.1 < temp <= 12.4
    chill[N.where((temp_in>9.1) & (temp_in<=12.4))] = 0.5
    # 0.0 for 12.4 < temp <= 15.9
    # do nothing, already initialized to 0.0
    # -0.5 for 15.9 < temp <= 18.0
    chill[N.where((temp_in>15.9) & (temp_in<=18.0))] = -0.5
    # -1.0 for temp > 18.0
    chill[N.where(temp_in>18)] = -1.0

    print 'Utah', datetime.now() - start
    print len(N.where(chill == 0)), chill.max(), chill.mean()
    return chill

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
def CHDynamic_model(temp_in, year):
    """ convert temperatures to chill factors using Dynamic Chilling Unit
    Accumulation Model

        argument:
            temp_in = hourly temperature in degress C
                      dimensions = (days by hours per day)
        returns:
            array of chiil factors equal in size to temp_in array
    """
    start = datetime.now()

    e0 = 4.15E+03 # activation energy for formation
    e1 = 1.29E+04 # activation energy for destruction
    a0 = 1.40E+05 #
    a1 = 2.57E+18 #
    slp = 1.6
    tetmlt = 277.   
    aa = 5.43E-14 # a0/a1
    ee = 8.74E+03 # e1-e0

    #delt = N.empty_like(temp_in)
    #delt.fill(N.NaN)
    delt = N.full(len(temp_in), N.NaN, dtype=float)

    tempK = temp_in+273    #convert to K

    flmprt = slp*tetmlt*(tempK-tetmlt)/tempK

    sr = N.exp(flmprt)

    xi = sr/(1+sr)
    xs = aa*N.exp(ee/tempK)

    ak1 = a1*N.exp(-e1/tempK)

    # initialize values first hour
    delt[0] = 0.
    # Inter_s term was removed from the frist Inter_e calculation
    # because it is 0.0 at the first hour.
    Inter_e = xs[0] - xs[0] * math.exp(-ak1[0])
    #Inter_s_array = N.zeros_like(temp_in)

    # each hour depends values of Inter_e from previous hour 
    for hr in range(1,len(temp_in)):
        if Inter_e < 1: Inter_s = Inter_e
        else: Inter_s = Inter_e * (1-xi[hr])         
        #Inter_s_array[hr] = Inter_s

        Inter_e = xs[hr] - (xs[hr]-Inter_s) * N.exp(-ak1[hr])
        if Inter_e < 1: delt[hr]=0
        else: delt[hr] = xi[hr] * Inter_e

    print 'Dynamic', datetime.now() - start
    print len(N.where(delt == 0)), delt.max(), delt.mean()

    #dyn_chill_file = open('new_dynamic_chill_%d.dat' % year, 'w')
    #for indx in range(0, len(temp_in), 24):
    #    hours = [str(Inter_s_array[i]) for i in range(indx,indx+24)]
    #    dyn_chill_file.write('%s\n' % ', '.join(hours))
    #    hours = [str(delt[i]) for i in range(indx,indx+24)]
    #    dyn_chill_file.write('%s\n' % ', '.join(hours))
    #dyn_chill_file.close()

    return delt

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def GDD_Calc(tmax_in, tmin_in):
    
    adjust_max1 = N.where((tmax_in>=43) & (tmax_in<=86),tmax_in,0)
    adjust_max2 = N.where(tmax_in<43,43,0)
    adjust_max3 = N.where(tmax_in>86,86,0)
    
    gdd_max = adjust_max1 + adjust_max2 + adjust_max3
    
    adjust_min1 = N.where((tmin_in>=43) & (tmin_in<=86),tmax_in,0)
    adjust_min2 = N.where(tmin_in<43,43,0)
    adjust_min3 = N.where(tmin_in>86,86,0)
    
    gdd_min = adjust_min1 + adjust_min2 + adjust_min3
    
    GDD = N.round((gdd_max+gdd_min)/2.,decimals=0)-43.
    
    return GDD

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

## FINAL PROGRAM TO GENERATE GDD DATES LAST TEMP DATES FROST RISK FOR CURRENT AND FUTURE PERIODS BASED ON GCM OUTPUT. 
## RUNS USING THE OUTPUT FROM fit_harm_clim_mod2_ithaca.py
import csv
import scipy
from scipy import stats
import numpy as N
from numpy.linalg import inv, cholesky

#from mx import DateTime
from datetime import datetime
import os, sys, urllib, urllib2

try :
    import json 
except ImportError:
    import simplejson as json

ofile_45 = open('new_stage_date_45.dat','w')
ofile_Utah = open('new_stage_date_Utah.dat','w')
ofile_dynamic = open('new_stage_date_dynamic.dat','w')

print "Please enter the starting year for spring(s) you wish to analyze in the format YYYY"

start_yr=raw_input()

print "Please enter the ending year for spring(s) you wish to analyze in the format YYYY For a single year this should be the same as the start year"
end_yr=raw_input()

accum_thresh_45 = 1000   ##CHILL ACCUMULATION

##GDD PHENOLOGY ACCUMULATIONS

# TODO make the phenology and kill temps into Python collections.OrderedDict 
# TODO or update ConfigObject to respect order of insertion

#Phenology_dict = {'stip':97,'gtip': 132,'ghalf':192,'cluster':248,'pink':331,'bloom':424,'petalfall':539}  ## Red delicious
Phenology_dict = {'stip':85,'gtip': 121,'ghalf':175,'cluster':233,'pink':295,'bloom':382,'petalfall':484} ##(mac Geneva)
stage_list = ['stip','gtip','ghalf','cluster','pink','bloom','petalfall']
last_cold_temps = [12,16,20,24,28,32]
kill_temps = {'stip':(11,5,0),'gtip':(19,10,4),'ghalf':(22,17,11),'cluster':(25,21,18),'pink':(27,26,24),'bloom':(28,26,25),'petalfall':(29,27.1,26.6)}


chill_unit_type =['CU45','CUUtah','CUDynamic']
for year in range(int(start_yr),int(end_yr)+1):
    start_date = (year-1,10,01)   ### need to start chill computation in previous October   
    end_date = (year,06,30)
    
    start_date_str = str(start_date[0])+'-%02d'%(start_date[1])+'-%02d'%(start_date[2])
    
    end_date_str= str(end_date[0])+'-%02d'%(end_date[1])+'-%02d'%(end_date[2])
    
#       input_dict = {"sid":"304174","sdate":start_date_str,"edate":end_date_str,"elems":"maxt,mint","meta":"ll"}

    input_dict = {"sid":"303184","sdate":start_date_str,"edate":end_date_str,"elems":"maxt,mint","meta":"ll"}       
    #print datetime.now(),'BEFORE ACIS CALL',year
    params = urllib.urlencode({'params':json.dumps(input_dict)})
    req = urllib2.Request('http://data.rcc-acis.org/StnData', params, {'Accept':'application/json'})
    response = urllib2.urlopen(req)
    data_vals = json.loads(response.read())
#'Air temperature parameters for sine wave'
    #print datetime.now(),'AFTER ACIS CALL'
    
    data_array = N.array(data_vals['data'])
    t_max=data_array[:,1]
    t_min=data_array[:,2]
    
    t_max[t_max=='M']=-999
    t_min[t_min=='M']=-999
    
    t_max=t_max.astype(float)
    t_min=t_min.astype(float)

#       t_max[t_max<-100] = N.nan
#       t_min[t_min<-100] = N.nan

    t_max[t_max<-100] = 43.
    t_min[t_min<-100] = 43.
    
    date=data_array[:,0]

    date = date.astype(str)
    
    lat = data_vals['meta']['ll'][1]
    
#########################################################################

    lat = lat*N.pi/180    ###convert lat to radians

#LINVILL

    CD = []
    for dstrg in (date):
        month = int(dstrg[5:7])
        day = int(dstrg[8:10])
        
        CD.append(int(30.6*month + day +1 - 91.3))
    
    CD = N.array(CD)
    
    DL = 12.25 + (1.6164 + 1.7643*N.tan(lat)**2)*(N.cos(0.0172*CD - 1.95))

# Observations #####################################################################

    ###DAY TIME VALUES
    Day_temp_obs =[]
    for tval in range(len(date)):
        temp =[]
        for k in range(int(DL[tval])):
            test = (((float(t_max[tval])-32)*5/9) - ((float(t_min[tval])-32)*5/9))*N.sin((N.pi*(k+1))/(DL[tval]+4))+(float(t_min[tval])-32)*5/9
            temp.append(test)

        Day_temp_obs.append(temp)

    
####  APPEND NIGHT TIME VALUES TO DAYTIME LISTS
    for tval in range(len(date)):
        temp=[]
        for k in range(24-int(DL[tval])):
            test = Day_temp_obs[tval][-1:][0] -((Day_temp_obs[tval][-1:][0] - (float(t_min[tval])-32)*5/9)/int(24-DL[tval]))*N.log(k+1)
            temp.append(test)
            
            Day_temp_obs[tval].append(test)     

#####################################################################
    Day_temp_obs=N.array(Day_temp_obs)

    CH_45 = CH45_model(Day_temp_obs)
    CH_Utah= CHUtah_model(Day_temp_obs)
    CH_Dynamic = CHDynamic_model(Day_temp_obs.flatten(), year).reshape(Day_temp_obs.shape)

    CH_45_sum=[sum(CH_45[i]) for i in range(len(CH_45))]
    CH_Utah_sum=[sum(CH_Utah[i]) for i in range(len(CH_Utah))]
    CH_Dynamic_sum=[sum(CH_Dynamic[i]) for i in range(len(CH_Dynamic))]

    CH_45_sum=N.cumsum(CH_45_sum)
    CH_Utah_sum=N.cumsum(CH_Utah_sum)
    CH_Dynamic_sum=N.cumsum(CH_Dynamic_sum)

#########################################################

    # The conversions below match those in Figure 4 of 
    # Int. J. Biometeorol. 2011 May; 55(3) 411-421
    # Eike Luedeling and Patrick H. Brown
    # A global analysis of the comparability of winter chill models for
    # fruit and nut trees.

    # conversion is  average CHU/CH ratio for 117 years at ITH
    accum_thresh_Utah = accum_thresh_45*0.875

    # conversion is  average CP/CH ratio for 117 years at ITH 
    accum_thresh_Dynamic = accum_thresh_45*0.048

    GDD = GDD_Calc(t_max,t_min)     

    GDD_CH45 = N.where(CH_45_sum>accum_thresh_45,GDD,0)
    GDD_CHUtah = N.where(CH_Utah_sum>accum_thresh_Utah,GDD,0)
    GDD_CHDynamic = N.where(CH_Dynamic_sum>accum_thresh_Dynamic,GDD,0)
    
    GDD_CH45 = N.cumsum(GDD_CH45)
    GDD_CHUtah = N.cumsum(GDD_CHUtah)
    GDD_CHDynamic = N.cumsum(GDD_CHDynamic)
    
    stage_dates = {}
    stage_indices = {}
    for stage in Phenology_dict.keys():
        stage_dates[stage]=(date[N.argmax(GDD_CH45>=Phenology_dict[stage])],date[N.argmax(GDD_CHUtah>=Phenology_dict[stage])],date[N.argmax(GDD_CHDynamic>=Phenology_dict[stage])])
        stage_indices[stage]=(N.argmax(GDD_CH45>=Phenology_dict[stage]),N.argmax(GDD_CHUtah>=Phenology_dict[stage]),N.argmax(GDD_CHDynamic>=Phenology_dict[stage]))

    last_cold_dates = {}
    for xtmin in last_cold_temps:
        ixmin = N.where(t_min<=xtmin)
        last_cold_dates[xtmin]=date[N.max(ixmin)]

    kill_occur={}
    for stage in kill_temps.keys():
        kill_occur[stage]={}
        for unit in range(len(chill_unit_type)):
            kill_list = []
            for kill_pcnt in range(3):
                kill_list.append((t_min[stage_indices[stage][unit]:]<kill_temps[stage][kill_pcnt]).sum())
            
            kill_occur[stage][chill_unit_type[unit]]=kill_list      

    ofile_45.write('%4d\t'%(year))
    ofile_Utah.write('%4d\t'%(year))
    ofile_dynamic.write('%4d\t'%(year))
    for stage in stage_list:
        dt_date = datetime(int(stage_dates[stage][0][0:4]),int(stage_dates[stage][0][5:7]),int(stage_dates[stage][0][8:10]))
        ofile_45.write('%s\t'%(dt_date.timetuple().tm_yday))
        dt_date = datetime(int(stage_dates[stage][1][0:4]),int(stage_dates[stage][1][5:7]),int(stage_dates[stage][1][8:10]))
        ofile_Utah.write('%s\t'%(dt_date.timetuple().tm_yday))
        dt_date = datetime(int(stage_dates[stage][2][0:4]),int(stage_dates[stage][2][5:7]),int(stage_dates[stage][2][8:10]))
        ofile_dynamic.write('%s\t'%(dt_date.timetuple().tm_yday))
         
    ofile_45.write('\n')
    ofile_Utah.write('\n')
    ofile_dynamic.write('\n')
