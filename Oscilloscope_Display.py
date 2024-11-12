import tkinter as tk
from tkinter import *
import numpy as np
import matplotlib
# matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from typing import List

from Waveforms.Waveform import Waveform

##Its job is to be a TKinter Canvas to plot onto
##Basically this is to have oscilloscope pyplots plotted onto in TKinter
class Oscilloscope_Display(FigureCanvasTkAgg):
    def __init__(self, parent, width=6, height=4):
        # Create a Figure instance for plotting
        self.figure = Figure(figsize=(width, height))
        self.parent = parent
        super().__init__(self.figure, self.parent)

        self.figure.subplots_adjust(left=0.04, right=0.97, top=0.9, bottom=0.1)
        
        self.ax = self.figure.add_subplot(111)
        self.figure.patch.set_facecolor('black')
        self.ax.set_facecolor('black')
        self.ax.grid(True, color='white')

        self.ax.tick_params(axis='both', colors='white')

        for spine in self.ax.spines.values():
            spine.set_color('white')  # Set spine color to white
            spine.set_linewidth(2)  

    def ungrid(self):
        if self.get_tk_widget().winfo_ismapped():
            self.get_tk_widget().grid_forget()

    def plot_waveform(self, waveforms : list[Waveform] = None):
        if waveforms != None:
            self.waveforms = waveforms

        self.ax.clear()
        self.ax.grid(True)

        for i, trace in enumerate(self.waveforms):
            if trace != None:
                if self.parent.settings_frame.arr_plot[i] == True:
                    trace.plotWaveform(ax = self.ax, colour = self.parent.colours[i], scale = self.parent.settings_frame.arr_scale[i], offset = self.parent.settings_frame.arr_offset[i], pos=0.18*i)

        self.ax.set_title("Channel Traces", color='white')
        self.ax.set_xlabel('Time (ns)', color='white')
        self.ax.set_ylabel('ADC Counts', color='white')

        self.ax.legend(loc="lower right")
        self.draw()

    def plot_fft(self, spectra : list[Waveform] = None):
        if spectra != None:
            self.waveforms = spectra

        if all(not item for item in self.parent.settings_frame.arr_fft) == True:
            self.parent.update_layout(True, False)
            return

        if not self.waveforms:
            self.parent.update_layout(True, False)
            return
        
        self.ax.clear()
        self.ax.grid(True)

        if self.get_tk_widget().winfo_ismapped() != True:
            self.parent.update_layout(True, True)

        for i, spectrum in enumerate(self.waveforms):
            if spectrum != None:
                if self.parent.settings_frame.arr_fft[i] == True:
                    spectrum.plotFFT(ax = self.ax, colour = self.parent.colours[i])

        self.ax.set_title("Channel Spectra", color='white')
        self.ax.set_xlabel('Frequency (MHz)', color='white')
        self.ax.set_ylabel('Magnitude (arb.)', color='white')
        
        self.ax.legend()
        self.draw()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Oscilloscope GUI")

    # Create an instance of Oscilloscope_Display with desired width and height
    oscilloscope_display = Oscilloscope_Display(root, width=8, height=5)
    oscilloscope_display.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Example data to plot (replace with FPGA data as needed)
    sample_data = [Waveform([np.sin(0.05 * x) for x in range(1000)]), Waveform([np.sin(0.1 * x) for x in range(1000)])]
    oscilloscope_display.plot_waveform(sample_data)

    root.mainloop()