
"""

Author: F. Thomas
Date: February 22, 2021

"""

import hercules as he
from pathlib import Path

module_dir = Path(__file__).parent.absolute()

config = he.SimConfig('some_name', n_channels=15, seed_locust=1, v_range=7.0, n_subarrays=3,
                    egg_filename='x.egg', seed_kass =12534, x_min=0.05e-6, 
                    x_max=0.1e-5, geometry='FreeSpaceGeometry_V00_00_10.xml',
                    unknown_parameter1 = 'foo', unknown_parameter2 = 'bar' )

json_file = module_dir/'SimConfig.json'
locust_file = module_dir/'Locust.json'
kass_file = module_dir/'Kass.xml'

config.to_json(json_file)

config2 = he.SimConfig.from_json(json_file)
config2.make_config_file(locust_file, kass_file)
print(config2.to_dict())
