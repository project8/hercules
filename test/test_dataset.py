
"""

Author: F. Thomas
Date: Aug 05, 2023

"""

from hercules import SimpleSimConfig, Dataset, ConfigList
import hercules
from hercules.constants import CONFIG
from pathlib import Path
import unittest
import numpy as np
import shutil

module_dir = Path(__file__).parent.absolute()
test_dataset_name = 'test_directory'
test_path = module_dir / test_dataset_name

class DatasetTest(unittest.TestCase):

    def setUp(self) -> None:

        clist = ConfigList(sr=200., info='hello')

        y = 3.
        for x in range(10):
            for z in range(5,7,1):
                clist.add_config(SimpleSimConfig(x=x, y=y, z=z))

        self.d = Dataset(test_path, clist)

    def tearDown(self) -> None:
        shutil.rmtree(test_path)

    def test_axes(self) -> None:
        expected_result = [np.array([0., 1., 2., 3., 4., 5., 6., 7., 8., 9.]), np.array([3.]), np.array([5., 6.])]
        axes = self.d.axes
        equals = min([np.array_equal(axes[i], expected_result[i]) for i in range(len(expected_result))])
        self.assertTrue(equals)

    def test_config_data_keys(self) -> None:
        expected_result = ['x', 'y', 'z']
        self.assertTrue(expected_result==self.d.config_data_keys)

    def test_shape(self) -> None:
        expected_result = (10, 1, 2)
        self.assertTrue(expected_result==self.d.shape)

    def test_meta_data(self) -> None:
        expected_result = {'sr': 200.0, 
                           'info': 'hello',
                            'hercules-version': hercules.__version__,
                            'hexbug-version': hercules.__hexbug_version__,
                            'python-script-version': hercules.__python_script_version__,
                            'python-script-dir': CONFIG.python_script_path}
        self.assertTrue(expected_result==self.d.meta_data)

    def test_get_path(self) -> None:

        expected_result_1 = ((9.0, 3.0, 6.0), (test_path / 'run19').absolute())
        expected_result_2 = ((1.0, 3.0, 5.0), (test_path /'run2').absolute())
        expected_result_3 = ((4.0, 3.0, 6.0), (test_path / 'run9').absolute())

        self.assertTrue(expected_result_1==self.d.get_path([100, 100, 100], method='interpolated'))
        self.assertTrue(expected_result_2==self.d.get_path([1., 3., 5.], method='exact'))
        self.assertTrue(expected_result_3==self.d.get_path([4, 0, 1], method='index'))

        with self.assertRaises(ValueError) as cm:
            self.d.get_path([4, 0, 1], method='inde')

    def test_iterator(self) -> None:

        expected_result = [((0.0, 3.0, 5.0), (test_path / 'run0').absolute()),
                            ((0.0, 3.0, 6.0), (test_path / 'run1').absolute()),
                            ((1.0, 3.0, 5.0), (test_path / 'run2').absolute()),
                            ((1.0, 3.0, 6.0), (test_path / 'run3').absolute()),
                            ((2.0, 3.0, 5.0), (test_path / 'run4').absolute()),
                            ((2.0, 3.0, 6.0), (test_path / 'run5').absolute()),
                            ((3.0, 3.0, 5.0), (test_path / 'run6').absolute()),
                            ((3.0, 3.0, 6.0), (test_path / 'run7').absolute()),
                            ((4.0, 3.0, 5.0), (test_path / 'run8').absolute()),
                            ((4.0, 3.0, 6.0), (test_path / 'run9').absolute()),
                            ((5.0, 3.0, 5.0), (test_path / 'run10').absolute()),
                            ((5.0, 3.0, 6.0), (test_path / 'run11').absolute()),
                            ((6.0, 3.0, 5.0), (test_path / 'run12').absolute()),
                            ((6.0, 3.0, 6.0), (test_path / 'run13').absolute()),
                            ((7.0, 3.0, 5.0), (test_path / 'run14').absolute()),
                            ((7.0, 3.0, 6.0), (test_path / 'run15').absolute()),
                            ((8.0, 3.0, 5.0), (test_path / 'run16').absolute()),
                            ((8.0, 3.0, 6.0), (test_path / 'run17').absolute()),
                            ((9.0, 3.0, 5.0), (test_path / 'run18').absolute()),
                            ((9.0, 3.0, 6.0), (test_path / 'run19').absolute())]
        
        result = []

        for entry in self.d:
            result.append(entry)

        self.assertTrue(result==expected_result)

    def test_dump_load(self) -> None:

        self.d.dump()
        d = Dataset.load(test_path)

        axes_self = self.d.axes
        axes_load = d.axes
        equals = min([np.array_equal(axes_self[i], axes_load[i]) for i in range(len(axes_self))])
        self.assertTrue(equals)
        self.assertTrue(self.d.meta_data == d.meta_data)
        self.assertTrue(self.d.config_data_keys == d.config_data_keys)
        self.assertTrue(self.d._directory == d._directory)
        self.assertTrue(self.d._index == d._index)


if __name__ == '__main__':
    unittest.main()
