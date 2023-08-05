"""

Author: F. Thomas, Mingyu (Charles) Li
Date: Apr. 12, 2021

"""

from pathlib import Path
FILE_DIR = Path(__file__).parent.absolute()

import unittest
from hercules import SimConfig, SimpleSimConfig, ConfigList
import numpy as np


class SimConfigTest(unittest.TestCase):

    def setUp(self) -> None:
        
        n_channels = 3
        x = 1.
        y = 0.
        theta = 90.

        self.config = SimConfig(
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
        
        self.file_name_locust = Path('locust.json')
        self.file_name_kass = Path('kass.xml') 
        self.file_name_json = Path('test.json')

    def tearDown(self) -> None:
        
        if self.file_name_json.exists():
            self.file_name_json.unlink()

        if self.file_name_locust.exists():
            self.file_name_locust.unlink()

        if self.file_name_kass.exists():
            self.file_name_kass.unlink()
        
    def test_meta_data(self):
        expected = {'trap': '[config_path]/Trap/FreeSpaceGeometry_V00_00_10.xml',
                    'transfer-function': '/tmp/Phase3/TransferFunctions/FiveSlotTF.txt',
                    'n-channels': 3,
                    'lo-frequency': 25878100000.0}
        
        self.assertTrue(expected==self.config.get_meta_data())

    def test_config_data(self):
        expected = {'r': 1.0, 'phi': 0.0, 'z': 0, 'pitch': 90.0, 'energy': 18600.0}

        self.assertTrue(expected==self.config.get_config_data())

    def test_to_json(self):

        self.config.to_json(self.file_name_json)
        config_loaded = SimConfig.from_json(self.file_name_json)
        self.assertTrue(config_loaded.to_dict()==self.config.to_dict())

    def test_make_config_file(self):

        self.config.make_kass_config_file(self.file_name_kass)
        self.config.make_locust_config_file(self.file_name_locust, self.file_name_kass)

        self.assertTrue(self.file_name_kass.exists())
        self.assertTrue(self.file_name_locust.exists())

    def test_add_metadata(self):

        additional_meta_data = {'trap': 'this should be overwritten', 
                                'info': 'this is some additional info', 
                                'acquisition-rate': 'this will not be overwritten because SimConfig does not set it. Adding metadata CANNOT overwrite the config!'}

        expected = {'trap': '[config_path]/Trap/FreeSpaceGeometry_V00_00_10.xml',
                    'info': 'this is some additional info',
                    'acquisition-rate': 'this will not be overwritten because SimConfig does not set it. Adding metadata CANNOT overwrite the config!',
                    'transfer-function': '/tmp/Phase3/TransferFunctions/FiveSlotTF.txt',
                    'n-channels': 3,
                    'lo-frequency': 25878100000.0}

        self.config.add_meta_data(additional_meta_data)
        self.assertTrue(self.config.get_meta_data()==expected)


"""
class ConfigListTest(unittest.TestCase):
        
    def setUp(self) -> None:
            
        self.configlist = ConfigList(acquisition_rate=1., info='hello', trap='nonsense')

        n_channels = 3
        r_range = np.linspace(0.002, 0.008, 8)
        theta_range = np.linspace(89.7, 90.0, 30)

        r_phi_range = np.linspace(0, 2 * np.pi / n_channels, 1)

        for theta in theta_range:
            for r_phi in r_phi_range:
                for r in r_range:
                    x = r * np.cos(r_phi)
                    y = r * np.sin(r_phi)
                    r_phi_deg = np.rad2deg(r_phi)

                    config = SimConfig(
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
                    
                    self.clist.add_config(config)

                # json_file = FILE_DIR/'SimConfig.json'
                # locust_file = FILE_DIR/'Locust.json'
                    # Note kass file name has to be the following for dict comparison
                # kass_file = FILE_DIR/'LocustKassElectrons.xml'

                # config.to_json(json_file)

                    #config2 = he.SimConfig.from_json(json_file)
                    #config2.make_config_file(locust_file, kass_file)
                    #self.assertDictEqual(config.to_dict(), config2.to_dict())

                    #config_list.append(config)

    def test_meta_data(self) -> None:
    
        expected = {'acquisition_rate': 1.0, 'info': 'hello', 'trap': '[config_path]/Trap/FreeSpaceGeometry_V00_00_10.xml', 
                    'transfer-function': '/tmp/Phase3/TransferFunctions/FiveSlotTF.txt', 'n-channels': 3, 'lo-frequency': 25878100000.0}
        
        self.assertTrue(self.clist.get_meta_data()==expected)
        
        for config in self.clist.get_internal_list():
             self.assertTrue(config.get_meta_data()==expected)

    def test_config_data(self) ->None:

        

    def test_generate_configs(self) -> None:

        clist = ConfigList(acquisition_rate=1., info='hello')
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
                    config = he.SimConfig(
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
"""

if __name__ == '__main__':
    unittest.main()
