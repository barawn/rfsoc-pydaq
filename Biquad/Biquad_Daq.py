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
    def __init__(self, sample_size: int = 200*8, 
                 channel_names = ["ADC224_T0_CH0", "ADC224_T0_CH1", "Biquad_Output", None], A=0, B=1, P=0, theta=np.pi):
        RFSoC_Daq.__init__(self, sample_size, channel_names)
        Biquad.__init__(self, A, B, P, theta)

        super().rfsocLoad('iir')

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

    ############################
    ##Extracts
    ############################
    def extract_raw(self):
        return self.waveforms[0]

    def extract_biquad(self):
        return self.waveforms[2]

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

if __name__ == '__main__':
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

    from RFSoC_Daq import RFSoC_Daq
    from Biquad import Biquad

    daq = Biquad_Daq()


    print("\nStandard biquad setup (i.e. 1 sample delay) : ")
    daq.run_Biquad()
    # print(daq.waveforms[0].calc_rms())
    # print(daq.waveforms[2].calc_rms())


    print("\nSetting A = 7 (expect gain) : ")
    daq.A=7

    daq.run_Biquad()
    # print(daq.waveforms[0].calc_rms())
    # print(daq.waveforms[2].calc_rms())

    # print('\n')
    # print(len(daq.waveforms[0]))
    # print(len(daq.waveforms[2]))

    print("Relevant Stuff")

    clocks = daq.waveforms[2].waveform.reshape(-1, 8)
    print(daq.waveforms[2].find_first_clock(clocks))
    clock = 130
    print(daq.waveforms[2].waveform[clock*8:(clock+64)*8])
