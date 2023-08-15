
"""

Author: F. Thomas
Date: October 17, 2022

"""

import numpy as np
from scipy.interpolate import interp1d
import dill as pickle
from pathlib import Path
import numbers

from .constants import PY_DATA_NAME


class Constant:
    
    def __init__(self, x):
        
        self.x = x
        
    def __call__(self, x):
        return self.x


class Dataset:
    
    _class_version = '2.0'
    
    def __init__(self, directory, config_list, interpolate=True):
        
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._version = self._class_version
        self._interpolate_axes = interpolate
        self._make_index(config_list)
        
    def _make_index(self, config_list):
        """Create the index dictionary.
        
        Parameters
        ----------
        config_list : ConfigList
            A ConfigList object
        """
        
        print('Making file index')
        
        self._index = {}
        self._meta_data = config_list.get_meta_data()
        self._config_data_keys = list(config_list.get_config_data_keys()) # maps a list index to a key
        config_list_internal = config_list.get_internal_list()

        self._initialize_axes(config_list_internal)
        
        for i, sim_config in enumerate(config_list_internal):
            path = sim_config.sim_name
            config_data = sim_config.get_config_data()

            for k in config_data:
                k_ind = self._config_data_keys.index(k)
                self._axes[k_ind][i] = config_data[k]
            
            self._index[tuple(config_data.values())] = path

        for i in range(len(self._axes)):
            self._axes[i] = np.sort(np.unique(self._axes[i]))
        
        if self._interpolate_axes:
            self._interpolate_all()

    def _initialize_axes(self, config_list_internal):
        self._axes = []
        config_data0 = config_list_internal[0].get_config_data()
        for k in self._config_data_keys:
            var0 = config_data0[k]

            if isinstance(var0, numbers.Number):
                self._axes.append(np.empty(len(config_list_internal), dtype=type(var0)))
            else:
                self._axes.append([i for i in range(len(config_list_internal))])
                if self._interpolate:
                    print('Warning! Interpolation of axes not possible for non-numeric types! Deactivating interpolation')
                    self._interpolate_axes = False
        
    def _interpolate_all(self):
        
        print('Making interpolation')

        self._axes_int = []

        for ax in self._axes:
            self._axes_int.append(self._interpolate(ax))
        
    def _interpolate(self, x):
        
        if len(x)>1:
            x_int = interp1d(x, x, kind='nearest', bounds_error=None, fill_value='extrapolate')
        else:
            x_int = Constant(x)
            
        return x_int
        
    def get_data(self, params, interpolation=True):
        
        parameters, sim_path = self.get_path(params, interpolation=interpolation)
        
        path = sim_path.relative_to(self._directory)
        
        return parameters, self.load_sim(path)
        
    def _load_sim(self, path):
        return np.load(self._directory / path / PY_DATA_NAME)
        
    def get_path(self, params, method='interpolated'):

        if len(params) != len(self._axes):
            raise ValueError(f'params has len {len(params)} but dataset expects len {len(self._axes)}!')

        if method == 'interpolated':
            if not self._interpolate:
                raise ValueError('Dataset is not interpolated!') 
            key = [self._axes_int[i](params[i]).item() for i in range(len(params))]
        elif method == 'index':
            key = [self._axes[i][params[i]] for i in range(len(params))]
        elif method == 'exact':
            key = params
        else:
            raise ValueError("method can only take values 'interpolated', 'index' or 'exact'!")

        parameters = tuple(key)

        sim_path = self._index.get(parameters) # self._index[parameters]

        if sim_path is None:
            raise KeyError(f'{parameters} is not part of the dataset!')
        
        return parameters, self._directory / sim_path
    
    def __iter__(self):
        self._it_index = tuple(0 for i in range(len(self.shape)))
        self._it_stop = False
        return self

    def __next__(self):

        if not self._it_stop:

            new_index = list(self._it_index)

            for i in reversed(range(len(self._it_index))):
                new_index[i] += 1
                if new_index[i] == self.shape[i]:
                    new_index[i] = 0
                else:
                    break

            old_index = self._it_index
            self._it_index = tuple(new_index)

            if self._it_index == tuple(0 for i in range(len(self.shape))):
                self._it_stop = True

            return self.get_path(old_index, method='index')
        else:
            raise StopIteration
    
    @property
    def config_data_keys(self):
        return self._config_data_keys
    
    @property
    def axes(self):
        return self._axes
    
    @property
    def shape(self):
        return tuple(len(ax) for ax in self._axes)
    
    @property
    def meta_data(self):
        return self._meta_data
        
    def dump(self):
        with open(self._directory/'index.he', "wb") as f:
            pickle.dump(self, f, protocol=4)

        with open(self._directory/'info.txt', "w") as f:
            f.write(f'Hercules dataset version {self._version}\n')
            f.write('Metadata:\n')
            f.write(str(self._meta_data))
            f.write('\n\n')
            f.write('Dataset has following configurations:\n')

            for i, ax in enumerate(self._axes):
                n = len(ax)
                lower = ax[0]
                upper = ax[-1]
                ax_name = self._config_data_keys[i]
                f.write(f'{ax_name}: {n} values in [{lower},{upper}] \n')
        
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

        instance._directory = path_p
        return instance