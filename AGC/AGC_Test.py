##Python Imports
import numpy as np
import tkinter as tk
from tkinter import filedialog
from scipy.fft import fft, ifft, fftfreq
from scipy.constants import speed_of_light
from typing import Callable

#System Imports
import logging
import subprocess
import os, sys, inspect, importlib, configparser, csv
import threading

from AGC.AGC_Daq import AGC_Daq

from widgets.SubmitButton import submitButton
from widgets.TaskManager import TaskManager

logger = logging.getLogger(__name__)

#FPGA Class
class AGC_Test(AGC_Daq):
    def __init__(self,
                 root: tk.Tk,
                 frame: tk.Frame,
                 numChannels: int = 4,
                 numSamples: int = 2**11,
                 channelName = ["","","","","","","",""]):
        super().__init__(root, frame, numChannels, numSamples, channelName)

        self.pid_loop=False
        self.task_thread = None

    ############################
    ##Maybe write your code here?
    ############################

    ############################
    ##PID Loops
    ############################
    def run_pid_loop(self, input: bool):
        self.pid_loop = input
        if input is True:
            self.task_thread = threading.Thread(target=self.pid_loop)
            self.task_thread.start()

    def pid_loop(self):
        logger.debug("PID!!!")
        self.setOffset(0)
        self.setScaling(4096)
        self.runAGC()

        kp_val = 0
        ki_val = - 1 / 256 # from the scales.py

        err_vals = [] # empty array for the error values
        err =np.sqrt( self.getAccum()) - 4  # sqrt accumulator we want an RMS of 4  
        err_vals.append(0)
        scaleFracBits = 12
        convalScale = 1 # control value for the scaling 
        arrconvalScale = []
        arrconvalScale.append(convalScale)

        while self.pid_loop is True:
            self.setScaling(int(convalScale*(2**scaleFracBits))) 
            self.runAGC()

            sqrtFracBits = 9
            rawVal = np.round(np.sqrt(self.getAccum())*(2**sqrtFracBits))/(2**sqrtFracBits)
            err = rawVal - 4
        
            convalScale +=  kp_val * ( err - err_vals[iter - 1]) + ki_val * err
            convalScale = np.round(convalScale*(2**scaleFracBits))/(2**scaleFracBits)

            err_vals.append(err)
            arrconvalScale.append(convalScale)

    def smoothing(self):# i am not quick this will take me a hot minute 

        self.setOffset(200) # set initial offset
        self.setScaling(2**16) # set initial scaling
        self.dev.internal_capture(self.adcBuffer, self.numChannels) # initial acquire
        self.runAGC() # run the Agc

        err_vals = [] # empty array for the error values
        err_vals.append(self.getTailDiff()) # gt - lt 

        for iter in range(1,10): # loop for offset
            print(self.sdv.read(0x8))
            print(self.sdv.read(0xC))
            self.setOffset( 200 + iter * 10 ) # adjust the offset value  
            self.runAGC() 
            err = self.getTailDiff() # new gt - lt 
            print(err) 
            alpha = 1/4 # alpha value est by Patrick
            err_vals.append( alpha * err + ( 1 - alpha ) * err_vals[ iter - 1 ]) # y = ae + (1-a)y^-1
           
        print(err_vals)


    def pid_loop_offset(self, testval): # for real this time
        self.setOffset(0) # set initial offset
        self.setScaling(6000) # set initial scaling
        #self.dev.internal_capture(self.adcBuffer, self.numChannels) # initial acquire
        self.runAGC() # run the
        
        #kp_val = 1/128  # to begin with I guess
        kp_val = 0
        ki_val = - 1 / 256 # from the scales.py

        err_vals = [] # empty array for the error values
        err = self.getTailDiff()
        err_vals.append(0) # gt - lt 
        conval = 0 
        convals = []
        convals.append(conval)
        for iter in range(1,1000):
            self.setOffset(conval) 
            self.runAGC()
            err = self.getTailDiff()
            # no bigger than 32767 or less than -32768 --> clamp it yo
            conval +=  kp_val * ( err - err_vals[iter - 1]) + ki_val * err
            conval = int(conval)
            if conval < -32768:
                conval = -32768
            if conval > 32767:
                conval = 32767
                
            err_vals.append(err)
            convals.append(conval)

        combined = np.column_stack((err_vals, convals))
        np.savetxt(f'/home/xilinx/data/Testing_stuff.csv', combined, delimiter=',')
        #np.savetxt(f'/home/xilinx/data/pid_loop_test{testval}.csv', combined, delimiter=',')
        #self.writeCSV("Testing_stuff", err_vals, convals)
        #self.writeCSV(f"pid_loop_test{testval}", err_vals, convals)


    def pid_loop_scaling(self):
        self.setOffset(0)
        self.setScaling(4096)
        self.runAGC()

        kp_val = 0
        ki_val = - 1 / 256 # from the scales.py

        err_vals = [] # empty array for the error values
        err =np.sqrt( self.getAccum()) - 4  # sqrt accumulator we want an RMS of 4  
        err_vals.append(0)
        scaleFracBits = 12
        convalScale = 1 # control value for the scaling 
        arrconvalScale = []
        arrconvalScale.append(convalScale)
        for iter in range(1,10000):
            self.setScaling(int(convalScale*(2**scaleFracBits))) 
            self.runAGC()

            # need to add an exponential portion to this otherwise it will do nothing
            # number of fractional bits out of sqrt
            sqrtFracBits = 9
            rawVal = np.round(np.sqrt(self.getAccum())*(2**sqrtFracBits))/(2**sqrtFracBits)
            err = rawVal - 4
        
            # no bigger than 32767 or less than -32768 --> clamp it yo
            convalScale +=  kp_val * ( err - err_vals[iter - 1]) + ki_val * err
            convalScale = np.round(convalScale*(2**scaleFracBits))/(2**scaleFracBits)
            # if convalScale < -32768:
             #   convalScale = -32768
            # if convalScale > 32767:
             #   convalScale = 32767
                
            err_vals.append(err)
            arrconvalScale.append(convalScale)
            if (iter % 100) == 0:
                print("err", err, "convalScale", convalScale)

        combined = np.column_stack((err_vals, arrconvalScale))
        np.savetxt(f'/home/xilinx/data/pid_loop_scale1.csv', combined, delimiter=',')
        #np.savetxt(f'/home/xilinx/data/pid_loop_test{testval}.csv', combined, delimiter=',')
        #self.writeCSV("Testing_stuff", err_vals, convals)
        #self.writeCSV(f"pid_loop_test{testval}", err_vals, convals)
        


    ############################
    ##This is the accumulator stuff from earlier
    ############################
    def test_Accumulator(self):
        self.runAGC()
        out = self.getAdc(0)
        rms_Waveform = np.average(np.square(out))

        rms_Accumulator = self.getAccum()
        return rms_Waveform, rms_Accumulator

    def multiple_Accumulator(self, duration = 100):
        waveform_arr = []
        accumulator_arr = []
        for i in range(100):
            waveform, accumulator = self.test_Accumulator()
            waveform_arr.append(waveform)
            accumulator_arr.append(accumulator)
        return np.mean(waveform_arr), np.mean(accumulator_arr)
    
    def rms_Diff(self, duration = 100):
        waveform_Avg, accumulator_Avg = self.multiple_Accumulator(duration)
        return waveform_Avg, accumulator_Avg

    def all_Accumulator(self, duration = 100):
        waveform_arr = []
        accumulator_arr = []
        for i in range(duration):
            self.setScaling(i*10)
            waveform_Avg, accumulator_Avg = self.multiple_Accumulator()
            waveform_arr.append(waveform_Avg)
            accumulator_arr.append(accumulator_Avg)
        return np.array(waveform_arr), np.array(accumulator_arr)

    def all_RMS_Diff(self, duration = 100):
        waveform, accumulator = self.all_Accumulator()
        return waveform-accumulator

    def save_Accumulator(self):
        self.writeCSV("Temporary", *self.all_Accumulator())
        

    ############################
    ##Display
    ############################
    def setDisplay(self):
        super().setDisplay()
        button = self.root.nametowidget("button")
        buttons = {}
        buttons['PID'] = TaskManager(button, "PID_Loop", self.run_pid_loop)
        buttons['PID'].grid(row=0, column=10)

