import numpy as np
import tkinter as tk

import logging

from textconsole.TextConsole import TextConsole
from scrolledlog.ScrolledLog import ScrolledLog
from waveframe.Waveframe import Waveframe

logger = logging.getLogger(__name__)

# GLOBAL CONFIGS
# THESE ARE STORED IN THE RFSoC_Daq CLASS
# BUT ARE HERE SO THEY CAN BE CHANGED EASY
numChannels = 4
numSamples = 2048
sampleRate = 3.E9


# THIS IS THE GLOBAL CLASS
# It gets passed to the internal Python console,
# so it has stuff stored in it.
# It internally holds the top displays.
class RFSoC_Daq:
    def __init__(self,
                 frame,
                 numChannels = 4,
                 numSamples = 2048,
                 sampleRate = 3.E9
                 ):
        self.numChannels = numChannels
        self.numSamples = numSamples
        self.frame = frame
        self.adcBuffer = np.zeros( (numChannels, numSamples), np.int16 )
        self.dev = None
        self.wf = []
        for i in range(numChannels):
            self.wf.append(Waveframe(self.frame, sampleRate))
            self.wf.pack()

def defaultUserCommand():
    return

def rfsocLoad():
    return

def rfsocAcquire():
    return

if __name__ == 'main':
    root = tk.Tk()
    # We have 4 overall frames, just arranged
    # in a single column, so we can just use
    # the straight pack geometry manager.
    displayFrame = tk.Frame(master = root,
                            relief = tk.RAISED,
                            borderwidth = 1)
    buttonFrame = tk.Frame(master = root,
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
                     sampleRate )
    displayFrame.pack( side = tk.TOP )

    buttons = {}
    buttons['Load'] = tk.Button(buttonFrame,
                                text = "Load",
                                command = rfsocLoad)
    buttons['Acquire'] = tk.Button(buttonFrame,
                                   text = "Aqcuire",
                                   command = rfsocAcquire)
    buttons['User'] = tk.Button(buttonFrame,
                                text = "User",
                                command = defaultUserCommand)
    buttons['Load'].pack( side = tk.LEFT )
    buttons['Acquire'].pack( side = tk.LEFT )
    buttons['User'].pack( side = tk.LEFT )

    locals = { 'daq' : daq,
               'buttons' : buttons }
    console = TextConsole( consoleFrame,
                           locals=locals )
    console.pack(fill='bot', expand=True)

    log = ScrolledLog( logFrame, logger )
    log.pack()

    root.mainLoop()
