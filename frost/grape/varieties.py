
from collections import OrderedDict

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# grape variety configurtion parameters
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
PHENOLOGY = { 'lambruscana' : OrderedDict( ( ('woolly',-9.2), ('break',-6.4),
                                             ('leaf1',-4.5), ('leaf2',-3.9),
                                             ('leaf4',-2.5 ) ) ),
              'vinifera' : OrderedDict( ( ('woolly',-3.4), ('break',-2.2),
                                          ('leaf1',-2.0), ('leaf2',-1.7),
                                          ('leaf4',-1.2 ) ) ),
            }

GRAPES = (
{'name':'barbera',    'description':'Barbera',            'cultivar':'vinifera',   'hardiness':{'init':-10.1,'min':-1.2,'max':-23.5}, 'stage_thresholds':{'endo':15.0,'eco':3.0}, 'ecodormancy_threshold':-700, 'acclimation_rate':{'endo':0.06,'eco':0.02}, 'deacclimation_rate':{'endo':0.10,'eco':0.08}, 'theta':7.0},
{'name':'cab_franc',  'description':'Cabernet Franc',     'cultivar':'vinifera',   'hardiness':{'init': -9.9,'min':-1.2,'max':-25.4}, 'stage_thresholds':{'endo':13.0,'eco':4.0}, 'ecodormancy_threshold':-500, 'acclimation_rate':{'endo':0.12,'eco':0.10}, 'deacclimation_rate':{'endo':0.04,'eco':0.10}, 'theta':7.0},
{'name':'cab_sauv',   'description':'Cabernet Sauvignon', 'cultivar':'vinifera',   'hardiness':{'init':-10.3,'min':-1.2,'max':-25.1}, 'stage_thresholds':{'endo':13.0,'eco':5.0}, 'ecodormancy_threshold':-700, 'acclimation_rate':{'endo':0.12,'eco':0.10}, 'deacclimation_rate':{'endo':0.08,'eco':0.10}, 'theta':7.0},
{'name':'chard',      'description':'Chardonnay',         'cultivar':'vinifera',   'hardiness':{'init':-11.8,'min':-1.2,'max':-25.7}, 'stage_thresholds':{'endo':14.0,'eco':3.0}, 'ecodormancy_threshold':-600, 'acclimation_rate':{'endo':0.10,'eco':0.02}, 'deacclimation_rate':{'endo':0.10,'eco':0.08}, 'theta':7.0},
{'name':'chen_blanc', 'description':'Chenin blanc',       'cultivar':'vinifera',   'hardiness':{'init':-12.1,'min':-1.2,'max':-24.1}, 'stage_thresholds':{'endo':14.0,'eco':4.0}, 'ecodormancy_threshold':-700, 'acclimation_rate':{'endo':0.10,'eco':0.02}, 'deacclimation_rate':{'endo':0.04,'eco':0.10}, 'theta':7.0},
{'name':'concord',    'description':'Concord',            'cultivar':'lambruscana','hardiness':{'init':-12.8,'min':-2.5,'max':-29.5}, 'stage_thresholds':{'endo':13.0,'eco':3.0}, 'ecodormancy_threshold':-600, 'acclimation_rate':{'endo':0.12,'eco':0.10}, 'deacclimation_rate':{'endo':0.02,'eco':0.10}, 'theta':3.0},
{'name':'dolcetto',   'description':'Dolcetto',           'cultivar':'vinifera',   'hardiness':{'init':-10.1,'min':-1.2,'max':-23.2}, 'stage_thresholds':{'endo':12.0,'eco':4.0}, 'ecodormancy_threshold':-600, 'acclimation_rate':{'endo':0.16,'eco':0.10}, 'deacclimation_rate':{'endo':0.10,'eco':0.12}, 'theta':3.0},
{'name':'gewurtz',    'description':'Gewurztraminer',     'cultivar':'vinifera',   'hardiness':{'init':-11.6,'min':-1.2,'max':-24.9}, 'stage_thresholds':{'endo':13.0,'eco':6.0}, 'ecodormancy_threshold':-400, 'acclimation_rate':{'endo':0.12,'eco':0.02}, 'deacclimation_rate':{'endo':0.06,'eco':0.18}, 'theta':5.0},
{'name':'grenache',   'description':'Grenache',           'cultivar':'vinifera',   'hardiness':{'init':-10.0,'min':-1.2,'max':-22.7}, 'stage_thresholds':{'endo':12.0,'eco':3.0}, 'ecodormancy_threshold':-500, 'acclimation_rate':{'endo':0.16,'eco':0.10}, 'deacclimation_rate':{'endo':0.02,'eco':0.06}, 'theta':5.0},
{'name':'lemberger',  'description':'Lemberger',          'cultivar':'vinifera',   'hardiness':{'init':-13.0,'min':-1.2,'max':-25.6}, 'stage_thresholds':{'endo':13.0,'eco':5.0}, 'ecodormancy_threshold':-800, 'acclimation_rate':{'endo':0.10,'eco':0.10}, 'deacclimation_rate':{'endo':0.02,'eco':0.18}, 'theta':7.0},
{'name':'malbac',     'description':'Malbec',             'cultivar':'vinifera',   'hardiness':{'init':-11.5,'min':-1.2,'max':-25.1}, 'stage_thresholds':{'endo':14.0,'eco':4.0}, 'ecodormancy_threshold':-400, 'acclimation_rate':{'endo':0.10,'eco':0.08}, 'deacclimation_rate':{'endo':0.06,'eco':0.08}, 'theta':7.0},
{'name':'merlot',     'description':'Merlot',             'cultivar':'vinifera',   'hardiness':{'init':-10.3,'min':-1.2,'max':-25.0}, 'stage_thresholds':{'endo':13.0,'eco':5.0}, 'ecodormancy_threshold':-500, 'acclimation_rate':{'endo':0.10,'eco':0.02}, 'deacclimation_rate':{'endo':0.04,'eco':0.10}, 'theta':7.0},
{'name':'mourverde',  'description':'Mourvedre',          'cultivar':'vinifera',   'hardiness':{'init': -9.5,'min':-1.2,'max':-22.1}, 'stage_thresholds':{'endo':13.0,'eco':6.0}, 'ecodormancy_threshold':-600, 'acclimation_rate':{'endo':0.12,'eco':0.06}, 'deacclimation_rate':{'endo':0.08,'eco':0.14}, 'theta':5.0},
{'name':'nebbiolo',   'description':'Nebbiolo',           'cultivar':'vinifera',   'hardiness':{'init':-11.1,'min':-1.2,'max':-24.4}, 'stage_thresholds':{'endo':11.0,'eco':3.0}, 'ecodormancy_threshold':-700, 'acclimation_rate':{'endo':0.16,'eco':0.02}, 'deacclimation_rate':{'endo':0.02,'eco':0.10}, 'theta':3.0},
{'name':'pin_gris',   'description':'Pinot Gris',         'cultivar':'vinifera',   'hardiness':{'init':-12.0,'min':-1.2,'max':-24.1}, 'stage_thresholds':{'endo':13.0,'eco':6.0}, 'ecodormancy_threshold':-400, 'acclimation_rate':{'endo':0.12,'eco':0.02}, 'deacclimation_rate':{'endo':0.02,'eco':0.20}, 'theta':3.0},
{'name':'riesling',   'description':'Riesling',           'cultivar':'vinifera',   'hardiness':{'init':-12.6,'min':-1.2,'max':-26.1}, 'stage_thresholds':{'endo':12.0,'eco':5.0}, 'ecodormancy_threshold':-700, 'acclimation_rate':{'endo':0.14,'eco':0.10}, 'deacclimation_rate':{'endo':0.02,'eco':0.12}, 'theta':7.0},
{'name':'sangiovese', 'description':'Sangiovese',         'cultivar':'vinifera',   'hardiness':{'init':-10.7,'min':-1.2,'max':-21.9}, 'stage_thresholds':{'endo':11.0,'eco':3.0}, 'ecodormancy_threshold':-700, 'acclimation_rate':{'endo':0.14,'eco':0.02}, 'deacclimation_rate':{'endo':0.02,'eco':0.06}, 'theta':7.0},
{'name':'sauv_blanc', 'description':'Sauvignon Blanc',    'cultivar':'vinifera',   'hardiness':{'init':-10.6,'min':-1.2,'max':-24.9}, 'stage_thresholds':{'endo':14.0,'eco':5.0}, 'ecodormancy_threshold':-300, 'acclimation_rate':{'endo':0.08,'eco':0.10}, 'deacclimation_rate':{'endo':0.06,'eco':0.12}, 'theta':7.0},
{'name':'semillon',   'description':'Semillon',           'cultivar':'vinifera',   'hardiness':{'init':-10.4,'min':-1.2,'max':-22.4}, 'stage_thresholds':{'endo':13.0,'eco':7.0}, 'ecodormancy_threshold':-300, 'acclimation_rate':{'endo':0.10,'eco':0.02}, 'deacclimation_rate':{'endo':0.08,'eco':0.20}, 'theta':5.0},
{'name':'sunbelt',    'description':'Sunbelt',            'cultivar':'lambruscana','hardiness':{'init':-11.8,'min':-2.5,'max':-29.1}, 'stage_thresholds':{'endo':14.0,'eco':3.0}, 'ecodormancy_threshold':-400, 'acclimation_rate':{'endo':0.10,'eco':0.10}, 'deacclimation_rate':{'endo':0.06,'eco':0.12}, 'theta':1.5},
{'name':'syrah',      'description':'Syrah',              'cultivar':'vinifera',   'hardiness':{'init':-10.3,'min':-1.2,'max':-24.2}, 'stage_thresholds':{'endo':14.0,'eco':4.0}, 'ecodormancy_threshold':-700, 'acclimation_rate':{'endo':0.08,'eco':0.04}, 'deacclimation_rate':{'endo':0.06,'eco':0.08}, 'theta':7.0},
{'name':'viogmier',   'description':'Viognier',           'cultivar':'vinifera',   'hardiness':{'init':-11.2,'min':-1.2,'max':-24.0}, 'stage_thresholds':{'endo':14.0,'eco':5.0}, 'ecodormancy_threshold':-300, 'acclimation_rate':{'endo':0.10,'eco':0.10}, 'deacclimation_rate':{'endo':0.08,'eco':0.10}, 'theta':7.0},
{'name':'zinfandel',  'description':'Zinfandel',          'cultivar':'vinifera',   'hardiness':{'init':-10.4,'min':-1.2,'max':-24.4}, 'stage_thresholds':{'endo':12.0,'eco':3.0}, 'ecodormancy_threshold':-500, 'acclimation_rate':{'endo':0.16,'eco':0.10}, 'deacclimation_rate':{'endo':0.02,'eco':0.06}, 'theta':7.0},
)

