
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
sim = he.KassLocustP3(str(module_dir) + '/workingDir')

n_r = 1
r_vals = np.linspace(0.0, 0.03, n_r)

n_theta = 1
theta_vals = np.linspace(89.9, 90.0, n_theta)

for i, r in enumerate(r_vals):
    for j, theta in enumerate(theta_vals):
        config = he.SimConfig('someDirName_{0:1.3f}_{1:1.3f}'.format(r, theta), 
                                phase='Phase2', egg_filename='someFileName.egg', 
                                theta_min = theta, theta_max = theta,
                                x_min = r, x_max = r,
                                v_range=1.0e-6, record_size=20000, t_max=7.5e-5, 
                                geometry='Trap_3.xml')
                                
        config_list.append(config)

sim(config_list)
