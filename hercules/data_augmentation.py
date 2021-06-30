
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
    TO DO: Check amplitude calculation?
    """
    noise_amp = np.sqrt(constants.k*param_dict['noise_temperature']*param_dict['bandwidth'])
    return data+np.random.randn(*data.shape)*noise_amp

def experimental_noise(data, param_dict):
    """
    None white noise, meaning this is frequency dependent but still uncorrelated for different parameters
    Requires a noise PSD and normalisation.
    To Be implemented
    """
    return 0