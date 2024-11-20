##Python Imports
import tkinter as tk

#System Imports

from textconsole.TextConsole import TextConsole
from scrolledlog.ScrolledLog import ScrolledLog

from Waveforms.Waveform import Waveform

from Oscilloscope import Oscilloscope

from widgets.SubmitButton import submitButton

class APP_GUI(tk.Tk):
    def __init__(self, name = None):
        super().__init__()

        ##Basic Window Stuff
        self.title("RFSoC PyDaq Interface")
        self.screen_width = int(self.winfo_screenwidth())
        self.screen_height = int(self.winfo_screenheight())
        self.geometry(f"{self.screen_width}x{self.screen_height}")
        self.configure(bg="black")

        ##Setting up all the frames
        self.oscilloscope = Oscilloscope(self, 0.95*self.screen_width/100, 0.7*self.screen_height/100)
        self.oscilloscope.grid(row=0, column=0, columnspan=2)

    def load_GUI(self, daq, load=True):
        self.oscilloscope.update_channels(daq.channel_names)

        if load == True:
            self.load_button = tk.Button(self.oscilloscope.basic_frame, text = "Load", command = daq.rfsocLoad)
            self.load_button.grid(row=2, column=1)
            self.bit_name_submit = submitButton(self.oscilloscope.basic_frame, "Bit file : ", "top", lambda: daq.submit_bit_name(self.bit_name_submit.get_value()))
            self.bit_name_submit.grid(row=3, column=0, columnspan=4)

        
        self.sample_number_submit = submitButton(self.oscilloscope.basic_frame, "Clock no. : ", int(2048), lambda: daq.submit_sample_number(self.sample_number_submit.get_value()))
        self.save_name_submit = submitButton(self.oscilloscope.basic_frame, "Save Name : ", "Temp", lambda: daq.submit_save_name(self.save_name_submit.get_value()))

        self.sample_number_submit.grid(row=0, column=0, columnspan=4)
        self.save_name_submit.grid(row=1, column=0, columnspan=4)

        self.acquire_button = tk.Button(self.oscilloscope.basic_frame, text = "Acquire", command = daq.generate_waveforms)

        ##Hotkeys
        self.bind("<F6>", lambda event: daq.rfsocLoad())


        self.console = TextConsole( self,
                                    locals = { 'daq' : daq },
                                    height = 0.3*self.screen_height/27, 
                                    width = int(0.3*self.screen_width/10))
        self.console.grid(row = 1, column=0, sticky="NSEW")

        self.log = ScrolledLog( self, 
                        daq.logger, 
                        height = 0.3*self.screen_height/27,
                        width = int(0.3*self.screen_width/10))
        self.log.grid(row = 1, column=1, sticky="NSEW")

    def generate_GUI(self, load=True):

        if load == True:
            self.load_button.grid_forget()
            self.bit_name_submit.grid_forget()

        self.acquire_button.grid(row=2, column=2)

        self.oscilloscope.generate_local_GUI()

        ##Hotkeys
        self.unbind("<F6>")
        self.bind("<F7>", lambda event: self.generate_waveforms())
        self.bind("<F8>", lambda event: self.oscilloscope.update_settings())


    def launch_GUI(self, daq):
        self.load_GUI(daq, load=False)
        self.generate_GUI(load=False)

if __name__ == "__main__":
    app = APP_GUI()
    app.mainloop()