
"""

Author: F. Thomas
Date: Apr 29, 2021

"""

import hercules as he
from pathlib import Path
import numpy as np
import unittest

module_dir = Path(__file__).parent.absolute()

class LocustP2Test(unittest.TestCase):
    def setUp(self) -> None:
        
        r_range = np.linspace(0.0, 0.002, 2)
        theta_range = np.linspace(89.7, 90.0, 2)
        r_phi_range = np.linspace(0, 2 * np.pi, 1)

        config_list = []
        sim = he.KassLocustP3(str(module_dir) + '/out_test_locust_P2')
        
        for theta in theta_range:
            for r_phi in r_phi_range:
                for r in r_range:
                    x = r * np.cos(r_phi)
                    y = r * np.sin(r_phi)
                    r_phi_deg = np.rad2deg(r_phi)
                    name = "Sim_theta_{:.4f}_R_{:.4f}_phi_{:.4f}".format(
                        theta, r, r_phi_deg)
                    config = he.SimConfig(
                        name,
                        phase = 'Phase2',
                        seed_locust=42,
                        seed_kass=43,
                        egg_filename="simulation.egg",
                        x_min=x,
                        x_max=x,
                        y_min=y,
                        y_max=y,
                        z_min=0,
                        z_max=0,
                        theta_min=theta,
                        theta_max=theta,
                        t_max=5e-7,
                        record_size=3000,
                        v_range=3.0e-6,
                        geometry='Trap_3.xml')
                    config_list.append(config)
        
        sim(config_list)

    def test_locust(self) -> None:
        # Test sim generation (done in setUp), substitutes regular locust test
        # This test is always true.
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
