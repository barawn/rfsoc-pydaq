import numpy as np

from scipy.fft import fft
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, peak_widths, butter, filtfilt, correlate

from typing import List

class Waveform():
    def __init__(self, waveform: List, sampleRate = 3.E9):
        self.waveform = waveform
        self.sampleRate = sampleRate
        self.timelist = np.arange(len(self.waveform))/sampleRate
        
        self.N = len(self.waveform)
        self.dt = self.timelist[1]-self.timelist[0] ##In Nano Seconds
        
    def updateWaveform():
        pass
        
    def setFreqFFT(self):
        self.fft_result = fft(self.waveform)
    
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
        
    def doFFTs(self):
        self.setWaveFFT()
        
    def setPeaktoPeak(self):
        self.peakToPeak = abs(max(self.waveform) - min(self.waveform))/2
        
    def setRMS(self):
        square_sum = sum(x ** 2 for x in self.waveform)
        mean_square = square_sum / self.N
        self.RMS = np.sqrt(mean_square)
        
    def setOffset(self):
        self.offset = np.mean(self.waveform)
        
    def setOffsetAnalysis(self):
        try:
            self.peakToPeak
        except:
            self.setPeaktoPeak()
        try :
            self.offset
        except:
            self.setOffset()
            
        posAmp = self.peakToPeak + self.offset
        negAmp = self.offset - self.peakToPeak
        
        self.positiveCount = 0
        self.negativeCount = 0
        
        self.positiveAboveAmp = 0
        self.negativeAboveAmp = 0
        
        for point in self.waveform:
            if point>0:
                self.positiveCount+=1
                if point > posAmp:
                    self.positiveAboveAmp += point-posAmp
            elif point<0:
                self.negativeCount+=1
                if point < negAmp:
                    self.negativeAboveAmp += negAmp - point
        
        self.positiveAmpDiff = np.max(self.waveform) - posAmp
        self.neagtiveAmpDiff = negAmp - np.min(self.waveform)
        
    def getSine(self, t, w, A, phi, h):
        return A*np.sin((w*t)+phi)+h
        
    def setSineFit(self):
        try:
            self.frequencyFFT
        except:
            self.setWaveFFT()
        guessFreq = self.frequencyFFT
        if guessFreq == 0:
            guessFreq = 200
        guessOmega = guessFreq*2*np.pi
        guessAmp = self.amplitudeFFT
        guessPhase = self.phaseFFT
        try:
            guessOffset = self.offset
        except:
            guessOffset = np.mean(self.waveform)
        
        parameter = [guessOmega, guessAmp, guessPhase]
        
        parameter, covariance = curve_fit(self.getSine, self.timelist, self.waveform, 
                                          p0=[guessOmega,guessAmp,guessPhase,guessOffset], 
                                          bounds=([guessOmega*0.9, guessAmp*0.8, guessPhase-2*np.pi, min(self.waveform)], [guessOmega*1.1, guessAmp*1.2, guessPhase+2*np.pi, max(self.waveform)]))
        
        self.fitFrequency=parameter[0]/(2*np.pi)
        self.fitAmplitude=parameter[1]
        self.fitPhase=parameter[2]
        self.fitOffset = parameter[3]
        
    def compareToFit(self):
        try:
            self.fitFrequency
        except:
            self.setSineFit()
        try:
            self.RMS
        except:
            self.setRMS()    
        
        Omega = self.fitFrequency * (2*np.pi)
        fit = self.getSine(np.array(self.timelist), Omega, self.fitAmplitude, self.fitPhase, self.fitOffset)
        self.fitDiff = self.calculate_rms((self.waveform-fit)/self.RMS)


    def calcPeaks(self):
        self.peaks, _ = find_peaks(self.waveform, height=400) #the minumum height of a peak. Probably should calculate this or something idk

        self.widths = peak_widths(self.waveform, self.peaks, rel_height=0.5)

    def butterworth(self):
        nyq = 0.5 * self.sampleRate
        normal_cutoff = 1.E9 / nyq
        b, a = butter(5, normal_cutoff, btype='low', analog=False)
        return b, a
    
    def lowpass_filter(self):
        b, a = self.butterworth()
        self.filtered_signal = filtfilt(b, a, self.waveform)
        
    def calculate_rms(self, data):
        square_sum = sum(x ** 2 for x in data)
        mean_square = square_sum / len(data)
        rms = np.sqrt(mean_square)
        return rms
    
    def doAmps(self):
        self.setWaveFFT()
        self.setPeaktoPeak()
        self.setRMS()
        self.setSineFit()
        
    def wholeShebang(self):
        self.doFFTs()
        self.setPeaktoPeak()
        self.setRMS()
        self.setOffsetAnalysis()
        self.setSineFit()
    
if __name__ == '__main__':
    pass
