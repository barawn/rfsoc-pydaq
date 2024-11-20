##Python Imports
import numpy as np
import tkinter as tk

import sys, os

#Module Imports

from Biquad_Daq import Biquad_Daq
from App_GUI import APP_GUI

from Waveforms.Waveform import Waveform

from widgets.SubmitButton import submitButton


class Biquad_App(Biquad_Daq):
    def __init__(self,
                 sample_size: int = 150*8,
                 channel_names = ["ADC224_T0_CH0", "ADC224_T0_CH1", "Biquad_Output", None]):
        
        super().__init__(sample_size, channel_names)

        self.GUI = APP_GUI()

        self.GUI.launch_GUI(self)

        self.A_submit = submitButton(self.GUI.oscilloscope.basic_frame, "   A : ", 0, lambda: self.submit_A(self.A_submit.get_value()))
        self.B_submit = submitButton(self.GUI.oscilloscope.basic_frame, "   B : ", 1, lambda: self.submit_B(self.B_submit.get_value()))
        self.P_submit = submitButton(self.GUI.oscilloscope.basic_frame, "   P : ", 0, lambda: self.submit_P(self.P_submit.get_value()))
        self.theta_submit = submitButton(self.GUI.oscilloscope.basic_frame, "theta : ", 1, lambda: self.submit_theta(self.theta_submit.get_value()))
  
        self.A_submit.grid(row=4, column=0, columnspan=4)
        self.B_submit.grid(row=5, column=0, columnspan=4)
        self.P_submit.grid(row=6, column=0, columnspan=4)
        self.theta_submit.grid(row=7, column=0, columnspan=4)

        self.biquad_button = tk.Button(self.GUI.oscilloscope.basic_frame, text = "Biquad", command = self._update_coefficients)
        self.biquad_button.grid(row=8, column=1)

        self.GUI.mainloop()

    ############################
    ##Actual Biquad stuff
    ############################

    #############
    ##GUI methods
    #############

    def submit_A(self, value = 0):
        value = eval(value)
        self.logger.debug(f"Setting parameter A to {value}")
        self.A = value

    def submit_B(self, value = 1):
        value = eval(value)
        self.logger.debug(f"Setting parameter B to {value}")
        self.B = value

    def submit_P(self, value = 0):
        value = eval(value)
        self.logger.debug(f"Setting parameter P to {value}")
        self.P = value

    def submit_theta(self, value = 1):
        value = eval(value)
        self.logger.debug(f"Setting parameter theta to {value} radians")
        self.theta = value


    ## Too much inheritance going on and this copied and pasted from the RFSoC_App
    ############################
    ##Ignore
    ############################

    def submit_sample_number(self, value = 64):
        value = eval(value)
        self.logger.debug(f"Currently have {self.sample_size} samples, you have inputted {8*value} samples")
        self.sample_size = 8*value

    def submit_save_name(self, SaveName):
        self.logger.debug(f"You are setting the Save Files name to : {SaveName}")
        if SaveName and isinstance(SaveName, str) == False:
            SaveName=str(SaveName)
        self.save_name = SaveName

    def generate_waveforms(self):
        super().generate_waveforms()
        self.GUI.oscilloscope.display_frame.plot_waveform(self.waveforms)
        self.GUI.oscilloscope.display_frame.plot_fft()
        self.GUI.oscilloscope.update_settings()


if __name__ == "__main__":

    from RFSoC_Daq import RFSoC_Daq
    from Biquad_Daq import Biquad_Daq
    from Biquad import Biquad

    app = Biquad_App()