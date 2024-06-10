##Python Imports
import tkinter as tk
from tkinter import ttk
import numpy as np
from scipy.fft import fft
from scipy.optimize import curve_fit
from datetime import datetime
import csv
from screeninfo import get_monitors

#System Imports
import logging
from PIL import Image
import io

from typing import List

logger = logging.getLogger(__name__)

#Plotting imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    from Waveframe import Waveframe
except:
    pass

try:
    from .Waveframe import Waveframe
except:
    pass

try:
    from waveframe.Waveframe import Waveframe
except:
    pass


class Waveframes(tk.Frame):
    '''
    This contains the individual channel frames.
    
    This is mainly used since it is a lot easier to manage channel packing.
    
    Also certain attributes are the same for all individual waveframes and don't need multiple (i.e. 4) initialisations
    '''
    def __init__(self,
                 parent: tk.Frame,
                 numChannels: int):
        super().__init__(parent)
        
        self.parent = parent
        
        self.waveframes = []
        self.packed = []
        
        self.plotExtras = [False, False] ##To plot the FFT and fit
        self.saveText = "Temp"
        self.datatype = "pulse"
        self.directory = "testWidth"
        
        monitors = get_monitors()
        main_display = monitors[0]

        screen_width = main_display.width
        screen_height = main_display.height

        # screen_width = self.parent.winfo_screenwidth()
        # screen_height = self.parent.winfo_screenheight()

        self.figsize=(screen_width/(100*numChannels), screen_height/250)
        # self.figsize=(screen_width/(2000), screen_height/1000)
        
    ##Framing        

    def addWaveframe(self, waveframe: Waveframe):
        self.waveframes.append(waveframe)
        self.packed.append(False)
        
    def packFrames(self):
        for i, waveframe in enumerate(self.waveframes):
            waveframe.pack(side = tk.LEFT )
            self.packed[i] = True
            
    def unpackFrames(self):
        for i, waveframe in enumerate(self.waveframes):
            if self.packed[i] == True:
                waveframe.forget()
                self.packed[i] = False
        
    def oneFrame(self, index):
        for i, waveframe in enumerate(self.waveframes):
            if i==index:
                if self.packed[i] == False:
                    waveframe.pack(side = tk.LEFT )
            elif i!=index:
                if self.packed[i] == True:
                    waveframe.forget()
                    
    def resetFrames(self):
        self.unpackFrames()
        
        self.packFrames()
        
if __name__ == "__main__":
    
    root = tk.Tk()
    
    setofframes = Waveframes(root)
    
    for i in range(4):
        setofframes.addWaveframe(Waveframe(setofframes, i, str(i), 3.E9, (3.5,4)))
    
    
    setofframes.pack()
    setofframes.packFrames()
    setofframes.unpackFrames()
    setofframes.packFrames()
    
    root.mainloop()