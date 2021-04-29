"""

Author: F. Thomas, Mingyu (Charles) Li
Date: Apr. 12, 2021

"""

from pathlib import Path
FILE_DIR = Path(__file__).parent.absolute()

import unittest
import hercules as he
import numpy as np

class ConfigTest(unittest.TestCase):

    def test_generate_configs(self) -> None:
        # Generates a list of config
        n_channels = 3
        r_range = np.linspace(0.002, 0.008, 8)
        theta_range = np.linspace(89.7, 90.0, 30)

        r_phi_range = np.linspace(0, 2 * np.pi / n_channels, 1)

        config_list = []

        for theta in theta_range:
            for r_phi in r_phi_range:
                for r in r_range:
                    x = r * np.cos(r_phi)
                    y = r * np.sin(r_phi)
                    r_phi_deg = np.rad2deg(r_phi)
                    name = "Sim_theta_{:.4f}_R_{:.4f}_phi_{:.4f}".format(
                        theta, r, r_phi_deg)
                    config = he.SimConfig(name,
                                        n_channels=n_channels,
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
                                        t_max=5e-6,
                                        v_range=3.0e-7,
                                        geometry='FreeSpaceGeometry_V00_00_10.xml')

                    json_file = FILE_DIR/'SimConfig.json'
                    locust_file = FILE_DIR/'Locust.json'
                    # Note kass file name has to be the following for dict comparison
                    kass_file = FILE_DIR/'LocustKassElectrons.xml'

                    config.to_json(json_file)

                    config2 = he.SimConfig.from_json(json_file)
                    config2.make_config_file(locust_file, kass_file)
                    self.assertDictEqual(config.to_dict(), config2.to_dict())

                    config_list.append(config)

    def tearDown(self) -> None:
        # Clean up
        files_json = FILE_DIR.glob('*.json')
        files_xml = FILE_DIR.glob('*.xml')
        filtered_files = sorted(files_json) + sorted(files_xml)

        for f in filtered_files:
            # Note f is a Path object
            # Deletes the file
            f.unlink()


if __name__ == '__main__':
    unittest.main()
