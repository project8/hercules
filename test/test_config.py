"""

Author: F. Thomas, Mingyu (Charles) Li
Date: Apr. 12, 2021

"""

from pathlib import Path

module_dir = Path(__file__).parent.absolute()

import unittest
from hercules import SimConfig, SimpleSimConfig, ConfigList
import hercules
from hercules.constants import CONFIG
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
        
        self.file_name_locust = module_dir / 'locust.json'
        self.file_name_kass = module_dir / 'kass.xml' 
        self.file_name_json = module_dir / 'test.json'

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

class SimpleSimConfigTest(unittest.TestCase):

    def setUp(self) -> None:
        
        self.config = SimpleSimConfig(x=1., y=2., z=3.)
        self.file_name_json = module_dir / 'test.json'

    def tearDown(self) -> None:
        
        if self.file_name_json.exists():
            self.file_name_json.unlink()
        
    def test_meta_data(self):
        expected = {}
        
        self.assertTrue(expected==self.config.get_meta_data())

    def test_config_data(self):
        expected = {'x': 1., 'y': 2., 'z': 3.}

        self.assertTrue(expected==self.config.get_config_data())

    def test_to_json(self):

        self.config.to_json(self.file_name_json)
        config_loaded = SimpleSimConfig.from_json(self.file_name_json)
        self.assertTrue(config_loaded.to_dict()==self.config.to_dict())

    def test_add_metadata(self):

        meta_data = {'info1': 2, 
                                'info2': 'this is some additional info'}

        self.config.add_meta_data(meta_data)
        self.assertTrue(self.config.get_meta_data()==meta_data)


class ConfigListTest(unittest.TestCase):
        
    def setUp(self) -> None:
            
        n_channels = 3
        self.configlist = ConfigList(acquisition_rate=1., info='hello', trap='nonsense')
        self.configlist_simple = ConfigList(acquisition_rate=1., info='hello simple', trap='nonsense', n_channels=n_channels)

        self.configlist_l = []
        self.configlist_simple_l = []

        r_range = np.linspace(0.002, 0.008, 8)
        theta_range = np.linspace(89.7, 90.0, 30)

        r_phi_range = np.linspace(0, 2 * np.pi / n_channels, 1)

        for theta in theta_range:
            for r_phi in r_phi_range:
                for r in r_range:
                    x = r * np.cos(r_phi)
                    y = r * np.sin(r_phi)

                    sim_config = SimConfig(
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
                    
                    self.configlist_l.append(sim_config)

                    simple_config = SimpleSimConfig(r=r, phi=r_phi, z=0., energy=0., pitch=90.)
                    self.configlist_simple_l.append(simple_config)

    def test_add_config(self):
        
        self.configlist.add_config(self.configlist_l[0])
        self.configlist.add_config(self.configlist_l[1])

        #adding wrong type
        with self.assertRaises(TypeError) as cm:
            self.configlist.add_config(self.configlist_simple_l[0])

        self.configlist_simple.add_config(self.configlist_simple_l[0])
        self.configlist_simple.add_config(self.configlist_simple_l[1])

        #adding non matching config data
        with self.assertRaises(RuntimeError) as cm:
            self.configlist_simple.add_config(SimpleSimConfig(x='foo'))

    def test_type(self):

        self.configlist.add_config(self.configlist_l[0])

        self.configlist_simple.add_config(self.configlist_simple_l[0])

        self.assertEqual(self.configlist.get_list_type(), SimConfig)
        self.assertEqual(self.configlist_simple.get_list_type(), SimpleSimConfig)


    def add_all(self):
        for config in self.configlist_l:
            self.configlist.add_config(config)

        for config in self.configlist_simple_l:
            self.configlist_simple.add_config(config)

    def test_add_all(self):

        self.add_all()

        self.assertEqual(len(self.configlist.get_internal_list()), len(self.configlist_l))
        self.assertEqual(len(self.configlist_simple.get_internal_list()), len(self.configlist_simple_l))

    def test_meta_data(self):

        self.add_all()

        expected = {'acquisition_rate': 1.0,
                    'info': 'hello',
                    'trap': '[config_path]/Trap/FreeSpaceGeometry_V00_00_10.xml',
                    'transfer-function': '/tmp/Phase3/TransferFunctions/FiveSlotTF.txt',
                    'n-channels': 3,
                    'lo-frequency': 25878100000.0,
                    'hercules-version': hercules.__version__,
                    'hexbug-version': hercules.__hexbug_version__,
                    'python-script-version': hercules.__python_script_version__,
                    'python-script-dir': CONFIG.python_script_path}
        
        self.assertEqual(expected, self.configlist.get_meta_data())

        for config in self.configlist.get_internal_list():
            self.assertEqual(expected, config.get_meta_data())

        expected = {'acquisition_rate': 1.0,
                    'info': 'hello simple',
                    'trap': 'nonsense',
                    'n_channels': 3,
                    'hercules-version': hercules.__version__,
                    'hexbug-version': hercules.__hexbug_version__,
                    'python-script-version': hercules.__python_script_version__,
                    'python-script-dir': CONFIG.python_script_path}
        
        self.assertEqual(expected, self.configlist_simple.get_meta_data())

        for config in self.configlist_simple.get_internal_list():
            self.assertEqual(expected, config.get_meta_data())

    def test_config_data(self):

        self.add_all()
        
        expected = ['energy', 'phi', 'pitch', 'r', 'z']

        self.assertEqual(sorted(list(self.configlist.get_config_data_keys())), expected)
        self.assertEqual(sorted(list(self.configlist_simple.get_config_data_keys())), expected)

        for config in self.configlist.get_internal_list():
            config_data_keys = config.get_config_data().keys()
            self.assertEqual(sorted(list(config_data_keys)), expected)

        for config in self.configlist_simple.get_internal_list():
            config_data_keys = config.get_config_data().keys()
            self.assertEqual(sorted(list(config_data_keys)), expected)

    def test_names(self):

        self.add_all()

        for i, config in enumerate(self.configlist.get_internal_list()):
            self.assertEqual(config.sim_name,f'run{i}')

        for i, config in enumerate(self.configlist_simple.get_internal_list()):
            self.assertEqual(config.sim_name,f'run{i}')

if __name__ == '__main__':
    unittest.main()
