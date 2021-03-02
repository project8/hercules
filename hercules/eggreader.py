
"""

Authors: F. Thomas, Mingyu (Charles) Li
Date: February 22, 2021

"""

import numpy as np
import h5py
from scipy.fft import fft, fftshift, fftfreq

def _applyDFT(data, dt, dftWindow):
        
    mean = np.mean(data, axis=-1)
    
    dataFreq = fftshift(fft(data-mean.reshape((data.shape[0],data.shape[1],1)), axis=-1),axes=-1)*np.sqrt(1/dftWindow)
    frequency = fftshift(fftfreq(dftWindow, d=dt))
    
    return frequency, dataFreq

class LocustP3File:
    
    #todo only public access maybe
    
    __intMax = {8:255, 16:65535}
    
    def __init__(self, filename):
        
        self.__inputfile = h5py.File(filename, 'r')
        self.__getAttributes()
        
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
        
        return self.__inputfile.keys()
        
    def __convertToVoltage(self, data):
        
        return data/self.__intMax[self.__bit_depth]*self.__voltage_range\
                + self.__voltage_offset
        
    def __reshapeTS(self, data):
        
        return data.reshape((self.n_channels, -1))
        
        
    def __TStoComplex(self, data):
        
        return data[::2] + 1j*data[1::2]
        
    def loadTS(self):
        """
        TODO: Change this to a stream by stream basis
        Load the time series.
        """
        
        data = self.__inputfile['streams']['stream0']['acquisitions']['0'][0]
        data = self.__convertToVoltage(data)
        data = self.__TStoComplex(data)
        data = self.__reshapeTS(data)
        
        return data
        
    def loadFFT(self, dftWindow):
        """
        TODO: Change this to a stream by stream basis
        Load the FFT of the time series
        """
        
        ts = self.loadTS()
        
        nSlices = int(ts.shape[1]/dftWindow)
        tsSliced = ts[:,:nSlices*dftWindow].reshape(
                                                (self.n_channels, nSlices, -1))
        
        #explicit copy to rearange order in memory
        tsFinal = tsSliced.transpose(1,0,2).copy()
        
        frequency, dataFreq = _applyDFT(tsFinal, 1/self.acq_rate, dftWindow)
        
        return frequency, dataFreq
