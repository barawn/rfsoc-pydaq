import numpy as np
import tkinter as tk
from tkinter import filedialog

import logging
import os, sys, inspect, importlib

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

theDaq = None

# THIS IS THE GLOBAL CLASS
# It gets passed to the internal Python console,
# so it has stuff stored in it.
# It internally holds the top displays.
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
            thisWf = Waveframe(self.frame, sampleRate)
            self.wf.append(thisWf)
            thisWf.pack(side = tk.LEFT )

def defaultUserCommand():
    return


def rfsocLoad():
    """Load an overlay file describing an RFSoC instance.
    The overlay needs to support being created bare (just "overlayName()")
    and must support the "internal_capture( buffer, numChannels )"
    function.
    """    
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

def rfsocAcquire():
    if theDaq.dev is None:
        logger.error("No RFSoC device is loaded!")
    theDaq.dev.internal_capture(theDaq.adcBuffer,
                                theDaq.numChannels)
    for i in range(theDaq.numChannels):
        theDaq.wf[i].plot(theDaq.adcBuffer[i])

if __name__ == '__main__':
    root = tk.Tk()
    logging.basicConfig(level=logging.DEBUG)
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
    theDaq = daq
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

    buttonFrame.pack( side = tk.TOP )

    locals = { 'daq' : daq,
               'buttons' : buttons }
    banner =  "rfsoc-pydaq Python %s\n" % sys.version
    banner += "Locals:"
    for local in locals:
        banner += " %s (%s)" % ( local, type(locals[local]).__name__)
    banner += "\n"

    console = TextConsole( consoleFrame,
                           banner=banner,
                           locals=locals )
    console.pack(fill='both', expand=True)
    consoleFrame.pack( fill='both', expand=True, side = tk.TOP )


    log = ScrolledLog( logFrame, logger )
    log.pack(fill='x', expand=True)
    logFrame.pack( fill='x', side = tk.TOP )

    root.mainloop()
