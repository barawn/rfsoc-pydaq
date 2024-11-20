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
        self._waveform = arr[35*8 : 99*8]
        self._N = len(self.waveform)

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