##Python Imports
import numpy as np
import tkinter as tk
from tkinter import filedialog

#System Imports
import logging
import os, sys, configparser, inspect, importlib

from textconsole.TextConsole import TextConsole
from scrolledlog.ScrolledLog import ScrolledLog

from waveframe.Waveframe import Waveframe
from waveframe.Waveframes import Waveframes

from Waveforms.Waveform import Waveform

from Oscilloscope_GUI import Oscilloscope_GUI

logger = logging.getLogger(__name__)

class APP_GUI(tk.Tk):
    def __init__(self, name = None):
        super().__init__()

        ##Basic Window Stuff
        self.title("RFSoC PyDaq Interface")

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        # logging.basicConfig(level=logging.DEBUG)

        self.geometry(f"{self.screen_width}x{self.screen_height}")

        self.logger = logging.getLogger(__name__)

        ##Setting up all the frames
        self.oscilloscope = Oscilloscope_GUI(self, self.screen_width/108, 0.8*self.screen_height/108)
        # self.oscilloscope.grid(row=0, column=1, rowspan=2)
        self.oscilloscope.grid(row=0, column=0, columnspan=2)

        # locals = { 'daq' : daq}

        self.console = TextConsole( self,
                                    locals = None,
                                    height = 0.3*self.screen_height/20, 
                                    width = int(0.3*self.screen_width/10))
        # self.console.grid(row = 0, column=0, sticky="NSEW")
        self.console.grid(row = 1, column=0, sticky="NSEW")

        self.log = ScrolledLog( self, 
                                self.logger, 
                                height = 0.3*self.screen_height/20,
                                width = int(0.3*self.screen_width/10))
        # self.log.grid(row = 1, column=0, sticky="NSEW")
        self.log.grid(row = 1, column=1, sticky="NSEW")

    def getSubmitInput(self, value, needNumber):
        if isinstance(value, object):
            self.logger.debug("Passed in an object, attempting to .entry.get()")
            try:
                result = eval(value.entry.get())
            except (NameError, SyntaxError):
                if needNumber == False:
                    result = value.entry.get()
                else:
                    self.logger.debug("Please pass in a number")
        else:
            self.logger.debug("Passed in an value")
            result = value
        return result
    
    def toggle(self, tg, setFunc):
        if tg.config('relief')[-1] == 'sunken':
            tg.config(relief="raised")
            setFunc(True)
        else:
            tg.config(relief="sunken")
            setFunc(False)
        return 'Updated plotting'
    
if __name__ == "__main__":
    app = APP_GUI()
    app.mainloop()