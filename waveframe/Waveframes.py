##Python Imports
import tkinter as tk

from screeninfo import get_monitors

#System Imports
import logging

logger = logging.getLogger(__name__)

try:
    from Waveframe import Waveframe
except:
    pass

try:
    from .Waveframe import Waveframe
except:
    pass

try:
    from waveframe.Waveframe import Waveframe
except:
    pass


class Waveframes(tk.Frame):
    '''
    This contains the individual channel frames.
    
    This is mainly used since it is a lot easier to manage channel packing.
    
    Also certain attributes are the same for all individual waveframes and don't need multiple (i.e. 4) initialisations
    '''
    def __init__(self,
                 parent: tk.Frame,
                 numChannels: int):
        super().__init__(parent)
        
        self.parent = parent

        self.numChannels = numChannels
        
        self.waveframes = []
        self.packed = []
        
        self.saveText = "Temp"
        self.directory = "/pulse/testWidth/"
        
        monitors = get_monitors()
        main_display = monitors[0]

        screen_width = main_display.width
        screen_height = main_display.height

        self.plotExtras = {"fft":False}

        self.figsize=(screen_width/(100*self.numChannels), screen_height/250)

    ##Framing
    def addWaveframe(self, waveframe: Waveframe):
        self.waveframes.append(waveframe)
        self.packed.append(False)
        
    def packFrames(self):
        for i, waveframe in enumerate(self.waveframes):
            waveframe.pack(side = tk.LEFT )
            self.packed[i] = True
            
    def unpackFrames(self):
        for i, waveframe in enumerate(self.waveframes):
            if self.packed[i] == True:
                waveframe.forget()
                self.packed[i] = False
        
    def oneFrame(self, index):
        for i, waveframe in enumerate(self.waveframes):
            if i==index:
                if self.packed[i] == False:
                    waveframe.pack(side = tk.LEFT )
            elif i!=index:
                if self.packed[i] == True:
                    waveframe.forget()
                    
    def resetFrames(self):
        self.unpackFrames()
        
        self.packFrames()
        
if __name__ == "__main__":
    
    root = tk.Tk()
    
    numChannels = 2

    setofframes = Waveframes(root, numChannels)
    
    for i in range(numChannels):
        setofframes.addWaveframe(Waveframe(setofframes, i, str(i)))
    
    
    setofframes.pack()
    setofframes.packFrames()
    setofframes.unpackFrames()
    setofframes.packFrames()
    
    root.mainloop()