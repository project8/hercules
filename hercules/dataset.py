
"""

Author: F. Thomas
Date: October 17, 2022

"""

import numpy as np
from scipy.interpolate import interp1d
import pickle
from pathlib import Path
from math import sqrt, atan2

from .constants import PY_DATA_NAME


class Constant:
    
    def __init__(self, x):
        
        self.x = x
        
    def __call__(self, x):
        return self.x

class Dataset:
    
    _class_version = '2.0'
    
    def __init__(self, directory):
        
        self.directory = Path(directory)
        self._version = self._class_version
        
    def make_index(self, config_list):
        """Create the index dictionary.
        
        Parameters
        ----------
        config_list : ConfigList
            A ConfigList object
        """
        
        print('Making file index')
        
        self._index = {}
        self._meta_data = config_list.get_meta_data()
        self._config_data_keys = config_list.get_config_data_keys()
        config_list_internal = config_list.get_internal_list()

        self._axes_dict = {k: np.empty(len(config_list_internal)) for k in self._config_data_keys}
        
        for i, sim_config in enumerate(config_list_internal):
            path = sim_config.sim_name
            config_data = sim_config.get_config_data()

            for k in config_data:
                self._axes_dict[k][i] = config_data[k]
            
            self._index[tuple(config_data.values())] = path

        for k in self._axes_dict:
            self._axes_dict[k] = np.sort(np.unique(self._axes_dict[k]))
        
        self.interpolate_all()
        
    def interpolate_all(self):
        
        print('Making interpolation')

        self._axes_dict_int = {}

        for k in self._axes_dict:
            self._axes_dict_int[k] = self.interpolate(self._axes_dict[k])    
        
    def interpolate(self, x):
        
        if len(x)>1:
            x_int = interp1d(x, x, kind='nearest', bounds_error=None, fill_value='extrapolate')
        else:
            x_int = Constant(x)
            
        return x_int
        
    def get_data(self, params, interpolation=True):
        
        parameters, sim_path = self.get_path(params, interpolation=interpolation)
        
        path = sim_path.relative_to(self.directory)
        
        return parameters, self.load_sim(path)
        
    def load_sim(self, path):
        return np.load(self.directory / path / PY_DATA_NAME)
        
    def get_path(self, params, method='interpolated'):

        if len(params) != len(self._axes_dict):
            raise ValueError(f'params has len {len(params)} but dataset expects len {len(self._axes_dict)}!')

        if method == 'interpolated':
            key = [self._axes_dict_int[i](params[i]).item() for i in range(len(params))]
        elif method == 'index':
            key = [self._axes_dict[i][params[i]] for i in range(len(params))]
        elif method == 'exact':
            key = params
        else:
            raise ValueError("method can only take values 'interpolated', 'index' or 'exact'!")

        parameters = tuple(key)

        sim_path = self._index.get(parameters) # self._index[parameters]

        if sim_path is None:
            raise KeyError(f'{parameters} is not part of the dataset!')
        
        return parameters, self.directory / sim_path
    
    @property
    def config_data_keys(self):
        return self._config_data_keys
    
    @property
    def axes_dict(self):
        return self._axes_dict
    
    @property
    def shape(self):
        return tuple(len(self._axes_dict[k] for k in self._axes_dict))
        
    def dump(self):
        with open(self.directory/'index.he', "wb") as f:
            pickle.dump(self, f, protocol=4)

        with open(self.directory/'info.txt', "w") as f:
            f.write(f'Hercules dataset version {self._version}\n')
            f.write('Metadata:\n')
            f.write(str(self._meta_data))
            f.write('\n\n')
            f.write('Dataset has following configurations:\n')

            for k in self._axes_dict:
                n = len(self._axes_dict[k])
                lower = self._axes_dict[k][0]
                upper = self._axes_dict[k][-1]
                f.write(f'{k}: {n} values in [{lower},{upper}] \n')
        
    @classmethod
    def load(cls, path):
        path_p = Path(path)

        with open(path_p/'index.he', "rb") as f:
            instance = pickle.load(f)

        if type(instance) is not cls:
            raise RuntimeError('Path does not point to a hercules dataset')
        
        if '_version' not in dir(instance):
            instance_version = '1.0'
        else:
            instance_version = instance._version
        
        if instance_version != cls._class_version:
            raise RuntimeError(f'Tried to load a version {instance_version} hercules dataset with version {cls._class_version}! To open this file you need an older hercules release')

        instance.directory = path_p
        return instance