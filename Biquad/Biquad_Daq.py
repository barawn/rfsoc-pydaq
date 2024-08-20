##Python Imports
import numpy as np
import tkinter as tk
from tkinter import filedialog
from scipy.fft import fft, ifft, fftfreq
from scipy.constants import speed_of_light
from typing import Callable

#System Imports
import logging
import subprocess
import os, sys, inspect, importlib, configparser, csv

from RFSoC_Daq import RFSoC_Daq

from widgets.SubmitButton import submitButton

from Biquad.BiquadNotebook import BiquadNotebook
from waveframe.Waveframe import Waveframe

from Waveforms.Waveform import Waveform
from Waveforms.Filterred import Filterred
from Waveforms.Gated import Gated
from Waveforms.SimFilter import SimFilter

logger = logging.getLogger(__name__)

#FPGA Class
class Biquad_Daq(RFSoC_Daq):
    def __init__(self,
                 root: tk.Tk = None,
                 frame: tk.Frame = None,
                 numChannels: int = 4,
                 numSamples: int = 2**10,
                 channelName = ["","","","","","","",""]):
        super().__init__(root, frame, numChannels, numSamples, channelName)

        self.A = 0
        self.B = 1
        self.P = 0
        self.theta = np.pi
        self.M = 8

        self.Xn = np.zeros(self.M)
        
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

        self.sdv = None
        self.rfsocLoad("zcubiquad")

        self.set_coefs()

        self.set_single_zero_fir()

        # self.setZero(0, 1)
        # self.sdv.write(0x00,1)

    ############################
    ##Maybe write your code here?
    ############################

    
    ############################
    ##Sets
    ############################
    def setSDV(self, sdv):
        self.sdv = sdv

    def setA(self, A):
        self.A = A
    
    def setB(self, B):
        self.B = B

    def setP(self,P):
        self.P=P
        self.set_coefs()

    def setTheta(self,theta):
        self.theta = theta
        self.set_coefs()

    def setM(self, M):
        self.M = M

    def set_coefs(self):
        self.set_Xn()
        self.set_As()
        self.set_crosslink()
        self.set_iir_coefs()
    
    #Indepnedent single FIR (only zero)
    def set_single_zero_fir(self, A = None, B = None):
        if B is None:
            self.sdv.write(0x04,np.round(self.B*16384))
        else:
            np.round(B)
            self.sdv.write(0x04,np.round(B*16384))

        if A is None:
            self.sdv.write(0x04,self.A*16384)
        else:
            np.round(A)
            self.sdv.write(0x04,A*16384)
        self.sdv.write(0x00,1)

    #Introduce Pole terms to FIR
    def set_f_fir(self, Dff = None, X1:int = 0, X2:int = 0, X3:int = 0, X4:int = 0, X5:int = 0, X6:int = 0):
        Dff = Dff if Dff is not None else self.Dff
        X1 = X1 if X1 is not None else self.Xn[1]
        X2 = X2 if X2 is not None else self.Xn[2]
        X3 = X3 if X3 is not None else self.Xn[3]
        X4 = X4 if X4 is not None else self.Xn[4]
        X5 = X5 if X5 is not None else self.Xn[5]
        X6 = X6 if X6 is not None else self.Xn[6]
        
        self.sdv.write(0x10, int(np.round(Dff * 16384)))
        Xn = [X6, X5, X4, X3, X2, X1]

        for x in Xn:
            self.sdv.write(0x10, int(np.round(x * 16384)))

        self.sdv.write(0x00,1)

    def set_g_fir(self, Egg=None, X1=None, X2=None, X3=None, X4=None, X5=None, X6=None, X7=None):
        Egg = Egg if Egg is not None else self.Egg
        X1 = X1 if X1 is not None else self.Xn[1]
        X2 = X2 if X2 is not None else self.Xn[2]
        X3 = X3 if X3 is not None else self.Xn[3]
        X4 = X4 if X4 is not None else self.Xn[4]
        X5 = X5 if X5 is not None else self.Xn[5]
        X6 = X6 if X6 is not None else self.Xn[6]
        X7 = X7 if X7 is not None else self.Xn[7]


        self.sdv.write(0x10, int(np.round(Egg * 16384)))
        
        Xn = [X7, X6, X5, X4, X3, X2, X1]
        for x in Xn:
            self.sdv.write(0x10, int(np.round(x * 16384)))

        self.sdv.write(0x00,1)

    #Finalise 2 clock delay to FIR -> IIR
    def set_F_fir(self, Dfg = None):
        Dfg = Dfg if Dfg is not None else self.Dfg

        self.sdv.write(0x10, int(np.round(Dfg * 16384)))

        self.sdv.write(0x00,1)
    
    def set_G_fir(self, Egf = None):
        Egf = Egf if Egf is not None else self.Egf

        self.sdv.write(0x10, int(np.round(Egf * 16384)))
        
        self.sdv.write(0x00,1)

    #Set IIR matrix coefficients
    def set_pole_coef(self, C0=None, C1=None, C2=None, C3=None):
        C0 = C0 if C0 is not None else self.C0
        C1 = C1 if C1 is not None else self.C1
        C2 = C2 if C2 is not None else self.C2
        C3 = C3 if C3 is not None else self.C3

        self.sdv.write(0x08, int(np.round(C2 * 16384)))
        self.sdv.write(0x08, int(np.round(C3 * 16384)))
        self.sdv.write(0x08, int(np.round(C1 * 16384)))
        self.sdv.write(0x08, int(np.round(C0 * 16384)))
        self.sdv.write(0x00, 1)

    def set_incremental(self, a1 = None, a2 = None):
        a1 = a1 if a1 is not None else self.a1
        a2 = a2 if a2 is not None else self.a2

        self.sdv.write(0x08, int(np.round(a1 * 16384)))
        self.sdv.write(0x08, int(np.round(a2 * 16384)))
        self.sdv.write(0x00, 1)

    def update(self):
        self.set_single_zero_fir()
        # self.set_f_fir()
        # self.set_g_fir()
        # self.set_F_fir()
        # self.set_G_fir()
        # self.set_pole_coef()
        # self.set_incremental()

    ############################
    ##Gets
    ############################

    def get_Xns(self):
        return np.round(self.Xn*16384)/16384
        
    def get_crosslink(self):
        return [np.round(self.Dff*16384)/16384, np.round(self.Egg*16384)/16384, np.round(self.Dfg*16384)/16384, np.round(self.Egf*16384)/16384]

    def get_poleCoef(self):
        return [np.round(self.C0*16384)/16384, np.round(self.C1*16384)/16384, np.round(self.C2*16384)/16384, np.round(self.C3*16384)/16384]

    def get_incremental(self):
        return [np.round(self.a1*16384)/16384, np.round(self.a2*16384)/16384]

    def get_coeffs(self):
        return self.get_Xns(), self.get_crosslink(), self.get_poleCoef(), self.get_incremental()

    ############################
    ##Prints
    ############################
    def printPoles(self):
        pole1, pole2 = self.calc_poles()
        print(f"Poles are : {pole1} || {pole2}")
        logger.debug(f"Poles are : {pole1} || {pole2}")

    def printParams(self):
        print(f"A : {self.A}\nB : {self.B}\nP : {self.P}\nTheta : {self.theta}\nM : {self.M}")

    def printCoeffs(self):
        print(f"X1 : {self.Xn[1]}\nX2 : {self.Xn[2]}\nX3 : {self.Xn[3]}\nX4 : {self.Xn[4]}\nX5 : {self.Xn[5]}\nX6 : {self.Xn[6]}\nX7 : {self.Xn[7]}\n")

        print(f"\nDff : {self.Dff}\nEgg : {self.Egg}\nDfg : {self.Dfg}\nEgf : {self.Egf}\n")

        print(f"\nC0 : {self.C0}\nC1 : {self.C1}\nC2 : {self.C2}\nC3 : {self.C3}\n")

        print(f"\na1 : {self.a1}\na2 : {self.a2}")

    ############################
    ##Calcs
    ############################

    def calc_poles(self):
        return self.P*np.exp(1j * self.theta), self.P*np.exp(-1 * 1j * self.theta)

    def chebyshev(self, num):
        return np.sin((num+1)*self.theta)/np.sin(self.theta)
    
    def set_Xn(self):
        for n in range(self.M):
            self.Xn[n] = self.P**n * self.chebyshev(n)

        self.Xn[0] = 1

    def set_Dff(self):
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
    
    def set_a1(self):
        self.a1 = 2*self.P*np.cos(self.theta)
    
    def set_a2(self):
        self.a2 = self.P**2

    def set_crosslink(self):
        self.set_Dff()
        self.set_Dfg()
        self.set_Egg()
        self.set_Egf()

    def set_iir_coefs(self):
        self.set_C0()
        self.set_C1()
        self.set_C2()
        self.set_C3()
    
    def set_As(self):
        self.set_a1()
        self.set_a2()

    ############################
    ##App
    ############################
    
    def submitAValue(self, value):
        A = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the A to: {A}")
        self.setA(A)

    def submitBValue(self, value):
        B = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the B to: {B}")
        self.setB(B)

    def submitPValue(self, value):
        P = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the P to: {P}")
        self.setP(P)

    def submitThetaValue(self, value):
        Theta = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the Theta to: {Theta}")
        self.setTheta(Theta*np.pi)

    def setHotKeys(self):
        super().setHotKeys()
        self.root.bind("<F7>", lambda event: self.update())

    ############################
    ##Display
    ############################

    def setDisplay(self):
        button = self.root.nametowidget("button")
        buttons = {}
        buttons['Update'] = tk.Button(button,
                                text = "Update",
                                command = self.update)
        
        buttons['Update'].grid( row = 0, column=3, padx=5 )

        submit = self.root.nametowidget("submit")
        submits = {}
        submits['SetA'] = submitButton(submit, "Set A:", 0, lambda: self.submitAValue(submits['SetA']), 10)
        submits['SetB'] = submitButton(submit, "Set B:", 1, lambda: self.submitBValue(submits['SetB']), 11)
        submits['SetP'] = submitButton(submit, "Set P:", 0, lambda: self.submitPValue(submits['SetP']), 12)
        submits['SetTheta'] = submitButton(submit, "Set Theta * pi :", 1, lambda: self.submitThetaValue(submits['SetTheta']), 13)
    
    ############################
    ##DAQ Methods
    # I woudln't touch
    ############################

    def rfsocLoad(self, hardware = None):
        super().rfsocLoad(hardware)
        try:
            from serialcobsdevice import SerialCOBSDevice       ###Since this comes from the loaded zcuagc overlay it may not be recognised in vscode without the explicit import 
            self.setSDV(SerialCOBSDevice('/dev/ttyPS1', 1000000))
        except:
            logger.debug("It would appear the overloay you have tried to load doesn't contain SerialCOBSDevice")
        return

    def GuiAcquire(self):
        self.rfsocAcquire()
        arr = [Gated,Gated,Filterred,Filterred]
        for i in range(self.numChannels):
            self.wf.waveframes[i].setWaveform(arr[i](self.adcBuffer[i] >> 4))
            if self.wf.waveframes[i].toPlot == True:
                self.wf.waveframes[i].notebook.plot()
                
        logger.debug("Acquired data and Plotted")

    def JupyterAcquire(self):
        self.rfsocAcquire()
        
        self.waveforms = []
        
        self.waveforms.append(Gated(self.adcBuffer[0] >> 4))
        self.waveforms.append(Gated(self.adcBuffer[1] >> 4))
        self.waveforms.append(Filterred(self.adcBuffer[2] >> 4))
        # self.waveforms.append(Filterred(self.adcBuffer[3] >> 4))

if __name__ == '__main__':
    pass
