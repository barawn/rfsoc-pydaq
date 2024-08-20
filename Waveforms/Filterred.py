import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import lombscargle

from typing import List

from .Waveform import Waveform

class Filterred(Waveform):
    def __init__(self, waveform: List, sampleRate = 3.E9, start=400, end=920):
        super().__init__(waveform, sampleRate = 3.E9)
        
        self.shortenWaveform(start, end)
        self.setClocks()

        self.decimated_WF = None
        self.decimated_TL = None

        self.periodogram_freqs = None
        self.periodogram = None
        self.periodogram_freq = None
    
    def convert_Decimated(self, start=0, end=7):
        if self.clocks is None:
            self.setClocks()
        self.decimated_WF = np.zeros((len(self.clocks),2))
        self.decimated_TL = np.zeros((len(self.clockTime),2))
        length = len(self.clocks)

        for b in range(length):
            self.decimated_WF[b, 0] = self.clocks[b, 0]  # First output of the clock period
            self.decimated_WF[b, 1] = self.clocks[b, 1]  # Last output of the clock period

            self.decimated_TL[b, 0] = self.clockTime[b, 0]
            self.decimated_TL[b, 1] = self.clockTime[b, 1]

        self.decimated_WF = self.decimated_WF.flatten()
        self.decimated_TL = self.decimated_TL.flatten()

    def Lomb_Scargle(self):
        self.convert_Decimated()

        n = len(self.decimated_WF)
        dxmin = np.diff(self.decimated_TL).min()
        duration = self.decimated_TL.ptp()

        self.periodogram_freqs = np.linspace(1/duration, n/duration, 5*n)

        self.periodogram = lombscargle(self.decimated_TL, self.decimated_WF, self.periodogram_freqs)

        self.periodogram_freq = self.periodogram.argmax()
        print(self.periodogram_freq)


    def plotWaveform(self, ax: plt.Axes=None, title = None, figsize=(25, 15)):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        x_axis = np.arange(len(self.waveform)) / 8

        ax.plot(x_axis, self.waveform)

        if title is not None:
            ax.set_title(title)

        ax.set_xlabel('Clocks')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        self.setWaveFFT()
        self.setPeaktoPeak()

        stats_text = f"Peak-Peak : {self.peakToPeak:.2f} ADC\nFrequency : {self.frequencyFFT*10**(-6):.2f} MHz"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))
        
    
    def plotDecimated(self, ax=None, title=None, figsize=(25, 15)):
        
        if self.decimated_WF is None:
            self.convert_Decimated()

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        ax.plot(self.decimated_TL, self.decimated_WF)

        ax.set_xlabel('Samples')
        ax.set_ylabel('ADC Counts')



    def plotPeriodogram(self, ax=None, title=None, figsize=(25, 15)):
        if self.periodogram_freqs is None:
            self.Lomb_Scargle()

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        # Convert frequencies to MHz (assuming decimated_TL is in seconds)
        freqs_mhz = self.periodogram_freqs * 1e-6

        ax.plot(freqs_mhz, self.periodogram)

        if title:
            ax.set_title(title)
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Power')
        plt.show()

    # def plotPeriodogram(self, ax: plt.Axes=None, title = None, figsize=(25, 15)):

    #     self.Lomb_Scargle()

    #     if ax is None:
    #         fig, ax = plt.subplots(figsize=figsize)

    #     ax.plot(self.periodogram_freqs, np.sqrt(4*self.periodogram/5*len(self.decimated_WF)))

    #     ax.set_xlabel('Frequency (rad/s)')
    #     ax.set_ylabel('No idea (arb)')