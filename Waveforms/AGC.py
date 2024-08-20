import numpy as np
import matplotlib.pyplot as plt

from scipy.fft import fft

from typing import List

from .Waveform import Waveform

class AGC(Waveform):
    def __init__(self, waveform: List, sampleRate=3.E9):
        super().__init__(waveform, sampleRate)
        
        self.setClocks()
        self.offset = None

    def setOffset(self):
        self.offset = np.mean(self.waveform)

    def plotWaveform(self, ax: plt.Axes=None, title = None, figsize=(25, 15)):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
    
        ax.plot(self.timelist*10**9, self.waveform)

        if title is not None:
            ax.set_title(title)

        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        self.setOffset()
        
        ax.axhline(y=self.offset, color='black', linewidth=0.4, label='Offset')

        self.setWaveFFT()
        self.setPeaktoPeak()

        stats_text = f"Peak-Peak : {self.peakToPeak:.2f} ADC\nOffset : {self.offset:.2f} ADC\nFrequency : {self.frequencyFFT*10**(-6):.2f} MHz"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))