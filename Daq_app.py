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

from DAQ import RFSoC_Daq
from App_GUI import APP_GUI

logger = logging.getLogger(__name__)

#FPGA Class
class RFSoC_App(RFSoC_Daq):
    def __init__(self,
                 sample_size: int = 2**11,
                 channel_names = ["ADC224_T0_CH0 (LF)", None, "ADC225_T1_CH0 (HF)", "ADC225_T1_CH1 (HF)"]):
        
        super().__init__(sample_size, channel_names)

        self.app = APP_GUI()

        self.gen_test_waveforms()

        self.app.oscilloscope.trace_display.plot_waveform(self.waveforms)

        self.app.oscilloscope.fft_display.plot_fft(self.waveforms)

        self.app.oscilloscope.settings_frame.update_channels(channel_names)

        self.app.mainloop()


    def gen_test_waveforms(self):
        self.waveforms = []
        for i in range(4):
            if self.channel_names[i] != None:
                self.waveforms.append(Waveform([np.sin((i+1)/40 * x) for x in range(1000)]))
            else:
                self.waveforms.append(None)

if __name__ == "__main__":
    obj = RFSoC_App()

    obj.gen_test_waveforms()

    # obj.channel_names = ["Channel 0", "Channel 1", "Channel 2", None]
    # obj.sample_size = 16

    # print(obj.adcBuffer.shape)

    # obj.sample_size = 32
    # print(obj.adcBuffer.shape)

    # obj.channel_names = ["Channel 1", "Channel 2", None, None]
    # print(obj.adcBuffer.shape)