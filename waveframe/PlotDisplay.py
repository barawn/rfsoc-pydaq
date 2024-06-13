import tkinter as tk
from tkinter import ttk
import numpy as np

#Plotting imports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    from Waveform import Waveform
except:
    pass

try:
    from .Waveform import Waveform
except:
    pass

try:
    from waveframe.Waveform import Waveform
except:
    pass

class PlotDisplay(ttk.Frame):
    '''
    This purely exists becuase one cannot directly populate notebooks with canvases. The canvases must be attached to a frame
    
    This automatically handles the packing of the canvas onto the notebook

    Probably shouldn't be edited. It handles stuff pretty well
    '''
    def __init__(self,
                 notebook: ttk.Notebook,
                 figsize: tuple,
                 title,
                 waveform):
        super().__init__(notebook)
        
        self.notebook = notebook
        
        self.display = PlotCanvas(self, figsize, title, waveform)
        
        self.display.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.notebook.add(self, text=title)
        
        
    def updateWaveform(self, waveform):
        self.display.waveform = waveform
        
class PlotCanvas(FigureCanvasTkAgg):
    '''
    This manages plotting/what is plotted, onto a canvas frame
    
    Currently has methods for:
    Plotting the raw waveform
    Plotting the FFT spectrum of the waveform
    Plotting a sinusoidal fitted plot
    '''
    def __init__(self, display: ttk.Frame, figsize: tuple, title: str, waveform: Waveform):
        self.figure = Figure(figsize=figsize)
        super().__init__(self.figure, display)
        
        self.display = display
        
        self.title = self.display.notebook.frame.title
        
        self.waveform = waveform
        
        self.draw()
    
    def plotWaveForm(self):
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        
        ax.plot(self.waveform.timelist*10**9, self.waveform.waveform)
        
        ax.set_title(self.title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        self.waveform.setRMS()
        self.waveform.setOffset()
        
        ax.axhline(y=self.waveform.offset, color='black', linewidth=0.4, label='Offset')
        
        try:
            self.waveform.frequencyFFT
        except:
            self.waveform.setWaveFFT()
            
        stats_text = f"RMS : {self.waveform.RMS:.2f} ADC\nFrequency : {self.waveform.frequencyFFT*10**(-6):.2f} MHz\nOffset : {self.waveform.offset:.2f} ADC"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

        self.draw()

    def plotPulseWave(self):
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        
        ax.plot(self.waveform.timelist*10**9, self.waveform.waveform)
        
        ax.set_title(self.title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        self.waveform.setRMS()
        self.waveform.setOffset()
        
        ax.axhline(y=0, color='black', linewidth=0.4, label='Zero Line')
        
        try:
            self.waveform.frequencyFFT
        except:
            self.waveform.setWaveFFT()
            
        stats_text = f"Frequency : {self.waveform.frequencyFFT*10**(-6):.2f} MHz"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

        self.draw()

    def plotSineWave(self):
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        
        ax.plot(self.waveform.timelist*10**9, self.waveform.waveform)
        
        ax.set_title(self.title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        self.waveform.setRMS()
        self.waveform.setOffset()
        
        ax.axhline(y=self.waveform.offset, color='black', linewidth=0.4, label='Offset')
        ax.axhline(y=self.waveform.RMS+self.waveform.offset, color='black', linestyle='--', linewidth=0.3, label='RMS Line')
        ax.axhline(y=-self.waveform.RMS+self.waveform.offset, color='black', linestyle='--', linewidth=0.3, label='RMS Line')
        
        try:
            self.waveform.frequencyFFT
        except:
            self.waveform.setWaveFFT()
            
        stats_text = f"Amplitude : {self.waveform.amplitudeFFT} ADC\nRMS : {self.waveform.RMS:.2f} ADC\nFrequency : {self.waveform.frequencyFFT*10**(-6):.2f} MHz\nOffset : {self.waveform.offset:.2f} ADC"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

        self.draw()

    def plotFFT(self):
        self.figure.clear()
        
        self.waveform.doFFTs()
        
        axFreq = self.figure.add_subplot(111)
        
        axFreq.plot(self.waveform.xf*10**(-6), self.waveform.mag_spectrum, label='scipy FFT')
        
        axFreq.set_title(self.title)
        axFreq.set_xlabel("Frequency (MHz)")
        axFreq.set_ylabel("Magnitude (arb.)")
        
        # axFreq.legend(loc='upper right')
        
        stats_text = f"Frequency : {self.waveform.frequencyFFT*10**(-6):.2f} MHz\nAmplitude : {self.waveform.amplitudeFFT:.2f} ADC"
        
        axFreq.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=axFreq.transAxes, bbox=dict(facecolor='white', alpha=0.5))
        
        self.draw()
    
    def plotFit(self):
        self.figure.clear()
        
        self.waveform.setSineFit()
        
        axFit = self.figure.add_subplot(111)
        axFit.plot(self.waveform.timelist, self.waveform.waveform, alpha = 0.5, label='Data')
        axFit.plot(self.waveform.timelist, self.waveform.getSine(self.waveform.timelist,self.waveform.fitFrequency*2*np.pi,self.waveform.fitAmplitude,self.waveform.fitPhase,self.waveform.fitOffset), label='Fit')
        axFit.set_title(self.title)
        axFit.set_xlabel('time (s)')
        axFit.set_ylabel('ADC Counts', labelpad=-3.5)
        
        axFit.axhline(y=self.waveform.fitOffset, color='black', linestyle='--', linewidth=0.5, label='Offset Line')
        axFit.axhline(y=self.waveform.fitAmplitude+self.waveform.fitOffset, color='red', linestyle='--', linewidth=0.3, label='Amplitude Line')
        axFit.axhline(y=-self.waveform.fitAmplitude+self.waveform.fitOffset, color='red', linestyle='--', linewidth=0.3)

        # axFit.legend(loc='center right')
        
        try:
            self.waveform.fitDiff
        except:
            self.waveform.compareToFit()
            
        stats_text = f"Data                               \nFrequency : {self.waveform.frequencyFFT*10**(-6):.2f} MHz\nAmplitude : {self.waveform.amplitudeFFT:.2f} ADC\nOffset : {self.waveform.offset:.2f} ADC"
        
        axFit.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=axFit.transAxes, bbox=dict(facecolor='white', alpha=0.5))
            
        stats_text_fit = f"Fit                                \nFrequency : {self.waveform.fitFrequency*10**(-6):.2f} MHz\nAmplitude : {self.waveform.fitAmplitude:.2f} ADC\nOffset : {self.waveform.fitOffset:.2f} ADC\n'Fit Quality' : {self.waveform.fitDiff*100:.2f} Arb"
        
        axFit.text(0.97, 0.01, stats_text_fit, verticalalignment='bottom', horizontalalignment='right',
            transform=axFit.transAxes, bbox=dict(facecolor='white', alpha=0.5))
        
        self.draw()

if __name__ == "__main__":
    
    root = tk.Tk()
    notebook = ttk.Notebook(root)
    display = PlotDisplay(notebook, (3,2), "Temp")
    notebook.pack()
    
    root.mainloop()
