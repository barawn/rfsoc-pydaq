import numpy as np
import matplotlib.pyplot as plt

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from Waveforms.Waveform import Waveform
from Biquad import Biquad

from scipy.ndimage import gaussian_filter1d

class SpectrumAnalyser():
    def __init__(self, sample_frequency=3000, clocks=376):
        self.sample_frequency = sample_frequency
        self.dt = 1/self.sample_frequency

        self._clocks = clocks

        ##This is for the noises
        self.duration = 8 * self.clocks * self.dt
        self.t = np.arange(0, self.duration, self.dt)

        ##This is for the fft
        self.N = 8 * self.clocks
        self.xf = np.linspace(0.0, 1.0 / (2 * self.dt), self.N // 2)

    ###########################################
    ##### Field setters
    ###########################################

    @property
    def clocks(self):
        return self._clocks

    @clocks.setter
    def clocks(self, value):
        if value <= 0:
            raise ValueError("Number of clocks must be positive")
        self._clocks = value

    @property
    def S1(self):
        return self._S1

    @S1.setter
    def S1(self, waveform:Waveform):
        self._S1 = waveform

    @property
    def S2(self):
        return self._S2
    
    @S2.setter
    def S2(self, waveform:Waveform):
        self._S2 = waveform

    @property
    def S21(self):
        return self._S2.fft/self._S1.fft

    @property
    def S3(self):
        return self._S3

    @S3.setter
    def S3(self, waveform:Waveform):
        self._S3 = waveform

    @property
    def S31(self):
        return self._S3.fft/self._S1.fft
    
    ###########################################
    ##### Main Processes
    ###########################################

    def single_S21(self, biquad : Biquad, loop):
        self.S2, self.S1 = biquad.extented_capture(loop)

    def S21_loop(self, biquad : Biquad, iterations = 100, loop = 6):
        S21_arr = []
        self.N = 512*loop
        T = 3.E9
        dt = 1/T
        xf = np.linspace(0.0, 1.0 / (2 * dt), self.N // 2)

        for _ in range(iterations):
            self.single_S21(biquad, loop)
            S21_arr.append(self.S21)

        S21_mean = [sum(x) / len(S21_arr) for x in zip(*S21_arr)]
        S21_log_mag = self.calc_log_spectrum(self.calc_mag_sepctrum(S21_mean))
        return xf, S21_log_mag
    
    #################
    ## Comparing Daq to Sim
    #################

    def single_S21_sim(self, daq : Biquad, sim : Biquad, loop : int):
        self.S2, self.S1, self.S3 = daq.extented_capture_sim(sim, loop)

    def S21_loop_sim(self, daq : Biquad, sim : Biquad, iterations = 100, loop = 6):
        S21_arr = []
        S21_arr_sim = []
        self.N = 512*loop
        T = 3.E9
        dt = 1/T
        xf = np.linspace(0.0, 1.0 / (2 * dt), self.N // 2)

        for _ in range (iterations):
            self.single_S21_sim(daq, sim, loop)
            S21_arr.append(self.S21)
            S21_arr_sim.append(self.S31)

        S21_mean = [sum(x) / len(S21_arr) for x in zip(*S21_arr)]
        S21_mean_sim = [sum(x) / len(S21_arr_sim) for x in zip(*S21_arr_sim)]

        S21_log_mag = self.calc_log_spectrum(self.calc_mag_sepctrum(S21_mean))
        S21_log_mag_sim = self.calc_log_spectrum(self.calc_mag_sepctrum(S21_mean_sim))
        return xf, S21_log_mag, S21_log_mag_sim
    
    #################
    ## Simulating Cascade (2 biquads)
    #################

    ##This won't currently work due to the Simulation assuming a particular input. To run this you'll have to edit SimFilter Waveform Class
    def S31_loop(self, daq : Biquad, sim : Biquad, iterations = 100, loop = 6):
        S31_arr = []
        self.N = 512*loop
        T = 3.E9
        dt = 1/T
        xf = np.linspace(0.0, 1.0 / (2 * dt), self.N // 2)
        for i in range(iterations):
            unfiltered_arr = np.array([])
            filtered_arr = np.array([])
            for _ in range(loop):
                filtered_arr, unfiltered_arr = daq.single_capture(filtered_arr, unfiltered_arr)

            self.S2 = Waveform(filtered_arr)
            self.S1 = Waveform(unfiltered_arr)

            ##So whats happening here is the output is an array (not gated at all) and the sim expects 64 clock gated array
            filtered_arr = sim.single_capture(filtered_arr, unfiltered_arr=None, data=daq.adcBuffer[2]>>4)
            self.S3 = Waveform(filtered_arr)

            S31_arr.append(self.S31)

        S31_mean = [sum(x) / len(S31_arr) for x in zip(*S31_arr)]
        S31_log_mag = self.calc_log_spectrum(self.calc_mag_sepctrum(S31_mean))
        return xf, S31_log_mag

    ###########################################
    ##### Calculators
    ###########################################

    def calc_mag_sepctrum(self, arr_fft):
        return np.abs(arr_fft[:self.N//2])
    
    def calc_log_spectrum(self, arr_mag):
        return 20 * np.log10(arr_mag)

    ###########################################
    ##### Plotters
    ###########################################

    def plot_S21_loop(self, biquad : Biquad, ax: plt.Axes=None, iterations = 1000, loop = 17, title : str = None, fit : bool = False):
        if ax is None:
            fig, ax = plt.subplots(figsize=(20, 10))

        xf, S21 = self.S21_loop(biquad, iterations, loop)

        x_min = 200*10**6
        x_max = 1200*10**6
        indices = (xf >= x_min) & (xf <= x_max)

        ax.plot(xf[indices]/10**6, S21[indices], label='Daq Specturm', color='orange', alpha=0.7, linewidth=0.7)
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("S21 Log Mag (dB)")
        ax.set_title(title)

        if fit is True:
            sigma = 10
            y_smoothed_gauss = gaussian_filter1d(S21[indices], sigma=sigma)

            ax.plot(xf[indices]/10**6, y_smoothed_gauss, label='Smoothed (Gaussian)', color='blue', linewidth=0.7)

            ax.legend()

        file_path = '/home/xilinx/rfsoc-pydaq/Biquad/images/'

        file_name = 'test_spectrum_analyser'

        fig.savefig(f'{file_path}{file_name}.png', bbox_inches='tight')

    def plot_S21_loop_Sim(self, daq : Biquad, sim : Biquad, ax: plt.Axes=None, iterations = 1000, loop = 17, title : str = None, fit : bool = False):
        if ax is None:
            fig, ax = plt.subplots(figsize=(20, 10))

        xf, S21, S21_sim = self.S21_loop_sim(daq, sim, iterations, loop)

        x_min = 200*10**6
        x_max = 1200*10**6
        indices = (xf >= x_min) & (xf <= x_max)

        ax.plot(xf[indices]/10**6, S21[indices], label='Daq Specturm', color='orange', alpha=0.7, linewidth=0.7)

        ax.plot(xf[indices]/10**6, S21_sim[indices], label='Sim Specturm', color='blue', linewidth=0.7)

        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("S21 Log Mag (dB)")
        ax.set_title(title)

        ax.legend()

        file_path = '/home/xilinx/rfsoc-pydaq/Biquad/images/'

        file_name = 'test_spectrum_analyser'

        fig.savefig(f'{file_path}{file_name}.png', bbox_inches='tight')

    def plot_S31_loop(self, daq : Biquad, sim : Biquad, ax: plt.Axes=None, iterations = 1000, loop = 17, title : str = None, fit : bool = False):
        if ax is None:
            fig, ax = plt.subplots(figsize=(20, 10))

        xf, S31 = self.S31_loop(daq, sim, iterations, loop)

        x_min = 200*10**6
        x_max = 1200*10**6
        indices = (xf >= x_min) & (xf <= x_max)

        ax.plot(xf[indices]/10**6, S31[indices], label='Cascade Specturm', color='orange', alpha=0.7, linewidth=0.7)

        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("S21 Log Mag (dB)")
        ax.set_title(title)

        if fit is True:
            sigma = 10
            y_smoothed_gauss = gaussian_filter1d(S31[indices], sigma=sigma)

            ax.plot(xf[indices]/10**6, y_smoothed_gauss, label='Smoothed (Gaussian)', color='blue', linewidth=0.7)

            ax.legend()

        file_path = '/home/xilinx/rfsoc-pydaq/Biquad/images/'

        file_name = 'test_spectrum_analyser'

        fig.savefig(f'{file_path}{file_name}.png', bbox_inches='tight')

if __name__ == '__main__':
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

    from RFSoC_Daq import RFSoC_Daq
    from Biquad import Biquad
    from Biquad_Daq import Biquad_Daq
    from SimBiquad import SimBiquad

    import matplotlib.pyplot as plt

    daq = Biquad_Daq()
    sim = SimBiquad()
    sam = SpectrumAnalyser()

    print('')

    A = 0.8028107634961998
    B = -0.9163499900207577
    P = 0.7782168894289043
    theta = 0.2996203532999784 * np.pi

    daq.update_params(A, B, P, theta)
    daq.quantise_coeffs()
    daq.run_Biquad()
    sim.update_params(A, B, P, theta)
    sim.quantise_coeffs()

    sim.data = daq.adcBuffer[0] >> 4

    fig, ax = plt.subplots(1, 1, figsize=(20, 10))

    # import time
    # start_time = time.time()
    # end_time = time.time()
    # print(f"Time taken: {end_time - start_time} seconds")

    ###########################################
    ##### Write code here
    ###########################################

    # xf, S21_Daq = sam.S21_loop(daq,1000,17)

    # sam.plot_S21_loop_Sim(daq,sim, iterations = 10, loop = 17)

    sam.plot_S31_loop(daq, sim, iterations = 10)


    # xf, S21_Daq, S21_Sim = sam.S21_loop_sim(daq, sim, 10, 17)

    # x_min = 200*10**6
    # x_max = 1200*10**6
    # indices = (xf >= x_min) & (xf <= x_max)

    # ax.plot(xf[indices]/10**6, S21_Daq[indices], label='Daq Specturm', color='orange', alpha=0.7, linewidth=0.7)
    # ax.plot(xf[indices]/10**6, S21_Sim[indices], label='Sim Specturm', color='blue')
    # ax.set_xlabel("Frequency (MHz)")
    # ax.set_ylabel("S21 Log Mag (dB)")

    # ax.legend()

    # file_path = '/home/xilinx/rfsoc-pydaq/Biquad/images/'

    # file_name = 'test_spectrum_analyser'

    # fig.savefig(f'{file_path}{file_name}.png', bbox_inches='tight')