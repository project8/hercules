
"""

Author: W. Van De Pontseele
Date: June 30, 2021

"""
import numpy as np 
from scipy import constants

def transform(data, func, param_dict):
    """
    Takes time series data from quick_load_ts_stream with shape:
    (n_acquisitions, n_channels, n_records * record_size)
    """
    return func(data, param_dict)

# --- Specific data augmentation functions below ---

def whitegaussiannoise(data, param_dict):
    """
    White Gaussian Noise added to the voltage time series
    This implementation is fully uncorrelated over time/channels.
    Requires a temperature and bandwidth
    https://en.wikipedia.org/wiki/Johnson%E2%80%93Nyquist_noise
    50 Ohm matched transmission line
    """
    noise_amp = np.sqrt(50*constants.k*param_dict['noise_temperature']*param_dict['bandwidth'])
    noise = np.random.multivariate_normal([0,0], np.eye(2) * noise_amp / 2, data.shape).view(np.complex128)
    return data+noise

def experimental_noise(data, param_dict):
    """
    None white noise, meaning this is frequency dependent but still uncorrelated for different parameters
    Requires a noise PSD and normalisation.
    """
    return 0