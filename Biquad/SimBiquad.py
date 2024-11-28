import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import freqz

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from Waveforms.Gated import Gated
from Waveforms.SimFilter import SimFilter
from Waveforms.Waveform import Waveform
from Biquad import Biquad

class SimBiquad(Biquad):
    def __init__(self, data=None, A=0, B=1, P=0, theta=np.pi):
        super().__init__(A, B, P, theta)
        self._data = None
        self._length = None
        self.u = None
        self.y = None
        self.f = None
        self.g = None
        self.F = None
        self.G = None

        if data is not None:
            self.data = data 

    ###########################################
    ##### Data
    ###########################################

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value:np.ndarray):
        self._data = value
        self._update_outputs()

    @property
    def length(self):
        return self._length

    def _update_outputs(self):
        self._length = len(self._data) // 8
        
        self.u = np.zeros((self._length, 8))
        self.y = np.zeros((self._length, 8))
        self.f = np.zeros(self._length)
        self.g = np.zeros(self._length)
        self.F = np.zeros(self._length)
        self.G = np.zeros(self._length)

    ###########################################
    ##### Implulse Response Filters
    ###########################################

    ##############
    ##### Zero FIR
    ##############

    def run_zeroFIR(self, quant = True):
        for b in range(self.length):
            for n in range(self.M):
                self.u[b][n] = self.A * self.data[self.M*b+n] + self.B * self.data[self.M*b+n-1] + self.A * self.data[self.M*b+n-2]

        if quant is True:
            ## I was under the impression this would be Q14.2 but empirically this is wrong
            self.u = self.calc_q_format(self.u, 12, 0)

        # Only if testing single zero fir output
        for b in range(self.length):
            self.y[b][0] = self.u[b][0]
            self.y[b][1] = self.u[b][1]

    ##############
    ##### Pole FIR
    ##############

    def run_poleFIR(self, quant = True):
        for b in range(self.length):

            # The bit width of f and g is large enough such that the inputs here cannot possibly exceed it
            self.f[b] = self.u[b][0] + (self.Xn[1] * self.u[b - 1][self.M - 1])
            self.g[b] = self.u[b][1] + (self.Xn[1] * self.u[b][0])
            
            for i in range(2, self.M - 1):
                self.f[b] += self.Xn[i] * self.u[b - 1][self.M - i]
                self.g[b] += self.Xn[i] * self.u[b - 1][self.M - i + 1]

                if quant is True:
                    self.f[b] = self.calc_q_format(self.f[b], 21, 27)
                    self.g[b] = self.calc_q_format(self.g[b], 21, 27)
            
            self.g[b] += self.Xn[self.M - 1] * self.u[b - 1][2]
            
            if quant is True:
                self.f[b] = self.calc_q_format(self.f[b], 21, 27)
                self.g[b] = self.calc_q_format(self.g[b], 21, 27)

            self.F[b] = self.Dff * self.f[b - 1] + self.Dfg * self.g[b - 1] + self.f[b]
            self.G[b] = self.Egg * self.g[b - 1] + self.Egf * self.f[b - 1] + self.g[b]
            
            self.y[b][0] = self.F[b]
            self.y[b][1] = self.G[b]
        
        if quant is True:
            self.F = self.calc_q_format(self.F, 21, 27)
            self.G = self.calc_q_format(self.G, 21, 27)

    ##############
    ##### Pole IIR
    ##############

    def run_poleIIR(self, quant = True):
        for b in range(self.length):
            self.y[b][0] = (self.C0 * self.y[b - 2][0]) + (self.C1 * self.y[b - 2][1]) + self.F[b]
            self.y[b][1] = (self.C2 * self.y[b - 2][0]) + (self.C3 * self.y[b - 2][1]) + self.G[b]

            if quant is True:
                self.y[b] = self.calc_q_format(self.y[b], 21, 27)

        if quant is True:
            self.y = self.calc_q_format(self.y, 14, 10)

    ##############
    ##### Restoring undecimated waveform
    ##############

    def run_incremental(self, quant = True):
        for b in range(self.length):
            for i in range(2, self.M):
                self.y[b][i] = self.a1 * self.y[b][i - 1] - self.a2 * self.y[b][i - 2] + self.u[b][i]
                
                if quant is True:
                    self.y[b][i] = self.calc_q_format(self.y[b][i], 14, 10)

    ###########################################
    ##### Misceleneous
    ########################################### 

    def set_daq_coeffs(self, params):
        self.Xn = params[0]

        self.Dff = params[1][0]
        self.Egg = params[1][1]
        self.Dfg = params[1][2]
        self.Egf = params[1][3]

        self.C0 = params[2][0]
        self.C1 = params[2][1]
        self.C2 = params[2][2]
        self.C3 = params[2][3]

        self.a1 = params[3][0]
        self.a2 = params[3][1]

        try:
            self.A = params[4][0]
            self.B = params[4][1]
        except:
            pass

    ###########################################
    ##### Access Outputs
    ########################################### 

    def update_waveforms(self, input_data = None):
        if input_data is None:
            noise_input = np.zeros(200 * 8)
            noise_input[35*8 : 99*8] = np.random.normal(0, 20, 512)
            self.data = noise_input
        else:
            self.data = input_data
        super().run_Biquad()

    def extract_raw(self, quant = True):
        if quant is True:
            output = self.calc_q_format(self.data, 12, 0)

        output = Gated(output)
        output.waveform = output.waveform
        return output
 
    def extract_biquad(self, quant = True):
        if quant is True:
            self.y = self.calc_q_format(self.y, 12, 0)
        output = SimFilter(self.y.flatten())
        output.waveform = output.waveform

        return output
    
    ############################
    ##Spectral Analysis
    ############################

    def run_S21_response(self, magnitude, clocks, quant = True):
        if quant is True:
            S1 = Waveform(np.random.normal(0, magnitude, clocks*8))
        else:
            S1 = Waveform(self.calc_q_format(np.random.normal(0, magnitude, clocks*8), 12, 0))

        biquad.data = S1.waveform
        biquad.run_Biquad(quant=quant)
        S2 = biquad.extract_biquad(quant=quant)

        S21 = S2.fft/S1.fft
        S21_mag = np.abs(S21[:S2.N//2])

        return S2.xf, S21_mag

    def run_impulse_response(self, magnitude, clocks, quant = True):
        impulse = np.zeros(clocks*8)
        impulse[0] = magnitude

        biquad.data = impulse

        biquad.run_Biquad(quant)
        # output = biquad.extract_biquad(quant)

if __name__ == '__main__':
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
    from Waveforms.Filtered import Filtered
    from Biquad import Biquad

    num_clocks = 64

    A = 0.8028107634961998
    B = -0.9163499900207577
    P = 0.7782168894289043
    theta = 0.2996203532999784 * np.pi
    
    sample_rate = 3e9
    frequency = 400e6
    
    t = np.arange(num_clocks * 8) / sample_rate
    sine_wave = 72*np.sin(2 * np.pi * frequency * t)
    
    biquad = SimBiquad(data=sine_wave, A=A, B=B, P=P, theta=theta)

    biquad.update_params(A, B, P, theta)
    biquad.quantise_coeffs()

    import time
    start_time = time.time()

    xf, S21_log_mag = biquad.S21_loop(10,17)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
