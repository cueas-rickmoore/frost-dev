""" Unit conversion utilities
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

FIVE_NINTHS = 5./9.
NINE_FIFTHS = 9./5.
                    
CONVERSION_FUNCS = {
    # temperature scales - - - - - - - - - - - - - - - - - - 
    'C_to_F'         : lambda x : (x * NINE_FIFTHS) + 32.
    , 'C_to_K'       : lambda x : x + 273.15
    , 'C_to_R'       : lambda x : (x * 1.8) + 491.67
    , 'F_to_C'       : lambda x : (x - 32.) * FIVE_NINTHS
    , 'F_to_K'       : lambda x : ((x - 32.) * FIVE_NINTHS) + 273.15
    , 'F_to_R'       : lambda x : x + 459.67
    , 'K_to_C'       : lambda x : x - 273.15
    , 'K_to_F'       : lambda x : ((x - 273.15) * NINE_FIFTHS) + 32.
    , 'K_to_R'       : lambda x : x * 1.8
    , 'R_to_C'       : lambda x : (x - 491.67) * 0.555556
    , 'R_to_F'       : lambda x : x - 459.67
    , 'R_to_K'       : lambda x : x * 0.555556
    # unit temperature - - - - - - - - - - - - - - - - - - - 
    , 'dC_to_dF'     : lambda x : x * NINE_FIFTHS
    , 'dC_to_dK'     : lambda x : x
    , 'dF_to_dC'     : lambda x : x * FIVE_NINTHS
    , 'dF_to_dK'     : lambda x : x * FIVE_NINTHS
    , 'dK_to_dC'     : lambda x : x
    , 'dK_to_dF'     : lambda x : x * NINE_FIFTHS
    # distance - - - - - - - - - - - - - - - - - - - - - - - 
    # US linear
    , 'ft_to_in'     : lambda x : x * 12.
    , 'in_to_ft'     : lambda x : x * 0.83333
    # metric lienar
    , 'cm_to_m'      : lambda x : x * 0.01
    , 'cm_to_mm'     : lambda x : x * 10.
    , 'm_to_cm'      : lambda x : x * 100.
    , 'm_to_mm'      : lambda x : x * 1000.
    , 'mm_to_cm'     : lambda x : x * 0.01
    , 'mm_to_m'      : lambda x : x * 0.001
    # US lienar to metric linear 
    , 'ft_to_cm'     : lambda x : x * 30.47999
    , 'ft_to_m'      : lambda x : x * 0.3047999
    , 'ft_to_mm'     : lambda x : x * 304.7999
    , 'in_to_cm'     : lambda x : x * 2.54
    , 'in_to_m'      : lambda x : x * 0.0254
    , 'in_to_mm'     : lambda x : x * 25.4
    # metric linear to US lieanr
    , 'cm_to_in'     : lambda x : x * 0.3937
    , 'cm_to_ft'     : lambda x : x * 0.32808
    , 'm_to_ft'      : lambda x : x * 3.2808399
    , 'm_to_in'      : lambda x : x * 39.3701
    , 'mm_to_in'     : lambda x : x * 0.03937
    , 'mm_to_ft'     : lambda x : x * 0.032808
    # rainfall rate  - - - - - - - - - - - - - - - - - - - - 
    , 'in_to_kg/m2'  : lambda x : x * 25.4
    , 'kg/m2_to_in'  : lambda x : x * 0.03937
    , 'kg/m2_to_mm'  : lambda x : x
    , 'mm_to_kg/m2'  : lambda x : x
    # atmospheric pressure - - - - - - - - - - - - - - - - -
    #  atm = atmospheres
    , 'atm_to_Pa'   : lambda x : x * 101325.
    , 'atm_to_hPa'  : lambda x : x * 1013.25
    , 'atm_to_kPa'  : lambda x : x * 101.325
    , 'atm_to_psi'  : lambda x : x * 14.69595
    , 'atm_to_mb'   : lambda x : x * 1013.25
    #  Pa = Pascals
    , 'Pa_to_atm'   : lambda x : x * 0.000986923
    , 'Pa_to_hPa'   : lambda x : x * 100.
    , 'Pa_to_inHg'  : lambda x : x * 0.00029529
    , 'Pa_to_kPa'   : lambda x : x * 1000.
    , 'Pa_to_mb'    : lambda x : x * 0.01
    , 'Pa_to_psi'   : lambda x : x * 0.0001450377
    #  psi - pounds / inch**2
    , 'psi_to_atm'  : lambda x : x * 0.0680459
    , 'psi_to_Pa'   : lambda x : x * 6894.757
    , 'psi_to_hPa'  : lambda x : x * 68.94757
    , 'psi_to_kPa'  : lambda x : x * 6.894757
    , 'psi_to_mb'   : lambda x : x * 68.94757
    #  hPa = hectopascals
    , 'hPa_to_atm'    : lambda x : x * 0.0986923
    , 'hPa_to_inHg'   : lambda x : x * 0.02953
    , 'hPa_to_inHg32' : lambda x : x * 0.02953
    , 'hPa_to_inHg60' : lambda x : x * 0.02961
    , 'hPa_to_mb'     : lambda x : x
    , 'hPa_to_psi'    : lambda x : x * 0.01450377
    #  inHg = inches of mercury
    , 'inHg_to_hPa'   : lambda x : x * 33.8639
    , 'inHg_to_kPa'   : lambda x : x * 3.38639
    , 'inHg_to_Pa'    : lambda x : x * 3386.39
    , 'inHg32_to_mb'  : lambda x : x * 33.8639
    , 'inHg60_to_hPa' : lambda x : x * 33.7685
    , 'inHg60_to_mb'  : lambda x : x * 33.7685
    #  kPa = kiloopascals
    , 'kPa_to_atm'    : lambda x : x * 0.986923
    , 'kPa_to_inHg'   : lambda x : x * 0.2953
    , 'kPa_to_inHg32' : lambda x : x * 0.2953
    , 'kPa_to_inHg60' : lambda x : x * 0.2961
    , 'kPa_to_mb'     : lambda x : x * 10.
    , 'kPa_to_psi'    : lambda x : x * 0.1450377
    #  mb = millibars
    , 'mb_to_atm'     : lambda x : x * 0.000986923
    , 'mb_to_hPa'     : lambda x : x
    , 'mb_to_kPa'     : lambda x : x * 0.1
    , 'mb_to_Pa'      : lambda x : x * 100.
    , 'mb_to_inHg'    : lambda x : x * 0.02953
    , 'mb_to_inHg32'  : lambda x : x * 0.02953
    , 'mb_to_inHg60'  : lambda x : x * 0.02961
    , 'mb_to_psi'     : lambda x : x * 0.00006894
    # solar radiation  - - - - - - - - - - - - - - - - - - -
    #  W/m2 = watts/meter**2
    , 'W/m2_to_langley' : lambda x : x * 0.0861
    , 'langley_to_W/m2' : lambda x : x / 0.0861
    #  BTU/m2 = BTU/meter**2
    , 'BTU/ft2_to_W/m2' : lambda x : x / 0.316
    , 'W/m2_to_BTU/ft2' : lambda x : x * 0.316
    #  MJ/m2 = MegaJoules/meter**2
    , 'MJ/m2_to_W/m2'   : lambda x : x / 0.0036
    , 'W/m2_to_MJ/m2'   : lambda x : x * 0.0036
    # energy - - - - - - - - - - - - - - - - - - - - - - - -
    #  J = joules
    , 'J_to_BTU' : lambda x : x * 0.00094786
    , 'BTU_to_J' : lambda x : x * 1055.
    #         cal = calories
    , 'BTU_to_cal' : lambda x : x * 252.1
    , 'cal_to_BTU' : lambda x : x * 0.0039667
    # power  - - - - - - - - - - - - - - - - - - - - - - - -
    #  Wh = watt hour & kWh = kilowatt hour
    , 'Wh_to_kWh'     : lambda x : x * 0.001
    , 'kWh_to_Wh'     : lambda x : x * 1000.
    , 'Wh_to_J'   : lambda x : x * 3600.
    , 'J_to_Wh'   : lambda x : x * 0.0002777
    , 'kWh_to_J'  : lambda x : x * 3600000.
    , 'J_to_kWh'  : lambda x : * 0.2777
    # velocity - - - - - - - - - - - - - - - - - - - - - - -
    , 'mph_to_miles/hour' : lambda x : x
    , 'miles/hour_to_mph' : lambda x : x
    , 'ft/s_to_knots'     : lambda x : x * 0.5924838
    , 'ft/s_to_kph'       : lambda x : x * 1.09728
    , 'ft/s_to_mph'       : lambda x : x * 0.681818
    , 'ft/s_to_m/s'       : lambda x : x * 0.3048
    , 'knots_to_ft/s'     : lambda x : x * 1.678099
    , 'knots_to_kph'      : lambda x : x * 1.852
    , 'knots_to_m/s'      : lambda x : x * 0.514444
    , 'knots_to_mph'      : lambda x : x * 1.1507794
    , 'kph_to_ft/s'       : lambda x : x * 0.911344
    , 'kph_to_knots'      : lambda x : x * 0.5399568
    , 'kph_to_mph'        : lambda x : x * 0.621317119
    , 'kph_to_m/s'        : lambda x : x * 0.277778
    , 'mph_to_ft/s'       : lambda x : x * 1.466666
    , 'mph_to_knots'      : lambda x : x * 0.86897624
    , 'mph_to_kph'        : lambda x : x * 1.609344
    , 'mph_to_m/s'        : lambda x : x * 0.44704 
    , 'm/s_to_ft/s'       : lambda x : x * 3.28084
    , 'm/s_to_knots'      : lambda x : x * 1.943846
    , 'm/s_to_kph'        : lambda x : x * 3.6
    , 'm/s_to_mph'        : lambda x : x * 2.2369363
    }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def convertUnits(data, from_units, to_units):
    if from_units == to_units: return data

    if '*' in from_units:
        from_units, from_scale =  from_units.split('*')
        if data.dtype.kind == 'f': data /= float(from_scale)
        elif data.dtype.kind == 'i': data /= int(from_scale)

    if '*' in to_units: to_units, to_scale = to_units.split('*')
    else: to_scale = None

    func = CONVERSION_to_FUNCS.get('%s_to_%s' % (from_units,to_units), None)
    if func is not None: data = func(data)
    else:
        errmsg = 'Cannot convert %s uints to %s units'
        raise ValueError, errmsg % (from_units, to_units)

    if to_scale is not None:
        if data.dtype.kind == 'f': data *= float(to_scale)
        elif data.dtype.kind == 'i': data *= int(to_scale)
    return data

def getConversionFunction(from_units, to_units):
    if from_units is not None and to_units is not None:
        def convert(data): return convertUnits(data, from_units, to_units)
        return convert
    return None

def isSupportedUnitConversion(from_units, to_units):
    conversion = '%s_to_%s' % (from_units, to_units)
    return conversion in CONVERSION_FUNCS

