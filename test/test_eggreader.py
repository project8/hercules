"""

Author: Mingyu (Charles) Li, Florian Thomas
Date: Apr. 12, 2021

"""

import os
from pathlib import Path

from matplotlib.figure import Figure

import matplotlib
import unittest
from hercules import KassLocustP3, SimConfig, ConfigList, Dataset, LocustP3File
import numpy as np
import matplotlib.pyplot as plt
import shutil

#matplotlib.use("Agg")  # No GUI

module_dir = Path(__file__).parent.absolute()
test_dataset_name = 'egg_reader_test'
test_path = module_dir / test_dataset_name
egg_filename = 'simulation.egg'


class EggReaderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        n_ch = 3
        r_range = np.linspace(0.000, 0.010, 1)
        theta_range = np.linspace(85.0, 90.0, 2)
        r_phi_range = np.linspace(0, 2 * np.pi / n_ch, 1)

        sim = KassLocustP3(test_path, use_kass=True, use_locust=True)
        configlist = ConfigList()
        
        for theta in theta_range:
            for r_phi in r_phi_range:
                for r in r_range:
                    x = r * np.cos(r_phi)
                    y = r * np.sin(r_phi)
                    config = SimConfig(
                        n_channels=n_ch,
                        seed_locust=42,
                        seed_kass=43,
                        egg_filename=egg_filename,
                        x_min=x,
                        x_max=x,
                        y_min=y,
                        y_max=y,
                        z_min=0,
                        z_max=0,
                        theta_min=theta,
                        theta_max=theta,
                        t_max=1e-6,
                        record_size=10000,
                        v_range=1.5e-7,
                        lo_frequency=25.8881e9,
                        acq_rate=250.0,
                        geometry='FreeSpaceGeometry_V00_00_10.xml')
                    configlist.add_config(config)

        sim(configlist)

        cls.dataset = Dataset.load(test_path)

    @classmethod
    def tearDownClass(cls) -> None:
        pass
        #shutil.rmtree(test_path)

    def test_0(self) -> None:

        paths =[test_path / 'index.he',
                test_path / 'info.txt',
                test_path / 'run0' / 'simulation.egg',
                test_path / 'run1' / 'simulation.egg'
                ]
        print('Testing simulation successful')
        for path in paths:
            self.assertTrue(path.exists())

    def test_ts_stream(self) -> None:
        for _, path in self.dataset:
            print(path)
            self._load_ts_stream(path)
            self._quick_load_ts_stream(path)

        ok = input('Plots look ok? (y/n): ').lower().strip() == 'y'
        self.assertTrue(ok)

    def _load_ts_stream(self, name) -> None:
        # Plot some specific test data

        file = LocustP3File(str(name / egg_filename))
        n_streams = file.n_streams

        for s in range(n_streams):
            data = file.load_ts_stream(s)
            channels = data.keys()
            acq_rate = file.get_stream_attrs()['acquisition_rate'] * 1e6

            fig, ax = plt.subplots()
            title = "DAQ Stream {} of {}".format(s, name)
            ax.set_title(title)

            for i in range(min(5, len(channels))):
                # Acq 0 and record 0
                data_ch = data[i][0, 0, :]
                ax.plot(np.arange(0, len(data_ch)) / acq_rate,
                        np.real(data_ch),
                        label="Ch {} Re".format(i),
                        ls="-",
                        color="C{}".format(i))
                ax.plot(np.arange(0, len(data_ch)) / acq_rate,
                        np.imag(data_ch),
                        label="Ch {} Im".format(i),
                        ls="--",
                        color="C{}".format(i))
            ax.set_xlabel(r"Time $[s]$")
            ax.set_ylabel(r"DAQ V $[V]$")
            ax.legend(loc="best")
            #self._save_fig(fig, f'{name}/plot_{s}.pdf', title)
            plt.show()

    def _quick_load_ts_stream(self, name) -> None:
        # Plot some specific test data
        file = LocustP3File(str(name / egg_filename))
        n_streams = file.n_streams
        n_ch = file.n_channels

        for s in range(n_streams):
            data = file.quick_load_ts_stream(s)
            acq_rate = file.get_stream_attrs()['acquisition_rate'] * 1e6

            n_acq = file.get_stream_attrs(s)['n_acquisitions']
            self.assertEqual((n_acq, n_ch), data.shape[:2])

            fig, ax = plt.subplots()
            title = "Quick DAQ Stream {} of {}".format(s, name)
            ax.set_title(title)

            for i in range(min(5, n_ch)):
                # Acq 0 and record 0
                data_ch = data[0, i, :]
                ax.plot(np.arange(0, len(data_ch)) / acq_rate,
                        np.real(data_ch),
                        label="Ch {} Re".format(i),
                        ls="-",
                        color="C{}".format(i))
                ax.plot(np.arange(0, len(data_ch)) / acq_rate,
                        np.imag(data_ch),
                        label="Ch {} Im".format(i),
                        ls="--",
                        color="C{}".format(i))
            ax.set_xlabel(r"Time $[s]$")
            ax.set_ylabel(r"DAQ V $[V]$")
            ax.legend(loc="best")
            #self._save_fig(fig, f'{name}/plot_quick_{s}.pdf', title)
            plt.show()

    def test_fft_stream(self) -> None:
        for _, path in self.dataset:
            print(path)
            self._load_fft_stream(path)
            self._quick_load_fft_stream(path)

        ok = input('Plots look ok? (y/n): ').lower().strip() == 'y'
        self.assertTrue(ok)

    def _load_fft_stream(self, name) -> None:

        file = LocustP3File(str(name / egg_filename))
        n_streams = file.n_streams

        for s in range(n_streams):
            freq, data = file.load_fft_stream(1024, s)
            channels = data.keys()

            fig, ax = plt.subplots()
            title = "FFT DAQ Stream {} of {}".format(s, name)
            ax.set_title(title)

            for i in channels:
                # Acq 0 and record 0
                data_ch = data[i][0, 0, :]
                ax.plot(
                    freq,
                    np.abs(np.mean(data_ch, axis=0)),
                    label="Ch {}".format(i),
                )
            ax.set_xlabel(r"Frequency $[Hz]$")
            ax.set_ylabel(r"FFT")
            ax.legend(loc="best")
            #self._save_fig(fig, title)
            plt.show()

    def _quick_load_fft_stream(self, name) -> None:
        # Plot some specific test data
        file = LocustP3File(str(name / egg_filename))
        n_streams = file.n_streams
        n_ch = file.n_channels

        window_size = 1024
        for s in range(n_streams):
            freq, data = file.quick_load_fft_stream(window_size, s)

            n_acq = file.get_stream_attrs(s)['n_acquisitions']
            self.assertEqual((n_acq, n_ch), data.shape[:2])
            self.assertEqual(window_size, data.shape[-1])

            fig, ax = plt.subplots()
            title = "FFT Quick DAQ Stream {} of {}".format(s, name)
            ax.set_title(title)

            for i in range(n_ch):
                # Acq 0
                data_ch = data[0, i, :]
                ax.plot(
                    freq,
                    np.abs(np.mean(data_ch, axis=0)),
                    label="Ch {}".format(i),
                )
            ax.set_xlabel(r"Frequency $[Hz]$")
            ax.set_ylabel(r"FFT")
            ax.legend(loc="best")
            #self._save_fig(fig, title)
            plt.show()

    def _save_fig(self, fig: Figure, out_file: str, title: str = None) -> None:
        # Saves the figure to data/images with title and closes the figure.
        # Default title to axes title if there's only one axes
        if title is None:
            ax_list = fig.get_axes()
            if len(ax_list) == 1:
                title = ax_list[0].get_title()
            else:
                raise ValueError("title cannot be None")
        fig.savefig(out_file, bbox_inches='tight', dpi=300)
        plt.close(fig) 


if __name__ == '__main__':
    unittest.main()
