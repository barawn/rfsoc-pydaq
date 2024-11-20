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
        self._waveform = arr[53*8 : 117*8]
        self._N = len(self.waveform)

#########################
## Automatic gating
#########################
    def find_first_clock(self, clocks):
        first_clock=0
        for clock in clocks:
            if clock[0] == 0 and clock[1] == 0:
                first_clock+=1
            else:
                break
        return first_clock
    
    def find_last_clock(self, start, clocks):
        last_clock=start
        for i in range(start, len(clocks)):
            if clocks[i][0] == 0 and clocks[i][1] == 0:
                break
            else:
                last_clock+=1
        return last_clock
    
    def set_waveform_range(self):
        clocks = self.waveform.reshape(-1, 8)

        first_clock = self.find_first_clock(clocks)
        last_clock = first_clock+64 ##This will ignore any only iir part
        # last_clock = self.find_last_clock(first_clock, clocks)
        self.shorten_waveform(first_clock*8, last_clock*8)


#########################
## Miscleneuous
#########################
    def calc_rms(self):
        clocks = self.waveform.reshape(-1, 8)

        decimated = np.zeros((len(clocks),2))

        for b, clock in enumerate(clocks):
            decimated[b, 0] = clock[0]
            decimated[b, 1] = clock[1]

        decimated = decimated.flatten()

        square_sum = sum(x ** 2 for x in decimated)
        mean_square = square_sum / len(decimated)
        return np.sqrt(mean_square)


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
        