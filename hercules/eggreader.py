
"""

Author: F. Thomas
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
        attr = self.__inputfile['streams']['stream0'].attrs
        self.sr = attr['acquisition_rate']*1e6
        self.__bitDepth = attr['bit_depth']
        self.nChannels = attr['n_channels']
        self.__recordSize = attr['record_size']
        
        attr = self.__inputfile['channels']['channel0'].attrs
        self.__vRange = attr['voltage_range']
        self.__vOffset = attr['voltage_offset']
        
    def keys(self):
        
        return self.__inputfile.keys()
        
    def __convertToVoltage(self, data):
        
        return data/self.__intMax[self.__bitDepth]*self.__vRange\
                + self.__vOffset
        
    def __reshapeTS(self, data):
        
        return data.reshape((self.nChannels, -1))
        
        
    def __TStoComplex(self, data):
        
        return data[::2] + 1j*data[1::2]
        
    def loadTS(self):
        
        data = self.__inputfile['streams']['stream0']['acquisitions']['0'][0]
        data = self.__convertToVoltage(data)
        data = self.__TStoComplex(data)
        data = self.__reshapeTS(data)
        
        return data
        
    def loadFFT(self, dftWindow):
        
        ts = self.loadTS()
        
        nSlices = int(ts.shape[1]/dftWindow)
        tsSliced = ts[:,:nSlices*dftWindow].reshape(
                                                (self.nChannels, nSlices, -1))
        
        #explicit copy to rearange order in memory
        tsFinal = tsSliced.transpose(1,0,2).copy()
        
        frequency, dataFreq = _applyDFT(tsFinal, 1/self.sr, dftWindow)
        
        return frequency, dataFreq
