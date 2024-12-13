import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import freqz

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from Waveforms.Waveform import Waveform
from Biquad import Biquad


class Transfer():
    def __init__(self):
        self._fs = 3E9
        self._A = None
        self._P = None
        self._fz = None
        self._fp = None

    ###########################################
    ##### Class instance setters
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
    def B(self):
        return 2*self._A*np.cos(self.theta_z)

    @B.setter
    def B(self, value):
        if abs(value) > 8:
            raise ValueError("B must be 4 bits wide")
        self._A = value/(2*np.cos(self.theta_z))

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

    def set_params(self, A, P, fz, fp, **kwargs):
        self.A = A
        self.P = P
        self.fz = fz
        self.fp = fp

    ###########################################
    ##### Class Methods
    ###########################################

    ## z here is a signal array 
    def transfer_function_signal(self, z : list):
        return (self.A*z - 2*self.A*np.cos(self.theta_z)*np.pad(z[:-1], (1, 0)) + self.A*np.pad(z[:-2], (2, 0))) / (1 - 2*self.P*np.cos(self.theta_p)*np.pad(z[:-1], (1, 0)) + self.P**2*np.pad(z[:-2], (2, 0)))

    ## z will be represented as exp(i*omega), since this is only dependent on the frequency
    def transfer_function_frequency(self, freq : int):
        omega = 2 * np.pi * freq / self.fs
        z = np.exp(1j * omega)
        return self.transfer_function(z)
    
    def transfer_function(self, z):
        num = self.A * z**2  -  2 * self.A * np.cos(self.theta_z) * z  +  self.A
        den = z**2  -  2 * self.P * np.cos(self.theta_p) * z  +  self.P**2
        return num / den
    
    def response(self, Hjw):
        return np.abs(Hjw), np.angle(Hjw)
    
    # -3dB bandwidth
    def calc_quality(self, frequencies, mag_spectrum, fc):
        max_index = np.argmax(mag_spectrum)
        max_dB = mag_spectrum[max_index]

        cutoff_dB = max_dB - 3

        above_cutoff = mag_spectrum <= cutoff_dB

        indices = np.where(above_cutoff)[0]
        f_low = frequencies[indices[0]]
        f_high = frequencies[indices[-1]] 

        bandwidth = f_high - f_low

        quality = 10**6*fc/bandwidth


        return quality

        
if __name__ == '__main__':
    
    from Filter import Filter

    filter = Filter()

    Hz = Transfer()

    filter.calc_params(460)
    # filter.A = 0.8028107634961998
    print(filter.fp)
    print(filter.P)
    # filter.fp = 459.5
    # filter.P = 0.94
    # filter.fp = 440
    # filter.P = 0.72

    Hz.set_params(**filter.get_params())

    frequencies = np.linspace(0, 1500E6, 1000)
    magnitude = []
    phase = []

    for freq in frequencies:
        response = Hz.response(Hz.transfer_function_frequency(freq))
        magnitude.append(response[0])
        phase.append(response[1])

    print(Hz.calc_quality(frequencies, 20*np.log10(magnitude), filter.fz))

    plt.figure(figsize=(12, 6))

    plt.subplot(2, 1, 1)
    plt.plot(frequencies, 20*np.log10(magnitude))
    plt.title("Magnitude Response")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    # plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(frequencies, phase)
    plt.title("Phase Response")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Phase (radians)")
    # plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()