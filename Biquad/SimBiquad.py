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

    def quant_data(self, value:np.ndarray, quant = True):
        if quant is True:
            self.data = self.calc_q_format(value, 12, 0)
        else:
            self.data = value

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
            # self.u = self.calc_q_format(self.u, 12, 0)
            self.u = self.calc_q_format(self.u, 14, 2)

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

    def update_waveforms(self, data):
        self.data = data
        super().run_Biquad()

    def extract_raw(self, quant = True):
        if quant is True:
            output = self.calc_q_format(self.data, 12, 0)

        output = Gated(output)
        output.waveform = output.waveform
        return output

     
    def extract_biquad(self, quant = True, buffer = 0):
        if quant is True:
            self.y = self.calc_q_format(self.y, 12, 0)
        output = SimFilter(self.y.flatten())
        output.waveform = output.waveform[buffer*8:]
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

    def run_S21_response_loop(self, filter, magnitude, clocks, loop=100):

        data = np.zeros((clocks+5) * 8)

        S21_quant_arr = []
        S21_arr = []
        for _ in range(loop):
            noise = np.random.normal(0, magnitude, clocks*8)
            quant_noise = self.calc_q_format(noise, 12, 0)

            data[5*8 : (clocks+5)*8] = quant_noise

            S1_quant = Waveform(quant_noise)
            
            self.update_params(**filter.get_params())
            self.quantise_coeffs()
            self.data = data
            self.run_Biquad(quant=True)
            S2_quant = self.extract_biquad(quant=True, buffer=5)

            data[5*8 : (clocks+5)*8] = noise
            S1 = Waveform(noise)

            self.update_params(**filter.get_params())
            self.data = data
            self.run_Biquad(quant=False)
            # self.run_IIR(quant=False)
            S2 = self.extract_biquad(quant=False, buffer=5)

            S21_quant_arr.append(S2_quant.fft/S1_quant.fft)
            S21_arr.append(S2.fft/S1.fft)

        S21_mean_quant = [sum(x) / len(S21_quant_arr) for x in zip(*S21_quant_arr)]
        S21_mean = [sum(x) / len(S21_arr) for x in zip(*S21_arr)]

        S21_log_mag_quant = np.abs(S21_mean_quant[:len(S21_mean_quant)//2])
        S21_log_mag = np.abs(S21_mean[:len(S21_mean)//2])

        return S2.xf, S21_log_mag_quant, S21_log_mag
    

    def run_impulse_response(self, magnitude, clocks, quant = True):
        impulse = np.zeros(clocks*8)
        impulse[0] = magnitude

        biquad.data = impulse

        biquad.run_Biquad(quant)
        # output = biquad.extract_biquad(quant)


def rms(data):
    square_sum = sum(x ** 2 for x in data)
    mean_square = square_sum / len(data)
    return np.sqrt(mean_square)

##Calculates the quantisation error in the biquad. Use the new Filter class
def calculate_error(biquad:Biquad, filter):
    length = 32
    result = []
    arr = np.arange(-2048, 2048, 1)
    x_axis = []
    for i in arr:
        if i == 0:
            continue
        x_axis.append(i)
        magnitude = i

        biquad.update_params(**filter.get_params())
        biquad.quantise_coeffs()

        biquad.run_impulse_response(magnitude, length)
        output1 = biquad.extract_biquad()

        biquad.update_params(**filter.get_params())
        biquad.run_impulse_response(magnitude, length, quant=False)
        output2 = biquad.extract_biquad(quant=False)

        result.append(rms(output2-output1))

    return x_axis, result


if __name__ == '__main__':
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
    from Waveforms.Filtered import Filtered
    from Biquad import Biquad
    from Filter import Filter
    from SpectrumAnalyser import SpectrumAnalyser

    filter = Filter()
    sam = SpectrumAnalyser()

    fz = 375

    filter.calc_params(fz)

    biquad = SimBiquad()
    biquad.update_params(**filter.get_params())
    biquad.quantise_coeffs()


    magnitude = 100
    num_clocks = 64

    noise_input = np.zeros(num_clocks * 8)
    noise = np.random.normal(0, magnitude, num_clocks*8)
    noise_input[35*8: 99*8] = noise

    biquad.data = noise_input
    

    # import time
    # start_time = time.time()

    # xf, S21_log_mag = sam.S21_loop(10,17)

    # end_time = time.time()
    # print(f"Time taken: {end_time - start_time} seconds")
