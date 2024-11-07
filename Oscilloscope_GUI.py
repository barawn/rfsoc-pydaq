import tkinter as tk
import math
import numpy as np

from Oscilloscope_Display import Oscilloscope_Display
from Oscilloscope_Settings import Oscilloscope_Settings
from Waveforms.Waveform import Waveform

class Oscilloscope_GUI(tk.Frame):
    def __init__(self, root, width, height):
        self.root = root
        super().__init__(self.root)
        self.width, self.height = width, height


        self.grid_rowconfigure(0, weight=1)  # Row for trace_display
        self.grid_rowconfigure(1, weight=0)  # Initially, fft_display is hidden
        self.grid_columnconfigure(0, weight=1)

        self.trace_display = Oscilloscope_Display(self, width=self.width, height=self.height)
        self.trace_display.get_tk_widget().grid(row=0, column=0)

        self.fft_display = Oscilloscope_Display(self, width=self.width, height=self.height)
        # self.fft_display.get_tk_widget().grid(row=1, column=0)

        self.settings_frame = Oscilloscope_Settings(self)
        self.settings_frame.grid(row=0, rowspan=2, column=1, padx=10, pady=10)

        channel_names = ["ADC224_T0_CH0 (LF)", None, "ADC225_T1_CH0 (HF)", "ADC225_T1_CH1 (HF)"]

        self.settings_frame.update_channels(channel_names)

        # self.settings_frame.update_channels(channels)

    def update_layout(self, show_canvas1, show_canvas2):
        if show_canvas1 and show_canvas2:
            # Both canvases are gridded; set height to h/2
            self.trace_display.get_tk_widget().grid(row=0, column=0)
            self.trace_display.get_tk_widget().config(height=100*self.height//2)

            self.fft_display.get_tk_widget().grid(row=1, column=0)
            self.fft_display.get_tk_widget().config(height=100*self.height//2)
        elif show_canvas1:
            # Only canvas1 is gridded; set height to h
            self.trace_display.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            self.trace_display.get_tk_widget().config(height=100*self.height)

            # Remove canvas2 if it's not shown
            self.fft_display.get_tk_widget().grid_forget()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Oscilloscope")

    GUI = Oscilloscope_GUI(root,20,13)
    GUI.pack(fill=tk.BOTH, expand=True)

    # Example data to plot (replace with FPGA data as needed)
    sample_data = [Waveform([np.sin(0.05 * x) for x in range(1000)]), Waveform([np.sin(0.1 * x) for x in range(1000)])]
    GUI.trace_display.plot_waveform(sample_data)
    # GUI.fft_display.plot_fft([])
    GUI.fft_display.plot_fft(sample_data)

    root.mainloop()