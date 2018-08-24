import numpy as N

from frost.chill.accum import ChillingUnitAccumulator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def DynamicChillingModel(ChillingUnitAccumulator):

    def __init__(self, accumulated_chill_units=None):
    """ convert temperatures to chill factors using Dynamic Chilling Unit
    Accumulation Model
    """
    ChillingUnitAccumulator.__init__(self, accumulated_chill_units)

    self.e0 = 4.15E+03 # activation energy for formation
    self.e1 = 1.29E+04 # activation energy for destruction
    self.a0 = 1.40E+05 #
    self.a1 = 2.57E+18 #
    self.slp = 1.6
    self.tetmlt = 277.   
    self.aa = 5.43E-14 # a0/a1
    self.ee = 8.74E+03 # e1-e0

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcChillUnits(self, hourly_temps):
    # initialize the chill units array to all zeros ... saves significant
    # processing time when converting temps to chill factors

    delt = N.full(len(hourly_temps), N.NaN, dtype=float)

    # convert to degrees Kelvin
    kelvin_temps = hourly_temps + 273

    flmprt = slp * tetmlt * (kelvin_temps - tetmlt) / kelvin_temps

    sr = N.exp(flmprt)

    xi = sr / (1 + sr)
    xs = aa * N.exp(ee / kelvin_temps)

    ak1 = a1 * N.exp(-e1 / kelvin_temps)

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

    return delt

