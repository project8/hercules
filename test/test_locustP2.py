
"""

Author: F. Thomas
Date: Apr 29, 2021

"""

from hercules import KassLocustP3, ConfigList, SimConfig
from pathlib import Path
import numpy as np
import unittest
import shutil

module_dir = Path(__file__).parent.absolute()
test_dataset_name = 'working_directory'
test_path = module_dir / test_dataset_name

class LocustP2Test(unittest.TestCase):
    def setUp(self) -> None:
        
        r_range = np.linspace(0.0, 0.002, 2)
        theta_range = np.linspace(89.7, 90.0, 2)
        r_phi_range = np.linspace(0, 2 * np.pi, 1)

        sim = KassLocustP3(test_path, use_kass=True, use_locust=True)
        configlist = ConfigList(acquisition_rate=1., info='hello', trap='nonsense')
        
        for theta in theta_range:
            for r_phi in r_phi_range:
                for r in r_range:
                    x = r * np.cos(r_phi)
                    y = r * np.sin(r_phi)
                    config = SimConfig(
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
                    configlist.add_config(config)
        
        sim(configlist)

    def tearDown(self) -> None:
        shutil.rmtree(test_path)

    def test_locust(self) -> None:

        paths =[test_path / 'index.he',
                test_path / 'info.txt',
                test_path / 'run0' / 'simulation.egg',
                test_path / 'run1' / 'simulation.egg',
                test_path / 'run2' / 'simulation.egg',
                test_path / 'run3' / 'simulation.egg'
                ]
        
        for path in paths:
            self.assertTrue(path.exists())
                

if __name__ == '__main__':
    unittest.main()
