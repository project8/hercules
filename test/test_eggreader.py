"""

Author: Mingyu (Charles) Li
Date: Apr. 12, 2021

"""

# Add module to sys path for detection in case the user has yet installed the module
import sys
import os
from pathlib import Path

from matplotlib.figure import Figure
FILE_DIR = Path(__file__).parent.absolute()
ROOT_DIR = FILE_DIR.parent
sys.path.insert(0, ROOT_DIR)

import matplotlib
import unittest
import hercules as he
import numpy as np
import matplotlib.pyplot as plt
matplotlib.use("Agg")  # No GUI


class LocustTest(unittest.TestCase):
    def setUp(self) -> None:
        n_ch = 3
        r_range = np.linspace(0.002, 0.008, 2)
        theta_range = np.linspace(89.7, 90.0, 2)
        r_phi_range = np.linspace(0, 2 * np.pi / n_ch, 1)

        test_data_dict = {}
        for theta in theta_range:
            for r_phi in r_phi_range:
                for r in r_range:
                    x = r * np.cos(r_phi)
                    y = r * np.sin(r_phi)
                    r_phi_deg = np.rad2deg(r_phi)
                    name = "Sim_theta_{:.4f}_R_{:.4f}_phi_{:.4f}".format(
                        theta, r, r_phi_deg)
                    config = he.SimConfig(
                        name,
                        n_channels=n_ch,
                        seed_locust=42,
                        seed_kass=43,
                        egg_filename="simulation.egg",
                        x_min=x,
                        x_max=x,
                        y_min=y,
                        y_max=y,
                        z_min=0,
                        z_max=0,
                        theta_min=theta,
                        theta_max=theta,
                        t_max=5e-7,
                        record_size=3000,
                        v_range=3.0e-7,
                        geometry='FreeSpaceGeometry_V00_00_10.xml')
                    test_data_dict[name] = config

        self.test_data_dict = test_data_dict

        # Check if the test dir exists and names are correct
        self.test_data_dir = test_data_dir = FILE_DIR / "test_dir"
        if not self.test_data_dir.is_dir():
            print("Test directory not found. Creating one...")
            os.mkdir(test_data_dir)
        sub_dir_list = [d.parts[-1] for d in test_data_dir.iterdir() if d.is_dir()]
        missing_dir_list = list(
            set(self.test_data_dict.keys()) - set(sub_dir_list))
        print(
            "The following test data are missing: {}".format(missing_dir_list))

        # Create missing test data
        # Note: if data is missing, must run the tests in cmd line to create the data
        for l in missing_dir_list:
            print("Creating test data: {}".format(l))
            sim = he.KassLocustP3(str(test_data_dir))
            sim(self.test_data_dict[l])

    def test_ts_stream(self) -> None:
        for k in self.test_data_dict.keys():
            self._load_ts_stream(k)
            self._quick_load_ts_stream(k)

    def _load_ts_stream(self, name) -> None:
        # Plot some specific test data
        file_name = self.test_data_dir.joinpath(name).joinpath(
            "simulation.egg")
        file = he.LocustP3File(str(file_name))
        n_streams = file.n_streams

        for s in range(n_streams):
            data = file.load_ts_stream(s)
            channels = data.keys()
            acq_rate = file.get_stream_attrs()['acquisition_rate'] * 1e6

            fig, ax = plt.subplots()
            title = "DAQ Stream {} of {}".format(s, name)
            ax.set_title(title)

            for i in channels:
                # Acq 0 and record 0
                data_ch = data[i][0, 0, :]
                ax.plot(
                    np.arange(0, len(data_ch)) / acq_rate,
                    np.abs(data_ch),
                    label="Ch {}".format(i),
                )
            ax.set_xlabel(r"Time $[s]$")
            ax.set_ylabel(r"DAQ V $[V]$")
            ax.legend(loc="best")
            self._save_fig(fig, title)

    def _quick_load_ts_stream(self, name) -> None:
        # Plot some specific test data
        file_name = self.test_data_dir.joinpath(name).joinpath(
            "simulation.egg")
        file = he.LocustP3File(str(file_name))
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

            for i in range(n_ch):
                # Acq 0
                data_ch = data[0, i, :]
                ax.plot(
                    np.arange(0, len(data_ch)) / acq_rate,
                    np.abs(data_ch),
                    label="Ch {}".format(i),
                )
            ax.set_xlabel(r"Time $[s]$")
            ax.set_ylabel(r"DAQ V $[V]$")
            ax.legend(loc="best")
            self._save_fig(fig, title)

    def test_fft_stream(self) -> None:
        for k in self.test_data_dict.keys():
            self._load_fft_stream(k)
            self._quick_load_fft_stream(k)

    def _load_fft_stream(self, name) -> None:
        # Plot some specific test data
        file_name = self.test_data_dir.joinpath(name).joinpath(
            "simulation.egg")
        file = he.LocustP3File(str(file_name))
        n_streams = file.n_streams

        for s in range(n_streams):
            freq, data = file.load_fft_stream(256, s)
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
            self._save_fig(fig, title)

    def _quick_load_fft_stream(self, name) -> None:
        # Plot some specific test data
        file_name = self.test_data_dir.joinpath(name).joinpath(
            "simulation.egg")
        file = he.LocustP3File(str(file_name))
        n_streams = file.n_streams
        n_ch = file.n_channels

        for s in range(n_streams):
            freq, data = file.quick_load_fft_stream(256, s)

            n_acq = file.get_stream_attrs(s)['n_acquisitions']
            self.assertEqual((n_acq, n_ch), data.shape[:2])

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
            self._save_fig(fig, title)

    def _save_fig(self, fig: Figure, title: str = None) -> None:
        # Saves the figure to data/images with title and closes the figure.
        # Default title to axes title if there's only one axes
        if title is None:
            ax_list = fig.get_axes()
            if len(ax_list) == 1:
                title = ax_list[0].get_title()
            else:
                raise ValueError("title cannot be None")
        out_file = os.path.join(
            str(self.test_data_dir),
            title.replace(' ', '_').replace('.', '-') + ".pdf")
        fig.savefig(out_file, bbox_inches='tight', dpi=300)
        plt.close(fig)


if __name__ == '__main__':
    unittest.main()
    