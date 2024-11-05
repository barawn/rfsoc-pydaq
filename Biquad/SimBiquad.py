import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import freqz

# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from Waveforms.Filterred import Filterred, Waveform
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
        if self._data is not None:
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
            self.u = np.floor(self.calc_n_bit(self.u, 12))

    ##############
    ##### Pole FIR
    ##############

    def run_poleFIR(self):
        for b in range(self.length):
            #Current clock single FIR output

            self.f[b] = self.u[b][0]
            self.g[b] = self.u[b][1] + (self.Xn[1] * self.u[b][0])
            
            #Previous clocks output

            self.f[b] += self.Xn[1] * self.u[b - 1][self.M - 1]
            
            for i in range(2, self.M - 1):
                self.f[b] += self.Xn[i] * self.u[b - 1][self.M - i]
                self.g[b] += self.Xn[i] * self.u[b - 1][self.M - i + 1]
            
            self.g[b] += self.Xn[self.M - 1] * self.u[b - 1][2]

            self.F[b] = self.Dff * self.f[b - 1] + self.Dfg * self.g[b - 1] + self.f[b]
            self.G[b] = self.Egg * self.g[b - 1] + self.Egf * self.f[b - 1] + self.g[b]

    ##############
    ##### Pole IIR
    ##############

    def run_poleIIR(self):
        self.F = self.calc_n_bit(self.F, 11)
        self.G = self.calc_n_bit(self.G, 11)

        for b in range(self.length):
            self.y[b][0] = (self.C0 * self.y[b - 2][0]) + (self.C1 * self.y[b - 2][1]) + self.F[b]
            self.y[b][1] = (self.C2 * self.y[b - 2][0]) + (self.C3 * self.y[b - 2][1]) + self.G[b]

    ##############
    ##### Pole IIR
    ##############

    def run_incremental(self):
        for b in range(self.length):
            for i in range(2, self.M):
                self.y[b][i] = self.a1 * self.y[b][i - 1] - self.a2 * self.y[b][i - 2] + self.u[b][i]

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
 
    def extract_biquad(self):
        return Filterred(np.array( np.floor(self.calc_n_bit(self.y, 12)).flatten() ))

if __name__ == '__main__':
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
    from Waveforms.Filterred import Filterred, Waveform
    from Biquad import Biquad

    print(Biquad)


    num_clocks = 64

    A = 1.2
    B = -1.60591345526
    P = 0.1
    theta = 0.2
    
    sample_rate = 3e9
    frequency = 400e6
    
    t = np.arange(num_clocks * 8) / sample_rate
    sine_wave = 72*np.sin(2 * np.pi * frequency * t)
    
    biquad = SimBiquad(data=sine_wave, A=A, B=B, P=P, theta=theta)

    biquad.run_Biquad()
    output = biquad.extract_biquad()

    other = Waveform(sine_wave)

    print(output.setFreqFFT()[100])

    # fig, ax = plt.subplots(figsize=(14,7))

    # output.plotFFT(ax)
    # other.plotFFT(ax)

    # plt.legend()
    # plt.show()
