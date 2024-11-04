import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import freqz

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Waveforms.Filterred import Filterred, Waveform

class SimBiquad():
    def __init__(self, data, A=0, B=1, P=0, theta=np.pi, M=8):

        ##Setting the parameters from initialisation
        self.A = A
        self.B = B
        self.P = P
        self.theta = theta
        self.M = M

        ##This is the rms of the original gated input. Necessary for controlling the gain. (P2P not great for the decimated Waveform waveform)
        # self.amp = amp

        self.length = int(len(data)/8)
        
        self.data = data
        self.clocks = data.reshape(-1, 8)
        
        ##Setting up the output values
        self.u = np.zeros((self.length, 8))
        self.y = np.zeros((self.length, 8))
        
        self.f = np.zeros(self.length)
        self.g = np.zeros(self.length)
        self.F = np.zeros(self.length)
        self.G = np.zeros(self.length)
        

        ##Setting up the coefficients
        self.Xn = np.zeros(M)
        
        self.C0 = 0 
        self.C1 = 0
        self.C2 = 0
        self.C3 = 0
        
        self.Dff = 0
        self.Dfg = 0
        self.Egg = 0
        self.Egf = 0
        
        self.a1 = 0
        self.a2 = 0
        
        ##Will set the coefficients to calculated values
        self.set_Xn()
        self.set_Cross()
        self.set_Cs()
        self.set_As()

####################
## Set Parameter methods
#################### 
    ##The original RMS of the waveform
    def setA(self, A):
        self.A = A
    
    def setB(self, B):
        self.B = B

    def setP(self,P):
        self.P=P
        ##Since each depends on P
        self.set_Xn()
        self.set_Cross()
        self.set_Cs()
        self.set_As()

    def setTheta(self,theta):
        self.theta = theta
        ##Since each depends on Theta
        self.set_Xn()
        self.set_Cross()
        self.set_Cs()
        self.set_As()

    def setData(self, data):
        ##For new daq acquires

        self.data = data
        
        self.clocks = data.reshape(-1, 8)
        self.length = int(len(data)/8)

        self.u = np.zeros((self.length, 8))
        self.y = np.zeros((self.length, 8))
        
        self.f = np.zeros(self.length)
        self.g = np.zeros(self.length)
        self.F = np.zeros(self.length)
        self.G = np.zeros(self.length)

####################
## Set Coefficients
#################### 
    
    def set_Xn(self):
        for n in range(self.M):
            self.Xn[n] = self.P**n * self.chebyshev(n)

    def chebyshev(self, num):
        return np.sin((num + 1) * self.theta) / np.sin(self.theta)
    
    def set_Dff(self, input = None):
        self.Dff = -1 * (self.P**self.M) * self.chebyshev(self.M - 2)

    def set_Egg(self):
        self.Egg = self.P**self.M * self.chebyshev(self.M)
    
    def set_Dfg(self):
        self.Dfg = self.P**(self.M - 1) * self.chebyshev(self.M - 1)

    def set_Egf(self):
        self.Egf = -1 * (self.P**(self.M + 1)) * self.chebyshev(self.M - 1)
    
    def set_C0(self):
        self.C0 = self.P**(2*self.M) * (self.chebyshev(self.M - 2)**2 - self.chebyshev(self.M - 1)**2)
    
    def set_C1(self):
        self.C1 = self.P**(2*self.M - 1) * self.chebyshev(self.M - 1) * (self.chebyshev(self.M) - self.chebyshev(self.M - 2))
    
    def set_C2(self):
        self.C2 = self.P**(2*self.M + 1) * self.chebyshev(self.M - 1) * (self.chebyshev(self.M - 2) - self.chebyshev(self.M))
    
    def set_C3(self):
        self.C3 = self.P**(2*self.M) * (self.chebyshev(self.M)**2 - self.chebyshev(self.M - 1)**2)
    
    def set_As(self):
        self.a1 = 2 * self.P * np.cos(self.theta)
        self.a2 = self.P**2
    
####################
## Set Batch Coefficients
#################### 

    def set_Cross(self):
        self.set_Dff()
        self.set_Egg()
        self.set_Dfg()
        self.set_Egf()
    
    def set_Cs(self):
        self.set_C0()
        self.set_C1()
        self.set_C2()
        self.set_C3()

