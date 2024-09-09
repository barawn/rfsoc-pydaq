import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import freqz

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Waveforms.Filterred import Filterred

class SimBiquad():
    def __init__(self, data, A=0, B=1, P=0, theta=np.pi, M=8):
        self.A = A
        self.B = B
        self.P = P
        self.theta = theta
        self.M = M
        self.length = int(len(data)/8)
        
        self.data = data
        self.clocks = data.reshape(-1, 8)
        
        self.u = np.zeros((self.length, 8))
        self.y = np.zeros((self.length, 8))
        
        self.f = np.zeros(self.length)
        self.g = np.zeros(self.length)
        self.F = np.zeros(self.length)
        self.G = np.zeros(self.length)
        
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
        
        self.set_Xn()
        self.set_Cross()
        self.set_Cs()
        self.set_As()


    def setA(self, A):
        self.A = A
    
    def setB(self, B):
        self.B = B

    def setP(self,P):
        self.P=P
        self.set_Xn()
        self.set_Cross()
        self.set_Cs()
        self.set_As()

    def setTheta(self,theta):
        self.theta = theta
        self.set_Xn()
        self.set_Cross()
        self.set_Cs()
        self.set_As()

    def setData(self, data):
        self.data = data
        
        self.clocks = data.reshape(-1, 8)
        self.length = int(len(data)/8)

        self.u = np.zeros((self.length, 8))
        self.y = np.zeros((self.length, 8))
        
        self.f = np.zeros(self.length)
        self.g = np.zeros(self.length)
        self.F = np.zeros(self.length)
        self.G = np.zeros(self.length)
    
    def set_Xn(self):
        for n in range(self.M):
            self.Xn[n] = self.P**n * self.chebyshev(n)

        # self.Xn[0] = 1
    
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

    def to_4bit_signed(self, nested_values, scale_factor=16384):
        processed_nested_values = []
        
        for sublist in nested_values:
            processed_sublist = []
            for value in sublist:
                # Scale and round the value
                scaled_value = np.round(value * scale_factor)
                
                # Handle wrapping for values outside the 4-bit signed integer range [-8, 7]
                wrapped_scaled_value = ((scaled_value + (8 * scale_factor)) % (16 * scale_factor)) - (8 * scale_factor)
                
                # Convert back to floating-point representation
                fixed_point_value = wrapped_scaled_value / scale_factor
                
                processed_sublist.append(fixed_point_value)
            
            processed_nested_values.append(processed_sublist)
        
        return processed_nested_values


    def calc_12_bit(self, value):
        # Define the range limits
        min_val = -2048
        max_val = 2048
        
        # Calculate the range width
        range_width = max_val - min_val
        
        # Wrap the value around using modulo
        wrapped_value = ((value - min_val) % range_width) + min_val
        
        return wrapped_value

    def calc_12_bit_array(self, array):
        # Define the range limits
        min_val = -2048
        max_val = 2048
        
        # Calculate the range width
        range_width = max_val - min_val
        
        # Wrap the values around using modulo for the entire array
        wrapped_array = ((array - min_val) % range_width) + min_val
        
        return wrapped_array


    def set_daq_coeffs(self, params):
        # params = self.to_4bit_signed(params)
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

        
    def single_zero_fir(self):
        for b, clock in enumerate(self.clocks):
            for n, sample in enumerate(clock):
                if b==0 and n == 0:
                    self.u[0][0] = self.A * self.data[0]
                elif b==0 and n==1:
                    self.u[0][1] = self.A * self.data[1] + self.B * self.data[0]
                else:
                    self.u[b][n] = self.A * self.data[self.M*b+n] + self.B * self.data[self.M*b+n-1] + self.A * self.data[self.M*b+n-2]

        self.u = np.floor(self.calc_12_bit_array(self.u))
            
    def set_u(self):
        for b, clock in enumerate(self.clocks):
            for n, sample in enumerate(clock):
                self.u[b][n] = self.clocks[b][n]

    def single_zero_fir2(self):
        for b, clock in enumerate(self.clocks):
            for n, sample in enumerate(clock):
                place = self.M*b + n
                if b==0 and n == 0:
                    self.y[b][n] = self.A * self.y[place//self.M][place%self.M]
                elif b==0 and n==1:
                    self.y[b][n] = self.A * self.y[place//self.M][place%self.M] + self.y[(place-1)//self.M][(place-1)%self.M]
                else:
                    self.y[b][n] =self.A * self.y[place//self.M][place%self.M] + self.y[(place-1)//self.M][(place-1)%self.M] + self.A * self.y[(place-1)//self.M][(place-1)%self.M]

    def first_constants(self):
        for b, clock in enumerate(self.u):
            #Current clock single FIR output
            # self.f[b] = clock[0]
            # self.g[b] = clock[1] + (self.P * self.chebyshev(1) * clock[0])
            self.f[b] = self.u[b][0]
            self.g[b] = self.u[b][1] + (self.Xn[1] * self.u[b][0]) 
            
            #Previous clocks output
            if b>0:
                self.f[b] += self.Xn[1] * self.u[b - 1][self.M - 1]
                
                for i in range(2, self.M - 1):
                    self.f[b] += self.Xn[i] * self.u[b - 1][self.M - i]
                    self.g[b] += self.Xn[i] * self.u[b - 1][self.M - i + 1]
                
                self.g[b] += self.Xn[self.M - 1] * self.u[b - 1][2]
                    
    def second_constants(self):
        self.F[0] = self.f[0]
        self.G[0] = self.g[0]
        for b in range(1, len(self.f)):
            self.F[b] = self.Dff * self.f[b - 1] + self.Dfg * self.g[b - 1] + self.f[b]
            self.G[b] = self.Egg * self.g[b - 1] + self.Egf * self.f[b - 1] + self.g[b]
    
    def IIR_calculation(self):
        self.y[0][0] = self.F[0]
        self.y[0][1] = self.G[0]
        
        self.y[1][0] = self.F[1]
        self.y[1][1] = self.G[1]
        
        for b in range(2, len(self.clocks)):
            self.y[b][0] = self.C0 * self.y[b - 2][0] + self.C1 * self.y[b - 2][1] + self.F[b]
            self.y[b][1] = self.C2 * self.y[b - 2][0] + self.C3 * self.y[b - 2][1] + self.G[b]

    def implementation(self):
        for b, clock in enumerate(self.y):
            for i in range(2, self.M):
                self.y[b][i] = -self.a1 * self.y[b][i - 1] - self.a2 * self.y[b][i - 2] + self.u[b][i]
    
    def FIR(self):
        self.single_zero_fir()

        # self.set_u()
        self.first_constants()
        self.second_constants()
    
    def IIR(self):
        self.FIR()
        self.IIR_calculation()
        self.implementation()
        # self.single_zero_fir2()
        
        
    def get_fir(self):
        return np.array([item for sublist in self.u for item in sublist])

    def get_u(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = np.floor(self.calc_12_bit(self.u[b,0]))
            result[b, 1] = np.floor(self.calc_12_bit(self.u[b,1]))
        return result.flatten()
    
    def get_decimated1(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = self.calc_12_bit(np.floor(self.f[b]))
            result[b, 1] = self.calc_12_bit(np.floor(self.g[b]))
        return result.flatten()
    
    def get_decimated2(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = np.floor(self.calc_12_bit(self.F[b]))
            result[b, 1] = np.floor(self.calc_12_bit(self.G[b]))
        return result.flatten()
        
    def get_biquad(self):
        return np.array([int(item) for sublist in self.y for item in sublist])
    
    def get_decimated(self):
        result = np.zeros_like(self.y)
        for b in range(self.length):
            result[b, 0] = np.floor(self.calc_12_bit(self.y[b, 0]))  # First output of the clock period
            result[b, 1] = np.floor(self.calc_12_bit(self.y[b, 1]))  # Last output of the clock period
        return result.flatten()
    
    
if __name__ == '__main__':
    P = 0.001
    theta = np.pi
    M = 8
    num_clocks = 64
    A = 20
    B = 20
    
    sample_rate = 3e9  # 3 GS/s
    frequency = 400e6  # 400 MHz
    
    t = np.arange(num_clocks * M) / sample_rate  # Time vector
    sine_wave = np.sin(2 * np.pi * frequency * t)

    # data = sine_wave.reshape(num_clocks, M)
    
    biquad = Biquad(data=sine_wave, A=A, B=B, P=P, theta=theta, M=M)
    
    biquad.IIR()
    # output = biquad.get_fir()
    # output = biquad.get_decimated1()
    # output = biquad.get_decimated2()
    output = biquad.get_biquad()

    output_flat = np.array(output).flatten()

    plt.figure(figsize=(14, 7))
    
    plt.subplot(3, 1, 1)
    plt.plot(t, sine_wave)
    plt.title('Input Sine Wave')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')

    plt.subplot(3, 1, 2)
    plt.plot(t[:len(output_flat)], output_flat)
    plt.title('Output of Biquad Filter')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    
    plt.subplot(3, 1, 3)
    plt.plot(t[:len(output_flat)], output_flat)
    plt.plot(t, sine_wave)
    plt.title('On top each other')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')

    plt.tight_layout()
    plt.show()
