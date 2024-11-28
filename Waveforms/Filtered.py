import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import lombscargle

from typing import List

from .Waveform import Waveform

class Filtered(Waveform):
    ##Was 400->920
    ##Now 424->952
    ##Do additional multiple clocks for testing

    ##Maybe we have it automatically pick a start and end
    ##Like do shorten wavelength when it finds first clock to when the clock goes to zero
    
    def __init__(self, waveform: np.ndarray, sampleRate = 3.E9, tag : str = ""):
        ## start=280, end=800 for Simulation biquad
        super().__init__(waveform, sampleRate, tag)

        # self.set_waveform_range()

    @property
    def waveform(self):
        return super().waveform

    @waveform.setter
    def waveform(self, arr):
        if not isinstance(arr, np.ndarray):
            raise ValueError("Waveform must be of type ndarray")
        
        del self._waveform

        ##Due to the inclusion of the iir portion the number of clocks with data might extend 64.
        # last = self.find_last_clock(arr, 53)
        # self._waveform = arr[53*8 : last*8]

        self._waveform = arr[53*8 : 117*8]
        self._N = len(self.waveform)

#########################
## Miscleneuous
#########################
    def calc_rms(self):
        return 2*super().calc_rms()

#########################
## Plots
#########################

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
        