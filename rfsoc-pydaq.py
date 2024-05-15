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
from textconsole.TextConsole import TextConsole
from scrolledlog.ScrolledLog import ScrolledLog
from waveframe.Waveframe import Waveframe
from waveframe.Waveframes import Waveframes

logger = logging.getLogger(__name__)

#Establishing base values for parameters
default_numChannels = 4
default_numSamples = 2048
default_sampleRate = 3.E9

numChannels = 4
sampleExponent = 5
numSamples = 2**sampleExponent
sampleRate = 3.E9

figsize = (3,2)

##Not all screens are so accomadating to this quick change
sizeEditor = (1, 1)

portNames = ["ADC224_T0_CH0 (LF)","ADC224_T0_CH1 (LF)","ADC225_T1_CH0 (HF)","ADC225_T1_CH1 (HF)","Port_5","Port_6","Port_7"," Port_8"]

##Allows it to be globally accessible
theDaq = None

#Maybe add a 'continous' waveform 'generator'. I.e. every 10 seconds it runs acquire

#GUI classe(s)

##Submit button requires numerous compoennts and was easier to make a class
class submitButton:
    def __init__(self,
                 frame: tk.Frame,
                 label_text,
                 placeholder_text,
                 submit_command: Callable,
                 Auto=False):
        
        self.frame=frame
        
        self.label =tk.Label(self.frame, text=label_text)
        self.label.pack(side=tk.LEFT)
        
        vcmd = self.frame.register(self.validate)
        
        if Auto:
            self.Auto = Auto
            self.entry = tk.Entry(self.frame, width=12, validate="key", validatecommand=(vcmd, '%P'))
        else:
            self.entry = tk.Entry(self.frame, width=12)
        self.entry.insert(0, placeholder_text)
        self.entry.pack(side=tk.LEFT)
        self.entry.bind("<Return>", lambda event: submit_command())
        
        self.submit_button = tk.Button(self.frame, text="Submit", command=submit_command)
        self.submit_button.pack(side=tk.LEFT)

    def validate(self, new_text):
        if not new_text:
            self.input = None
            return True
        try:
            input = int(new_text)
            if self.Auto[0] <= input <= self.Auto[1]:
                self.input = input
                return True
            else:
                return False
        except ValueError:
            return False

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
                 frame: tk.Frame,
                 numChannels: int = 4,
                 numSamples: int = 2048,
                 sampleRate = 3.E9):
        
        #Inputs
        self.frame = frame
        self.numChannels = numChannels
        self.numSamples = numSamples
        self.sampleRate = sampleRate
        #Inititalising instance attributes
        self.adcBuffer = np.zeros( (numChannels, numSamples), np.int16 )
        self.dev = None
        self.plotFreq = False
        self.plotFit = False
        self.wf = Waveframes(self.frame)

        self.startWaveFrame()
        
    def startWaveFrame(self):
        for i in range(self.numChannels):
            self.wf.addWaveframe(Waveframe(self.wf, i, portNames[i].split()[0], self.sampleRate))
            logger.debug(f"Waveframe {i} has been made")
        self.wf.packFrames()
        self.wf.pack()
    
    ##Sets
    def setNumChannels(self, Channels = 4):
        self.numChannels = Channels
        ##This needs to be edited
        ##to gather what frames have been plotted and what frames need to be added or removed
        ##and update the display frame accordingly. Will probably involve repacking
        ##Or changing the figure size
        
        
        logger.debug(f"You will now record {self.numChannels} channels")
        return f"You will now record {self.numChannels} channels"
    def setNumSamples(self, NSum = 2**11):
        self.numSamples = NSum
        logger.debug(f"You will now take {self.numSamples} samples")
        return f"You will now take {self.numSamples} samples"
    def setSampleRate(self, rate = 3*10**9):
        self.sampleRate = rate
        for waveFrame in self.wf:
            waveFrame.sampleRate = rate
        logger.debug(f"Sample rate is now {self.sampleRate/10**9} GSPS")
        return f"Sample rate is now {self.sampleRate/10**9} GSPS"
    def setAdcBuffer(self):
        self.adcBuffer = np.zeros( (theDaq.numChannels, theDaq.numSamples), np.int16 )
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
    def setPlotFit(self, Value=True):
        if isinstance(Value, bool):
            self.plotFit = Value
            self.wf.plotExtras[1] = Value
            logger.debug(f"{'Plotting' if Value else 'Not plotting'} the fitted curve")
            return f"{'Plotting' if Value else 'Not plotting'} the fitted curve"
        else:
            logger.debug("Please input a valid option")
            return"Please input a valid option"
    
    ##Gets
    def getNumChannels(self):
        logger.debug(f"You are recording from {self.numChannels} channels")
        return self.numChannels
    def getNumSamples(self):
        logger.debug(f"You are taking {self.numSamples} channels")
        return self.numSamples
    def getSampleRate(self):
        logger.debug(f"You are recording {self.sampleRate/10**9} GSPS")
        return self.sampleRate
    def getFigSize(self):
        logger.debug(f"You displaying figures on a {self.figsize} grid")
        return self.figsize
    def getAdcBuffer(self):
        logger.debug(f"There is no way I'm printing the adcBuffer. That thing is huge")
        return self.adcBuffer
    def getPlotFreq(self):
        Value = self.plotFreq
        logger.debug(f"You are currently {'Plotting' if Value else 'Not plotting'} the frequency")
        return Value
    def getPlotFit(self):
        Value = self.plotFit
        logger.debug(f"You are currently {'Plotting' if Value else 'Not plotting'} the fitted waveform")
        return Value
    
    def writeCSV(self, fileName, columns, data):
        with open(fileName, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(data)
    
    def saveWaveData(self, Level, Frequency):
        path = f"/home/xilinx/rfsoc-pydaq/csvs/{Level}_{Frequency}.csv"
        columns = ["Frequency", "Amplitude", "Max"]
        data = []
        for i in range(self.numChannels):
            amplitude, frequency, phase = self.calcWave(i)
            if abs(Frequency-frequency/10**6)>10:
                print("Bad Frequency Measurement")
            data.append([frequency/10**6, amplitude, self.calcPeakToPeakAmp(i), self.calcRMS(i)])
        self.writeCSV(path, columns, data)
        
    def saveWaveform(self, Ch, Level, Frequency):
        
        path = f"/home/xilinx/rfsoc-pydaq/data/{portNames[Ch]}{Level}_{Frequency}.csv"
        
        data = list(zip(np.arange(len(self.waveForm))/self.sampleRate, self.adcBuffer[Ch]))
        
        with open(path, mode='a', newline='') as file: #mode='w'
            writer = csv.writer(file)
            writer.writerows(data)  
        logger.debug("Waveform data saved")
        return 'Saved Waveform'
    
    def printHotkeys(self):
        print("Hotkeys:\nf1-4 : Toggle Enlarge on Channel 0-3\n\nf5 : Invokes Acquire Method\n\nCtrl+s : Invoke Save buttons method\nCtrl+p : Saves plot of enlarged canvas\nCtrl+f : Toggle both the freq and fit off\n\nf9-12 : Switch all Notebook tabs to index 0-3\nPage Up and Page Down : Toggle up and down in notebook tabs\n")
        
    #Could have a method that returns a measure of how 'janky' the plot is. 
    ##I.e. channel 1's cable is poor quality and results in a janky plot (when viewed at significantly large sample size). If it's above a certian jankness then ditch
    ##Also low power signals are pretty janky. Could use the fit function but that isn't great for non-sinusoidal waveforms (It's not great for sinusoidal waves either now that I think of it)
    
    #Standard deviation of peaks. 
    ##Highly effected by the sample rate and kinda factors into the jankyness
    
    #You need better analysis tools


def defaultUserCommand():
    logger.debug("Default Command Called")
    return

def rfsocLoad(hardware = ""):
    """Load an overlay file describing an RFSoC instance.
    The overlay needs to support being created bare (just "overlayName()")
    and must support the "internal_capture( buffer, numChannels )"
    function.
    """    
    
    output = subprocess.check_output(['lsmod'])
    if b'zocl' in output:
        rmmod_output = subprocess.run(['rmmod', 'zocl'])
        assert rmmod_output.returncode == 0, "Could not restart zocl. Please Shutdown All Kernels and then restart"
        modprobe_output = subprocess.run(['modprobe', 'zocl'])
        assert modprobe_output.returncode == 0, "Could not restart zocl. It did not restart as expected"
    else:
        modprobe_output = subprocess.run(['modprobe', 'zocl'])
        assert modprobe_output.returncode == 0, "Could not restart ZOCL!"
    
    
    ##Edited such that one can automatically load zcumts from within the main loop
    if hardware == "zcumts":
        ##Ammend this location to your leisure
        file_path = '/home/xilinx/python/zcumts.py'
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
        theDaq.dev = theClass()
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
    return

def Acquire(Channel = 0):
    if theDaq.dev is None:
        logger.error("No RFSoC device is loaded!")
        
    theDaq.dev.internal_capture(theDaq.adcBuffer,
                                theDaq.numChannels)
    
    theDaq.wf.waveframes[Channel].setWaveform(theDaq.adcBuffer[Channel])
    
    logger.debug("Acquired data")

##This is used for saving data
def rfsocAcquire():
    if theDaq.dev is None:
        logger.error("No RFSoC device is loaded!")
        
    theDaq.dev.internal_capture(theDaq.adcBuffer,
                                theDaq.numChannels)
    
    for i in range(theDaq.numChannels):
        theDaq.wf.waveframes[i].setWaveform(theDaq.adcBuffer[i])
        if theDaq.wf.waveframes[i].toPlot == True:
            theDaq.wf.waveframes[i].notebook.plot()
            
    logger.debug("Acquired data and Plotted")
    
def ContAcquire():
    return 'Not complete'

##Buttons
##Simply retrieves the value from an input 'entry' box connected to a submit button
def getSubmitInput(value, needNumber):
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

##Action for submit butttons
def submitNumSamples(value = 11):
    NSamp = getSubmitInput(value, True)
    logger.debug(f"Currently have {theDaq.numSamples} samples, you have inputted {2**NSamp} samples")
    
    if isinstance(NSamp, int) and 0<NSamp<=14:
        theDaq.setNumSamples(2**NSamp)
        theDaq.setAdcBuffer()
        return f"You will now take {theDaq.numSamples} samples"
    else:
        logger.debug("Please input an appropriate Sample Size. The maximum is 14")
        return 'Please input an appropriate Sample Size'
    
def submitSampleRate(value = 3*10**9):
    rate = getSubmitInput(value, True)
    logger.debug(f"Currently have {theDaq.sampleRate} samples, you have inputted {rate} samples")
    
    if rate>=10**5:
        theDaq.setSampleRate(rate)
        return f"You will now take {theDaq.sampleRate} GSPS"
    else:
        logger.debug("Please input an appropriate Sample Rate")
        return 'Please input an appropriate Sample Rate'
    
def submitNumberOfChannels(value = 4):
    Channels = getSubmitInput(value, True)
    ##Something probably needs to happen here but this whole method is somewhat pointless
    logger.debug(f"Currently have {theDaq.numChannels} samples, you have inputted {Channels} samples")
    
    if isinstance(Channels, int) and 0<Channels<=8:
        theDaq.setNumChannels(Channels)
        return f"You will now have {theDaq.numChannels} Channels"
    else:
        logger.debug("Please input an appropriate number of channels")
        return 'Please input an appropriate number of channels'
    
def submitSaveName(value):
    SaveName = getSubmitInput(value, False)
    logger.debug(f"You are setting the Save Files name to : {SaveName}")
    if SaveName and isinstance(SaveName, str) == False:
        SaveName=str(SaveName)
    theDaq.wf.saveText = SaveName
    
##Toggle action
def toggle(tg, setFunc):
    if tg.config('relief')[-1] == 'sunken':
        tg.config(relief="raised")
        setFunc(True)
    else:
        tg.config(relief="sunken")
        setFunc(False)
    return 'Updated plotting'

##This is to easily have both plot options turned off
def toggleOff():
    if toggles["Freq"].config('relief')[-1] == 'raised':
        toggles["Freq"].config(relief="sunken")
        theDaq.setPlotFreq(False)
    if toggles["Fit"].config('relief')[-1] == 'raised':
        toggles["Fit"].config(relief="sunken")
        theDaq.setPlotFit(False)

def contAcquire():
    toggle()
    
    
def getEnlargedNotebook():
    index = 0
    for waveframe in theDaq.wf.waveframes:
        if waveframe.enlarged == True:
            index = waveframe.index
    return index

def Save():
    index = getEnlargedNotebook()
    rfsocAcquire()
    for i in range(1000):
        print(i)
        theDaq.wf.waveframes[index].saveWF()
        Acquire(index)
    theDaq.wf.waveframes[index].setSaveWFName()
        

def switchToTab(index):
    for waveframe in theDaq.wf.waveframes:
        waveframe.notebook.switchToTab(index)

def switchTab():
    for waveframe in theDaq.wf.waveframes:
        waveframe.notebook.switchTab()

def switchTabBack():
    for waveframe in theDaq.wf.waveframes:
        waveframe.notebook.switchTabBack()

##Miscellaneous
def getAppropriateFigSize():
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return (screen_width/(100*theDaq.numChannels),screen_height/250)

##This currently doesn't do what I want
##This doesn't account for zocl not restarting
def reload_script():
    print("Trying to restart")
    python = sys.executable
    script = os.path.abspath(sys.argv[0])
    
    os.execl(python, python, script)
        
##This just a method for a slider that can be ignored
def degis(value):
    global buton
    if(value == "1"):
        buton["label"] = "  On"
    else:
        buton["label"] = "  Off"
    
if __name__ == '__main__':
    root = tk.Tk()
    
    screen_width = root.winfo_screenwidth() * sizeEditor[0]
    screen_height = root.winfo_screenheight() * sizeEditor[1]
    figsize=(screen_width/(100*numChannels), screen_height/250)
    ##My Display appears to be not using the full 1920 width
    # figsize = (4.77, 4.32)
    
    logging.basicConfig(level=logging.DEBUG)
    displayFrame = tk.Frame(master = root,
                            relief = tk.RAISED,
                            borderwidth = 1)
    buttonFrame = tk.Frame(master = root,
                           relief = tk.RAISED,
                           borderwidth = 1)
    toggleFrame = tk.Frame(master = root,
                           relief = tk.RAISED,
                           borderwidth = 1)
    submitFrame = tk.Frame(master = root,
                           relief = tk.RAISED,
                           borderwidth = 1)
    consoleFrame = tk.Frame(master = root,
                            relief = tk.RAISED,
                            borderwidth = 1)
    logFrame = tk.Frame(master = root,
                        relief = tk.RAISED,
                        borderwidth = 1)

    daq = RFSoC_Daq( displayFrame,
                     numChannels,
                     numSamples,
                     sampleRate)
    theDaq = daq   
    
    displayFrame.pack( side = tk.TOP )

    buttons = {}
    buttons['Load'] = tk.Button(buttonFrame,
                                text = "Load",
                                command = rfsocLoad)
    buttons['Acquire'] = tk.Button(buttonFrame,
                                   text = "Acquire",
                                   command = rfsocAcquire)
    buttons['ContAcquire'] = tk.Button(buttonFrame,
                                   text = "ContAcquire",
                                   command = defaultUserCommand)
    buttons['User'] = tk.Button(buttonFrame,
                                text = "User",
                                command = defaultUserCommand)
    ##This button throws an error but doesn't stop the program. May as well be ignored till it works
    buttons['Restart'] = tk.Button(buttonFrame,
                                text = "Restart",
                                command = defaultUserCommand)#reload_script)
    buttons['Save'] = tk.Button(buttonFrame,
                                text = "Save",
                                command = Save)
    
    
    buttons['Load'].pack( side = tk.LEFT )
    buttons['Acquire'].pack( side = tk.LEFT )
    buttons['User'].pack( side = tk.LEFT )
    buttons['Restart'].pack( side = tk.LEFT )
    buttons['Save'].pack( side = tk.LEFT )

    #A slider that works (as a piece of GUI) but don't have a use for currently
    # buton = tk.Scale(orient = tk.HORIZONTAL,length = 50,to = 1,showvalue = False,sliderlength = 25,label = "  Off",command = degis)
    # buton.pack()
    
    buttonFrame.pack( side = tk.TOP )

    toggles = {}
    toggles["Freq"] = tk.Button(toggleFrame,
                                    text="Freq", 
                                    width=8, 
                                    relief="sunken",
                                    command=lambda: toggle(toggles["Freq"], theDaq.setPlotFreq))
    toggles["Fit"] = tk.Button(toggleFrame,
                                    text="Fit", 
                                    width=8, 
                                    relief="sunken",
                                    command=lambda: toggle(toggles["Fit"], theDaq.setPlotFit))
    
    toggles["Freq"].pack( side = tk.LEFT )
    toggles['Fit'].pack( side = tk.LEFT )
    
    toggleFrame.pack( side = tk.TOP )
    
    ##Most of these don't do anything important. But it's nice that the submit button infrasturctture is there
    buttons['SetSampleSize'] = submitButton(submitFrame, "Set Sample Number (exponent of 2):", sampleExponent, lambda: submitNumSamples(buttons['SetSampleSize']), (1,14))
    # buttons['SetSampleRate'] = submitButton(root, submitFrame, "Set Sample Rate (Redundant):", sampleRate, lambda: submitSampleRate(buttons['SetSampleRate']))
    # buttons['SetChannelCount'] = submitButton(root, submitFrame, "Set Number of Channels:", numChannels, lambda: submitNumberOfChannels(buttons['SetChannelCount']))
    buttons['SetSaveText'] = submitButton(submitFrame, "Set the FileName:", "Temp", lambda: submitSaveName(buttons['SetSaveText']))   
    
    submitFrame.pack( side = tk.TOP )
        
    root.bind("<Control-s>", lambda event: buttons['Save'].invoke())
    root.bind("<Control-p>", lambda event: displayFrame.winfo_children()[getEnlargedNotebook()].btns['SavePlt'].invoke())
    
    root.bind("<Control-f>", lambda event: toggleOff())
        
    root.bind("<F1>", lambda event: theDaq.wf.waveframes[0].btns['Enlarge'].invoke())
    root.bind("<F2>", lambda event: theDaq.wf.waveframes[1].btns['Enlarge'].invoke())
    root.bind("<F3>", lambda event: theDaq.wf.waveframes[2].btns['Enlarge'].invoke())
    root.bind("<F4>", lambda event: theDaq.wf.waveframes[3].btns['Enlarge'].invoke())
    
    root.bind("<F5>", lambda event: buttons['Acquire'].invoke())
    
    root.bind("<F7>", lambda event: buttons['Restart'].invoke())
    
    root.bind("<F9>", lambda event: switchToTab(0))
    root.bind("<F10>", lambda event: switchToTab(1))
    root.bind("<F11>", lambda event: switchToTab(2))
    root.bind("<F12>", lambda event: switchToTab(3))
    
    root.bind("<Next>", lambda event: switchTab())
    root.bind("<Prior>", lambda event: switchTabBack())
    

    locals = { 'daq' : theDaq,
               'buttons' : buttons }
    console = TextConsole( consoleFrame,
                           locals=locals )
    console.pack(fill='both', expand=True)
    consoleFrame.pack( fill='both', expand=True, side = tk.TOP )

    log = ScrolledLog( logFrame, logger )
    log.pack(fill='x', expand=True)
    logFrame.pack( fill='x', side = tk.TOP )
    
    rfsocLoad(hardware = "zcumts")
    
    logger.debug("Hotkeys:\nf1-4 : Toggle Enlarge on Channel 0-3\n\nf5 : Invokes Acquire Method\n\nCtrl+s : Invoke Save buttons method\nCtrl+p : Saves plot of enlarged canvas\nCtrl+f : Toggle both the freq and fit off\n\nf9-12 : Switch all Notebook tabs to index 0-3\nPage Up and Page Down : Toggle up and down in notebook tabs\n")
        
    root.mainloop()
