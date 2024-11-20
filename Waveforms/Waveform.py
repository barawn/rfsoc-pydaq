import numpy as np
import matplotlib.pyplot as plt

from scipy.fft import fft

class Waveform():
    def __init__(self, waveform: np.ndarray, sample_frequency = 3.E9, tag : str = ""):

        self.tag = tag

        self._waveform = waveform
        self._sample_frequency = sample_frequency

        self._N = len(self.waveform)
        self._dt = 1/self._sample_frequency

    def __len__(self):
        return len(self.waveform)
    
    def __getitem__(self, index):
        return self.waveform[index]
    
    def __setitem__(self, index, value):
        self.waveform[index] = value

    def __iter__(self):
        return iter(self.waveform)
    
    def __add__(self, other):
        return self.waveform + other

    def __sub__(self, other):
        return self.waveform - other

    def __mul__(self, other):
        return self.waveform * other

    def __truediv__(self, other):
        return self.waveform / other
    
    def __array__(self):
        return self.waveform

    @property
    def waveform(self):
        return self._waveform

    @waveform.setter
    def waveform(self, arr):
        if not isinstance(arr, np.ndarray):
            raise ValueError("Waveform must be of type ndarray")
        self._waveform = arr
        self._N = len(self.waveform)

    @property
    def sample_frequency(self):
        return self._sample_frequency

    @sample_frequency.setter
    def sample_frequency(self, value):
        if value <= 0:
            raise ValueError("Sample frequency can't be negative or zero")
        self._sample_frequency = value

    @property
    def time_list(self):
        return np.arange(len(self.waveform))/self.sample_frequency

    @property
    def N(self):
        return self._N
    
    @N.setter
    def N(self, value):
        self._N = value

    @property
    def fft(self):
        return fft(self.waveform)

    @property
    def xf(self):
        return np.linspace(0.0, self.sample_frequency / 2, self.N // 2)
    
    @property
    def mag_spectrum(self):
        return np.abs(self.fft[:self.N//2]) * 2 / self.N

    #####
    ## Clock formatting stuff
    #####

    def shorten_waveform(self, start, end):
        self.waveform = self.waveform[start:end]

    #####
    ## Amplitudes
    #####

    def calc_PtP(self):
        return abs(max(self.waveform) - min(self.waveform))/2
        
    def calc_rms(self):
        square_sum = sum(x ** 2 for x in self.waveform)
        mean_square = square_sum / self.N
        return np.sqrt(mean_square)

    #####
    ## Miscellaneous
    #####

    ## I end up always having to write one of these anyway
    def calculate_rms(self, data):
        square_sum = sum(x ** 2 for x in data)
        mean_square = square_sum / len(data)
        rms = np.sqrt(mean_square)
        return rms
    
    #####
    ## Plotting stuff (Replacing the previous notebook structure, which was kinda horrible)
    ### Since this is the superclass this has the most basic plots. Inherited classes will have more specific plots (potential overrides)
    #####

    def plotWaveform(self, ax: plt.Axes=None, title = None, figsize=(25, 15), colour = None, scale = 1, offset = 0, pos = 0):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        ax.plot(self.time_list*10**9, scale * self.waveform + offset, color=colour, label = self.tag)

        if title is not None:
            ax.set_title(title)

        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        stats_text = f"P2P : {self.calc_PtP():.2f} ADC\nRMS : {self.calc_rms():.2f} ADC"
        
        ax.text(1, 0.98 - pos, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, color=colour, bbox=dict(facecolor='black', alpha=0.5))
        
    def plotClocks(self, clocks, ax: plt.Axes=None, title = None, figsize=(25, 15)):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        self.shorten_waveform(0,8*clocks)

        x_axis = np.arange(len(self.waveform)) / 8

        ax.plot(x_axis, self.waveform)

        if title is not None:
            ax.set_title(title)

        ax.set_xlabel('Clocks')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        stats_text = f"Peak-Peak : {self.calc_PtP():.2f} ADC\nRMS : {self.calc_rms():.2f} ADC"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

    def plotFFT(self, ax: plt.Axes=None, title = None, figsize=(25, 15), colour = None):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        # try:
        ax.plot(self.xf*10**(-6), 20 * np.log10(self.mag_spectrum), label=self.tag, color=colour)
        # except:
        #     print(f"It's just not possible to plot {self.tag}'s fft at this moment")

        if title is not None:
            ax.set_title(title)
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("Magnitude (arb.)")