####################
## Miscleneous methods
####################     
    
    ##Converts to output bit width
    def calc_n_bit(self, value, n):
        # Define the range limits
        min_val = -2**(n-1)
        max_val = 2**(n-1)
        
        # Calculate the range width
        range_width = max_val - min_val
        
        # Wrap the value around using modulo
        wrapped_value = ((value - min_val) % range_width) + min_val
        
        return wrapped_value

    def calc_n_bit_array(self, array, n):
        # Define the range limits
        min_val = -2**(n-1)
        max_val = 2**(n-1)
        
        # Calculate the range width
        range_width = max_val - min_val
        
        # Wrap the values around using modulo for the entire array
        wrapped_array = ((array - min_val) % range_width) + min_val
        
        return wrapped_array

    ##Input should be daq calculated Coefficients (divided by 2^14) so the sim has the exact same values as the daq
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

####################
## Calculate Results Results
####################    

    def single_zero_fir(self):
        for b, clock in enumerate(self.clocks):
            for n, sample in enumerate(clock):
                self.u[b][n] = self.A * self.data[self.M*b+n] + self.B * self.data[self.M*b+n-1] + self.A * self.data[self.M*b+n-2]

        self.u = np.floor(self.calc_n_bit_array(self.u, 12))

    def first_constants(self):
        for b, clock in enumerate(self.u):
            #Current clock single FIR output

            self.f[b] = self.u[b][0]
            self.g[b] = self.u[b][1] + (self.Xn[1] * self.u[b][0])
            
            #Previous clocks output

            self.f[b] += self.Xn[1] * self.u[b - 1][self.M - 1]
            
            for i in range(2, self.M - 1):
                self.f[b] += self.Xn[i] * self.u[b - 1][self.M - i]
                self.g[b] += self.Xn[i] * self.u[b - 1][self.M - i + 1]
            
            self.g[b] += self.Xn[self.M - 1] * self.u[b - 1][2]
                    
    def second_constants(self):        
        for b in range(0, len(self.f)):
            self.F[b] = self.Dff * self.f[b - 1] + self.Dfg * self.g[b - 1] + self.f[b]
            self.G[b] = self.Egg * self.g[b - 1] + self.Egf * self.f[b - 1] + self.g[b]

    
    def IIR_calculation(self):
        self.F = self.calc_n_bit_array(self.F, 11)
        self.G = self.calc_n_bit_array(self.G, 11)

        for b in range(len(self.clocks)):
            self.y[b][0] = (self.C0 * self.y[b - 2][0]) + (self.C1 * self.y[b - 2][1]) + self.F[b]
            self.y[b][1] = (self.C2 * self.y[b - 2][0]) + (self.C3 * self.y[b - 2][1]) + self.G[b]

    def incremental(self):
        for b, clock in enumerate(self.y):
            for i in range(2, self.M):
                self.y[b][i] = self.a1 * self.y[b][i - 1] - self.a2 * self.y[b][i - 2] + self.u[b][i]
    
####################
## Run Batch
####################    

    def FIR(self):
        self.single_zero_fir()

        self.first_constants()
        self.second_constants()
    
    def IIR(self):
        self.FIR()
        self.IIR_calculation()
        # self.incremental()

    def whole(self):
        self.IIR()
        self.incremental()
####################
## Get Details
####################

    def get_Xns(self):
        return self.Xn
        
    def get_crosslink(self):
        return [self.Dff, self.Egg, self.Dfg, self.Egf]

    def get_poleCoef(self):
        return [self.C0, self.C1, self.C2, self.C3]

    def get_incremental(self):
        return [self.a1, self.a2]
    
    def get_zero(self):
        return [self.A, self.B]

    def get_coeffs(self):
        return self.get_Xns(), self.get_crosslink(), self.get_poleCoef(), self.get_incremental(), self.get_zero()
    
    def printCoeffs(self):
        print(f"X1 : {self.Xn[1]}\nX2 : {self.Xn[2]}\nX3 : {self.Xn[3]}\nX4 : {self.Xn[4]}\nX5 : {self.Xn[5]}\nX6 : {self.Xn[6]}\nX7 : {self.Xn[7]}\n")

        print(f"\nDff : {self.Dff}\nEgg : {self.Egg}\nDfg : {self.Dfg}\nEgf : {self.Egf}\n")

        print(f"\nC0 : {self.C0}\nC1 : {self.C1}\nC2 : {self.C2}\nC3 : {self.C3}\n")

        print(f"\na1 : {self.a1}\na2 : {self.a2}")

