import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import math
import numpy as np
import matplotlib.pyplot as plt

from Waveforms.Waveform import Waveform
from widgets.SubmitButton import submitButton

class Oscilloscope(tk.Frame):
    def __init__(self, root, width, height):
        self.root = root
        self.width, self.height = width, height
        super().__init__(self.root, width=self.width, height=self.height)

        #The colours for the 4 optional channel traces. Only works on black background
        self.colours = ['dodgerblue', 'gold', 'red', 'limegreen']
        #White background colours. I know purple is not ideal hear but yellow won't show up on white
        # self.colours = ['royalblue', 'red', 'green', 'purple']

        self.arr_plot = [False, False, False, False]
        self.arr_fft = [False, False, False, False]
        self.arr_offset = [0, 0, 0, 0]
        self.arr_scale = [1, 1, 1, 1]

        self.display_frame = Oscilloscope_Display(self, width=0.8*self.width, height=self.height)
        self.display_frame.get_tk_widget().grid(row=0, column=0)

        self.settings_frame = tk.Frame(self, width=0.2*self.width)
        self.settings_frame.grid(row=0, column=1)

        self.channels_frame = tk.Frame(self.settings_frame)
        self.channels_frame.grid(row=0, column=0)

        self.basic_frame = tk.Frame(self.settings_frame)
        self.basic_frame.grid(row=1, column=0)

        self.update_button = tk.Button(self.basic_frame, text = "Update", command = self.update_settings)
        self.save_plot_button = tk.Button(self.basic_frame, text = "Save Plt")#, command = self.parent.trace_display.save_plots)
        self.save_trace_button = tk.Button(self.basic_frame, text = "Save trace")#, command = self.parent.trace_display.save_traces)

        self.update_button.grid(row=2, column=3)

    def update_settings(self):
        self.get_channel_plot()
        self.get_channel_fft()
        self.get_channel_offset()
        self.get_channel_scale()

        self.display_frame.update_axes()
        self.display_frame.plot_waveform()
        self.display_frame.plot_fft()

    def update_channels(self, channel_names : list[str], daq = None):
        for widget in self.channels_frame.winfo_children():
            widget.destroy()

        self.channels = []

        for i, channel in enumerate(channel_names):
            if channel != None and channel != "":
                self.channels.append(Oscilloscope_Channels(self.channels_frame, channel, border_colour=self.colours[i]))

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
    
    def get_channel_offset(self):
        self.arr_offset = []
        for channel in self.channels:
            if channel != None:
                val = channel.channel_offset_entry.get()
                if val == "" or val == None:
                    self.arr_offset.append(0)
                else:
                    self.arr_offset.append(eval(val))
            else:
                self.arr_offset.append(None)
        return self.arr_offset

    def get_channel_scale(self):
        self.arr_scale = []
        for channel in self.channels:
            if channel != None:
                val = channel.channel_scale_entry.get()
                if val == "" or val == None:
                    self.arr_scale.append(1)
                else:
                    self.arr_scale.append(eval(val))
            else:
                self.arr_scale.append(None)
        return self.arr_scale
    
    def generate_local_GUI(self):
        self.save_plot_button.grid(row = 2, column= 0)
        self.save_trace_button.grid(row = 2, column= 1)

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
    def __init__(self, parent : tk.Frame, title : str, var : bool = False, border_width=10, border_colour="red", colour_thickness=5):
        self.parent = parent
        super().__init__(self.parent, 
                         bd=border_width, 
                         highlightbackground=border_colour,
                         highlightthickness=colour_thickness)

        self.highlightbackground = 'red'
        self.highlightthickness = 2

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

class Oscilloscope_Display(FigureCanvasTkAgg):
    def __init__(self, parent:Oscilloscope, width=6, height=4):
        self.parent = parent
        self.figure = Figure(figsize=(width, height))

        self.figure.patch.set_facecolor('black')

        self.update_axes()

        
        super().__init__(self.figure, self.parent)

        self.figure.subplots_adjust(left=0.04, right=0.97, top=0.9, bottom=0.1)

        self.draw()

        # self.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)


    def update_axes(self):
        self.figure.clear()
        if all(not item for item in self.parent.arr_fft) == True:
            self.ax1 = self.figure.add_axes([0.1, 0.1, 0.85, 0.8])
            self.ax2 = None
        else:
            self.ax1 = self.figure.add_axes([0.1, 0.55, 0.85, 0.35])
            self.ax2 = self.figure.add_axes([0.1, 0.1, 0.85, 0.35])
            
        self.apply_axis_style(self.ax1)
        if self.ax2:
            self.apply_axis_style(self.ax2)

    def apply_axis_style(self, ax: plt.Axes):
        ax.set_facecolor('black')
        ax.tick_params(axis='both', colors='white')

        for spine in ax.spines.values():
            spine.set_color('white')
            spine.set_linewidth(1)

    def plot_waveform(self, waveforms : list[Waveform] = None):
        if waveforms != None:
            self.waveforms = waveforms

        self.ax1.clear()
        self.ax1.grid(True)

        for i, trace in enumerate(self.waveforms):
            if trace != None:
                if self.parent.arr_plot[i] == True:
                    trace.plotWaveform(ax = self.ax1, colour = self.parent.colours[i], scale = self.parent.arr_scale[i], offset = self.parent.arr_offset[i], pos=0.18*i)
            # trace.plotWaveform(ax = self.ax1)

        self.ax1.set_title("Channel Traces", color='white')
        self.ax1.set_xlabel('Time (ns)', color='white')
        self.ax1.set_ylabel('ADC Counts', color='white')

        if all(not item for item in self.parent.arr_plot) == False:
            self.ax1.legend(loc="lower right")
        self.draw()

    def plot_fft(self):
        if self.ax2:
            self.ax2.clear()
            self.ax2.grid(True)

            for i, spectrum in enumerate(self.waveforms):
                if spectrum != None:
                    if self.parent.arr_fft[i] == True: 
                        spectrum.plotFFT(ax = self.ax2, colour = self.parent.colours[i])
                # spectrum.plotFFT(ax = self.ax2)

            self.ax2.set_title("Channel Spectra", color='white')
            self.ax2.set_xlabel('Frequency (MHz)', color='white')
            self.ax2.set_ylabel('Magnitude (arb.)', color='white')
            
            self.ax2.legend()
            self.draw()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Oscilloscope GUI")
    root.configure(bg="green")

    screen_width = root.winfo_screenwidth()/100
    screen_height = root.winfo_screenheight()/100

    GUI = Oscilloscope(root,width=0.95*screen_width,height=0.8*screen_height)
    GUI.pack(fill=tk.BOTH, expand=True)

    channel_names = ["ADC224_T0_CH0 (LF)", None, "ADC225_T1_CH0 (HF)", "ADC225_T1_CH1 (HF)"]

    GUI.update_channels(channel_names)

    sample_data = [Waveform(np.array([np.sin(0.05 * x) for x in range(1000)]), tag='Demo 1'), 
                   Waveform(np.array([np.sin(0.1 * x) for x in range(1000)]), tag='Demo 2'),
                   Waveform(np.array([np.sin(0.2 * x) for x in range(1000)]), tag='Demo 3'),
                   Waveform(np.array([np.sin(0.01 * x) for x in range(1000)]), tag='Demo 4')]

    GUI.display_frame.update_axes()
    GUI.display_frame.plot_waveform(sample_data)

    GUI.display_frame.plot_fft()

    root.mainloop()