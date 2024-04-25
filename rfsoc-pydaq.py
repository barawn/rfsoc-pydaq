##Python Imports
import numpy as np
import tkinter as tk
from tkinter import filedialog
from scipy.fft import fft, ifft, fftfreq
from scipy.constants import speed_of_light

#System Imports
import logging
import os, sys, inspect, importlib, csv

#Module Imports
from textconsole.TextConsole import TextConsole
from scrolledlog.ScrolledLog import ScrolledLog
from waveframe.Waveframe import Waveframe

logger = logging.getLogger(__name__)

#Establishing base values for parameters
numChannels = 4     ##Probably shouldn't change
sampleExponent = 5#11
numSamples = 2**sampleExponent#2**12#2**11
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
                 master,
                 frame,
                 label_text,
                 placeholder_text,
                 submit_command):
        
        self.frame=frame
        
        self.label =tk.Label(self.frame, text=label_text)
        self.label.pack(side=tk.LEFT)
        
        self.entry = tk.Entry(self.frame, width=12)
        self.entry.insert(0, placeholder_text)
        self.entry.pack(side=tk.LEFT)
        self.entry.bind("<Return>", lambda event: submit_command())
        
        self.submit_button = tk.Button(self.frame, text="Submit", command=submit_command)
        self.submit_button.pack(side=tk.LEFT)

