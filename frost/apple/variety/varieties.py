# apple variety configurations

from collections import OrderedDict

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

APPLE_STAGES = ('stip','gtip','ghalf','cluster','pink','bloom','petalfall')
# kills 10%, 50%, 90% of buds at temp
APPLE_KILL_TEMPS = ( (11,5,0), (19,10,4), (22,17,11), (25,21,18), (27,26,24),
                     (28,26,25), (29,27.1,26.6) )

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

APPLES = { }

phenology = tuple( zip( APPLE_STAGES, (91, 107, 170, 224, 288, 384, 492) ) )
APPLES['empire'] = { 'description':'Empire Apple',
                     'min_chill_units':1100, 'phenology':OrderedDict(phenology),
                     'kill_temps':tuple(zip(APPLE_STAGES, APPLE_KILL_TEMPS)),
         }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

phenology = tuple( zip(APPLE_STAGES, (85, 121, 175, 233, 295, 382, 484) ) )
APPLES['mac_geneva'] = { 'description':'Macintosh Apple (Geneva)',
                     'min_chill_units':1100, 'phenology':OrderedDict(phenology),
                     'kill_temps':tuple(zip(APPLE_STAGES, APPLE_KILL_TEMPS)), 
         }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

phenology = tuple( zip( APPLE_STAGES, (97, 132, 192, 248, 331, 424, 539) ) )
APPLES['red_delicious'] = { 'description':'Red Delicious Apple',
                     'min_chill_units':1200, 'phenology':OrderedDict(phenology),
                     'kill_temps':tuple(zip(APPLE_STAGES, APPLE_KILL_TEMPS)),
         }

del phenology

