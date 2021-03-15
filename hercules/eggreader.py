
"""

Authors: F. Thomas, Mingyu (Charles) Li
Date: February 22, 2021

"""

__all__ = ['LocustP3File']

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
        
    def __getAttributes(self):
        #not a full list of attributes -> expand

        ### Attrs see https://monarch.readthedocs.io/en/latest/EggStandard.v3.2.0.html#file-structure
        # A dict for file attrs
        self.file_attrs = self.__inputfile.attrs

        # A dict of dict for stream attrs (includes all streams)
        self.streams_attrs = self.__get_streams_attrs()

        # A dict of dict for channel attrs (includes all channels)
        self.channels_attrs = self.__get_channels_attrs()

        # Some useful attributes obtained from default file/stream0
        self.n_channels = self.file_attrs['n_channels']
        self.n_streams = self.file_attrs['n_streams']
        # Channel -> Stream mapping
        self.channel_streams = self.file_attrs['channel_streams']

        # TODO: Consider move this to individual stream processing?
        attr = self.get_stream_attrs(0)
        # Acquisition rate from MHz -> Hz
        self.acq_rate = attr['acquisition_rate'] * 1e6
        # bit_depth
        self.__bit_depth = attr['bit_depth']
        self.__record_size = attr['record_size']
        
        attr = self.get_channel_attrs(0)
        self.__voltage_range = attr['voltage_range']
        self.__voltage_offset = attr['voltage_offset']
        
    def print_file_attrs(self):
        """
        Print egg file attributes
        """
        for (k, it) in self.file_attrs.items():
            print("key: " + k)
            print("value: " + str(it))

    def __get_streams_attrs(self):
        """
        Get all streams attrs
        """
        h5file = self.__inputfile
        streams_attr = {}
        for (key, item) in h5file['streams'].items():
            att = item.attrs
            streams_attr[key] = att
        return streams_attr

    def get_stream_attrs(self, stream: int=0):
        """
        Get the attributes of a specific stream. Only a single stream number is allowed. Defaults to stream 0.
        """
        try:
            attrs = self.streams_attrs["stream{}".format(stream)]
        except KeyError as kerr:
            print(kerr)
        except Exception as e:
            print(e)
            raise
        return attrs

    def print_stream_attrs(self, streams=[0]):
        """
        Print the attributes of streams. Defaults to only stream 0.
        """
        for s in streams:
            print("Getting attributes for stream {}".format(s))
            attrs = self.get_stream_attrs(s)
            for (k, it) in attrs.items():
                print("key: " + k)
                print("value: " + str(it))

    def __get_channels_attrs(self):
        """
        Get all channels attrs
        """
        h5file = self.__inputfile
        channels_attr = {}
        for (key, item) in h5file['channels'].items():
            att = item.attrs
            channels_attr[key] = att
        return channels_attr

    def get_channel_attrs(self, channel: int=0):
        """
        Get the attributes of a specific channel. Only a single channel number is allowed. Defaults to channel 0.
        """
        try:
            attrs = self.channels_attrs["channel{}".format(channel)]
        except KeyError as kerr:
            print(kerr)
        except Exception as e:
            print(e)
            raise
        return attrs

    def print_channel_attrs(self, channels=[0]):
        """
        Print the attributes of channels. Defaults to only channel 0.
        """
        for c in channels:
            print("Getting attributes for channel {}".format(c))
            attrs = self.get_channel_attrs(c)
            for (k, it) in attrs.items():
                print("key: " + k)
                print("value: " + str(it))

    def keys(self):
        
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
        """
        TODO: Change this to a stream by stream basis
        Load the time series.
        """
        
        data = self._input_file['streams']['stream0']['acquisitions']['0'][0]
        data = self._convert_to_voltage(data)
        data = self._ts_to_complex(data)
        data = self._reshape_ts(data)
        
        return data
        
    def load_fft(self, dft_window):
        """
        TODO: Change this to a stream by stream basis
        Load the FFT of the time series
        """
                
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
