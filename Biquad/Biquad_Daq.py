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
    """
    This is the base class for using the agc overlay.

    Should only be ammended with core agc methods/protocols
    """
    def __init__(self,
                 root: tk.Tk,
                 frame: tk.Frame,
                 numChannels: int = 4,
                 numSamples: int = 2**11,
                 channelName = ["","","","","","","",""]):
        super().__init__(root, frame, numChannels, numSamples, channelName)

        self.sdv = None
        self.rfsocLoad("zcubq8")
    ############################
    ##Maybe write your code here?
    ############################



    ############################
    ##Sets
    ############################
    def setSDV(self, sdv):
        self.sdv = sdv        

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
