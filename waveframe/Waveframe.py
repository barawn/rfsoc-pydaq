import tkinter as tk
from tkinter import ttk
import numpy as np

import logging

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

class Waveframe(ttk.Notebook):
    def __init__(self,
                 parent,
                 sampleRate=3.E9,
                 figsize=(3,2)):
        self.sampleRate = sampleRate
        super().__init__(parent)
        self.td = ttk.Frame(self)
        self.fd = ttk.Frame(self)
        self.user = ttk.Frame(self)
        # now add a matplotlib canvas in each one
        self.figs = {}
        self.figs['time'] = Figure(figsize=figsize)
        self.figs['freq'] = Figure(figsize=figsize)
        self.figs['user'] = Figure(figsize=figsize)
        self.canvs = {}
        self.canvs['time'] = FigureCanvasTkAgg(self.figs['time'],
                                               master=self.td)
        self.canvs['freq'] = FigureCanvasTkAgg(self.figs['freq'],
                                               master=self.fd)
        self.canvs['user'] = FigureCanvasTkAgg(self.figs['user'],
                                               master=self.user)
        self.canvs['time'].draw()
        self.canvs['time'].get_tk_widget().pack()
        self.canvs['freq'].draw()
        self.canvs['freq'].get_tk_widget().pack()
        self.canvs['user'].draw()
        self.canvs['user'].get_tk_widget().pack()
        self.add(self.td, text='Time')
        self.add(self.fd, text='Freq')
        self.add(self.user, text='User')
        # Callback signature is data, figure, canvas
        self.user_callback = None

    def set_user_callback(self, fn):
        if fn is None:
            logging.debug("removing user_callback")
            return
        if callable(fn):
            logging.debug("adding user_callback %s" % fn.__name__)
            self.user_callback = fn

    # Pass data to this, and it'll plot in
    # time domain/freq domain/user pane
    def plot(self, data):
        self.figs['time'].clear()
        self.figs['freq'].clear()
        self.figs['user'].clear()
        # we want this in nanoseconds, so divide samplerate by 1E9
        samplePeriod = 1.E9/self.sampleRate
        xaxis = np.arange(len(data))*samplePeriod
        self.figs['time'].add_subplot(111).plot(xaxis, data)

        self.canvs['time'].draw()
        
        # figure out FFT stuff here
        

        if callable(self.user_callback):
            try:
                self.user_callback(data,
                                   self.figs['user'],
                                   self.canvs['user'])
            except TypeError:
                logging.error("user_callback '%s' type error: check arguments (data, fig, canvas)" % self.user_callback.__name__)        
