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

class Waveframe(ttk.Notebook):
    def __init__(self,
                 parent,
                 index,
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
        
        super().__init__(self.parent)
        
        ##Required otherwise it won't render due to the addition of buttons
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        ##I've re-orded this section so it is a lot easier to add more figure if need be
        self.figs = {}
        self.canvs = {}
        self.btns = {}
        
        ##Set up the time figure
        self.td = ttk.Frame(self)
        self.figs['time'] = Figure(figsize=figsize)
        self.canvs['time'] = FigureCanvasTkAgg(self.figs['time'],
                                               master=self.td)
        self.canvs['time'].draw()
        self.canvs['time'].get_tk_widget().pack()
        self.notebook.add(self.td, text='Time')
        
        ##Set up the Fourier Transform Frequency Figure
        self.fd = ttk.Frame(self)
        self.figs['freq'] = Figure(figsize=figsize)
        self.canvs['freq'] = FigureCanvasTkAgg(self.figs['freq'],
                                               master=self.fd)
        self.canvs['freq'].draw()
        self.canvs['freq'].get_tk_widget().pack()
        self.notebook.add(self.fd, text='Freq')
        
        ##Set up the fitted Waveform Figure
        self.ad = ttk.Frame(self)
        self.figs['fit'] = Figure(figsize=figsize)
        self.canvs['fit'] = FigureCanvasTkAgg(self.figs['fit'],
                                               master=self.ad)
        self.canvs['fit'].draw()
        self.canvs['fit'].get_tk_widget().pack()
        self.notebook.add(self.ad, text='Fit')
        
        ##I don't know why this is here
        self.user = ttk.Frame(self)
        self.figs['user'] = Figure(figsize=figsize)
        self.canvs['user'] = FigureCanvasTkAgg(self.figs['user'],
                                               master=self.user)
        self.canvs['user'].draw()
        self.canvs['user'].get_tk_widget().pack()
        self.notebook.add(self.user, text='User')
        
        #Template for adding new things
        
        # self.new = ttk.Frame(self)
        # self.figs['new'] = Figure(figsize=figsize)
        # self.canvs['new'] = FigureCanvasTkAgg(self.figs['new'],
        #                                        master=self.new)
        # self.canvs['new'].draw()
        # self.canvs['new'].get_tk_widget().pack()
        # self.add(self.new, text='New')


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
    
    ##This returns all the display frames (widgets) in the display frame
    def getWidgets(self):
        widgets = []
        for widget in self.parent.winfo_children():
            widgets.append(widget)
        return widgets
    
    ##This orders all the widgets in the correct order, used for reseting the diplay frame
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
    
    ##Don't want the widgets saved within the class. Easiest to delete and whilst it is still stored in the frame add it. No in-built method to re-order.
    def packNew(self, widget):
        widget.pack_forget()
        widget.pack(side="left")
        
    def repack(self, widgets):
        for widget in widgets:
            widget.pack_forget()
            widget.pack(side="left")
    
    def reset(self):
        return 'Reset'
    
    ##Resets the frame to the original position
    def resetFrame(self):
        for widget in self.orderWidgets():
            self.packNew(widget)
            widget.setPlot(True)
        return 'Frames Re-ordered'        

    ##Buttons
    def saveWF(self):
        directory = "/home/xilinx/rfsoc-pydaq/data/"

        # This needs a better automatic file name system
        fileName = self.title + "_" + datetime.now().strftime("%H-%M-%S_%d-%m-%Y") + ".csv"
        path = directory+fileName
        
        data = list(zip(np.arange(len(self.waveForm))/self.sampleRate, self.waveForm))
        
        with open(path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)        
        return 'Maybe completed'
    
    def SavePlt(self):
        current_canvas = self.getCanvas()
        
        if self.enlarged == False:
            self.Enlarge(current_canvas)
            
        directory = "/home/xilinx/rfsoc-pydaq/figures/"
        file = "canvas_snapshot.png"
        filename = directory+file
        
        #This is because the canvas width is probably too small (and overal size might be too small as well to be fair)
        width_multiplier = 3
        height_multiplier = 1.5
        quality = 6
        original_width = self.figsize[0]*100
        original_height = self.figsize[1]*100
        # current_canvas.config(width=original_width * width_multiplier, height = original_height * height_multiplier)
        # current_canvas.config(width=1920, height = 800)
        
        #Makes sure the canvas size is edited. Will edit on GUI as well until image saved
        current_canvas.update()

        #Otherwise the image quality will be awful
        #Pixels per inch (maybe) * better image quality * the relative size between width and height
        ps = current_canvas.postscript(colormode='color', pagewidth=self.figsize[0]*72*quality*width_multiplier, pageheight=self.figsize[1]*72*quality*height_multiplier)

        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img.save(filename)
                
        #Returns the GUI to normal. As long as this may or may not take (and also essential that this happens) it is also a clear indicator that the file has been saved when it resumes to normal
        current_canvas.config(width=original_width, height=original_height)
        
        self.Shrink(current_canvas)
        self.resetFrame()
        
        logger.debug(f"Saved plot as {filename}")
        
        
    def Shrink(self, canvas):
        self.btns['Enlarge'].config(relief="raised")
        self.resetFrame()
        canvas.config(width=self.figsize[0]*100, height = self.figsize[1]*100)
        self.enlarged = False
    
    def Enlarge(self, canvas):
        self.btns['Enlarge'].config(relief="sunken")
        for widget in self.orderThisWidget():
            print(f"Widget index : {widget.index}")
            self.packNew(widget)
            
        canvas.config(width=1920, height = 800)
        self.enlarged = True
        
    def enlargeButton(self):        
        canvas = self.getCanvas()
        print(f"Current widget index : {self.index}\n")
        if self.btns['Enlarge'].config('relief')[-1] == 'sunken':
            print("Reseting")
            self.Shrink(canvas)
            for widget in self.parent.winfo_children():
                widget.setPlot(True)
        else:
            print("Enlarging")
            self.Enlarge(canvas)
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
        
        omega=freq=amp=phase=failCount=0
        parameter = [guessOmega, guessAmp, guessPhase]
        
        parameter, covariance = curve_fit(self.getSine, np.arange(len(waveForm))*1.E9/self.sampleRate, waveForm, 
                                          p0=[guessOmega,guessAmp,guessPhase], 
                                          bounds=([guessOmega*0.9, guessAmp, guessPhase-0.25*np.pi], [guessOmega/0.9, guessAmp/0.7, guessPhase+0.25*np.pi]))
        omega=parameter[0]
        freq=parameter[0]/(2*np.pi)
        amp=parameter[1]
        phase=parameter[2]
        return omega,freq,amp,phase
        
        
    def plot(self, data, title, Wave, toPlot):#, Amp, Freq):
        self.setWaveform(data)
        Amp = Wave[0]
        Freq = Wave[1]
        Phase = Wave[2]
    
        self.figs['time'].clear()
        self.figs['freq'].clear()
        self.figs['fit'].clear()
        self.figs['user'].clear()
        # we want this in nanoseconds, so divide samplerate by 1E9
        samplePeriod = 1.E9/self.sampleRate
        xaxis = np.arange(len(data))*samplePeriod
        
        
        self.plotWaveForm(data, xaxis, title, Amp, Freq, Phase)
        
        # ax = self.figs['time'].add_subplot(111)
        # ax.plot(xaxis, data)
        # ax.set_title(title)
        # ax.set_xlabel('time (ns)')
        # ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        # ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5, label='Zero Line')
        # ax.axhline(y=Amp, color='black', linestyle='--', linewidth=0.3, label='Amplitude Line')
        
        # stats_text = f"Amplitude: {Amp:.2f} Counts\nFrequency: {(Freq/10**6):.2f} MHz\nPhase: {Phase:.2f} radians"
        # ax.text(0.95, 0.95, stats_text, verticalalignment='top', horizontalalignment='right',
        #     transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

        # self.canvs['time'].draw()
        
        ##Plotting additional optional plots. These more than double the aqcuire time so making them optional is nice
        if toPlot[0]:
            self.plotFreq(data, title, Amp, Freq)
            
        if toPlot[1]:
            self.plotFit(data, title, xaxis, Amp, Freq, Phase)

        if callable(self.user_callback):
            try:
                self.user_callback(data,
                                   self.figs['user'],
                                   self.canvs['user'])
            except TypeError:
                logging.error("user_callback '%s' type error: check arguments (data, fig, canvas)" % self.user_callback.__name__)        

    def plotWaveForm(self, data, xaxis, title, Amp, Freq, Phase):
        ax = self.figs['time'].add_subplot(111)
        ax.plot(xaxis, data)
        ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5, label='Zero Line')
        ax.axhline(y=Amp, color='black', linestyle='--', linewidth=0.3, label='Amplitude Line')
        
        stats_text = f"Amplitude: {Amp:.2f} Counts\nFrequency: {(Freq/10**6):.2f} MHz\nPhase: {Phase:.2f} radians"
        ax.text(0.95, 0.95, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

        self.canvs['time'].draw()

    ##Additional plots
    def plotFreq(self, data, title, Amp, Freq):
        scipy_fft = fft(data)
        
        xf = np.linspace(0.0, 1.0/(2.0/self.sampleRate), len(data)//2)/(10**6)
        
        axFreq = self.figs['freq'].add_subplot(111)
        
        axFreq.plot(xf, self.convertToMag(scipy_fft), label='scipy')
        
        axFreq.set_title(title)
        axFreq.set_xlabel("Frequency (MHz)")
        axFreq.set_ylabel("Magnitude (arb.)")
        
        axFreq.axvline(x=Freq/(10**6), color='r', linestyle='--',  linewidth=0.3, label='Frequency')
        axFreq.axhline(y=Amp, color='r', linestyle='--', linewidth=0.3, label='Amplitude')
        
        axFreq.legend(loc='upper right')
        
        self.canvs['freq'].draw()
        return 'Plotted frequency'
    
    def plotFit(self, data, title, xaxis, Amp, Freq, Phi):
        
        Omega,Frequency,Amplitude,Phase=self.doSineWaveFit(data, Amp, Freq, Phi)
                        
        axFit = self.figs['fit'].add_subplot(111)
        axFit.plot(xaxis, data, label='Data')
        axFit.plot(xaxis, self.getSine(xaxis,Omega,Amplitude,Phase), label='Fit')
        axFit.set_title(title)
        axFit.set_xlabel('time (ns)')
        axFit.set_ylabel('ADC Counts', labelpad=-3.5)
        
        axFit.axhline(y=0, color='black', linestyle='--', linewidth=0.5, label='Zero Line')
        axFit.axhline(y=Amp, color='black', linestyle='--', linewidth=0.3, label='Amplitude Line')
        
        axFit.legend(loc='upper right')
        
        self.canvs['fit'].draw()