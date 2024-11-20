##Python Imports
import numpy as np
import tkinter as tk

import sys, os

#Module Imports

from AGC_Daq import AGC_Daq
from App_GUI import APP_GUI

from widgets.SubmitButton import submitButton
from widgets.TaskManager import TaskManager


class AGC_App(AGC_Daq):
    def __init__(self,
                 sample_size: int = 150*8,
                 channel_names = ["AGC_Core", "ADC224_T0_CH0", None, None]):
        
        super().__init__(sample_size, channel_names)

        self.GUI = APP_GUI()

        self.GUI.launch_GUI(self)

        self.scaling_submit = submitButton(self.GUI.oscilloscope.basic_frame, "   Scaling : ", 4096, lambda: self.submit_scaling(self.scaling_submit.get_value()))
        self.offset_submit = submitButton(self.GUI.oscilloscope.basic_frame, "   Offset : ", 0, lambda: self.submit_offset(self.offset_submit.get_value()))
  
        self.scaling_submit.grid(row=4, column=0, columnspan=4)
        self.offset_submit.grid(row=5, column=0, columnspan=4)

        self.biquad_button = tk.Button(self.GUI.oscilloscope.basic_frame, text = "AGC", command = self.run_AGC)
        self.biquad_button.grid(row=6, column=1)

        self.pid_button = TaskManager(self.GUI.oscilloscope.basic_frame, "PID_Loop", self.run_pid_loop)
        self.pid_button.toggle_button.grid(row=6, column=2)

        self.GUI.mainloop()

    ############################
    ##Actual Biquad stuff
    ############################

    #############
    ##GUI methods
    #############

    def submit_scaling(self, value):
        value = eval(value)
        self.logger.debug(f"Setting Scaling to {value}")
        self.scaling = value

    def submit_offset(self, value):
        value = eval(value)
        self.logger.debug(f"Setting Offset to {value}")
        self.offset = value


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

    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

    from RFSoC_Daq import RFSoC_Daq
    from AGC_Daq import AGC_Daq

    app = AGC_App()