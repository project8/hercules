
"""

Author: F. Thomas
Date: February 19, 2021

"""

import numpy as np
from scipy.interpolate import interp1d
import pickle
from pathlib import Path
from math import sqrt, atan2

from .constants import PY_DATA_NAME


class FileIndex:
    
    def __init__(self, directory):
        
        self.directory = Path(directory)
        
    def make_index(self, config_list):
        
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
        self.phi = np.sort(np.unique(phi))
        self.z = np.sort(np.unique(z))
        self.pitch = np.sort(np.unique(pitch))
        self.energy = np.sort(np.unique(energy))
        
        self.interpolate_all()
        
    def interpolate_all(self):
        
        #~ self.r_int = interp1d(self.r, self.r, kind='nearest', bounds_error=None, fill_value='extrapolate')
        #~ self.phi_int = interp1d(self.phi, self.phi, kind='nearest', bounds_error=None, fill_value='extrapolate')
        #~ self.z_int = interp1d(self.z, self.z, kind='nearest', bounds_error=None, fill_value='extrapolate')
        #~ self.pitch_int = interp1d(self.pitch, self.pitch, kind='nearest', bounds_error=None, fill_value='extrapolate')
        #~ self.energy_int = interp1d(self.energy, self.energy, kind='nearest', bounds_error=None, fill_value='extrapolate')
        
        self.r_int = self.interpolate(self.r)
        self.phi_int = self.interpolate(self.phi)
        self.z_int = self.interpolate(self.z)
        self.pitch_int = self.interpolate(self.pitch)
        self.energy_int = self.interpolate(self.energy)      
        
    def interpolate(self, x):
        
        if len(x)>1:
            x_int = interp1d(x, x, kind='nearest', bounds_error=None, fill_value='extrapolate')
        else:
            x_int = lambda y: x
            
        return x_int
        
    def get_data(self, energy, pitch, r, phi, z, interpolation=True):
        
        if interpolation:
            energy_i = self.energy_int(energy)
            pitch_i = self.pitch_int(pitch)
            r_i = self.r_int(r)
            phi_i = self.phi_int(phi)
            z_i = self.z_int(z)
        else:
            energy_i = energy
            pitch_i = pitch
            r_i = r
            phi_i = phi
            z_i = z
    
        sim_path = self.index[energy_i, pitch_i, r_i, phi_i, z_i]
        
        return load_sim(sim_path)
        
    def load_sim(self, path):
        return np.load(self.directory / path / PY_DATA_NAME)
        
    def dump(self):
        pickle.dump(self, open(self.directory/'index.p', "wb"))
        
    @classmethod
    def load(cls, path):
        path_p = Path(path)
        instance = pickle.load(open(path_p/'index.p', "rb"))
        instance.directory = path_p
        return instance
