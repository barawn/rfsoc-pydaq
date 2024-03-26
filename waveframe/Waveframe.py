##Python Imports
import tkinter as tk
from tkinter import ttk
import numpy as np
from scipy.fft import fft, ifft, fftfreq
from scipy.constants import speed_of_light
from scipy.optimize import curve_fit

#System Imports
import logging

#Plotting imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

class Waveframe(ttk.Notebook):
    def __init__(self,
                 parent,
                 sampleRate=3.E9,
                 figsize=(3,2)):
        
        self.sampleRate = sampleRate
        
        super().__init__(parent)
        
        ##I've re-orded this section so it is a lot easier to add more figure if need be
        self.figs = {}
        self.canvs = {}
        
        ##Set up the time figure
        self.td = ttk.Frame(self)
        self.figs['time'] = Figure(figsize=figsize)
        self.canvs['time'] = FigureCanvasTkAgg(self.figs['time'],
                                               master=self.td)
        self.canvs['time'].draw()
        self.canvs['time'].get_tk_widget().pack()
        self.add(self.td, text='Time')
        
        ##Set up the Fourier Transform Frequency Figure
        self.fd = ttk.Frame(self)
        self.figs['freq'] = Figure(figsize=figsize)
        self.canvs['freq'] = FigureCanvasTkAgg(self.figs['freq'],
                                               master=self.fd)
        self.canvs['freq'].draw()
        self.canvs['freq'].get_tk_widget().pack()
        self.add(self.fd, text='Freq')
        
        ##Set up the fitted Waveform Figure
        self.ad = ttk.Frame(self)
        self.figs['fit'] = Figure(figsize=figsize)
        self.canvs['fit'] = FigureCanvasTkAgg(self.figs['fit'],
                                               master=self.ad)
        self.canvs['fit'].draw()
        self.canvs['fit'].get_tk_widget().pack()
        self.add(self.ad, text='Fit')
        
        ##I don't know why this is here
        self.user = ttk.Frame(self)
        self.figs['user'] = Figure(figsize=figsize)
        self.canvs['user'] = FigureCanvasTkAgg(self.figs['user'],
                                               master=self.user)
        self.canvs['user'].draw()
        self.canvs['user'].get_tk_widget().pack()
        self.add(self.user, text='User')
        
        #Template for adding new things
        
        # self.new = ttk.Frame(self)
        # self.figs['new'] = Figure(figsize=figsize)
        # self.canvs['new'] = FigureCanvasTkAgg(self.figs['new'],
        #                                        master=self.new)
        # self.canvs['new'].draw()
        # self.canvs['new'].get_tk_widget().pack()
        # self.add(self.new, text='New')
        
        # Callback signature is data, figure, canvas
        self.user_callback = None
        
    def convertToMag(self, yf):
        N = len(yf)
        return 2.0/N * np.abs(yf[0:N//2])
        
    def getSine(self, t,w,A,phi):
        return A*np.sin((w*t)+phi)
    
    def doSineWaveFit(self, waveForm, Amplitude, Frequency, Phase):
        guessFreq=Frequency
        guessOmega=guessFreq*2*np.pi/10**9
        guessAmp=Amplitude
        guessPhase = Phase
        
        omega=freq=amp=phase=failCount=0
        parameter = [guessOmega, guessAmp, guessPhase]
        
        parameter, covariance = curve_fit(self.getSine, np.arange(len(waveForm))*1.E9/self.sampleRate, waveForm, 
                                          p0=[guessOmega,guessAmp,guessPhase], 
                                          bounds=([guessOmega*0.9, guessAmp, guessPhase-0.25*np.pi], [guessOmega/0.9, guessAmp/0.7, guessPhase+0.25*np.pi]))
        omega=parameter[0]
        freq=parameter[0]/(2*np.pi)
        amp=parameter[1]
        phase=parameter[2]
        return omega,freq,amp,phase
        
        
    def plot(self, data, title, Wave, toPlot):#, Amp, Freq):
        Amp = Wave[0]
        Freq = Wave[1]
        Phase = Wave[2]
    
        self.figs['time'].clear()
        self.figs['freq'].clear()
        self.figs['fit'].clear()
        self.figs['user'].clear()
        # we want this in nanoseconds, so divide samplerate by 1E9
        samplePeriod = 1.E9/self.sampleRate
        xaxis = np.arange(len(data))*samplePeriod
        
        ax = self.figs['time'].add_subplot(111)
        ax.plot(xaxis, data)
        ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5, label='Zero Line')
        ax.axhline(y=Amp, color='black', linestyle='--', linewidth=0.3, label='Amplitude Line')
        
        stats_text = f"Amplitude: {Amp:.2f} Counts\nFrequency: {(Freq/10**6):.2f} MHz\nPhase: {Phase:.2f} radians"
        ax.text(0.95, 0.95, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

        self.canvs['time'].draw()
        
        ##Plotting additional optional plots. These more than double the aqcuire time so making them optional is nice
        if toPlot[0]:
            self.plotFreq(data, title, Amp, Freq)
            
        if toPlot[1]:
            self.plotFit(data, title, xaxis, Amp, Freq, Phase)

        if callable(self.user_callback):
            try:
                self.user_callback(data,
                                   self.figs['user'],
                                   self.canvs['user'])
            except TypeError:
                logging.error("user_callback '%s' type error: check arguments (data, fig, canvas)" % self.user_callback.__name__)        

    ##Additional plots
    def plotFreq(self, data, title, Amp, Freq):
        scipy_fft = fft(data)
        
        xf = np.linspace(0.0, 1.0/(2.0/self.sampleRate), len(data)//2)/(10**6)
        
        axFreq = self.figs['freq'].add_subplot(111)
        
        axFreq.plot(xf, self.convertToMag(scipy_fft), label='scipy')
        
        axFreq.set_title(title)
        axFreq.set_xlabel("Frequency (MHz)")
        axFreq.set_ylabel("Magnitude (arb.)")
        
        axFreq.axvline(x=Freq/(10**6), color='r', linestyle='--',  linewidth=0.3, label='Frequency')
        axFreq.axhline(y=Amp, color='r', linestyle='--', linewidth=0.3, label='Amplitude')
        
        axFreq.legend(loc='upper right')
        
        self.canvs['freq'].draw()
        return 'Plotted frequency'
    
    def plotFit(self, data, title, xaxis, Amp, Freq, Phi):
        
        Omega,Frequency,Amplitude,Phase=self.doSineWaveFit(data, Amp, Freq, Phi)
                        
        axFit = self.figs['fit'].add_subplot(111)
        axFit.plot(xaxis, data, label='Data')
        axFit.plot(xaxis, self.getSine(xaxis,Omega,Amplitude,Phase), label='Fit')
        axFit.set_title(title)
        axFit.set_xlabel('time (ns)')
        axFit.set_ylabel('ADC Counts', labelpad=-3.5)
        
        axFit.axhline(y=0, color='black', linestyle='--', linewidth=0.5, label='Zero Line')
        axFit.axhline(y=Amp, color='black', linestyle='--', linewidth=0.3, label='Amplitude Line')
        
        axFit.legend(loc='upper right')
        
        self.canvs['fit'].draw()