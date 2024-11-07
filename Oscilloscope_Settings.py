import tkinter as tk
import math
import numpy as np

from widgets.SubmitButton import submitButton

class Oscilloscope_Settings(tk.Frame):
    def __init__(self, parent : tk.Frame):
        self.parent = parent
        super().__init__(self.parent)

        self.channels_frame = tk.Frame(self)
        self.channels_frame.grid(row=0, column=0)

        self.basic_frame = tk.Frame(self)
        self.basic_frame.grid(row=1, column=0)

        self.acquire_button = tk.Button(self.basic_frame, text = "Update", command = self.update_settings)

        self.acquire_button.grid(row=0, column=0)

        self.arr_plot = [False, False, False, False]
        self.arr_fft = [False, False, False, False]


    def update_settings(self):
        self.get_channel_plot()
        self.get_channel_fft()

        self.parent.trace_display.plot_waveform()
        self.parent.fft_display.plot_fft()

    def update_channels(self, channel_names : list[str], daq = None):
        for widget in self.channels_frame.winfo_children():
            widget.destroy()

        self.channels = []

        for i, channel in enumerate(channel_names):
            if channel != None and channel != "":
                self.channels.append(Oscilloscope_Channels(self.channels_frame, channel))

                ##its because you're indexing here
                self.channels[i].grid(row=i, column=0, padx=10, pady=10)
            else:
                self.channels.append(None)

    def get_channel_plot(self):
        self.arr_plot = []
        for channel in self.channels:
            if channel != None:
                val = channel.plot_trace_var.get()
                self.arr_plot.append(val)
            else:
                self.arr_plot.append(None)
        return self.arr_plot
    
    def get_channel_fft(self):
        self.arr_fft = []
        for channel in self.channels:
            if channel != None:
                val = channel.plot_fft_var.get()
                self.arr_fft.append(val)
            else:
                self.arr_fft.append(None)
        return self.arr_fft

    def create_submit_boxes(self, daq):
        self.sample_number_submit = submitButton(self.basic_frame, "Sample Number (multiplied by 8) : ", int(200), lambda: daq.submitNumSamples(self.sample_number), 0)
        
        self.save_name_submit = submitButton(self.basic_frame, "Save Name : ", "Temp", lambda: daq.submitSaveName(self.save_name_submit), 1)

    def create_buttons(self, daq):

        self.save_button = tk.Button(self.basic_frame, text = "Save", command = daq.Save)
        self.load_button = tk.Button(self.basic_frame, text = "Load", command = daq.rfsocLoad)
        self.acquire_button = tk.Button(self.basic_frame, text = "Acquire", command = daq.GuiAcquire)

    def create_GUI(self, daq, channel_names):
        self.update_channels(channel_names, daq)
        self.create_submit_boxes(daq)
        self.create_buttons(daq)

class Oscilloscope_Channels(tk.Frame):
    def __init__(self, parent : tk.Frame, title : str, var : bool = False):
        self.parent = parent
        super().__init__(self.parent)

        self.highlightbackground = 'red'
        self.highlightthickness = 2

        # self.borderwidth = 1
        # self.highlightbackground="blue"

        self.channel_label = tk.Label(self, text=title, font=("Arial Rounded MT Bold", 12))
        self.channel_label.grid(row=0, column=0)

        ##Plot
        self.plot_trace_var = tk.BooleanVar(value=var)

        self.plot_trace_frame = tk.Frame(self)

        self.plot_trace_label = tk.Label(self.plot_trace_frame, text="Plot Trace : ")
        self.plot_trace_label.grid(row=0, column=0)

        self.plot_trace_check = tk.Checkbutton(self.plot_trace_frame, variable=self.plot_trace_var)
        self.plot_trace_check.grid(row=0, column=1, sticky='e')

        self.plot_trace_frame.grid(row=1, column=0)

        ##FFT
        self.plot_fft_var = tk.BooleanVar(value=False)

        self.plot_fft_frame = tk.Frame(self)

        self.plot_fft_label = tk.Label(self.plot_fft_frame, text="    Plot FFT : ")
        self.plot_fft_label.grid(row=0, column=0)

        self.plot_fft_check = tk.Checkbutton(self.plot_fft_frame, variable=self.plot_fft_var)
        self.plot_fft_check.grid(row=0, column=1, sticky='e')

        self.plot_fft_frame.grid(row=2, column=0)


        ##Offset
        self.channel_offset_frame = tk.Frame(self)

        self.channel_offset_label = tk.Label(self.channel_offset_frame, text='Offset : ')
        self.channel_offset_label.grid(row=0, column=0, sticky="w")

        self.channel_offset_entry = tk.Entry(self.channel_offset_frame, width=10)
        self.channel_offset_entry.grid(row=0, column=1, sticky="w")

        self.channel_offset_frame.grid(row=1, column=1)

        ##Scale
        self.channel_scale_frame = tk.Frame(self)

        self.channel_scale_label = tk.Label(self.channel_scale_frame, text=' Scale : ')
        self.channel_scale_label.grid(row=0, column=0, sticky="w")

        self.channel_scale_entry = tk.Entry(self.channel_scale_frame, width=10)
        self.channel_scale_entry.grid(row=0, column=1, sticky="w")

        self.channel_scale_frame.grid(row=2, column=1)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Oscilloscope Channel Settings")

    settings_frame = Oscilloscope_Settings(root)
    settings_frame.grid(row=0, rowspan=2, column=1, padx=10, pady=10)

    channel_names = ["ADC224_T0_CH0 (LF)", None, "ADC225_T1_CH0 (HF)", "ADC225_T1_CH1 (HF)"]

    settings_frame.update_channels(channel_names)

    root.mainloop()