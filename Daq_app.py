##Python Imports
import numpy as np
from tkinter import filedialog
import tkinter as tk


#System Imports
import logging
import os, sys, inspect, importlib

#Module Imports
from waveframe.Waveframe import Waveframe
from waveframe.Waveframes import Waveframes

from Waveforms.Waveform import Waveform

from DAQ import RFSoC_Daq
from App_GUI import APP_GUI
from widgets.SubmitButton import submitButton

# logger = logging.getLogger(__name__)

#FPGA Class
class RFSoC_App(RFSoC_Daq):
    def __init__(self,
                 sample_size: int = 2**11,
                 channel_names = ["ADC224_T0_CH0 (LF)", "ADC224_T0_CH1 (LF)", "ADC225_T1_CH0 (HF)", "ADC225_T1_CH1 (HF)"]):
        
        super().__init__(sample_size, channel_names)

        self.save_name = 'Temp'

        self.app = APP_GUI()

        # self.generate_test_waveforms()

        self.app.oscilloscope.update_channels(channel_names)

        self.load_button = tk.Button(self.app.oscilloscope.basic_frame, text = "Load", command = self.rfsocLoad)
        self.load_button.grid(row=2, column=1)

        self.sample_number_submit = submitButton(self.app.oscilloscope.basic_frame, "Clock no. : ", int(200), lambda: self.submit_sample_number(self.sample_number_submit.get_value()))
        self.save_name_submit = submitButton(self.app.oscilloscope.basic_frame, "Save Name : ", "Temp", lambda: self.submit_save_name(self.submit_save_name.get_value()))

        self.sample_number_submit.grid(row=0, column=0, columnspan=4)
        self.save_name_submit.grid(row=1, column=0, columnspan=4)
        
        self.acquire_button = tk.Button(self.app.oscilloscope.basic_frame, text = "Acquire", command = self.generate_waveforms)

        self.app.mainloop()

    def submit_sample_number(self, value = 64):
        value = eval(value)
        logger.debug(f"Currently have {self.sample_size} samples, you have inputted {8*value} samples")
        self.sample_size = 8*value

    def submit_save_name(self, SaveName):
        logger.debug(f"You are setting the Save Files name to : {SaveName}")
        if SaveName and isinstance(SaveName, str) == False:
            SaveName=str(SaveName)
        self.save_name = SaveName


    def rfsocLoad(self, hardware='top'):
        super().rfsocLoad(hardware)
        self.generate_GUI()

    def generate_GUI(self):
        self.load_button.grid_forget()

        self.acquire_button.grid(row=2, column=2)

        self.app.oscilloscope.generate_local_GUI()

    def generate_waveforms(self):
        super().generate_waveforms()
        self.app.oscilloscope.display_frame.plot_waveform(self.waveforms)
        self.app.oscilloscope.display_frame.plot_fft()
        self.app.oscilloscope.update_settings()

    def generate_test_waveforms(self):
        self.waveforms = []
        for i in range(4):
            if self.channel_names[i] != None:
                self.waveforms.append(Waveform(np.array([np.sin((i+1)/40 * x) for x in range(1000)]), tag=f"lamba : {(i+1)/40}"))
            else:
                self.waveforms.append(None)

        self.app.oscilloscope.display_frame.plot_waveform(self.waveforms)
        self.app.oscilloscope.display_frame.plot_fft()


if __name__ == "__main__":

    logger = logging.getLogger(__name__)

    obj = RFSoC_App()

    # obj.generate_test_waveforms()

    # obj.channel_names = ["Channel 0", "Channel 1", "Channel 2", None]
    # obj.sample_size = 16

    # print(obj.adcBuffer.shape)

    # obj.sample_size = 32
    # print(obj.adcBuffer.shape)

    # obj.channel_names = ["Channel 1", "Channel 2", None, None]
    # print(obj.adcBuffer.shape)