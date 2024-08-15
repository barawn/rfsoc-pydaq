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

logger = logging.getLogger(__name__)

#FPGA Class
class Biquad_Daq(RFSoC_Daq):
    def __init__(self,
                 root: tk.Tk,
                 frame: tk.Frame,
                 numChannels: int = 4,
                 numSamples: int = 2**11,
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
            self.sdv.write(0x04,np.round(self.B)*16384)
        else:
            np.round(B)
            self.sdv.write(0x04,np.round(B)*16384)

        if A is None:
            self.sdv.write(0x04,self.A*16384)
        else:
            np.round(A)
            self.sdv.write(0x04,A*16384)
        self.sdv.write(0x00,1)

    #Introduce Pole terms to FIR
    def set_f_fir(self, Dff = None, X1:int = 0, X2:int = 0, X3:int = 0, X4:int = 0, X5:int = 0, X6:int = 0):
        if Dff == None:
            self.sdv.write(0x10, int(self.Dff*16384))
            for i in range(self.M-2, 0, -1):
                self.sdv.write(0x10,int(self.Xn[i]*16384))
        else:
            self.sdv.write(0x10, Dff*16384)
            self.sdv.write(0x10, X6*16384)
            self.sdv.write(0x10, X5*16384)
            self.sdv.write(0x10, X4*16384)
            self.sdv.write(0x10, X3*16384)
            self.sdv.write(0x10, X2*16384)
            self.sdv.write(0x10, X1*16384)
        self.sdv.write(0x00,1)

    def set_g_fir(self,Egg = None, X1:int = 0, X2:int = 0, X3:int = 0, X4:int = 0, X5:int = 0, X6:int = 0, X7:int = 0):
        if Egg is None:
            self.sdv.write(0x14,int(self.Egg*16384))

            for i in range(self.M-1, 0, -1):
                self.sdv.write(0x14,int(self.Xn[i]*16384))

        else:
            self.sdv.write(0x14,Egg*16384)

            self.sdv.write(0x14, X7*16384)
            self.sdv.write(0x14, X6*16384)
            self.sdv.write(0x14, X5*16384)
            self.sdv.write(0x14, X4*16384)
            self.sdv.write(0x14, X3*16384)
            self.sdv.write(0x14, X2*16384)
            self.sdv.write(0x14, X1*16384)

        self.sdv.write(0x00,1)

    #Finalise 2 clock delay to FIR -> IIR
    def set_F_fir(self, Dfg = None):
        if Dfg is None:
            self.sdv.write(0x18,int(self.Dfg))
        else:
            self.sdv.write(0x18,Dfg*16384)
        self.sdv.write(0x00,1)
    
    def set_G_fir(self, Egf = None):
        if Egf is None:
            self.sdv.write(0x1C,int(self.Egf))
        else:
            self.sdv.write(0x1C,Egf*16384)
        self.sdv.write(0x00,1)

    #Set IIR matrix coefficients
    def set_pole_coef(self, C0 = None, C1:int = None, C2:int = None, C3:int = None):
        if C0 is None:
            self.sdv.write(0x08,int(self.C2*16384))
            self.sdv.write(0x08,int(self.C3*16384))
            self.sdv.write(0x08,int(self.C1*16384))
            self.sdv.write(0x08,int(self.C0*16384))
        else:
            self.sdv.write(0x08,C2*16384)
            self.sdv.write(0x08,C3*16384)
            self.sdv.write(0x08,C1*16384)
            self.sdv.write(0x08,C0*16384)
        self.sdv.write(0x00,1)

    def set_incremental(self, a1 = None,a2:int = None):
        if a1 is None:
            self.sdv.write(0x0C,int(self.a1*16384))
            self.sdv.write(0x0C,int(self.a2*16384))
        else:
            self.sdv.write(0x0C,a1*16384)
            self.sdv.write(0x0C,a2*16384)
        self.sdv.write(0x00,1)

    def update(self):
        self.set_single_zero_fir()
        # self.set_f_fir()
        # self.set_g_fir()
        # self.set_F_fir()
        # self.set_G_fir()
        # self.set_pole_coef()
        # self.set_incremental()
        logger.debug("Updating the filter coefficients")

    ############################
    ##Gets
    ############################

    def printPoles(self):
        pole1, pole2 = self.poles()
        print(f"Poles are : {pole1} || {pole2}")
        logger.debug(f"Poles are : {pole1} || {pole2}")

    def printCoef(self):
        print(f"A : {self.A}\nB : {self.B}\nP : {self.P}\nTheta : {self.theta}\nM : {self.M}")

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

    def set_Dff(self):
        self.Dff = -1 * self.P**self.M * self.chebyshev(self.M-2)

    def set_Egg(self):
        self.Egg = self.P**self.M * self.chebyshev(self.M)
    
    def set_Dfg(self):
        self.Dfg = self.P**(self.M-1) * self.chebyshev(self.M-1)

    def set_Egf(self):
        self.Egf = -1 * self.P**(self.M+1) * self.chebyshev(self.M-1)

    def set_C0(self):
        self.C0 = self.P**(2*self.M) * (self.chebyshev(self.M-2)**2 - self.chebyshev(self.M-1)**2)
    
    def set_C1(self):
        self.C1 = self.P**(2*self.M - 1) * self.chebyshev(self.M-1) * (self.chebyshev(self.M) - self.chebyshev(self.M-2))
    
    def set_C2(self):
        self.C2 = self.P**(2*self.M + 1) * self.chebyshev(self.M-1) * (self.chebyshev(self.M-2) - self.chebyshev(self.M))

    def set_C3(self):
        self.C3 = self.P**(2*self.M) * (self.chebyshev(self.M)**2 - self.chebyshev(self.M-1)**2)
    
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
        submits['SetP'] = submitButton(submit, "Set P:", 1, lambda: self.submitPValue(submits['SetP']), 12)
        submits['SetTheta'] = submitButton(submit, "Set Theta * pi :", 0, lambda: self.submitThetaValue(submits['SetTheta']), 13)
    
    ############################
    ##DAQ Methods
    # I woudln't touch
    ############################

    def startWaveFrame(self):
        for i in range(self.numChannels):
            self.wf.addWaveframe(Waveframe(self.wf, i, self.channelName[i].split()[0], BiquadNotebook))
            logger.debug(f"Waveframe {i} has been made")
        self.wf.packFrames()
        self.wf.pack()

    def rfsocLoad(self, hardware = None):
        super().rfsocLoad(hardware)
        try:
            from serialcobsdevice import SerialCOBSDevice       ###Since this comes from the loaded zcuagc overlay it may not be recognised in vscode without the explicit import 
            self.setSDV(SerialCOBSDevice('/dev/ttyPS1', 1000000))
        except:
            logger.debug("It would appear the overloay you have tried to load doesn't contain SerialCOBSDevice")
        return

if __name__ == '__main__':
    pass
