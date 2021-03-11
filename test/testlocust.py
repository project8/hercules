
"""

Author: F. Thomas
Date: February 22, 2021

"""

import hercules as he
from pathlib import Path
import numpy as np

module_dir = Path(__file__).parent.absolute()

#just an example
config_list = []

r_vals = np.linspace(0.0,0.03,10)

for r in r_vals:
    config = he.SimConfig('someDirName_'+str(r), n_channels=2, seed_locust=1, 
                            v_range=7.0, egg_filename='someFileName.egg', 
                            x_min=r, x_max=r, t_max=0.5e-6,
                            geometry='FreeSpaceGeometry_V00_00_10.xml')
    config_list.append(config)


sim = he.KassLocustP3(str(module_dir) + '/workingDir')
sim(config_list)
