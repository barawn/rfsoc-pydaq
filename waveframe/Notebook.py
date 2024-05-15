##Python Imports
import tkinter as tk
from tkinter import ttk, PhotoImage
import numpy as np
from scipy.fft import fft, ifft, fftfreq
from scipy.constants import speed_of_light
from scipy.optimize import curve_fit
from datetime import datetime
import csv

#System Imports
import logging
from PIL import Image, ImageDraw
import io

logger = logging.getLogger(__name__)

#Plotting imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

try:
    from PlotDisplay import PlotDisplay
    from Waveform import Waveform
except:
    pass

try:
    from .PlotDisplay import PlotDisplay
    from .Waveform import Waveform
except:
    pass

try:
    from waveframe.PlotDisplay import PlotDisplay
    from waveframe.Waveform import Waveform
except:
    pass

class Notebook(ttk.Notebook):
    '''
    Notebook is of type ttk.Notebook
    It is useful because it provides tab one can populate with frames quickly allowing one to move between, in our case, plots
    
    This class is used to manage what canvas is being shown 
    
    Setting waveform instances for a channel
    
    Initialising the plotting of said waveform
    
    As well as the sizing of the canvases (if one wants to focus on a specifc channel)
    '''
    def __init__(self, frame: ttk.Frame, figsize: tuple):
        super().__init__(frame)
        self.frame = frame
        self.figsize = figsize
        
        self.pack(fill=tk.BOTH, expand=True)
        
        self.waveform = None
        
        self.time_frame = PlotDisplay(self, figsize, "time", self.waveform)
        
        self.fft_frame = PlotDisplay(self, figsize, "fft", self.waveform)
        
        self.fit_frame = PlotDisplay(self, figsize, "fit", self.waveform)
        
        self.user_frame = PlotDisplay(self, figsize, "user", self.waveform)
        
    def setWaveform(self, data: Waveform):
        self.waveform = data
        self.time_frame.updateWaveform(self.waveform)
        self.fft_frame.updateWaveform(self.waveform)
        self.fit_frame.updateWaveform(self.waveform)
        self.user_frame.updateWaveform(self.waveform)
        
    def plot(self):
        
        if self.frame.toPlot == True:
        
            self.time_frame.display.plotWaveForm()
            
            ##Plotting additional optional plots. These more than double the aqcuire time so making them optional is nice
            if self.frame.parent.plotExtras[0]:
                self.fft_frame.display.plotFFT()
                
            if self.frame.parent.plotExtras[1]:
                self.fit_frame.display.plotFit()

    
    ##Notebook tab stuff
    def switchToTab(self, index):
        self.select(index)
    
    def switchTab(self):
        num_tabs = len(self.tabs())
        current = self.index(self.select())
        self.select((current+1)%num_tabs)
        
    def switchTabBack(self):
        num_tabs = len(self.tabs())
        current = self.index(self.select())
        self.select((current-1)%num_tabs)
        
    ##Probably redundant canvas stuff. Might be necessary for saving
    
    def getCanvas(self):
        current_tab_index = self.index('current')
        current_frame = self.nametowidget(self.tabs()[current_tab_index])
        current_canvas = current_frame.winfo_children()[0]
        return current_canvas
    
    def getNotebookCanvases(self):
        other_canvases = []
        for tab_index in range(self.index("end")):
            tab = self.nametowidget(self.tabs()[tab_index])
            canvas = tab.winfo_children()[0]  # Assuming canvas is the first widget
            other_canvases.append(canvas)

        current_canvas = self.getCanvas()
        other_canvases.remove(current_canvas)

        return other_canvases
    
    
    ##Canvas Sizing
        
    def ShrinkNotebook(self):
        self.time_frame.display.get_tk_widget().config(width=self.figsize[0]*100, height = self.figsize[1]*100)
        self.fft_frame.display.get_tk_widget().config(width=self.figsize[0]*100, height = self.figsize[1]*100)
        self.fit_frame.display.get_tk_widget().config(width=self.figsize[0]*100, height = self.figsize[1]*100)
        self.user_frame.display.get_tk_widget().config(width=self.figsize[0]*100, height = self.figsize[1]*100)
        
    def EnlargeNoteBook(self):
        self.time_frame.display.get_tk_widget().config(width = self.figsize[0]*400 , height = self.figsize[1]*130)
        self.fft_frame.display.get_tk_widget().config(width = self.figsize[0]*400 , height = self.figsize[1]*130)
        self.fit_frame.display.get_tk_widget().config(width = self.figsize[0]*400 , height = self.figsize[1]*130)
        self.user_frame.display.get_tk_widget().config(width = self.figsize[0]*400 , height = self.figsize[1]*130)
        
if __name__ == "__main__":
    
    root = tk.Tk()
    notebook = Notebook(root, (10,10))
    notebook.pack()
    
    notebook.getCanvas()
    
    root.mainloop()