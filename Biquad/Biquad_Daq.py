##Python Imports
import numpy as np
import tkinter as tk

#System Imports
import logging

import sys, os

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from RFSoC_Daq import RFSoC_Daq

from widgets.SubmitButton import submitButton

from Biquad import Biquad
from waveframe.Waveframe import Waveframe

from Waveforms.Waveform import Waveform
from Waveforms.Filterred import Filterred
from Waveforms.Gated import Gated

logger = logging.getLogger(__name__)

class Biquad_Daq(RFSoC_Daq, Biquad):
    def __init__(self, root: tk.Tk = None, frame: tk.Frame = None, 
                 numChannels: int = 4, numSamples: int = 2**10, 
                 channelName = ["","","","","","","",""], A=0, B=1, P=0, theta=np.pi):
        RFSoC_Daq.__init__(self, root, frame, numChannels, numSamples, channelName)
        Biquad.__init__(self, A, B, P, theta)

        self.sdv = None
        self.rfsocLoad("zcubiquad")
        # self.run_zeroFIR()

    ############################
    ##Maybe write your code here?
    ############################

    
    ############################
    ##Sets
    ############################
    def setSDV(self, sdv):
        self.sdv = sdv

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

        ##Dfg
        self.sdv.write(0x18, self.calc_18_bit(self.Dfg))

        ##Egg
        self.sdv.write(0x14, self.calc_18_bit(self.Egg))
        for x in reversed(self.Xn[1:]):
            self.sdv.write(0x14, self.calc_18_bit(x))

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
        self.JupyterAcquire()

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
    ##App
    ############################
    
    def submitAValue(self, value):
        A = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the A to: {A}")
        self.setA(A)

    def submitBValue(self, value):
        B = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the B to: {B}")
        self.setB(B)

    def submitPValue(self, value):
        P = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the P to: {P}")
        self.setP(P)

    def submitThetaValue(self, value):
        Theta = self.getSubmitInput(value, True)
        logger.debug(f"You are setting the Theta to: {Theta}")
        self.setTheta(Theta*np.pi)

    def setHotKeys(self):
        super().setHotKeys()
        self.root.bind("<F7>", lambda event: self.update())

    ############################
    ##Display
    ############################

    def setDisplay(self):
        button = self.root.nametowidget("button")
        buttons = {}
        buttons['Update'] = tk.Button(button,
                                text = "Update",
                                command = self.update)
        
        buttons['Update'].grid( row = 0, column=3, padx=5 )

        submit = self.root.nametowidget("submit")
        submits = {}
        submits['SetA'] = submitButton(submit, "Set A:", 0, lambda: self.submitAValue(submits['SetA']), 10)
        submits['SetB'] = submitButton(submit, "Set B:", 1, lambda: self.submitBValue(submits['SetB']), 11)
        submits['SetP'] = submitButton(submit, "Set P:", 0, lambda: self.submitPValue(submits['SetP']), 12)
        submits['SetTheta'] = submitButton(submit, "Set Theta * pi :", 1, lambda: self.submitThetaValue(submits['SetTheta']), 13)
    
    ############################
    ##DAQ Methods
    # I woudln't touch
    ############################

    def rfsocLoad(self, hardware = None):
        super().rfsocLoad(hardware)
        try:
            from serialcobsdevice import SerialCOBSDevice       ###Since this comes from the loaded zcuagc overlay it may not be recognised in vscode without the explicit import 
            self.setSDV(SerialCOBSDevice('/dev/ttyPS1', 1000000))
        except:
            logger.debug("It would appear the overloay you have tried to load doesn't contain SerialCOBSDevice")
        return

    def GuiAcquire(self):
        self.rfsocAcquire()
        arr = [Gated,Gated,Filterred,Filterred]
        for i in range(self.numChannels):
            self.wf.waveframes[i].setWaveform(arr[i](self.adcBuffer[i] >> 4))
            if self.wf.waveframes[i].toPlot == True:
                self.wf.waveframes[i].notebook.plot()
                
        logger.debug("Acquired data and Plotted")

    def JupyterAcquire(self):
        self.rfsocAcquire()
        
        self.waveforms = []
        
        self.waveforms.append(Gated(self.adcBuffer[0] >> 4))
        self.waveforms.append(Gated(self.adcBuffer[1] >> 4))
        self.waveforms.append(Filterred(self.adcBuffer[2] >> 4))
        # self.waveforms.append(Filterred(self.adcBuffer[3] >> 4))

if __name__ == '__main__':
    import sys, os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

    from RFSoC_Daq import RFSoC_Daq
    from Biquad import Biquad

    print(type(RFSoC_Daq))
    print(type(Biquad))

    print(RFSoC_Daq.__class__)
    print(Biquad.__class__)


    daq = Biquad_Daq(None, None, 4, 2**10)