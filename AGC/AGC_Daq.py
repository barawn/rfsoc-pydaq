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

from AGC.AgcNotebook import AgcNotebook
from waveframe.Waveframe import Waveframe

logger = logging.getLogger(__name__)

#FPGA Class
class AGC_Daq(RFSoC_Daq):
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
        self.rfsocLoad("zcuagc")
    ############################
    ##Maybe write your code here?
    ############################



    ############################
    ##Running agc core stuff
    ############################
    def loadAGC(self):
        if self.sdv is not None:
            self.sdv.write(0x00, 0x300)
            logger.debug("AGC Loaded")
        else:
            logger.debug("AGC not loaded, no sdv set")
            raise ImportError("No serial cobbs device loaded the daq")

    def applyAGC(self):
        if self.sdv is not None:
            self.sdv.write(0x00, 0x400)
            logger.debug("AGC applied")
        else:
            logger.debug("AGC not applied, no sdv set")
            raise ImportError("No serial cobbs device loaded the daq")
        
    def getAGC(self):
        self.loadAGC()
        self.applyAGC()

    def runAGC(self):
        self.sdv.write(0,0x4)
        self.sdv.write(0,0x1)
        while ((self.sdv.read(0) & 0x2) == 0):
            pass

    ############################
    ##Sets
    ############################
    def setSDV(self, sdv):
        self.sdv = sdv
    
    def setOffset(self, Value=80):
        if isinstance(Value, int):
            try:
                self.sdv.write(0x14, Value)
                self.getAGC()

                if self.getOffset() == Value:
                    logger.debug(f"The offset has been set to {Value}")
                    return f"The offset has been set to {Value}"
                else:
                    logger.debug("The offset has not been correctly set")
                    return "The offset has not been correctly set"
        
            except:
                logger.debug("It would appear that you don't have a sdv loaded in")
        else:
            logger.debug("Please input a valid option")
            return "Please input a valid option"

    def setScaling(self, Value=4096):
        if isinstance(Value, int):
            try:
                self.sdv.write(0x10, Value)
                self.getAGC()

                if self.getScaling() == Value:
                    logger.debug(f"The scaling has been set to {Value}")
                    return f"The scaling has been set to {Value}"
                else:
                    logger.debug("The scaling has not been correctly set")
                    return "The scaling has not been correctly set"
        
            except:
                logger.debug("It would appear that you don't have a sdv loaded in")
        else:
            logger.debug("Please input a valid option")
            return "Please input a valid option"
        

    ############################
    ##Gets
    ############################
    def getOffset(self):
        offset  = self.sdv.read(0x14)
        logger.debug(f"The Offset is currently set to {offset}")
        return offset

    def getScaling(self):
        scaling  = self.sdv.read(0x10)
        logger.debug(f"The Scaling is currently set to {scaling}")
        return scaling
    
    def getAccum(self):
        return self.sdv.read(0x4)/131072
    
    def getTailDiff(self):
        gt = self.sdv.read(0x8)
        lt = self.sdv.read(0xc)
        return gt-lt

    ############################
    ##App
    ############################
    
    def submitOffsetValue(self, value):
        OffsetValue = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the offset to: {OffsetValue}")
        self.setScaling(OffsetValue)
    
    def submitScalingValue(self, value):
        ScalingValue = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the scaling to: {ScalingValue}")
        self.setScaling(ScalingValue)

    ############################
    ##Display
    ############################
    def setDisplay(self):
        submit = self.root.nametowidget("submit")
        submits = {}
        submits['SetOffset'] = submitButton(submit, "Set the offset:", 0, lambda: self.submitOffsetValue(submits['SetOffset']), 10)
        submits['SetScaling'] = submitButton(submit, "Set the scaling:", 0, lambda: self.submitScalingValue(submits['SetScaling']), 11)

    ############################
    ##DAQ Methods
    # I woudln't touch
    ############################

    def startWaveFrame(self):
        for i in range(self.numChannels):
            self.wf.addWaveframe(Waveframe(self.wf, i, self.channelName[i].split()[0], AgcNotebook))
            logger.debug(f"Waveframe {i} has been made")
        self.wf.packFrames()
        self.wf.pack()

    def rfsocLoad(self, hardware = None):
        """Load an overlay file describing an RFSoC instance.
        The overlay needs to support being created bare (just "overlayName()")
        and must support the "internal_capture( buffer, numChannels )"
        function.
        """            

        if hardware is not None:
            file_path = f'/home/xilinx/zcumts/{hardware}.py'
        else:
            file_path = filedialog.askopenfilename(title="Select an overlay module",
                                            filetypes=[("Python files","*.py"),
                                                        ("All files", "*.*")])
        
        logger.debug("Asked to load overlay at %s" % file_path)
        newdir = os.path.dirname(os.path.abspath(file_path))    

        curpath = sys.path
        logger.debug("Adding directory %s to module search path" % newdir)
        sys.path.insert(1, newdir)    
        curdir = os.path.abspath(os.curdir)
        logger.debug("Changing directory to %s" % newdir)
        os.chdir(newdir)
        base, extension = os.path.splitext(os.path.basename(file_path))
        logger.debug("Going to try to import %s", base)
            
        # create a custom exception
        class LocalException(Exception):
            pass
        
        try:
            module = importlib.import_module(base, package=None)
            # First try to find an Overlay or module.FakeOverlay module.
            # FakeOverlays need to be defined in the same file.
            overlayClass = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    if obj.__name__ == 'Overlay' and obj.__module__ == 'pynq.overlay':
                        overlayClass = obj
                    if obj.__name__ == 'FakeOverlay' and obj.__module__ == module.__name__:
                        overlayClass = obj
            if overlayClass is None:
                del sys.modules[module.__name__]
                raise LocalException("Unable to find Overlay class in module %s" % module.__name__)
            logger.debug("Found Overlay class %s from module %s" % (overlayClass.__name__ , overlayClass.__module__ ))
            # Now find the module to call
            theClass = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    if issubclass(obj, overlayClass) and obj != overlayClass:
                        theClass = obj
            if theClass is None:
                del sys.modules[module.__name__]            
                raise LocalException("Unable to find a subclassed Overlay in module %s" % module.__name__)
            captureFn = getattr(theClass, "internal_capture", None)
            if not callable(captureFn):
                del sys.modules[module.__name__]
                raise LocalException("The Overlay %s in module %s has no callable internal_capture method" % (theClass.__name__ , module.__name__ ))
            logger.debug("Found RFSoC overlay %s" % theClass.__name__)
            self.dev = theClass()
            logger.debug("Created RFSoC device")
        except LocalException as e:
            logger.error(str(e))
        except Exception as e:
            logger.error("Unable to load module %s" % base)
            logger.error(str(e))
            
        logger.debug("Restoring original module search path")
        sys.path = curpath
        logger.debug("Going back to original directory %s" % curdir)
        os.chdir(curdir)

        try:
            from serialcobsdevice import SerialCOBSDevice       ###Since this comes from the loaded zcuagc overlay it may not be recognised in vscode without the explicit import 
            self.setSDV(SerialCOBSDevice('/dev/ttyPS1', 1000000))
        except:
            logger.debug("It would appear the overloay you have tried to load doesn't contain SerialCOBSDevice")
        return

if __name__ == '__main__':
    pass
