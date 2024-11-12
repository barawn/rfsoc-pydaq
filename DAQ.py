##Python Imports
import numpy as np
from tkinter import filedialog


#System Imports
import logging
import os, sys, inspect, importlib

#Module Imports
from waveframe.Waveframe import Waveframe
from waveframe.Waveframes import Waveframes

from Waveforms.Waveform import Waveform

# logger = logging.getLogger(__name__)

#FPGA Class
class RFSoC_Daq:
    def __init__(self,
                 sample_size: int = 2**11,
                 channel_names = ["ADC224_T0_CH0 (LF)", "ADC224_T0_CH1 (LF)", "ADC225_T1_CH0 (HF)", "ADC225_T1_CH1 (HF)"]):
        
        self._sample_size = sample_size
        self.max_sample_size = 2**14
        self._channel_names = channel_names

        self._adcBuffer = np.zeros((self.channel_num, self._sample_size), np.int16)
        self.waveforms = []

        self.dev = None

        self.logger = logging.getLogger(__name__)

    ###########################################
    ##### Field setters
    ###########################################

    @property
    def sample_size(self):
        return self._sample_size

    @sample_size.setter
    def sample_size(self, value : int):
        if value % 8 != 0:
            raise ValueError("Sample size must be an integer multiple of clocks (8)")
        if value > 2**14:
            raise ValueError("Sample size must be within address range 2^14")
        if value > self.max_sample_size:
            raise ValueError(f"Sample size must be configured memory range {self.max_sample_size}")
        if value < 0:
            raise ValueError("Sample size must be physically possible")
        self._sample_size = value
        self._reset_adcBuffer()

    @property
    def channel_names(self):
        return self._channel_names

    @channel_names.setter
    def channel_names(self, arr : list[str]):
        if not isinstance(arr, list):
            raise ValueError("Channel Names must be supplied as a list")
        if len(arr) != 4:
            raise ValueError("Channel Names must be reflect the 4 ADC Channels")
        self._channel_names = arr
        self._reset_adcBuffer()

    @property
    def channel_num(self):
        return len(self._channel_names)
    
    @property
    def adcBuffer(self):
        return self._adcBuffer
    
    @adcBuffer.setter
    def adcBuffer(self, value):
        self._adcBuffer = value
    
    def _reset_adcBuffer(self):
        self._adcBuffer = np.zeros((self.channel_num, self._sample_size), np.int16)
    
    def extract_channel(self, ch: int):
        """Method to retrieve a specific channel by index."""
        if ch < 0 or ch >= self.channel_num:
            raise IndexError(f"Channel index {ch} out of range")
        return self.adcBuffer[ch] >> 4
    
    ###########################################
    ##### Actual Data Aquisition Stuff
    ###########################################

    def rfsocLoad(self, bit_name = "top"):
        """Load an overlay file describing an RFSoC instance.
        The overlay needs to support being created bare (just "overlayName()")
        and must support the "internal_capture( buffer, numChannels )"
        function.
        """            
        
        file_path = f'/home/xilinx/python/zcumts.py'
        # if hardware is not None:
        #     file_path = f'/home/xilinx/python/{hardware}.py'
        # else:
        #     file_path = filedialog.askopenfilename(title="Select an overlay module",
        #                                     filetypes=[("Python files","*.py"),
        #                                                 ("All files", "*.*")])
            
        self.logger.debug("Asked to load overlay at %s" % file_path)
        newdir = os.path.dirname(os.path.abspath(file_path))    

        curpath = sys.path
        self.logger.debug("Adding directory %s to module search path" % newdir)
        sys.path.insert(1, newdir)    
        curdir = os.path.abspath(os.curdir)
        self.logger.debug("Changing directory to %s" % newdir)
        os.chdir(newdir)
        base, extension = os.path.splitext(os.path.basename(file_path))
        self.logger.debug("Going to try to import %s", base)
            
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
            self.logger.debug("Found Overlay class %s from module %s" % (overlayClass.__name__ , overlayClass.__module__ ))
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
            self.logger.debug("Found RFSoC overlay %s" % theClass.__name__)
            ##Changed this to instantiate with bit file
            bitfile = f'zcu111_{bit_name}.bit'
            self.dev = theClass(bitfile)
            self.logger.debug("Created RFSoC device")
        except LocalException as e:
            self.logger.error(str(e))
        except Exception as e:
            self.logger.error("Unable to load module %s" % base)
            self.logger.error(str(e))
            
        self.logger.debug("Restoring original module search path")
        sys.path = curpath
        self.logger.debug("Going back to original directory %s" % curdir)
        os.chdir(curdir)

        self.dev.init_adc_memory(self.channel_names, self.sample_size*2)
        self.max_sample_size = self.sample_size

        ##This initiates the waveform instances so they can just be updated later
        ##Also initial Acquire doesn't work apparently and this gets it out the way
        self.rfsocAcquire()
        self.waveforms = []
        
        for i, channel in enumerate(self.channel_names):
            if channel != None and channel != "":
                self.waveforms.append(Waveform(self.extract_channel(ch=i), tag = channel))
            else:
                self.waveforms.append(None)

        try:
            from serialcobsdevice import SerialCOBSDevice       ###Since this comes from the loaded zcuagc overlay it may not be recognised in vscode without the explicit import 
            self.setSDV(SerialCOBSDevice('/dev/ttyPS1', 1000000))
        except:
            self.logger.debug("It would appear the overloay you have tried to load doesn't contain SerialCOBSDevice")
        return
    
    def rfsocAcquire(self):
        if self.dev is None:
            self.logger.error("No RFSoC device is loaded!")
            
        self.dev.internal_capture(self.adcBuffer)
        
    def generate_waveforms(self):
        self.rfsocAcquire()

        for i, waveform in enumerate(self.waveforms):
            if self.channel_names[i] != None and self.channel_names[i] != "":
                waveform.waveform = self.extract_channel(ch=i)

if __name__ == "__main__":
    import time

    daq = RFSoC_Daq(sample_size = 200*8, channel_names = ["ADC224_T0_CH0 (LF)", "", "ADC225_T1_CH0 (HF)", ""])

    daq.rfsocLoad(hardware='top')

    start_time = time.time()
    for i in range(100000):
        daq.generate_waveforms()

    end_time = time.time()

    # Calculate elapsed time
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")