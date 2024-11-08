import numpy as np
import matplotlib.pyplot as plt

from scipy.fft import fft

from typing import List

class Waveform():
    def __init__(self, waveform: np.ndarray, sampleRate = 3.E9, title : str = None):
        self.waveform = waveform
        self.sampleRate = sampleRate
        self.timelist = np.arange(len(self.waveform))/self.sampleRate
        self.title = title

        self.clocks = None
        self.clockTime = None

        self.N = len(self.waveform)
        self.dt = self.timelist[1]-self.timelist[0] ##In Nano Seconds
        
        ##FFT stuff
        self.fft_result = None
        
        self.xf = None
        
        self.mag_spectrum = None
        self.phase_spectrum = None
        
        self.peak_freq_index = None
        self.peak_phase_index = None
        
        self.frequencyFFT = None
        self.amplitudeFFT = None
        self.phaseFFT = None

        self.omega = None
        
        ##Amplitude Stuff
        self.peakToPeak = None
        
        self.RMS = None


    #####
    ## Clock formatting stuff
    #####

    ##Testing reason, first clock sometimes wildly different to rest and messes with the rms prediction
    ##Clock pos for sim is 35
    def removeFirstClock(self, clock_pos):
        self.waveform = self.waveform[8*clock_pos:]
        self.clocks = self.clocks[clock_pos:]
        self.clockTime = self.clockTime[clock_pos:]

    def shortenWaveform(self, start, end):
        self.waveform = self.waveform[start:end]
        self.timelist = self.timelist[start:end]
        self.N = len(self.waveform)

    def setClocks(self):
        self.clocks = self.waveform.reshape(-1, 8)        
        self.clockTime = self.timelist.reshape(-1, 8)
        
    #####
    ## Generic FFT Stuff
    #####
    
    def setFreqFFT(self):
        self.fft_result = fft(self.waveform)
        return self.fft_result
    
    def setFFTSpectrum(self):
        self.setFreqFFT()
        self.xf = np.linspace(0.0, 1.0 / (2 * self.dt), self.N // 2)
        self.mag_spectrum = np.abs(self.fft_result[:self.N//2])* 2 / self.N
        self.phase_spectrum = np.angle(self.fft_result[0:self.N//2])
        
    def setFFTIndices(self):
        self.setFFTSpectrum()
        self.peak_freq_index = np.argmax(self.mag_spectrum)
        self.peak_phase_index = np.argmax(self.phase_spectrum)
        
    def setWaveFFT(self):
        self.setFFTIndices()
        self.frequencyFFT = self.xf[self.peak_freq_index]
        self.amplitudeFFT = self.mag_spectrum[self.peak_freq_index]
        self.phaseFFT = self.phase_spectrum[self.peak_phase_index] 

        self.omega = 2*np.pi * self.frequencyFFT/self.sampleRate
        
    def doFFTs(self):
        self.setWaveFFT()
        
    #####
    ## Amplitudes
    #####

    def setPeaktoPeak(self):
        self.peakToPeak = abs(max(self.waveform) - min(self.waveform))/2
        
    def setRMS(self):
        square_sum = sum(x ** 2 for x in self.waveform)
        mean_square = square_sum / self.N
        self.RMS = np.sqrt(mean_square)

    #####
    ## Auto run stuff
    #####

    def doAmps(self):
        self.setWaveFFT()
        self.setPeaktoPeak()
        self.setRMS()
        
    def wholeShebang(self):
        self.doFFTs()
        self.setPeaktoPeak()
        self.setRMS()

    #####
    ## Miscellaneous
    #####

    ## I end up always having to write one of these anyway
    def calculate_rms(self, data):
        square_sum = sum(x ** 2 for x in data)
        mean_square = square_sum / len(data)
        rms = np.sqrt(mean_square)
        return rms
    
    
    #####
    ## Plotting stuff (Replacing the previous notebook structure, which was kinda horrible)
    ### Since this is the superclass this has the most basic plots. Inherited classes will have more specific plots (potential overrides)
    #####

    def plotWaveform(self, ax: plt.Axes=None, title = None, figsize=(25, 15), colour = None, scale = 1, offset = 0, pos = 0):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        if colour is not None:
            ax.plot(self.timelist*10**9, scale * self.waveform + offset, color=colour, label = self.title)
        else:
            ax.plot(self.timelist*10**9, scale * self.waveform + offset, self.title)

        if title is not None:
            ax.set_title(title)

        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        self.doAmps()

        ## For the basic plot not sure what else one might want

        stats_text = f" P2P : {self.peakToPeak:.2f} ADC\n RMS : {self.RMS:.2f} ADC\nFreq : {self.frequencyFFT*10**(-6):.2f} MHz"
        
        ax.text(1, 0.98 - pos, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, color=colour, bbox=dict(facecolor='black', alpha=0.5))
        
    def plotClocks(self, clocks, ax: plt.Axes=None, title = None, figsize=(25, 15)):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)


        self.shortenWaveform(0,8*clocks)

        x_axis = np.arange(len(self.waveform)) / 8

        ax.plot(x_axis, self.waveform)

        if title is not None:
            ax.set_title(title)

        ax.set_xlabel('Clocks')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        self.setWaveFFT()
        self.setPeaktoPeak()

        stats_text = f"Peak-Peak : {self.peakToPeak:.2f} ADC\nFrequency : {self.frequencyFFT*10**(-6):.2f} MHz"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

    def plotFFT(self, ax: plt.Axes=None, title = None, figsize=(25, 15), colour = None):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)

        try:
            self.doFFTs()

            if colour is not None:
                ax.plot(self.xf*10**(-6), 20 * np.log10(self.mag_spectrum), label=self.title, color=colour)
            else:
                ax.plot(self.xf*10**(-6), 20 * np.log10(self.mag_spectrum), label=self.title)

        except:
            ## Yeah, sometimes this won't work (typically an issue with the biquad), better not crash everything)
            print("It's just not possible")

        if title is not None:
            ax.set_title(title)
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("Magnitude (arb.)")
        
        # stats_text = f"Frequency : {self.frequencyFFT*10**(-6):.2f} MHz\nAmplitude : {self.amplitudeFFT:.2f} ADC"
        
        # ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
        #     transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))