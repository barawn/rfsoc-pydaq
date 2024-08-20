import numpy as np
import matplotlib.pyplot as plt

from scipy.fft import fft
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, peak_widths, butter, filtfilt, correlate, lombscargle

from typing import List

from .Waveform import Waveform

class SineWave(Waveform):
    def __init__(self, waveform: List, sampleRate = 3.E9):
        ##This is what the fit outputs
        self.fitFrequency=None
        self.fitAmplitude=None
        self.fitPhase=None
        self.fitOffset=None

        ##A measure of how good the fit was
        self.fitDiff=None


    def getSine(self, t, w, A, phi, h):
        return A*np.sin((w*t)+phi)+h
    

    def setSineFit(self):
        if self.frequencyFFT == None:
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
        if self.fitFrequency == None:
            self.setSineFit()
        if self.RMS == None:
            self.setRMS()    
        
        Omega = self.fitFrequency * (2*np.pi)
        fit = self.getSine(np.array(self.timelist), Omega, self.fitAmplitude, self.fitPhase, self.fitOffset)
        self.fitDiff = self.calculate_rms((self.waveform-fit)/self.RMS)