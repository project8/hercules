
"""

Author: F. Thomas
Date: February 22, 2021

"""

import numpy as np
import h5py
from scipy.fft import fft, fftshift, fftfreq

def _apply_DFT(data, dt, dft_window):
        
    mean = np.mean(data, axis=-1)
    
    normalization = np.sqrt(1/dft_window)
    data_freq = fft(data-mean.reshape((data.shape[0],data.shape[1],1)), axis=-1)
    data_freq = fftshift(data_freq, axes=-1)                 
    data_freq = data_freq*normalization
    frequency = fftshift(fftfreq(dft_window, d=dt))
    
    return frequency, data_freq

class LocustP3File:
    
    _int_max = {8:255, 16:65535}
    
    def __init__(self, file_name):
        
        self._input_file = h5py.File(file_name, 'r')
        self._get_attributes()
        
    # -------- private part --------
        
    def _get_attributes(self):
        
        #not a full list of attributes -> expand
        attr = self._input_file['streams']['stream0'].attrs
        self._sr = attr['acquisition_rate']*1e6
        self._bit_depth = attr['bit_depth']
        self._n_channels = attr['n_channels']
        self._record_size = attr['record_size']
        
        attr = self._input_file['channels']['channel0'].attrs
        self._v_range = attr['voltage_range']
        self._v_offset = attr['voltage_offset']
        
    def _convert_to_voltage(self, data):
        
        return data/self._int_max[self._bit_depth]*self._v_range\
                + self._v_offset
        
    def _reshape_ts(self, data):
        
        return data.reshape((self._n_channels, -1))
        
        
    def _ts_to_complex(self, data):
        
        return data[::2] + 1j*data[1::2]
        
    # -------- public part --------
        
    def keys(self):
        
        return self._input_file.keys()
        
    def load_ts(self):
        
        data = self._input_file['streams']['stream0']['acquisitions']['0'][0]
        data = self._convert_to_voltage(data)
        data = self._ts_to_complex(data)
        data = self._reshape_ts(data)
        
        return data
        
    def load_fft(self, dft_window):
        
        ts = self.load_ts()
        
        n_slices = int(ts.shape[1]/dft_window)
        ts_sliced = ts[:,:n_slices*dft_window].reshape(
                                                (self._n_channels, n_slices, -1))
        
        #explicit copy to rearange order in memory
        ts_final = ts_sliced.transpose(1,0,2).copy()
        
        frequency, data_freq = _apply_DFT(ts_final, 1/self._sr, dft_window)
        
        return frequency, data_freq
    
    @property
    def sr(self):
        return self._sr
        
    @property
    def n_channels(self):
        return self._n_channels
