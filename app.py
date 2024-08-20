# App basically runs the whole GUI

##Python Imports
import numpy as np
import tkinter as tk

#System Imports
import logging
import os, sys, configparser

from textconsole.TextConsole import TextConsole
from scrolledlog.ScrolledLog import ScrolledLog

from RFSoC_Daq import RFSoC_Daq

from AGC.AGC_Daq import AGC_Daq
from AGC.AGC_Test import AGC_Test
from Biquad.Biquad_Daq import Biquad_Daq
from Biquad.Biquad_Test import Biquad_Test
from Pulse.Pulse_Daq import Pulse_Daq
from Sine.Sine_Daq import Sine_Daq
from widgets.SubmitButton import submitButton

from waveframe.Waveframes import Waveframes

default_numChannels = 4
default_numSamples = 2**5
default_sampleRate = 3.E9

logger = logging.getLogger(__name__)

daq = None

def app(name):
    root = tk.Tk()
    logging.basicConfig(level=logging.DEBUG)

    pydaq_cfg = getConfig(name)
    DaqClass = getDaq(name)

    #############
    ##Display
    #############
    displayFrame = tk.Frame(master = root,
                            relief = tk.RAISED,
                            borderwidth = 1,
                            name = "display")
    daq = DaqClass( root,
                    displayFrame,
                    pydaq_cfg.getint('numChannels',
                                      fallback=default_numChannels),
                    pydaq_cfg.getint('numSamples',
                                      fallback=default_numSamples),
                    pydaq_cfg.get('channels', '').split(','))

    daq.startWaveFrame()

    displayFrame.grid( row = 0, column=0, sticky="NSEW" )


    #############
    ##Buttons
    #############
    buttonFrame = tk.Frame(master = root,
                        relief = tk.RAISED,
                        borderwidth = 1,
                        name = "button")
    
    buttons = {}
    buttons['Load'] = tk.Button(buttonFrame,
                                text = "Load",
                                command = daq.rfsocLoad)
    buttons['Acquire'] = tk.Button(buttonFrame,
                                   text = "Acquire",
                                   command = daq.GuiAcquire)
    ##This button throws an error but doesn't stop the program. May as well be ignored till it works
    # buttons['Restart'] = tk.Button(buttonFrame,
    #                             text = "Restart",
    #                             command = defaultUserCommand)#reload_script)
    buttons['Save'] = tk.Button(buttonFrame,
                                text = "Save",
                                command = daq.Save)
    
    buttons['Load'].grid( row = 0, column=0, padx=5 )
    buttons['Acquire'].grid( row = 0, column=1, padx=5 )
    # buttons['Restart'].pack( side = tk.LEFT )
    buttons['Save'].grid( row = 0, column=2, padx=5 )
    
    buttonFrame.grid( row = 1, column=0, pady=5 )

    #############
    ##Toggles
    #############
    toggleFrame = tk.Frame(master = root,
                           relief = tk.RAISED,
                           borderwidth = 1,
                           name = "toggle")
    
    toggles = {}
    toggles["Freq"] = tk.Button(toggleFrame,
                                    text="Freq", 
                                    width=8, 
                                    relief="sunken",
                                    command=lambda: toggle(toggles["Freq"], daq.setPlotFreq))
    
    toggles["Freq"].grid(row=0, column=0)
    
    toggleFrame.grid(row=2, column=0, pady=5)

    #############
    ##Submits
    #############
    submitFrame = tk.Frame(master = root,
                           relief = tk.RAISED,
                           borderwidth = 1,
                           name = "submit")
    
    submits = {}
    exponent =  np.log2(pydaq_cfg.getint('numSamples'))
    submits['SetSampleSize'] = submitButton(submitFrame, "Set Sample Number (exponent of 2):", int(exponent), lambda: daq.submitNumSamples(submits['SetSampleSize']), 0,(1,14))
    submits['SetSaveText'] = submitButton(submitFrame, "Set the FileName:", "Temp", lambda: daq.submitSaveName(submits['SetSaveText']), 1)
    # submits['SetOffset'] = submitButton(submitFrame, "Set the offset:", "", lambda: submitScalingValue(submits['SetScaling']))
    # submits['SetScaling'] = submitButton(submitFrame, "Set the scaling:", "", lambda: submitScalingValue(submits['SetScaling']))
    submitFrame.grid(row = 3, column=0)

    #############
    ##Console
    #############
    locals = { 'daq' : daq}
    console = TextConsole( root,
                           locals=locals, 
                           height = 15 )
    console.grid(row = 4, column=0, sticky="NSEW")

    #############
    ##Log
    #############
    log = ScrolledLog( root, logger, height = 10 )
    log.grid(row = 5, column=0, sticky="NSEW")
    
    # idk = root.nametowidget("display")

    try:
        daq.setHotKeys()
        daq.setDisplay()
    except:
        pass

    root.mainloop()

############################
##Required for running
############################
def getConfig(name = "rfsoc"):
    config = configparser.ConfigParser()
    config.read('/home/xilinx/rfsoc-pydaq/rfsoc-pydaq.ini')
    # config.read('/Users/hpumphrey/Com/rfsoc-pydaq/rfsoc-pydaq.ini') #This was used for testing on my local machine

    if name not in config:
        print("Bad config file")
        config[name] = {}

    return config[name]

def getDaq(name = "rfsoc"):
    if name == "rfsoc":
        return RFSoC_Daq
    if name == "agc":
        return AGC_Daq
    if name == "agc_test":
        return AGC_Test
    if name == "biquad":
        return Biquad_Daq
    if name == "biquad_test":
        return Biquad_Test
    if name == "pulse":
        return Pulse_Daq
    if name == "sine":
        return Sine_Daq
    else:
        return RFSoC_Daq
    
############################
##For submit buttons to work
############################
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

############################
##Toggles
############################

## Toggle method
def toggle(tg, setFunc):
    if tg.config('relief')[-1] == 'sunken':
        tg.config(relief="raised")
        setFunc(True)
    else:
        tg.config(relief="sunken")
        setFunc(False)
    return 'Updated plotting'

##This is to easily have both plot options turned off with a hotkey
# def toggleOff():
#     if toggles["Freq"].config('relief')[-1] == 'raised':
#         toggles["Freq"].config(relief="sunken")
#         theDaq.setPlotFreq(False)
#     if toggles["Fit"].config('relief')[-1] == 'raised':
#         toggles["Fit"].config(relief="sunken")
#         theDaq.setPlotFit(False)

############################
##Miscellaneous
############################

def getEnlargedNotebook():
    index = 0
    for waveframe in daq.wf.waveframes:
        if waveframe.enlarged == True:
            index = waveframe.index
    return index

def reload_script():
    print("Trying to restart")
    python = sys.executable
    script = os.path.abspath(sys.argv[0])
    
    os.execl(python, python, script)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-c", dest="config",
                        help="The Config you want to set up", default="rfsoc")

    args = parser.parse_args()

    app(args.config)