####################
## Get Results
####################        
 
    def get_single_zero_fir(self):
        return Filterred(np.array([item for sublist in self.u for item in sublist]))

    ##This gets the output of single_zero_fir
    def get_u(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = self.u[b,0]
            result[b, 1] = self.u[b,1]
        return Filterred(result.flatten(), self.A, self.B, self.P, self.theta)
    
    ##This gets the output of f and g
    def get_decimated1(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = np.floor(self.calc_n_bit(np.floor(self.f[b]), 12))
            result[b, 1] = np.floor(self.calc_n_bit(np.floor(self.g[b]), 12))
        return  Filterred(result.flatten(), self.A, self.B, self.P, self.theta)
    
    ##This gets the output of F and G
    def get_decimated2(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = np.floor(self.calc_n_bit(self.F[b], 12))
            result[b, 1] = np.floor(self.calc_n_bit(self.G[b], 12))
        return Filterred(result.flatten(), self.A, self.B, self.P, self.theta)
        
    def get_biquad(self):
        # return Filterred(np.array([int(item) for sublist in self.y for item in sublist]))
        return Filterred(np.array(np.floor(self.calc_n_bit_array(self.y, 12)).flatten()), self.A, self.B, self.P, self.theta)
    
    ##This gets the output of the IIR before the incremental implementation
    def get_decimated(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = np.floor(self.calc_n_bit(self.y[b, 0], 12))
            result[b, 1] = np.floor(self.calc_n_bit(self.y[b, 1], 12)) 
        return Filterred(np.array(result.flatten()), self.A, self.B, self.P, self.theta)
    

    def get_f_g(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = self.f[b]
            result[b, 1] = self.g[b]
        return Filterred(result.flatten(), self.A, self.B, self.P, self.theta)

    def get_F_G(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = self.F[b]
            result[b, 1] = self.G[b]
        return Filterred(result.flatten(), self.A, self.B, self.P, self.theta)
    

########################
## Additional stuff
########################

    def filter_frequency(self, freq):
        self.setB(-2*self.A*np.cos(2*np.pi*freq/3E9))

    def S12(self, iterations=100, clocks=64):
        sample_rate = 3e9
        dt = 1/sample_rate
        duration = 8*clocks * dt
        t = np.arange(0, duration, dt)

        S21_arr = []
        for i in range(100):
            noise = np.random.normal(0, 20, len(t))
            self.setData(data=noise)
            # self.IIR()
            self.whole()

            raw = Waveform(noise)
            filter = self.get_biquad()

            filter.setFreqFFT()
            raw.setFreqFFT()

            S21 = filter.fft_result/raw.fft_result

            S21_arr.append(S21)

        S21_mean = [sum(x) / len(S21_arr) for x in zip(*S21_arr)]
        return 20 * np.log10(np.abs(S21_mean[:len(self.data)//2]))



    
##I can't remember if this still works.
if __name__ == '__main__':
    M = 8
    num_clocks = 1000

    A = 3.4
    B = -7.2
    P = 0.93
    theta = 8/16
    
    sample_rate = 3e9  # 3 GS/s
    frequency = 400e6  # 400 MHz
    
    t = np.arange(num_clocks * M) / sample_rate  # Time vector
    sine_wave = 20*np.sin(2 * np.pi * frequency * t)

    # data = sine_wave.reshape(num_clocks, M)
    
    biquad = SimBiquad(data=sine_wave, A=A, B=B, P=P, theta=np.pi*theta, M=M)
    
    biquad.whole()
    output = biquad.get_biquad()

    other = Filterred(sine_wave)

    fig, ax = plt.subplots(figsize=(14,7))


    output.plotFFT(ax)
    other.plotFFT(ax)
    # ax.plot(np.arange(len(t)) / 8, sine_wave, label='Raw Sine')

    plt.legend()
    plt.show()
