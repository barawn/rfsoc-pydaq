import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import find_peaks, peak_widths, butter, filtfilt

from typing import List

from .Waveform import Waveform

class Pulse(Waveform):
    def __init__(self, waveform: List, sampleRate = 3.E9):
        self.peaks = None
        self.widths = None
        self.filtered_signal = None

    def calcPeaks(self):
        self.peaks, _ = find_peaks(self.waveform, height=400) #the minumum height of a peak. Probably should calculate this or something idk

        self.widths = peak_widths(self.waveform, self.peaks, rel_height=0.5)

    def butterworth(self):
        nyq = 0.5 * self.sampleRate
        normal_cutoff = 1.E9 / nyq
        b, a = butter(5, normal_cutoff, btype='low', analog=False)
        return b, a
    
    def lowpass_filter(self):
        b, a = self.butterworth()
        self.filtered_signal = filtfilt(b, a, self.waveform)