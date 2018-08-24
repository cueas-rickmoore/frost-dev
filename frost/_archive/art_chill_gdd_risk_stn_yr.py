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

def CHUtah_modelnp(temp_in):
        start = datetime.now()

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
        
        print 'Utah', datetime.now() - start
        print len(np.where(chill_out == 0)), chill_out.max(), chill_out.mean()
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
        
def CHDynamic_modelnp(temp_in, year):
        start = datetime.now() 

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

        Inter_s_array = np.zeros_like(temp_in)

        for dy in range(len(temp_in)):
                for hr in range (len(temp_in[dy])):
                        if dy == 0 and hr == 0:
                                Inter_s=0.0
                                intere_last = 0.7
                        elif intere_last < 1:
                                Inter_s = intere_last
                        else:
                                Inter_s = intere_last*(1-xi[dy][hr])
                        Inter_s_array[dy][hr] = Inter_s

                        Inter_e = xs[dy][hr] - (xs[dy][hr]-Inter_s)*math.exp(-ak1[dy][hr])
                        intere_last = Inter_e
                
                        if dy==0 and hr == 0:
                                delt[dy][hr]=0
                        elif Inter_e < 1:
                                delt[dy][hr]=0
                        else:
                                delt[dy][hr] = xi[dy][hr]*Inter_e

        print 'Dynamic', datetime.now() - start
        print len(np.where(delt == 0)), delt.max(), delt.mean()

        dyn_chill_file = open('art_dynamic_chill_%d.dat' % year, 'w') 
        for day in range(len(temp_in)):
            hours = [str(value) for value in Inter_s_array[day][:]]
            dyn_chill_file.write('%s\n' % ', '.join(hours))
            hours = [str(value) for value in delt[day][:]]
            dyn_chill_file.write('%s\n' % ', '.join(hours))
        dyn_chill_file.close()

        return delt

def GDD_Calc(tmax_in,tmin_in):
        
        adjust_max1 = np.where((tmax_in>=43) & (tmax_in<=86),tmax_in,0)
        adjust_max2 = np.where(tmax_in<43,43,0)
        adjust_max3 = np.where(tmax_in>86,86,0)
        
        gdd_max = adjust_max1 + adjust_max2 + adjust_max3
        
        adjust_min1 = np.where((tmin_in>=43) & (tmin_in<=86),tmax_in,0)
        adjust_min2 = np.where(tmin_in<43,43,0)
        adjust_min3 = np.where(tmin_in>86,86,0)
        
        gdd_min = adjust_min1 + adjust_min2 + adjust_min3
        
        GDD = np.round((gdd_max+gdd_min)/2.,decimals=0)-43.
        
        return GDD
## FINAL PROGRAM TO GENERATE GDD DATES LAST TEMP DATES FROST RISK FOR CURRENT AND FUTURE PERIODS BASED ON GCM OUTPUT. 
## RUNS USING THE OUTPUT FROM fit_harm_clim_mod2_ithaca.py
import csv
import scipy
from scipy import stats
import numpy as np
from numpy.linalg import inv, cholesky

#import rpy2.rpy_classic as rpy
#rpy.set_default_mode(rpy.NO_CONVERSION)

#from mx import DateTime
from datetime import datetime
import os, sys, urllib, urllib2

try :
        import json 
except ImportError:
        import simplejson as json

ofile_45 = open('art_stage_date_45.dat','w')
ofile_Utah = open('art_stage_date_Utah.dat','w')
ofile_dynamic = open('art_stage_date_dynamic.dat','w')

print "Please enter the starting year for spring(s) you wish to analyze in the format YYYY"

start_yr=raw_input()

print "Please enter the ending year for spring(s) you wish to analyze in the format YYYY For a single year this should be the same as the start year"
end_yr=raw_input()

accum_thresh_45 = 1000   ##CHILL ACCUMULATION

##GDD PHENOLOGY ACCUMULATIONS
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
        
        data_array = np.array(data_vals['data'])
        t_max=data_array[:,1]
        t_min=data_array[:,2]
        
        t_max[t_max=='M']=-999
        t_min[t_min=='M']=-999
        
        t_max=t_max.astype(float)
        t_min=t_min.astype(float)

