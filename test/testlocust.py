
"""

Author: F. Thomas
Date: February 22, 2021

"""

from hercules.simulation import KassLocustP3
from hercules.simconfig import SimConfig
from pathlib import Path

module_dir = Path(__file__).parent.absolute()

#just an example
config = SimConfig(n_channels=2, seed_locust=1, v_range=7.0,
                    egg_filename='someFileName.egg', x_min=-0.1e-5, 
                    x_max=0.1e-5, t_max=0.5e-6,
                    geometry='FreeSpaceGeometry_V00_00_10.xml')


sim = KassLocustP3(str(module_dir) + '/workingDir')
sim(config, 'someDirName')
