##Python Imports
import tkinter as tk
from tkinter import ttk
import numpy as np

#System Imports
import logging

logger = logging.getLogger(__name__)

try:
    from ..waveframe.PlotDisplay import PlotDisplay
    from ..waveframe.Waveform import Waveform
    from ..waveframe.Notebook import Notebook
except:
    pass

try:
    from waveframe.PlotDisplay import PlotDisplay
    from waveframe.Waveform import Waveform
    from waveframe.Notebook import Notebook
except:
    pass

class AgcNotebook(Notebook):
    def __init__(self, frame: ttk.Frame, figsize: tuple, index: int = None):
        super().__init__(frame, figsize)
        self.index = index

    def plot(self):
        if self.frame.toPlot == True:
            if self.index == 0:
                self.time_frame.display.plotAGC()
                
            if self.index == 1:
                self.time_frame.display.plotWaveForm()
                
            ##Plotting additional optional plots. These more than double the aqcuire time so making them optional is nice
            if self.frame.parent.plotExtras["fft"]:
                self.fft_frame.display.plotFFT()