import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import freqz, iirnotch, tf2zpk
import warnings
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Waveforms.Waveform import Waveform
from SimBiquad import SimBiquad

class Filter():
    def __init__(self, fs = 3000):
        """
        The job of this is just to manage and keep track of filter parameters.
        Can calculate new parameters
        Calculate useful physical meanings of the filter
        Expects the filter to be a notch filter
        Easy to tweak parameters
        """
        self._fs = fs
        self._A = None
        self._P = None
        self._fz = None
        self._fp = None

    ###########################################
    ##### Field setters
    ###########################################

    @property
    def fs(self):
        return self._fs

    @fs.setter
    def fs(self, value):
        if value <= 0:
            raise ValueError("Sample frequency can't be negative or zero")
        self._fs = value

    @property
    def A(self):
        return self._A

    @A.setter
    def A(self, value):
        if abs(value) > 8:
            raise ValueError("A must be 4 bits wide")
        self._A = value


    @property
    def P(self):
        return self._P

    @P.setter
    def P(self, value):
        if value >= 1:
            raise ValueError("P must be less than 1")
        if value < 0:
            raise ValueError("P must be positive")
        self._P = value

    @property
    def fz(self):
        return self._fz

    @fz.setter
    def fz(self, value):
        if value >= self.fs/2:
            raise ValueError("Zero Frequency must be less than Nyquist frequency")
        if value < 0:
            raise ValueError("Zero Frequency must be physically possible")
        self._fz = value

        self.calc_params()

    @property
    def fp(self):
        return self._fp

    @fp.setter
    def fp(self, value):
        if value >= self.fs/2:
            raise ValueError("Pole Frequency must be less than Nyquist frequency")
        if value < 0:
            raise ValueError("Pole Frequency must be physically possible")
        self._fp = value

    ###########################################
    ##### Class instance setters
    ###########################################

    @property
    def B(self):
        return -2*self._A*np.cos(self.theta_z)

    @B.setter
    def B(self, value):
        if abs(value) > 8:
            raise ValueError("B must be 4 bits wide")
        self._A = -value/(2*np.cos(self.theta_z))

    @property
    def theta_z(self):
        return 2 * np.pi * self._fz / self._fs

    @theta_z.setter
    def theta_z(self, value):
        if value <= 0:
            raise ValueError("Zero must be not be zero or negative")
        if value > np.pi:
            raise ValueError("Zero must be within semi-circle")
        self._fz = value * self._fs / (2 * np.pi)

    @property
    def theta_p(self):
        return 2 * np.pi * self._fp / self._fs

    @theta_p.setter
    def theta_p(self, value):
        if value <= 0:
            raise ValueError("Pole must be not be zero or negative")
        if value > np.pi:
            raise ValueError("Pole must be within semi-circle")
        self._fp = value * self._fs / (2 * np.pi)

    # @property
    # def quality(self):
    #     return self._quality

    # @quality.setter
    # def quality(self, value):
    #     if value <= 0:
    #         raise ValueError("Quality must be positive")
    #     self._quality = value
    #     self.calc_params()

    # def update_filter(self, **kwargs):
    #     for key, value in kwargs.items():
    #         if hasattr(self, key):
    #             setattr(self, key, value)
    #         else:
    #             raise AttributeError(f"Filter object has no attribute '{key}'")
    #     self.calc_params()

    ###########################################
    ##### Calculator
    ###########################################

    def calc_params(self, zero = None, quality = 5):
        if zero is not None:
            self.fz = zero

        b, a = iirnotch(self.fz, quality, self.fs)
        z, p, k = tf2zpk(b, a)

        if k > 1:
            warnings.warn("Filter Gain is greater than 1")

        self.A = b[0]
        self.P = np.abs(p[0])
        self.theta_p = np.angle(p[0])

    ###########################################
    ##### Complex Gets
    ###########################################

    def get_Biquad(self):
        return {"A" : self.A, "B" : self.B, "P" : self.P, "theta" : self.theta_p}

    def get_params(self):
        return {"A" : self.A, "B" : self.B, "P" : self.P, "theta" : self.theta_p,
                "fz" : self.fz*10**6, "fp" : self.fp*10**6, "theta_z" : self.theta_z, "theta_p" : self.theta_p}

    def get_stats(self, ax: plt.Axes):
        stats_text = self.__str__()
    
        ax.text(0.97, 0.80, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

    ###########################################
    ##### Magic Methods
    ###########################################

    def __str__(self):
        return (f"Parameters : \nA = {self.A:.3f}\nB = {self.B:.3f}\nP = {self.P:.3f}\ntheta = {self.theta_p:.3f}\n\n"
                f"Spectra : \nZero = {self.fz:.3f} MHz\nPole = {self.fp:.3f} MHz")
                # f"Other : \nSample Frequency = {self.fs/1000} GHz") #\nQuality = {self.quality}")

    def __repr__(self):
        return f"Filter(Zero = {self.fz} MHz, Sample Frequency = {self.fs/1000} GHz)"

    def to_dict(self):
        return {
            "zero": self.fz,
            "pole": self.fp,
            "A" : self.A,
            "B" : self.B,
            "P" : self.P,
            "theta" : self.theta_p,
            "sample_frequency": self.fs,
        }

if __name__ == '__main__':
    filter_instance = Filter()

    filter_instance.calc_params(460)
    # filter_instance.A = 0.9
    # filter_instance.B = -0.9
    # filter_instance.fp = 455
    # print(filter_instance.get_params())
    # print('')
    print(filter_instance)

    print('')

    filter_instance.calc_params(375)

    print(filter_instance)




