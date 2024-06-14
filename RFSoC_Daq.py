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

#Module Imports
from waveframe.Waveframe import Waveframe
from waveframe.Waveframes import Waveframes

logger = logging.getLogger(__name__)

#FPGA Class
class RFSoC_Daq:
    """ Class holding all of the data for the current program.
    The RFSoC_Daq class holds all of the user-accessible
    data for the current program instance involving accessing
    the RFSoC.
    
    Attributes
    ----------
    numChannels : int
       Number of channels accessible (usually 4).
    numSamples : int
       Number of samples in an acquisition.
    adcBuffer : numpy.ndarray
       Buffer containing the last acquired data
    dev : pynq.Overlay
       Class representing the current programmed RFSoC    
    frame : tkinter.Frame 
       Tk frame holding the Waveframes
    wf : :obj:`list` of :obj:`waveframe.Waveframe`
       numChannels list of the Waveframes in the DAQ
    """
    def __init__(self,
                 root: tk.Tk,
                 frame: tk.Frame,
                 numChannels: int = 4,
                 numSamples: int = 2**11,
                 channelName = ["","","","","","","",""]):
        
        #Inputs
        self.root = root
        self.frame = frame
        self.numChannels = numChannels
        self.numSamples = numSamples
        self.channelName = channelName

        #Inititalising instance attributes
        self.adcBuffer = np.zeros( (numChannels, numSamples), np.int16 )
        self.dev = None
        self.wf = Waveframes(self.frame, self.numChannels)

        self.startWaveFrame()
        self.setHotKeys()

    def startWaveFrame(self):
        for i in range(self.numChannels):
            self.wf.addWaveframe(Waveframe(self.wf, i, self.channelName[i]))
            logger.debug(f"Waveframe {i} has been made")
        self.wf.packFrames()
        self.wf.pack()

    ############################
    ##Sets
    ############################
    def setNumSamples(self, NSum = 2**11):
        self.numSamples = NSum
        logger.debug(f"You will now take {self.numSamples} samples")
        return f"You will now take {self.numSamples} samples"
    def setAdcBuffer(self):
        self.adcBuffer = np.zeros( (self.numChannels, self.numSamples), np.int16 )
        logger.debug("The adcBuffer has been updated")
        return 'adcBuffer Updated'
    def setPlotFreq(self, Value=True):
        if isinstance(Value, bool):
            self.plotFreq = Value
            self.wf.plotExtras[0] = Value
            logger.debug(f"{'Plotting' if Value else 'Not plotting'} the frequency")
            return f"{'Plotting' if Value else 'Not plotting'} the frequency"
        else:
            logger.debug("Please input a valid option")
            return"Please input a valid option"

    ############################
    ##Gets
    ############################
    def getNumSamples(self):
        logger.debug(f"You are taking {self.numSamples} channels")
        return self.numSamples
    def getAdcBuffer(self):
        logger.debug(f"There is no way I'm printing the adcBuffer. That thing is huge")
        return self.adcBuffer
    
    def getWaveform(self, ch=0):
        try:
            return self.wf.waveframes[ch].waveform
        except:
            print("Appears the waveform hasn't ben instantiated")
            logger.debug("Appears the waveform hasn't ben instantiated")
            return 0
        
    def getSaveName(self):
        logger.debug(f"The currently set save name is : {self.wf.saveText}")
        return self.wf.saveText
    
    def getAdc(self, ch = 0):
        return self.adcBuffer[ch]/256 - 15.5
        
    ############################
    ##Calculations
    ############################
    def calculate_rms(self, data):
        square_sum = sum(x ** 2 for x in data)
        mean_square = square_sum / len(data)
        rms = np.sqrt(mean_square)
        return rms

    ############################
    ##Saving Methods
    ############################
    def writeToCSV(self, data, filename = None):
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        np.savetxt(f'/home/xilinx/data/{filename if filename is not None else self.wf.saveText}.csv', data, delimiter=',')
    
    def writeCSV(self, data1, data2, filename = None):        
        if not isinstance(data1, np.ndarray):
            data1 = np.array(data1)
        if not isinstance(data2, np.ndarray):
            data2 = np.array(data2)
        
        combined = np.column_stack((data1, data2))
        np.savetxt(f'/home/xilinx/data/{filename if filename is not None else self.wf.saveText}.csv', combined, delimiter=',')

    def Save(self):
        index = self.getEnlargedNotebook()
        self.rfsocAcquire()
        for i in range(100):
            print(i)
            self.wf.waveframes[index].saveWF()
            self.Acquire(index)
        self.wf.waveframes[index].setSaveWFName()
        
    ############################
    ##App
    ############################
    def getEnlargedNotebook(self):
        index = 0
        for waveframe in self.wf.waveframes:
            if waveframe.enlarged == True:
                index = waveframe.index
        return index
    
    def switchToTab(self, index):
        for waveframe in self.wf.waveframes:
            waveframe.notebook.switchToTab(index)

    def switchTab(self):
        for waveframe in self.wf.waveframes:
            waveframe.notebook.switchTab()

    def switchTabBack(self):
        for waveframe in self.wf.waveframes:
            waveframe.notebook.switchTabBack()


    def getSubmitInput(self, value, needNumber):
        if isinstance(value, object):
            logger.debug("Passed in an object, attempting to .entry.get()")
            try:
                result = eval(value.entry.get())
            except (NameError, SyntaxError):
                if needNumber == False:
                    result = value.entry.get()
                else:
                    logger.debug("Please pass in a number")
        else:
            logger.debug("Passed in an value")
            result = value
        return result
    
    def submitNumSamples(self, value = 11):
        NSamp = self.getSubmitInput(value, True)
        logger.debug(f"Currently have {self.numSamples} samples, you have inputted {2**NSamp} samples")
        
        if isinstance(NSamp, int) and 0<NSamp<=14:
            self.setNumSamples(2**NSamp)
            self.setAdcBuffer()
            return f"You will now take {self.numSamples} samples"
        else:
            logger.debug("Please input an appropriate Sample Size. The maximum is 14")
            return 'Please input an appropriate Sample Size'
        
    def submitSaveName(self, value):
        SaveName = self.getSubmitInput(value, False)
        logger.debug(f"You are setting the Save Files name to : {SaveName}")
        if SaveName and isinstance(SaveName, str) == False:
            SaveName=str(SaveName)
        self.wf.saveText = SaveName
        
    def setHotKeys(self):
        self.root.bind("<Control-s>", lambda event: self.Save())
        self.root.bind("<Control-p>", lambda event: self.frame.winfo_children()[self.getEnlargedNotebook()].btns['SavePlt'].invoke())
        
            
        self.root.bind("<F1>", lambda event: self.wf.waveframes[0].btns['Enlarge'].invoke())
        self.root.bind("<F2>", lambda event: self.wf.waveframes[1].btns['Enlarge'].invoke())
        self.root.bind("<F3>", lambda event: self.wf.waveframes[2].btns['Enlarge'].invoke())
        self.root.bind("<F4>", lambda event: self.wf.waveframes[3].btns['Enlarge'].invoke())
        
        self.root.bind("<F5>", lambda event: self.rfsocAcquire())
        
        self.root.bind("<F9>", lambda event: self.switchToTab(0))
        self.root.bind("<F10>", lambda event: self.switchToTab(1))
        self.root.bind("<F11>", lambda event: self.switchToTab(2))
        self.root.bind("<F12>", lambda event: self.switchToTab(3))
        
        self.root.bind("<Next>", lambda event: self.switchTab())
        self.root.bind("<Prior>", lambda event: self.switchTabBack())


    ############################
    ##DAQ Methods
    ############################

        
    def rfsocLoad(self, hardware = None):
        """Load an overlay file describing an RFSoC instance.
        The overlay needs to support being created bare (just "overlayName()")
        and must support the "internal_capture( buffer, numChannels )"
        function.
        """            

        try:
            file_path = f'/home/xilinx/python/{hardware}.py'
        except:
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

    def Acquire(self, Ch = 0):
        if isinstance(Ch, int):
            Ch = [Ch]
        if self.dev is None:
            logger.error("No RFSoC device is loaded!")
        self.dev.internal_capture(self.adcBuffer, self.numChannels)
        for ch in Ch:
            self.wf.waveframes[ch].setWaveform(self.adcBuffer[ch] >> 4)
        logger.debug("Acquired data")
    
    def rfsocAcquire(self):
        if self.dev is None:
            logger.error("No RFSoC device is loaded!")
            
        self.dev.internal_capture(self.adcBuffer,
                                    self.numChannels)
        
        for i in range(self.numChannels):
            self.wf.waveframes[i].setWaveform(self.adcBuffer[i] >> 4)
            if self.wf.waveframes[i].toPlot == True:
                self.wf.waveframes[i].notebook.plot()
                
        logger.debug("Acquired data and Plotted")


if __name__ == '__main__':
    pass
