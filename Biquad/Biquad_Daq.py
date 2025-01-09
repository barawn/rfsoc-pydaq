##Python Imports
import numpy as np

#System Imports
import logging

import sys, os

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from RFSoC_Daq import RFSoC_Daq

from Biquad import Biquad

from Waveforms.Waveform import Waveform
from Waveforms.Filtered import Filtered
from Waveforms.Gated import Gated

class Biquad_Daq(RFSoC_Daq, Biquad):
    def __init__(self, sample_size: int = 160*8, 
                 channel_names = ["ADC224_T0_CH0", "ADC224_T0_CH1", "Biquad_Output", None], A=0, B=1, P=0, theta=np.pi):
        RFSoC_Daq.__init__(self, sample_size, channel_names)
        Biquad.__init__(self, A, B, P, theta)

        ##This will depend on what you have called the file. Mines called zcu111_biquad.bit
        super().rfsocLoad('biquad')

    ############################
    ##Maybe write your code here?
    ############################

    
    ############################
    ##Sets
    ############################

    ##This isn't working so great. It's seems to preventing the properties to be overwritten again for some reason
    def reset(self):
        self.run_zeroFIR(0, 0)
        self.run_poleFIR(0,0,0,0,[0,0,0,0,0,0,0])
        self.run_poleIIR(0,0,0,0)
        self.run_incremental(0,0)
    
    #Indepnedent single FIR (only zero)
    def run_zeroFIR(self, A = None, B = None):
        super().set_zeroFIR(A, B)

        self.sdv.write(0x04,self.calc_18_bit(self.B))
        self.sdv.write(0x04,self.calc_18_bit(self.A))
        self.sdv.write(0x00,1)

    def run_poleFIR(self, Dff = None, Dfg = None, Egg = None, Egf = None, Xn : list = None):
        if Xn is not None:
            super().set_Xn(*Xn)
        super().set_poleFIR(Dff, Dfg, Egg, Egf)
        
        ##Dff
        self.sdv.write(0x10, self.calc_18_bit(self.Dff))
        for x in reversed(self.Xn[1:-1]):
            self.sdv.write(0x10, self.calc_18_bit(x))

        ##Egg
        self.sdv.write(0x14, self.calc_18_bit(self.Egg))
        for x in reversed(self.Xn[1:]):
            self.sdv.write(0x14, self.calc_18_bit(x))

        ##Dfg
        self.sdv.write(0x18, self.calc_18_bit(self.Dfg))

        ##Egf
        self.sdv.write(0x1C, self.calc_18_bit(self.Egf))

        self.sdv.write(0x00,1)

    def run_poleIIR(self, C0=None, C1=None, C2=None, C3=None):
        super().set_poleIIR(C0, C1, C2, C3)
        self.sdv.write(0x08, self.calc_18_bit(self.C2))
        self.sdv.write(0x08, self.calc_18_bit(self.C3))
        self.sdv.write(0x08, self.calc_18_bit(self.C1))
        self.sdv.write(0x08, self.calc_18_bit(self.C0))
        self.sdv.write(0x00, 1)

    def run_incremental(self, a1 = None, a2 = None):
        super().set_incremental(a1, a2)

        self.sdv.write(0x0C, self.calc_18_bit(self.a1))
        self.sdv.write(0x0C, self.calc_18_bit(self.a2))
        self.sdv.write(0x00, 1)

    def run_Biquad(self):
        super().run_Biquad()
        # self.generate_waveforms()

    ############################
    ##Extracts
    ############################
    def extract_raw(self):
        return self.waveforms[0]

    def extract_biquad(self):
        return self.waveforms[2]
    
    ## Since it doesn't exist in firmware yet and is computatiionally simple
    def extract_incremental(self):

        input = self.waveforms[0]

        u = np.zeros((64*8, 8))
        for b in range(64):
            for n in range(8):
                u[b][n] = self.A * input[8*b+n] + self.B * input[8*b+n-1] + self.A * input[8*b+n-2]


        u = self.calc_q_format(u, 14, 2)

        y = self.waveforms[2].waveform.reshape(-1, 8)

        for b in range(64):
            for i in range(2, 8):
                y[b][i] = self.a1 * y[b][i - 1] - self.a2 * y[b][i - 2] + u[b][i]

        y[b][i] = self.calc_q_format(y[b][i], 12, 0)
        
        output = Waveform(y.flatten())
        return output

    def get_Xns(self):
        return self.calc_4_bit(self.Xn)
        
    def get_crosslink(self):
        return [self.calc_4_bit(self.Dff), self.calc_4_bit(self.Egg), self.calc_4_bit(self.Dfg), self.calc_4_bit(self.Egf)]

    def get_poleCoef(self):
        return [self.calc_4_bit(self.C0), self.calc_4_bit(self.C1), self.calc_4_bit(self.C2), self.calc_4_bit(self.C3)]

    def get_incremental(self):
        return [self.calc_4_bit(self.a1), self.calc_4_bit(self.a2)]
    
    def get_zero(self):
        return [self.calc_4_bit(self.A), self.calc_4_bit(self.B)]

    def get_coeffs(self):
        return self.get_Xns(), self.get_crosslink(), self.get_poleCoef(), self.get_incremental(), self.get_zero()

    ############################
    ##DAQ Overload Methods
    ############################

    def create_waveforms(self):
        self.waveforms.append(Gated(self.extract_channel(ch=0), tag = self.channel_names[0]))
        self.waveforms.append(Gated(self.extract_channel(ch=1), tag = self.channel_names[1]))
        self.waveforms.append(Filtered(self.extract_channel(ch=2), tag = self.channel_names[2]))
        self.waveforms.append(None)

    def generate_waveforms(self):
        self.run_Biquad()
        super().generate_waveforms()

    def update_waveforms(self):
        super().generate_waveforms()

    ############################
    ##Spectral Analysis
    ############################
    def capture_sim(self,  sim : Biquad):
        self.update_waveforms()

        sim.update_waveforms(data = self.adcBuffer[0] >> 4)

        return self.extract_biquad(), self.extract_raw(), sim.extract_biquad()

    ## Just incase one wants to use the simBiquad for the same internal captures. Most likely to use for the incremental part
    def extented_capture_sim(self, sim : Biquad, loop=6):
        unfiltered_arr = np.array([])
        filtered_arr = np.array([])

        filtered_arr_sim = np.array([])

        for i in range(loop):
            filtered_arr, unfiltered_arr = self.single_capture(filtered_arr, unfiltered_arr)
            filtered_arr_sim = sim.single_capture(filtered_arr_sim, unfiltered_arr = None, data = self.adcBuffer[0] >> 4)

        filtered_output = Waveform(filtered_arr)
        unfiltered_output = Waveform(unfiltered_arr)
        sim_output = Waveform(filtered_arr_sim)

        del filtered_arr, unfiltered_arr, filtered_arr_sim

        return filtered_output, unfiltered_output, sim_output
    

if __name__ == '__main__':
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

    from RFSoC_Daq import RFSoC_Daq
    from Biquad import Biquad
    from SimBiquad import SimBiquad

    import matplotlib.pyplot as plt

    daq = Biquad_Daq()
    sim = SimBiquad()

    A = 0.8028107634961998
    B = -0.9163499900207577
    P = 0.7782168894289043
    theta = 0.2996203532999784 * np.pi

    daq.update_params(A, B, P, theta)
    daq.quantise_coeffs()
    daq.run_Biquad()
    sim.update_params(A, B, P, theta)
    sim.quantise_coeffs()

    sim.data = daq.adcBuffer[0] >> 4

    # for _ in range(10):
    daq.update_waveforms()
    sim.data = daq.adcBuffer[2] >> 4

    sim.run_IIR()
    sim_output = sim.extract_biquad()


