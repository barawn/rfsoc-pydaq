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

class PlotDisplay(ttk.Frame):
    def __init__(self,
                 parent: ttk.Notebook,
                 figs: object,
                 canvs: object,
                 figsize: tuple,
                 title):
        super().__init__(parent)
        
        self.parent = parent
        
        self.figs = figs
        self.canvs = canvs
        
        self.figs[title] = Figure(figsize=figsize)
        self.canvs[title] = FigureCanvasTkAgg(self.figs[title],
                                               master=self)
        self.canvs[title].draw()
        self.canvs[title].get_tk_widget().pack()
        self.parent.add(self, text=title)
    
class Waveframe(ttk.Notebook):
    def __init__(self,
                 parent: tk.Frame,
                 index: int,
                 title,
                 sampleRate=3.E9,
                 figsize=(3,2)):
        
        self.parent = parent
        self.sampleRate = sampleRate
        self.figsize = figsize
        self.index = index
        self.title = title
        
        self.toPlot = True
        self.enlarged = False
        self.waveForm = 0
        self.saveText = "Temp"
        
        super().__init__(self.parent)
        
        ##Required issues with buttons otherwise
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
                
        self.figs = {}
        self.canvs = {}
        self.btns = {}
        
        self.time = PlotDisplay(self.notebook, self.figs, self.canvs, figsize, "time")
        
        self.freq = PlotDisplay(self.notebook, self.figs, self.canvs, figsize, "freq") 
        
        self.fit = PlotDisplay(self.notebook, self.figs, self.canvs, figsize, "fit") 
        
        self.user = PlotDisplay(self.notebook, self.figs, self.canvs, figsize, "user")

        ##Buttons for the waveform to record stuff and change the view.
        self.btn_frame = tk.Frame(self)
        
        self.btns['SaveWF'] = tk.Button(self.btn_frame, relief="raised", text="SaveWF", command=self.saveWF)
        self.btns['SaveWF'].pack(side=tk.LEFT)
        
        self.btns['SavePlt'] = tk.Button(self.btn_frame, relief="raised", text="SavePlt", command=self.SavePlt)
        self.btns['SavePlt'].pack(side=tk.LEFT)
        
        self.btns['Enlarge'] = tk.Button(self.btn_frame, relief="raised", text="Enlarge", command=self.enlargeButton)
        self.btns['Enlarge'].pack(side=tk.LEFT)
        
        self.btns['Plot'] = tk.Button(self.btn_frame, relief="raised", text="Plot?", command=self.plotButton)
        self.btns['Plot'].pack(side=tk.LEFT)
        
        self.btn_frame.pack(side=tk.BOTTOM)
        
        self.pack(fill=tk.BOTH, expand=True)
        
        # Callback signature is data, figure, canvas
        self.user_callback = None
    
    def switchToTab(self, index):
        self.notebook.select(index)
    
    def switchTab(self):
        num_tabs = len(self.notebook.tabs())
        current = self.notebook.index(self.notebook.select())
        self.notebook.select((current+1)%num_tabs)
        
    def switchTabBack(self):
        num_tabs = len(self.notebook.tabs())
        current = self.notebook.index(self.notebook.select())
        self.notebook.select((current-1)%num_tabs)
        
    ##Sets
    def setWaveform(self, data):
        self.waveForm = data
        return 'The waveform has been set'
    
    ##Gets
    def getWaveform(self):
        return self.waveForm
        
    ##Waveform button methods
    
    ##This gets the canvas currently on display, the specific notebook tab
    def getCanvas(self):
        current_tab_index = self.notebook.index('current')
        current_frame = self.notebook.nametowidget(self.notebook.tabs()[current_tab_index])
        current_canvas = current_frame.winfo_children()[0]
        return current_canvas
    
    def getNotebookCanvases(self):
        other_canvases = []
        for tab_index in range(self.notebook.index("end")):
            tab = self.notebook.nametowidget(self.notebook.tabs()[tab_index])
            canvas = tab.winfo_children()[0]  # Assuming canvas is the first widget
            other_canvases.append(canvas)

        current_canvas = self.getCanvas()
        other_canvases.remove(current_canvas)

        return other_canvases
        
    ##This returns all the display frames (widgets) in the display frame
    def getWidgets(self):
        widgets = []
        for widget in self.parent.winfo_children():
            widgets.append(widget)
        return widgets
    
    ##This orders all the widgets in the correct (original) order, used for reseting the diplay frame
    def orderWidgets(self, widgets=None):
        if widgets is None:
            widgets = self.getWidgets()
        return sorted(widgets, key=lambda x: x.index)
    
    ##This moves the activated frame to the front of the widget order. This is required to enlarge a particular frame correctly
    def orderThisWidget(self, widgets=None):
        if widgets is None:
            widgets = self.getWidgets()
        for widget in widgets:
            if widget.index == self.index:
                widgets.remove(widget)
                widgets.insert(0, widget)
                break
        return widgets
    
    def packNew(self, widget):
        widget.pack_forget()
        widget.pack(side="left")
        logger.debug(f"Widget {widget} has been re-packed")
    
    ##Resets the frame to the original position
    def resetFrame(self):
        for widget in self.orderWidgets():
            self.packNew(widget)
            widget.setPlot(True)
        logger.debug("Frames returned to original")
        return 'Frames Re-ordered'        

    ##Buttons
    def saveName(self, subdir, fileType):
        #Needs better automatic naming system
        directory = "/home/xilinx/rfsoc-pydaq/"
        fileName = ""
        if self.saveText:
            fileName = subdir + self.title + "_" + self.saveText + fileType
        else:
            fileName = subdir + self.title + "_" + datetime.now().strftime("%H-%M-%S_%d-%m-%Y") + fileType
        path = directory+fileName
        logger.debug(f"Saving file to {path}")
        return path
    
    def saveWF(self):
        directory = "testConsistency"
        path = f"/home/xilinx/rfsoc-pydaq/{directory}/dummy.csv"
        
        data = list(zip(np.arange(len(self.waveForm))/self.sampleRate, self.waveForm))
        
        with open(path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)  
        logger.debug("Waveform data saved")
        return 'Saved Waveform'
    
    def setSaveWFName(self):
        directory = "testConsistency"
        pathTemp = f"/home/xilinx/rfsoc-pydaq/{directory}/dummy.csv"
        with open(pathTemp, 'r') as temp_file:
            temp_data = temp_file.readlines()
            
        path = self.saveName(f"{directory}/", ".csv")

        with open(path, 'w', newline='') as new_file:
            new_file.writelines(temp_data)

        # Clear temp.csv
        open(pathTemp, 'w').close()
    
    def SavePlt(self):
        current_canvas = self.getCanvas()
        
        if self.enlarged == False:
            self.Enlarge(current_canvas)

        path = self.saveName("figures/", ".png")
        
        quality = 2

        #Makes sure the canvas size is edited. Will edit on GUI as well until image saved
        current_canvas.update()

        ps = current_canvas.postscript(colormode='color', pagewidth=self.figsize[0]*400*quality, pageheight=self.figsize[1]*180*quality)

        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img.save(path)
                
        # current_canvas.config(width=original_width, height=original_height)
        
        self.Shrink(current_canvas)
        self.resetFrame()
        
        logger.debug(f"Saved plot as {path}")
        
    def Shrink(self, canvas):
        canvas.config(width=self.figsize[0]*100, height = self.figsize[1]*100)
        self.btns['Enlarge'].config(relief="raised")
        self.resetFrame()
        self.enlarged = False
        
    def ShrinkNotebook(self):
        for canvas in self.getNotebookCanvases():
            canvas.config(width=self.figsize[0]*100, height = self.figsize[1]*100)
    
    def Enlarge(self, canvas):
        self.btns['Enlarge'].config(relief="sunken")
        for widget in self.orderThisWidget():
            self.packNew(widget)
        ##My Display isn't going to 1920 for some reason
        canvas.config(width = self.figsize[0]*400 , height = self.figsize[1]*180)
        self.enlarged = True
        
    def EnlargeNoteBook(self):
        for canvas in self.getNotebookCanvases():
            canvas.config(width = self.figsize[0]*400 , height = self.figsize[1]*180)     
            
    def resetDisplay(self):
        widgets = self.parent.winfo_children()
        instance = False
        for widget in widgets:
            if widget != self:
                if widget.enlarged == True:
                    widget.btns['Enlarge'].invoke()
            
    def enlargeButton(self):
        ##May need deleting
        self.resetDisplay()
          
        canvas = self.getCanvas()
        if self.btns['Enlarge'].config('relief')[-1] == 'sunken':
            print("Reseting")
            self.ShrinkNotebook()
            self.Shrink(canvas)
            for widget in self.parent.winfo_children():
                widget.setPlot(True)
        else:
            print("Enlarging")
            self.Enlarge(canvas)
            self.EnlargeNoteBook()
            for widget in self.parent.winfo_children():
                if widget.index != self.index:
                    widget.setPlot(False)
            
        logger.debug("Updated the canvas size")
        return 'Updated canvas size' 
    
    def setPlot(self, choice):
        self.toPlot = choice
        if choice == True:
            self.btns['Plot'].config(relief="raised")
        else:
            self.btns['Plot'].config(relief="sunken")
            
    def plotButton(self):        
        if self.btns['Plot'].config('relief')[-1] == 'sunken':
            self.btns['Plot'].config(relief="raised")
            self.toPlot = True
            # for widget in self.parent.winfo_children():
            #     print(widget.index)
        else:
            self.btns['Plot'].config(relief="sunken")
            self.toPlot = False
            
        logger.debug("No plotting frame")
        return 'No plotting frame'   
        
    def convertToMag(self, yf):
        N = len(yf)
        return 2.0/N * np.abs(yf[0:N//2])
        
    def getSine(self, t,w,A,phi):
        return A*np.sin((w*t)+phi)
    
    def doSineWaveFit(self, waveForm, Amplitude, Frequency, Phase):
        guessFreq=Frequency
        guessOmega=guessFreq*2*np.pi/10**9
        guessAmp=Amplitude
        guessPhase = Phase
        
        omega=freq=amp=phase=0
        parameter = [guessOmega, guessAmp, guessPhase]
        
        parameter, covariance = curve_fit(self.getSine, np.arange(len(waveForm))*1.E9/self.sampleRate, waveForm, 
                                          p0=[guessOmega,guessAmp,guessPhase], 
                                          bounds=([guessOmega*0.9, guessAmp, guessPhase-np.pi], [guessOmega/0.9, guessAmp/0.7, guessPhase+np.pi]))
        omega=parameter[0]
        freq=parameter[0]/(2*np.pi)
        amp=parameter[1]
        phase=parameter[2]
        return omega,freq,amp,phase
        
    def plot(self, Wave, toPlot):#, Amp, Freq):
        # self.setWaveform(data)
        Amp = Wave[0]
        Freq = Wave[1]
        Phase = Wave[2]
    
        self.figs['time'].clear()
        self.figs['freq'].clear()
        self.figs['fit'].clear()
        self.figs['user'].clear()
        # we want this in nanoseconds, so divide samplerate by 1E9
        samplePeriod = 1.E9/self.sampleRate
        xaxis = np.arange(len(self.waveForm))*samplePeriod
        
        self.plotWaveForm(xaxis, Amp, Freq, Phase)
        
        ##Plotting additional optional plots. These more than double the aqcuire time so making them optional is nice
        if toPlot[0]:
            self.plotFreq(Amp, Freq)
            
        if toPlot[1]:
            self.plotFit(xaxis, Amp, Freq, Phase)

        if callable(self.user_callback):
            try:
                self.user_callback(self.waveForm,
                                   self.figs['user'],
                                   self.canvs['user'])
            except TypeError:
                logging.error("user_callback '%s' type error: check arguments (data, fig, canvas)" % self.user_callback.__name__)        

    def plotWaveForm(self, xaxis, Amp, Freq, Phase):
        ax = self.figs['time'].add_subplot(111)
        ax.plot(xaxis, self.waveForm)
        ax.set_title(self.title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        ax.axhline(y=0, color='black', linewidth=0.4, label='Zero Line')
        ax.axhline(y=Amp, color='black', linestyle='--', linewidth=0.3, label='Amplitude Line')
        ax.axhline(y=-Amp, color='black', linestyle='--', linewidth=0.3, label='Amplitude Line')
        
        stats_text = f"Amplitude: {Amp:.2f} Counts\nFrequency: {(Freq/10**6):.2f} MHz\nPhase: {Phase:.2f} radians"
        ax.text(0.95, 0.95, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

        self.canvs['time'].draw()

    ##Additional plots
    def plotFreq(self, Amp, Freq):
        scipy_fft = fft(self.waveForm)
        
        xf = np.linspace(0.0, 1.0/(2.0/self.sampleRate), len(self.waveForm)//2)/(10**6)
        
        axFreq = self.figs['freq'].add_subplot(111)
        
        axFreq.plot(xf, self.convertToMag(scipy_fft), label='scipy FFT')
        
        axFreq.set_title(self.title)
        axFreq.set_xlabel("Frequency (MHz)")
        axFreq.set_ylabel("Magnitude (arb.)")
        
        axFreq.axvline(x=Freq/(10**6), color='r', linestyle='--',  linewidth=0.15, label='Frequency')
        axFreq.axhline(y=Amp, color='g', linestyle='--', linewidth=0.15, label='Amplitude')
        
        axFreq.legend(loc='upper right')
        
        self.canvs['freq'].draw()
        return 'Plotted frequency'
    
    def plotFit(self, xaxis, Amp, Freq, Phi):
        
        Omega,Frequency,Amplitude,Phase=self.doSineWaveFit(self.waveForm, Amp, Freq, Phi)
                        
        axFit = self.figs['fit'].add_subplot(111)
        axFit.plot(xaxis, self.waveForm, label='Data')
        axFit.plot(xaxis, self.getSine(xaxis,Omega,Amplitude,Phase), label='Fit')
        axFit.set_title(self.title)
        axFit.set_xlabel('time (ns)')
        axFit.set_ylabel('ADC Counts', labelpad=-3.5)
        
        axFit.axhline(y=0, color='black', linestyle='--', linewidth=0.5, label='Zero Line')
        axFit.axhline(y=Amp, color='black', linestyle='--', linewidth=0.3, label='Amplitude Line')
        
        axFit.legend(loc='upper right')
        
        self.canvs['fit'].draw()