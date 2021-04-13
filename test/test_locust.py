"""

Author: Mingyu (Charles) Li
Date: Apr. 12, 2021

"""

# Add module to sys path for detection in case the user has yet installed the module
import sys
import os
from pathlib import Path
FILE_DIR = Path(__file__).parent.absolute()
ROOT_DIR = FILE_DIR.parent
sys.path.insert(0, ROOT_DIR)

import unittest
import hercules as he
import numpy as np

# class LocustTest(unittest.TestCase):

#     def setUp(self) -> None:
#         # Check if the test data exists
#         test_data_dir = FILE_DIR/"test_dir"
#         if 



#     def test_generate_configs(self) -> None:
#         # Generates a list of config
#         n_channels = 3
#         r_range = np.linspace(0.002, 0.008, 8)
#         theta_range = np.linspace(89.7, 90.0, 30)

#         r_phi_range = np.linspace(0, 2 * np.pi / 60, 1)

#         config_list = []

#         for theta in theta_range:
#             for r_phi in r_phi_range:
#                 for r in r_range:
#                     x = r * np.cos(r_phi)
#                     y = r * np.sin(r_phi)
#                     r_phi_deg = np.rad2deg(r_phi)
#                     name = "Sim_theta_{:.4f}_R_{:.4f}_phi_{:.4f}".format(
#                         theta, r, r_phi_deg)
#                     config = he.SimConfig(name,
#                                         n_channels=n_channels,
#                                         seed_locust=42,
#                                         seed_kass=43,
#                                         egg_filename="simulation.egg",
#                                         x_min=x,
#                                         x_max=x,
#                                         y_min=y,
#                                         y_max=y,
#                                         z_min=0,
#                                         z_max=0,
#                                         theta_min=theta,
#                                         theta_max=theta,
#                                         t_max=5e-6,
#                                         v_range=3.0e-7,
#                                         geometry='FreeSpaceGeometry_V00_00_10.xml')

#                     json_file = FILE_DIR/'SimConfig.json'
#                     locust_file = FILE_DIR/'Locust.json'
#                     # Note kass file name has to be the following for dict comparison
#                     kass_file = FILE_DIR/'LocustKassElectrons.xml'

#                     config.to_json(json_file)

#                     config2 = he.SimConfig.from_json(json_file)
#                     config2.make_config_file(locust_file, kass_file)
#                     self.assertDictEqual(config.to_dict(), config2.to_dict())

#                     config_list.append(config)

# #just an example
# config_list = []
# sim = he.KassLocustP3(str(module_dir) + '/workingDir')

# simulations = 20
# r_vals = np.linspace(0.0, 0.03, simulations)

# for i, r in enumerate(r_vals):
#     config = he.SimConfig('someDirName_{0:1.3f}'.format(r), n_channels=2, seed_locust=1, 
#                             v_range=7.0, egg_filename='someFileName.egg', 
#                             x_min=r, x_max=r, t_max=0.5e-6,
#                             geometry='FreeSpaceGeometry_V00_00_10.xml')
#     config_list.append(config)

# sim(config_list)