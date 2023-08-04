
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
        
        print('Making file index')
        
        self.index = {}
        r_np = np.empty(len(config_list))
        phi_np = np.empty(len(config_list))
        z_np = np.empty(len(config_list))
        pitch_np = np.empty(len(config_list))
        energy_np = np.empty(len(config_list))
        
        for i, sim_config in enumerate(config_list):
            path = sim_config.sim_name
            x = sim_config._kass_config._config_dict['x_min']
            y = sim_config._kass_config._config_dict['y_min']
            z = sim_config._kass_config._config_dict['z_min']
            pitch = sim_config._kass_config._config_dict['theta_min']
            energy = sim_config._kass_config._config_dict['energy']
            
            r = sqrt(x**2 + y**2)
            phi = atan2(y, x)
            
            self.index[energy, pitch, r, phi, z] = path
            
            r_np[i] = r
            phi_np[i] = phi
            z_np[i] = z
            pitch_np[i] = pitch
            energy_np[i] = energy
            
        self.r = np.sort(np.unique(r_np))
        self.phi = np.sort(np.unique(phi_np))
        self.z = np.sort(np.unique(z_np))
        self.pitch = np.sort(np.unique(pitch_np))
        self.energy = np.sort(np.unique(energy_np))
        
        self.interpolate_all()
        
    def interpolate_all(self):
        
        print('Making interpolation')
        
        self.r_int = self.interpolate(self.r)
        self.phi_int = self.interpolate(self.phi)
        self.z_int = self.interpolate(self.z)
        self.pitch_int = self.interpolate(self.pitch)
        self.energy_int = self.interpolate(self.energy)      
        
    def interpolate(self, x):
        
        if len(x)>1:
            x_int = interp1d(x, x, kind='nearest', bounds_error=None, fill_value='extrapolate')
        else:
            x_int = Constant(x)
            
        return x_int
        
    def get_data(self, energy, pitch, r, phi, z, interpolation=True):
        
        parameters, sim_path = self.get_path(energy, pitch, r, phi, z, interpolation=interpolation)
        
        path = sim_path.relative_to(self.directory)
        
        return parameters, self.load_sim(path)
        
    def load_sim(self, path):
        return np.load(self.directory / path / PY_DATA_NAME)
        
    def get_path(self, energy, pitch, r, phi, z, interpolation=True):
        
        if interpolation:
            energy_i = self.energy_int(energy).item()
            pitch_i = self.pitch_int(pitch).item()
            r_i = self.r_int(r).item()
            phi_i = self.phi_int(phi).item()
            z_i = self.z_int(z).item()
        else:
            energy_i = energy
            pitch_i = pitch
            r_i = r
            phi_i = phi
            z_i = z
            
        parameters = (energy_i, pitch_i, r_i, phi_i, z_i)
        sim_path = self.index[parameters]
        
        return parameters, self.directory / sim_path
        
    def dump(self):
        with open(self.directory/'index.he', "wb") as f:
            pickle.dump(self, f, protocol=4)
        
    @classmethod
    def load(cls, path):
        path_p = Path(path)

        with open(path_p/'index.he', "rb") as f:
            instance = pickle.load(f)

        if type(instance) is not cls:
            raise TypeError('Path does not point to a hercules dataset')
        
        if '_version' not in dir(instance):
            instance_version = '1.0'
        else:
            instance_version = instance._version
        
        if instance_version != cls._class_version:
            raise RuntimeError(f'Tried to load a version {instance_version} hercules dataset with version {cls._class_version}! To open this file you need an older hercules release')

        instance.directory = path_p
        return instance