import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import lombscargle

from typing import List

from .Waveform import Waveform

class Filterred(Waveform):
    ##Was 400->920
    ##Now 424->952
    ##Do additional multiple clocks for testing

    ##Maybe we have it automatically pick a start and end
    ##Like do shorten wavelength when it finds first clock to when the clock goes to zero
    
    def __init__(self, waveform: List, A=0, B=1, P=0, theta=0.01, amp=1, sampleRate = 3.E9):
        ## start=280, end=800 for Simulation biquad
        super().__init__(waveform, sampleRate = 3.E9)

        self.A = A
        self.B = B
        self.P = P
        self.theta = theta
        self.amp = amp
        
        self.setClocks()
        self.set_waveform_range()

        self.decimated_WF = None
        self.decimated_TL = None

        self.periodogram_freqs = None
        self.periodogram = None
        self.periodogram_freq = None

    ##Gated waveform starts ~35 clocks in. The Daq biquad starts I can't remember but setting this is very annoying

#########################
## Automatic gating
#########################
    def find_first_clock(self):
        first_clock=0
        for clock in self.clocks:
            if clock[0] == 0 and clock[1] == 0:
                first_clock+=1
            else:
                break
        return first_clock
    
    def find_last_clock(self, start):
        last_clock=start
        for i in range(start, len(self.clocks)):
            if self.clocks[i][0] == 0 and self.clocks[i][1] == 0:
                break
            else:
                last_clock+=1
        return last_clock
    
    def set_waveform_range(self):
        first_clock = self.find_first_clock()
        last_clock = first_clock+64 ##This will ignore any only iir part
        # last_clock = self.find_last_clock(first_clock)
        self.shortenWaveform(first_clock*8, last_clock*8)
        self.setClocks()

#########################
## Calculations
#########################

###########
## Single_Zero_fir
###########

    def calc_Lambda(self):
        return 2*self.A*np.cos(self.omega) + self.B
    
    def calc_B_destruction(self):
        return -2*self.A*np.cos(self.omega)
    
###########
## Pole fir
###########
    def mu_i(self, i):
        return self.P**(i-1) * np.sin(i*self.theta)

######
## f
######
    def D_f(self):
        D_f = 0
        for i in range(1,8):
            D_f += self.mu_i(i) * np.cos(self.omega*i)
        return D_f
    
    def E_f(self):
        E_f = 0
        for i in range(1,8):
            E_f += self.mu_i(i) * np.sin(self.omega*i)
        return E_f

    def R_f(self):
        return np.sqrt(self.D_f()**2 + self.E_f()**2)
######
## g
######
    def D_g(self):
        D_g = 0
        for i in range(1,9):
            D_g += self.mu_i(i) * np.cos(self.omega*i)
        return D_g
    
    def E_g(self):
        E_g = 0
        for i in range(1,9):
            E_g += self.mu_i(i) * np.sin(self.omega*i)
        return E_g

    def R_g(self):
        return np.sqrt(self.D_g()**2 + self.E_g()**2)
    
    def Average_R_fg(self):
        return (abs(self.R_f())+abs(self.R_g()))/2

    
    def setRMS(self):
        if self.decimated_WF is None:
            self.convert_Decimated()

        square_sum = sum(x ** 2 for x in self.decimated_WF)
        mean_square = square_sum / len(self.decimated_WF)
        self.RMS = np.sqrt(mean_square)

#########################
## Miscleneuous
#########################
    ##Just in case you got the full waveform
    def convert_Decimated(self, start=0, end=7):
        if self.clocks is None:
            self.setClocks()
        self.decimated_WF = np.zeros((len(self.clocks),2))
        self.decimated_TL = np.zeros((len(self.clockTime),2))
        length = len(self.clocks)

        for b in range(length):
            self.decimated_WF[b, 0] = self.clocks[b, 0]  # First output of the clock period
            self.decimated_WF[b, 1] = self.clocks[b, 1]  # Last output of the clock period

            self.decimated_TL[b, 0] = self.clockTime[b, 0]
            self.decimated_TL[b, 1] = self.clockTime[b, 1]

        self.decimated_WF = self.decimated_WF.flatten()
        self.decimated_TL = self.decimated_TL.flatten()

    ##This is redundant, and if I recall never worked
    def Lomb_Scargle(self):
        self.convert_Decimated()

        n = len(self.decimated_WF)
        dxmin = np.diff(self.decimated_TL).min()
        duration = self.decimated_TL.ptp()

        self.periodogram_freqs = np.linspace(1/duration, n/duration, 5*n)

        self.periodogram = lombscargle(self.decimated_TL, self.decimated_WF, self.periodogram_freqs)

        self.periodogram_freq = self.periodogram.argmax()
        print(self.periodogram_freq)


#########################
## Plots
#########################

    def plotWaveform(self, ax: plt.Axes=None, title = None, figsize=(25, 15)):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        x_axis = np.arange(len(self.waveform)) / 8

        ax.plot(x_axis, self.waveform)

        if title is not None:
            ax.set_title(title)

        ax.set_xlabel('Clocks')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        self.setWaveFFT()
        self.setPeaktoPeak()
        self.setRMS()

        stats_text = f"Peak-Peak : {self.peakToPeak:.2f} ADC\nRMS : {self.RMS:.2f} ADC\nFrequency : {self.frequencyFFT*10**(-6):.2f} MHz"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))
        
    
    def plotDecimated(self, ax=None, title=None, figsize=(25, 15)):
        
        if self.decimated_WF is None:
            self.convert_Decimated()

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        ax.plot(self.decimated_TL, self.decimated_WF)

        ax.set_xlabel('Samples')
        ax.set_ylabel('ADC Counts')



    def plotPeriodogram(self, ax=None, title=None, figsize=(25, 15)):
        if self.periodogram_freqs is None:
            self.Lomb_Scargle()

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        # Convert frequencies to MHz (assuming decimated_TL is in seconds)
        freqs_mhz = self.periodogram_freqs * 1e-6

        ax.plot(freqs_mhz, self.periodogram)

        if title:
            ax.set_title(title)
        ax.set_xlabel('Frequency (MHz)')
        ax.set_ylabel('Power')
        plt.show()

    # def plotPeriodogram(self, ax: plt.Axes=None, title = None, figsize=(25, 15)):

    #     self.Lomb_Scargle()

    #     if ax is None:
    #         fig, ax = plt.subplots(figsize=figsize)

    #     ax.plot(self.periodogram_freqs, np.sqrt(4*self.periodogram/5*len(self.decimated_WF)))

    #     ax.set_xlabel('Frequency (rad/s)')
    #     ax.set_ylabel('No idea (arb)')