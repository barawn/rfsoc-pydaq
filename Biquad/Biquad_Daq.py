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

        self.sdv = None
        self.rfsocLoad("zcubiquad")

        self.setZero(0, 1)
        self.update()
    
    ############################
    ##Maybe write your code here?
    ############################

    
    ############################
    ##Sets
    ############################
    def setSDV(self, sdv):
        self.sdv = sdv

    def setZero(self, A:int, B:int):
        A = A * 16384
        B = B * 16384
        self.sdv.write(0x04,B)
        self.sdv.write(0x04,A)

    def setPole(self, C0:int, C1:int, C2:int, C3:int):
        self.sdv.write(0x08,C2)
        self.sdv.write(0x08,C3)
        self.sdv.write(0x08,C1)
        self.sdv.write(0x08,C0)

    def setIncComp(self, a1:int,a2:int):
        self.sdv.write(0x0C,a1)
        self.sdv.write(0x0C,a2)

    def setFFFIR(self, Dff:int, X1:int, X2:int, X3:int, X4:int, X5:int, X6:int):
        self.sdv.write(0x10,Dff)
        self.sdv.write(0x10,X1)
        self.sdv.write(0x10,X2)
        self.sdv.write(0x10,X3)
        self.sdv.write(0x10,X4)
        self.sdv.write(0x10,X5)
        self.sdv.write(0x10,X6)

    def setGGFIR(self,Egg:int, X1:int, X2:int, X3:int, X4:int, X5:int, X6:int, X7:int):
        self.sdv.write(0x14,Egg)
        self.sdv.write(0x14,X1)
        self.sdv.write(0x14,X2)
        self.sdv.write(0x14,X3)
        self.sdv.write(0x14,X4)
        self.sdv.write(0x14,X5)
        self.sdv.write(0x14,X6)
        self.sdv.write(0x14,X7)

    def setGFFIR(self, Dfg:int):
        self.sdv.write(0x18,Dfg)
    
    def setFGFIR(self, Egf:int):
        self.sdv.write(0x18,Egf)

    def update(self):
        self.sdv.write(0x00,1)

    ############################
    ##Gets
    ############################

    def getAccum(self):
        return self.sdv.read(0x4)/131072
    
    def getTailDiff(self):
        gt = self.sdv.read(0x8)
        lt = self.sdv.read(0xc)
        return gt-lt

    ############################
    ##App
    ############################
    

    ############################
    ##Display
    ############################
    def setDisplay(self):
        pass
    
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