#       t_max[t_max<-100] = np.nan
#       t_min[t_min<-100] = np.nan

        t_max[t_max<-100] = 43.
        t_min[t_min<-100] = 43.
        
        date=data_array[:,0]

        date = date.astype(str)
        
        lat = data_vals['meta']['ll'][1]
        
#########################################################################

        lat = lat*np.pi/180    ###convert lat to radians

#LINVILL

        CD = []
        for dstrg in (date):
                month = int(dstrg[5:7])
                day = int(dstrg[8:10])
                
                CD.append(int(30.6*month + day +1 - 91.3))
        
        CD = np.array(CD)
        
        DL = 12.25 + (1.6164 + 1.7643*np.tan(lat)**2)*(np.cos(0.0172*CD - 1.95))

# Observations #####################################################################

        ###DAY TIME VALUES
        Day_temp_obs =[]
        for tval in range(len(date)):
                temp =[]
                for k in range(int(DL[tval])):
                        test = (((float(t_max[tval])-32)*5/9) - ((float(t_min[tval])-32)*5/9))*np.sin((np.pi*(k+1))/(DL[tval]+4))+(float(t_min[tval])-32)*5/9
                        temp.append(test)

                Day_temp_obs.append(temp)

        
####  APPEND NIGHT TIME VALUES TO DAYTIME LISTS
        for tval in range(len(date)):
                temp=[]
                for k in range(24-int(DL[tval])):
                        test = Day_temp_obs[tval][-1:][0] -((Day_temp_obs[tval][-1:][0] - (float(t_min[tval])-32)*5/9)/int(24-DL[tval]))*np.log(k+1)
                        temp.append(test)
                        
                        Day_temp_obs[tval].append(test)         

#####################################################################
        Day_temp_obs=np.array(Day_temp_obs)
        
        CH_45 = CH45_modelnp(Day_temp_obs)
        CH_Utah= CHUtah_modelnp(Day_temp_obs)
        CH_Dynamic = CHDynamic_modelnp(Day_temp_obs, year)

        CH_45_sum=[sum(CH_45[i]) for i in range(len(CH_45))]
        CH_Utah_sum=[sum(CH_Utah[i]) for i in range(len(CH_Utah))]
        CH_Dynamic_sum=[sum(CH_Dynamic[i]) for i in range(len(CH_Dynamic))]

        CH_45_sum=np.cumsum(CH_45_sum)
        CH_Utah_sum=np.cumsum(CH_Utah_sum)
        CH_Dynamic_sum=np.cumsum(CH_Dynamic_sum)

#########################################################

### the conversions below match those in Figure 4 of Int. J. Biometeorol. 2011 May; 55(3) 411-421
###Eike Luedeling and Patrick H. Brown A global analysis of the comparability of winter chill models for fruit and nut trees

        accum_thresh_Utah =accum_thresh_45*0.875     # conversion is  average CHU/CH ratio for 117 years at ITH

        accum_thresh_Dynamic = accum_thresh_45*0.048   # conversion is  average CP/CH ratio for 117 years at ITH 

        GDD = GDD_Calc(t_max,t_min)     

        GDD_CH45 = np.where(CH_45_sum>accum_thresh_45,GDD,0)
        GDD_CHUtah = np.where(CH_Utah_sum>accum_thresh_Utah,GDD,0)
        GDD_CHDynamic = np.where(CH_Dynamic_sum>accum_thresh_Dynamic,GDD,0)
        
        GDD_CH45 = np.cumsum(GDD_CH45)
        GDD_CHUtah = np.cumsum(GDD_CHUtah)
        GDD_CHDynamic = np.cumsum(GDD_CHDynamic)
        
        stage_dates = {}
        stage_indices = {}
        for stage in Phenology_dict.keys():
                stage_dates[stage]=(date[np.argmax(GDD_CH45>=Phenology_dict[stage])],date[np.argmax(GDD_CHUtah>=Phenology_dict[stage])],date[np.argmax(GDD_CHDynamic>=Phenology_dict[stage])])
                stage_indices[stage]=(np.argmax(GDD_CH45>=Phenology_dict[stage]),np.argmax(GDD_CHUtah>=Phenology_dict[stage]),np.argmax(GDD_CHDynamic>=Phenology_dict[stage]))

        last_cold_dates = {}
        for xtmin in last_cold_temps:
                ixmin = np.where(t_min<=xtmin)
                last_cold_dates[xtmin]=date[np.max(ixmin)]

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
