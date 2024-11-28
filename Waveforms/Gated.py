import numpy as np
import matplotlib.pyplot as plt

from scipy.fft import fft
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, peak_widths, butter, filtfilt, correlate, lombscargle

from typing import List

from .Waveform import Waveform

class Gated(Waveform):
    def __init__(self, waveform: List, sampleRate=3.E9, start=280, end=792, tag : str = ""):
        super().__init__(waveform, sampleRate, tag)

        # self.shorten_waveform(35*8, 99*8)

    @property
    def waveform(self):
        return super().waveform

    @waveform.setter
    def waveform(self, arr):
        if not isinstance(arr, np.ndarray):
            raise ValueError("Waveform must be of type ndarray")
        
        del self._waveform

        self._waveform = arr[35*8 : 99*8]
        self._N = len(self.waveform)

    # def plotWaveform(self, ax: plt.Axes=None, title = None, figsize=(25, 15)):
    #     if ax is None:
    #         fig, ax = plt.subplots(figsize=figsize)

    #     x_axis = np.arange(len(self.waveform)) / 8

    #     ax.plot(x_axis, self.waveform)

    #     if title is not None:
    #         ax.set_title(title)

    #     ax.set_xlabel('Clocks')
    #     ax.set_ylabel('ADC Counts', labelpad=-3.5)

    #     stats_text = f"Peak-Peak : {self.calc_PtP():.2f} ADC\nRMS : {self.calc_rms():.2f} ADC"
        
    #     ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
    #         transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))