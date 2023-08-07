
"""

Author: F. Thomas
Date: February 22, 2021

"""

from hercules import SimConfig, KassLocustP3, ConfigList
from pathlib import Path
import numpy as np

module_dir = Path(__file__).parent.absolute()

#just an example
sim = KassLocustP3(str(module_dir) + '/workingDirP3', use_kass=True, use_locust=True)
configlist = ConfigList()

simulations = 5
r_vals = np.linspace(0.0, 0.03, simulations)

for i, r in enumerate(r_vals):
    config = SimConfig(n_channels=2, seed_locust=1, 
                            v_range=7.0, egg_filename='someFileName.egg', 
                            x_min=r, x_max=r, t_max=0.5e-6,
                            geometry='FreeSpaceGeometry_V00_00_10.xml')
    configlist.add_config(config)

sim(configlist)