#FPGA Class
class RFSoC_Daq:
    """
    Class for data aquitisition on the RFSoC.
    
    Key methods to be accessed from the terminal (the rest should be run elsewhere)
    
    printWave(Channel Number), prints the amplitude, frequency and phase
    calcPeakToPeakAmp(Channel Number), returns the difference from min to max
    calcRMS(Channel Number), returns the RMS of the waveform
    
    saveWaveData(Level, Frequency), Saves data about wave, Level and Frequency should represent what one inputted into the wave
    One Can save the enitre waveframe data from within the TKInter GUI
    """
    def __init__(self,
                 frame,
                 numChannels = 4,
                 numSamples = 2048,
                 sampleRate = 3.E9,
                 figsize = (3,2)):
        
        #Inputs
        self.frame = frame
        self.numChannels = numChannels
        self.numSamples = numSamples
        self.sampleRate = sampleRate
        self.figsize = figsize
        #Inititalising instance attributes
        self.adcBuffer = np.zeros( (numChannels, numSamples), np.int16 )
        self.dev = None
        self.plotFreq = True
        self.plotFit = True
        self.wf = []

        self.startWaveFrame()
        
    def startWaveFrame(self):
        for i in range(self.numChannels):
            thisWf = Waveframe(self.frame, i, portNames[i].split()[0], self.sampleRate, self.figsize)
            self.wf.append(thisWf)
            thisWf.pack(side = tk.LEFT )
            logger.debug(f"Waveframe {i} has been made")
    
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
    def setFigSize(self, sizing = [3,2]):
        if isinstance(sizing, list):
            self.figsize = sizing
            logger.debug(f"The figure size is now {self.figsize}")
            return f"The figure size is now {self.figsize}"
        else:
            logger.debug("Not an appropriate input, please input an list")
            return 'Not an appropriate input, please input an list'
    def setAdcBuffer(self):
        self.adcBuffer = np.zeros( (theDaq.numChannels, theDaq.numSamples), np.int16 )
        logger.debug("The adcBuffer has been updated")
        return 'adcBuffer Updated'
    def setPlotFreq(self, Value=True):
        if isinstance(Value, bool):
            self.plotFreq = Value
            logger.debug(f"{'Plotting' if Value else 'Not plotting'} the frequency")
            return f"{'Plotting' if Value else 'Not plotting'} the frequency"
        else:
            logger.debug("Please input a valid option")
            return"Please input a valid option"
    def setPlotFit(self, Value=True):
        if isinstance(Value, bool):
            self.plotFit = Value
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
    
    ##Processes
    def convertToMag(self, yf):
        N = len(yf)
        return 2.0/N * np.abs(yf[0:N//2])
    
    def calcWave(self, Ch=0):
        if isinstance(Ch, int) and 0 <= Ch < self.numChannels:
            signal = self.adcBuffer[Ch]
            N = len(signal)
            dt = 1 / self.sampleRate
            df = 1 / (N * dt)
            fft_result = fft(signal)
            xf = np.linspace(0.0, 1.0 / (2 * dt), N // 2)
            mag_spectrum = np.abs(fft_result[:N//2])
            phase_spectrum = np.angle(fft_result[:N//2])
            peak_freq_index = np.argmax(mag_spectrum)
            frequency = xf[peak_freq_index]
            amplitude = self.calcPeakToPeakAmp(Ch) # mag_spectrum[peak_freq_index] * 2 / N
            phase = phase_spectrum[peak_freq_index]
            # logging.debug(f"Amplitude: {amplitude:.3f} ADC counts || Frequency: {(frequency/10**6):.3f} MHz || Phase: {phase:.3f} rad || Channel: {Ch}")
            return amplitude, frequency, phase
        else:
            raise ValueError('Not an available channel')
        
    def calcPeakToPeakAmp(self, Ch = 0):
        return abs(max(self.adcBuffer[Ch]) - min(self.adcBuffer[Ch]))/2
    
    def calcRMS(data):
        squared_sum = sum((1000*x) ** 2 for x in data)
        return math.sqrt(squared_sum / len(data))
        
    def calcWL(self, Ch=0):
        if isinstance(Ch, int) and 0<=Ch<self.numChannels:
            wavelength = speed_of_light/self.calcWave(Ch)[1]
            logging.debug(f"Wavelength : {wavelength} of Channel : {Ch}")
            return wavelength
        else:
            return 'Not an available channel'
        
    ##Prints. For use in the terminal. Don't serve an immense amount of use within the program
    def printWave(self, Ch=-1):
        if isinstance(Ch, int) and 0<=Ch<self.numChannels:
            amplitude, frequency, phase = self.calcWave(Ch)
            print(f"Amplitude : {amplitude} ADC counts || Frequency : {frequency/10**6} MHz || Channel : {Ch}")
        elif Ch==-1:
            for i in range(self.numChannels):
                amplitude, frequency, phase = self.calcWave(Ch)
                print(f"Channel {i} : Amplitude : {amplitude} ADC counts || Frequency : {frequency/10**6} MHz")
        else:
            return 'Not an available channel'
        
    def printWavelength(self, Ch=-1):
        if isinstance(Ch, int) and 0<=Ch<self.numChannels:
            wavelength = self.calcWL(Ch)
            print(f"Wavelength : {wavelength} metres || Channel : {Ch}")
        elif Ch==-1:
            for i in range(self.numChannels):
                wavelength = self.calcWL(Ch)
                print(f"Channel {i} : Wavelength : {wavelength} metres")
        else:
            return 'Not an available channel'
        
    #Other methods could be fun to have
    
    #Saving data from terminal
    ##Methods to save data from the terminal instead of the GUI
    
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
            
        
    
    ##Save the Calculated Data
    ##Amplitude, frequency maybe others || should also have sample rate details || User should Input parameters used in process (actual frequency and power level)
    ##Could compare how different things actually work compared to how they should
    
    #Number of Wave Lengths
    ##Could obviously do this by calculating the WL but could have a different method. Frequency recording is somewhat inaccurate
    
    #Could have a method that returns a measure of how janky the plot is. 
    ##I.e. channel 1's cable is poor quality and results in a janky plot (when viewed at significantly large sample size). If it's above a certian jankness then ditch
    ##Also low power signals are pretty janky. Could use the fit function but that isn't great for non-sinusoidal waveforms
    
    #Standard deviation of peaks. 
    ##Highly effected by the sample rate and kinda factors into the jankyness
    
    #You need better analysis tools


def defaultUserCommand():
    return

def rfsocLoad(hardware = ""):
    """Load an overlay file describing an RFSoC instance.
    The overlay needs to support being created bare (just "overlayName()")
    and must support the "internal_capture( buffer, numChannels )"
    function.
    """    
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
    
    theDaq.wf[Channel].setWaveform(theDaq.adcBuffer[Channel])
    
    logger.debug("Acquired data")

def rfsocAcquire():
    if theDaq.dev is None:
        logger.error("No RFSoC device is loaded!")
        
    theDaq.dev.internal_capture(theDaq.adcBuffer,
                                theDaq.numChannels)
    
    for i in range(theDaq.numChannels):
        theDaq.wf[i].setWaveform(theDaq.adcBuffer[i])
        if theDaq.wf[i].toPlot == True:
            theDaq.wf[i].plot(theDaq.calcWave(i), [theDaq.plotFreq, theDaq.plotFit])
            
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
    for i in range(theDaq.numChannels):
        theDaq.wf[i].saveText = SaveName
    
##Toggle action
def toggle(tg, setFunc):
    if tg.config('relief')[-1] == 'sunken':
        tg.config(relief="raised")
        setFunc(True)
    else:
        tg.config(relief="sunken")
        setFunc(False)
    return 'Updated plotting'

def contAcquire():
    toggle()
    
    
def Save():
    index = 0
    for widget in displayFrame.winfo_children():
        if widget.enlarged == True:
            index = widget.index
    rfsocAcquire()
    for i in range(1000):
        print(i)
        displayFrame.winfo_children()[index].saveWF()
        Acquire(index)

##Miscellaneous
def getAppropriateFigSize():
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return (screen_width/(100*theDaq.numChannels),screen_height/250)

##This currently doesn't do what I want
##Since one has to restart the entire script if any ammendments to methods or variables are made in the code I thought it would be nice to have some kind of reset feature that restarts the program with the ammendments. It doesn't work however.
def reload_script():
    main_script = sys.argv[0]
    
    main_script = main_script.replace('.py', '')
    
    if main_script in sys.modules:
        importlib.reload(sys.modules[main_script])
    else:
        logger.debug(f"Module '{main_script}' not found in sys.modules")
        
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
                     sampleRate,
                     figsize)
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
    buttons['Reset'] = tk.Button(buttonFrame,
                                text = "Reset",
                                command = reload_script)
    buttons['Save'] = tk.Button(buttonFrame,
                                text = "Save",
                                command = Save)
    
    
    buttons['Load'].pack( side = tk.LEFT )
    buttons['Acquire'].pack( side = tk.LEFT )
    buttons['User'].pack( side = tk.LEFT )
    buttons['Reset'].pack( side = tk.LEFT )
    buttons['Save'].pack( side = tk.LEFT )

    #A slider that works (as a piece of GUI) but don't have a use for currently
    # buton = tk.Scale(orient = tk.HORIZONTAL,length = 50,to = 1,showvalue = False,sliderlength = 25,label = "  Off",command = degis)
    # buton.pack()
    
    buttonFrame.pack( side = tk.TOP )
    
    toggles = {}
    toggles["Freq"] = tk.Button(toggleFrame,
                                    text="Freq", 
                                    width=8, 
                                    relief="raised",
                                    command=lambda: toggle(toggles["Freq"], theDaq.setPlotFreq))
    toggles["Fit"] = tk.Button(toggleFrame,
                                    text="Fit", 
                                    width=8, 
                                    relief="raised",
                                    command=lambda: toggle(toggles["Fit"], theDaq.setPlotFit))
    
    toggles["Freq"].pack( side = tk.LEFT )
    toggles['Fit'].pack( side = tk.LEFT )
    
    toggleFrame.pack( side = tk.TOP )
    
    ##Most of these don't do anything important. But it's nice that the submit button infrasturctture is there
    buttons['SetSampleSize'] = submitButton(root, submitFrame, "Set Sample Number (exponent of 2):", sampleExponent, lambda: submitNumSamples(buttons['SetSampleSize']))
    # buttons['SetSampleRate'] = submitButton(root, submitFrame, "Set Sample Rate (Redundant):", sampleRate, lambda: submitSampleRate(buttons['SetSampleRate']))
    # buttons['SetChannelCount'] = submitButton(root, submitFrame, "Set Number of Channels:", numChannels, lambda: submitNumberOfChannels(buttons['SetChannelCount']))
    buttons['SetSaveText'] = submitButton(root, submitFrame, "Set the FileName:", "None", lambda: submitSaveName(buttons['SetSaveText']))   
    
    submitFrame.pack( side = tk.TOP )

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
        
    root.mainloop()
