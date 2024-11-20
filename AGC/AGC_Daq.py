##Python Imports
import numpy as np

import sys, os

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from RFSoC_Daq import RFSoC_Daq
from Waveforms.Waveform import Waveform
from Waveforms.AGC import AGC

import threading
from widgets.TaskManager import TaskManager


#FPGA Class

class AGC_Daq(RFSoC_Daq):
    def __init__(self, sample_size: int = 64*8, 
                 channel_names = ["AGC_Core", "ADC224_T0_CH0", None, None]):
        super().__init__(sample_size, channel_names)

        self.rfsocLoad("agc")

    ############################
    ##Running agc core stuff
    ############################

    @property
    def scaling(self):
        return self.sdv.read(0x10)

    @scaling.setter
    def scaling(self, value):
        if isinstance(value, int):
            self.sdv.write(0x10, value)
            self.build_AGC()

    @property
    def offset(self):
        return self.sdv.read(0x14)
    
    @offset.setter
    def offset(self, value):
        if isinstance(value, int):
            self.sdv.write(0x14, value)
            self.build_AGC()
    
    @property
    def accumulator(self):
        return self.sdv.read(0x4)/131072
    
    @property
    def right_tail(self):
        return self.sdv.read(0x8)

    @property
    def left_tail(self):
        return self.sdv.read(0xc)
    
    @property
    def tail_diff(self):
        return self.right_tail-self.left_tail

    ############################
    ##Running agc core stuff
    ############################

    def load_AGC(self):
        if self.sdv is not None:
            self.sdv.write(0x00, 0x300)
        else:
            raise ImportError("No serial cobbs device loaded the daq")
        
    def apply_AGC(self):
        if self.sdv is not None:
            self.sdv.write(0x00, 0x400)
        else:
            raise ImportError("No serial cobbs device loaded the daq")
        
    def build_AGC(self):
        self.load_AGC()
        self.apply_AGC()

    def run_AGC(self):
        self.sdv.write(0,0x4)
        self.sdv.write(0,0x1)
        while ((self.sdv.read(0) & 0x2) == 0):
            pass

    ############################
    ##PID Loops
    ############################
    ##This is quite messy, but I didn't write half of this and don't know whats removable

    def run_pid_loop(self, should_run: bool):
        self._pid_loop_running = should_run
        if should_run:
            self.task_thread = threading.Thread(target=self._pid_loop_method)
            self.task_thread.start()
        else:
            self._pid_loop_running = False

    def _pid_loop_method(self):
        self.logger.debug("PID!!!")
        self.offset = 0
        self.scaling = 4096
        self.run_AGC()

        kp_val = 0
        ki_val = -1 / 256  # from the scales.py

        err_vals = []  # empty array for the error values
        err = np.sqrt(self.accumulator) - 4  # sqrt accumulator we want an RMS of 4  
        err_vals.append(0)
        scaleFracBits = 12
        convalScale = 1  # control value for the scaling 
        arrconvalScale = []
        arrconvalScale.append(convalScale)

        iter = 0
        while self._pid_loop_running:  # Use the new attribute to control the loop
            self.scaling =int(convalScale * (2**scaleFracBits))
            self.run_AGC()

            sqrtFracBits = 9
            rawVal = np.round(np.sqrt(self.accumulator) * (2**sqrtFracBits)) / (2**sqrtFracBits)
            err = rawVal - 4
            
            convalScale += kp_val * (err - err_vals[iter - 1]) + ki_val * err
            convalScale = np.round(convalScale * (2**scaleFracBits)) / (2**scaleFracBits)

            err_vals.append(err)
            arrconvalScale.append(convalScale)
            iter += 1

    def smoothing(self):# i am not quick this will take me a hot minute 
        self.offset = 200 # set initial offset
        self.scaling = 2**16 # set initial scaling
        self.dev.internal_capture(self.adcBuffer) # initial acquire
        self.run_AGC() # run the Agc

        err_vals = [] # empty array for the error values
        err_vals.append(self.tail_diff) # gt - lt 

        for iter in range(1,10): # loop for offset
            print(self.right_tail)
            print(self.left_tail)
            self.offset = 200 + iter * 10 # adjust the offset value  
            self.run_AGC() 
            err = self.tail_diff # new gt - lt 
            print(err) 
            alpha = 1/4 # alpha value est by Patrick
            err_vals.append( alpha * err + ( 1 - alpha ) * err_vals[ iter - 1 ]) # y = ae + (1-a)y^-1
           
        print(err_vals)


    def pid_loop_offset(self, testval): # for real this time
        self.offset = 0 # set initial offset
        self.scaling = 6000 # set initial scaling
        #self.dev.internal_capture(self.adcBuffer, self.numChannels) # initial acquire
        self.run_AGC() # run the
        
        #kp_val = 1/128  # to begin with I guess
        kp_val = 0
        ki_val = - 1 / 256 # from the scales.py

        err_vals = [] # empty array for the error values
        err = self.tail_diff()
        err_vals.append(0) # gt - lt 
        conval = 0 
        convals = []
        convals.append(conval)
        for iter in range(1,1000):
            self.offset = conval 
            self.run_AGC()
            err = self.tail_diff
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
        self.offset = 0
        self.scaling = 4096
        self.run_AGC()

        kp_val = 0
        ki_val = - 1 / 256 # from the scales.py

        err_vals = [] # empty array for the error values
        err =np.sqrt( self.accumulator()) - 4  # sqrt accumulator we want an RMS of 4  
        err_vals.append(0)
        scaleFracBits = 12
        convalScale = 1 # control value for the scaling 
        arrconvalScale = []
        arrconvalScale.append(convalScale)
        for iter in range(1,10000):
            self.scaling = int(convalScale*(2**scaleFracBits))
            self.run_AGC()

            # need to add an exponential portion to this otherwise it will do nothing
            # number of fractional bits out of sqrt
            sqrtFracBits = 9
            rawVal = np.round(np.sqrt(self.accumulator())*(2**sqrtFracBits))/(2**sqrtFracBits)
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
        self.run_AGC()
        out = self.get_Adc(0)
        rms_Waveform = np.average(np.square(out))

        return rms_Waveform, self.accumulator

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
            self.scaling = i*10
            waveform_Avg, accumulator_Avg = self.multiple_Accumulator()
            waveform_arr.append(waveform_Avg)
            accumulator_arr.append(accumulator_Avg)
        return np.array(waveform_arr), np.array(accumulator_arr)

    def all_RMS_Diff(self, duration = 100):
        waveform, accumulator = self.all_Accumulator()
        return waveform-accumulator
    
    ############################
    ##DAQ Overload Methods
    ############################

    def create_waveforms(self):
        self.waveforms.append(AGC(self.extract_channel(ch=0), tag = self.channel_names[0]))
        self.waveforms.append(Waveform(self.extract_channel(ch=1), tag = self.channel_names[1]))
        self.waveforms.append(None)
        self.waveforms.append(None)


if __name__ == "__main__":
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

    from RFSoC_Daq import RFSoC_Daq

    daq = AGC_Daq()

    daq.generate_waveforms()

    print(daq.waveforms[0].calc_rms())

    daq.load_AGC()
    daq.run_AGC()

    daq.scaling = 17284
    daq.offset = 93756

    daq.load_AGC()
    daq.run_AGC()

    print(daq.waveforms[0].calc_rms())

    print(daq.accumulator)