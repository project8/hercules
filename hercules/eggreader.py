"""

Authors: F. Thomas, Mingyu (Charles) Li
Date: February 22, 2021

"""

# __all__ = ['LocustP3File']

import numpy as np
import h5py
from scipy.fft import fft, fftshift, fftfreq


def _apply_DFT(data, dt, dft_window):

    mean = np.mean(data, axis=-1)

    normalization = np.sqrt(1 / dft_window)
    data_freq = fft(data - mean.reshape((data.shape[0], data.shape[1], 1)),
                    axis=-1)
    data_freq = fftshift(data_freq, axes=-1)
    data_freq = data_freq * normalization
    frequency = fftshift(fftfreq(dft_window, d=dt))

    return frequency, data_freq


def _to_complex(data):
    """
    Convert to complex
    """
    return data[::2] + 1j * data[1::2]


class LocustP3File:

    _int_max = {8: 255, 16: 65535}

    def __init__(self, file_name):

        self._input_file = h5py.File(file_name, 'r')
        self._get_attributes()

    def _get_attributes(self):
        #not a full list of attributes -> expand

        ### Attrs see https://monarch.readthedocs.io/en/latest/EggStandard.v3.2.0.html#file-structure
        # A dict for file attrs
        self._file_attrs = self._input_file.attrs

        # A dict of dict for stream attrs (includes all streams)
        self._streams_attrs = self._get_streams_attrs()

        # A dict of dict for channel attrs (includes all channels)
        self._channels_attrs = self._get_channels_attrs()

        # Some useful attributes obtained from default file/stream0
        self._n_channels = self._file_attrs['n_channels']
        self._n_streams = self._file_attrs['n_streams']
        # Channel -> Stream mapping
        self._channel_streams = self._file_attrs['channel_streams']

    def _get_streams_attrs(self):
        """
        Get all streams attrs
        """
        h5file = self._input_file
        streams_attr = {}
        for (key, item) in h5file['streams'].items():
            att = item.attrs
            streams_attr[key] = att
        return streams_attr

    def _get_channels_attrs(self):
        """
        Get all channels attrs
        """
        h5file = self._input_file
        channels_attr = {}
        for (key, item) in h5file['channels'].items():
            att = item.attrs
            channels_attr[key] = att
        return channels_attr

    def _convert_to_voltage(self, data, channel):
        """
        Convert data from digitizer unit to volts, specific by channel
        """
        attr = self.get_channel_attrs(channel)
        bit_depth = attr['bit_depth']
        voltage_range = attr['voltage_range']
        voltage_offset = attr['voltage_offset']
        result = data / self._int_max[
            bit_depth] * voltage_range + voltage_offset
        return result

    def _reshape_ts(self, data):

        return data.reshape((self._n_channels, -1))

    # -------- public part -------- #

    def load_ts_stream(self, stream: int = 0):
        """
        Load the time series in a stream by stream basis. Only a single stream is allowed.
        The dataset is structured as (dict of arrays):
        {Channel #: [Acquisition0: [Record0, Record1, ...], Acquisition1: [...], ...], Channel #: [...], ...}
        """
        try:
            s = self._input_file['streams']["stream{}".format(stream)]
        except KeyError as kerr:
            print(kerr)
        except Exception as e:
            print(e)
            raise
        attr = self.get_stream_attrs(stream)
        # Rate from MHz -> Hz
        n_acq = attr['n_acquisitions']
        channels = attr['channels']
        ch_format = attr['channel_format']

        data = []
        for i in range(n_acq):
            acq = s['acquisitions']['%s' % i]
            n_records = acq.attrs['n_records']
            temp = []
            for j in range(n_records):
                temp_data = _to_complex(acq[j])
                if ch_format == 1:
                    temp.append(temp_data.reshape((len(channels), -1)))
                elif ch_format == 0:
                    n_ch = len(channels)
                    for k in range(n_ch):
                        temp_data_copy = []
                        temp_data_copy.append(temp_data[k::n_ch])
                    temp.append(temp_data_copy)
                else:
                    raise RuntimeError("Invalid channel format")
            data.append(temp)

        data = np.asarray_chkfinite(data)
        result = {}
        for ch in channels:
            result[ch] = self._convert_to_voltage(data[:, :, ch, :], ch)

        return result

    def load_fft_stream(self, dft_window, stream: int = 0):
        """
        TODO: Change this to a stream by stream basis
        Load the FFT of the time series
        """
        try:
            s = self._input_file['streams']["stream{}".format(stream)]
        except KeyError as kerr:
            print(kerr)
        except Exception as e:
            print(e)
            raise
        attr = self.get_stream_attrs(stream)
        # Rate from MHz -> Hz
        acq_rate = attr['acquisition_rate'] * 1e6
        n_acq = attr['n_acquisitions']
        record_size = attr['record_size']
        channels = attr['channels']
        ch_format = attr['channel_format']

        ts = self.load_ts()

        n_slices = int(ts.shape[1] / dft_window)
        ts_sliced = ts[:, :n_slices * dft_window].reshape(
            (self._n_channels, n_slices, -1))

        #explicit copy to rearange order in memory
        ts_final = ts_sliced.transpose(1, 0, 2).copy()

        frequency, data_freq = _apply_DFT(ts_final, 1 / self._acq_rate,
                                          dft_window)

        return frequency, data_freq

    @property
    def n_channels(self):
        return self._n_channels

    @property
    def n_streams(self):
        return self._n_streams

    @property
    def channel_streams(self):
        return self._channel_streams

    def print_file_attrs(self):
        """
        Print egg file attributes
        """
        for (k, it) in self._file_attrs.items():
            print("key: " + k)
            print("value: " + str(it))

    def get_stream_attrs(self, stream: int = 0):
        """
        Get the attributes of a specific stream. Only a single stream number is allowed. Defaults to stream 0.
        """
        try:
            attrs = self._streams_attrs["stream{}".format(stream)]
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

    def get_channel_attrs(self, channel: int = 0):
        """
        Get the attributes of a specific channel. Only a single channel number is allowed. Defaults to channel 0.
        """
        try:
            attrs = self._channels_attrs["channel{}".format(channel)]
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
