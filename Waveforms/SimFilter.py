import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import lombscargle

from typing import List

from .Waveform import Waveform

class SimFilter(Waveform):
    def __init__(self, waveform: np.ndarray, sampleRate = 3.E9, tag : str = ""):
        ## start=280, end=800 for Simulation biquad
        super().__init__(waveform, sampleRate, tag)

    @property
    def waveform(self):
        return super().waveform

    @waveform.setter
    def waveform(self, arr):
        if not isinstance(arr, np.ndarray):
            raise ValueError("Waveform must be of type ndarray")
        
        del self._waveform

        ##Input is most likely gated. Do you want the code to automatically find the start and end of the gate or just clock 35 to 98. Or maybe you're only running simulated data in which ignore gating

        # first = self.find_first_clock(arr)
        # last = self.find_last_clock(arr, first)
        # self._waveform = arr[first*8 : last*8]

        self._waveform = arr[35*8 : 99*8]

        # self._waveform = arr
        
        self._N = len(self.waveform)

#########################
## Miscleneuous
#########################

    def calc_rms(self):
        return 2*super().calc_rms()