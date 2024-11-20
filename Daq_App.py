##Python Imports
import numpy as np

#Module Imports

from Waveforms.Waveform import Waveform

from RFSoC_Daq import RFSoC_Daq
from App_GUI import APP_GUI

#FPGA Class
class RFSoC_App(RFSoC_Daq):
    def __init__(self,
                 sample_size: int = 2**14,
                 channel_names = ["ADC224_T0_CH0", "ADC224_T0_CH1", "ADC225_T1_CH0", "ADC225_T1_CH1"]):
        
        super().__init__(sample_size, channel_names)

        self.bit_name = 'top'

        self.GUI = APP_GUI()

        self.GUI.load_GUI(self)

        self.GUI.mainloop()
        
    def submit_sample_number(self, value = 64):
        value = eval(value)
        self.logger.debug(f"Currently have {self.sample_size} samples, you have inputted {8*value} samples")
        self.sample_size = 8*value

    def submit_save_name(self, SaveName):
        self.logger.debug(f"You are setting the Save Files name to : {SaveName}")
        if SaveName and isinstance(SaveName, str) == False:
            SaveName=str(SaveName)
        self.save_name = SaveName

    def submit_bit_name(self, BitName):
        self.logger.debug(f"You are setting the bit file name to : zcu111_{BitName}.bit")
        if BitName and isinstance(BitName, str) == False:
            BitName=str(BitName)
        self.bit_name = BitName

    def rfsocLoad(self, hardware=None):
        if hardware:
            self.save_name = hardware
        super().rfsocLoad(self.bit_name)
        self.GUI.generate_GUI()
        self.generate_waveforms()

    def generate_waveforms(self):
        super().generate_waveforms()
        self.GUI.oscilloscope.display_frame.plot_waveform(self.waveforms)
        self.GUI.oscilloscope.display_frame.plot_fft()
        self.GUI.oscilloscope.update_settings()

    def generate_test_waveforms(self):
        self.waveforms = []
        for i in range(4):
            if self.channel_names[i] != None:
                self.waveforms.append(Waveform(np.array([np.sin((i+1)/40 * x) for x in range(1000)]), tag=f"lamba : {(i+1)/40}"))
            else:
                self.waveforms.append(None)

        self.GUI.oscilloscope.display_frame.plot_waveform(self.waveforms)
        self.GUI.oscilloscope.display_frame.plot_fft()


if __name__ == "__main__":

    app = RFSoC_App()

    # obj.generate_test_waveforms()

    # obj.channel_names = ["Channel 0", "Channel 1", "Channel 2", None]
    # obj.sample_size = 16

    # print(obj.adcBuffer.shape)

    # obj.sample_size = 32
    # print(obj.adcBuffer.shape)

    # obj.channel_names = ["Channel 1", "Channel 2", None, None]
    # print(obj.adcBuffer.shape)