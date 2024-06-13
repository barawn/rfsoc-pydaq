##Python Imports
import tkinter as tk
import numpy as np
from datetime import datetime
import csv

#System Imports
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)

try:
    from Notebook import Notebook
    from Waveform import Waveform
except:
    pass

try:
    from .Notebook import Notebook
    from .Waveform import Waveform
except:
    pass

try:
    from waveframe.Notebook import Notebook
    from waveframe.PlotDisplay import PlotDisplay
    from waveframe.Waveform import Waveform
except:
    pass

class Waveframe(tk.Frame):
    '''
    This is the frame for a particular channel
    
    A notebook with canvases (to be plotted) populate the top
    
    Buttons populate the bottom
    
    The current buttons are:
    
    saveWF which saves the currently plotted waveframe data (timelist and raw adc counts)
    savePlt which saves the current canvases plot (location should be automatic but can be changed)
    enlarge which toggles enlarging the Waveframe instance (allowing easier look at the plot) whilst unpacking other channels quickening acquire time
    plot? which toggles whether the channel will plot or not (which speeds up acquire time for the other channels)
    '''
    def __init__(self,
                 parent: tk.Frame,
                 index: int,
                 title: str,
                 notebookClass: Notebook = Notebook):
        
        self.parent = parent
        self.sampleRate = 3.E9
        self.index = index
        self.title = title
        
        self.enlarged = False
        self.toPlot = True
        
        super().__init__(self.parent)
        
        self.notebook = notebookClass(self, self.parent.figsize)

        self.btns = {}
        
        ##Buttons for the waveform to record stuff and change the view.
        self.btn_frame = tk.Frame(self)
        
        self.btns['SaveWF'] = tk.Button(self.btn_frame, relief="raised", text="SaveWF", command=self.saveWFButton)
        self.btns['SaveWF'].pack(side=tk.LEFT)
        
        self.btns['SavePlt'] = tk.Button(self.btn_frame, relief="raised", text="SavePlt", command=self.SavePlt)
        self.btns['SavePlt'].pack(side=tk.LEFT)
        
        self.btns['Enlarge'] = tk.Button(self.btn_frame, relief="raised", text="Enlarge", command=self.enlargeButton)
        self.btns['Enlarge'].pack(side=tk.LEFT)
        
        self.btns['Plot'] = tk.Button(self.btn_frame, relief="raised", text="Plot?", command=self.plotButton)
        self.btns['Plot'].pack(side=tk.LEFT)
        
        self.btn_frame.pack(side=tk.BOTTOM)
        
        self.pack(fill=tk.BOTH, expand=True)
        
        # Callback signature is data, figure, canvas
        self.user_callback = None
    
    def setWaveform(self, data):
        self.waveform = Waveform(data)
        self.notebook.setWaveform(self.waveform)

    #Saving
    
    def saveName(self, fileType):
        #Needs better automatic naming system
        directory = f"/home/xilinx/rfsoc-pydaq/data/{self.parent.datatype}/{self.parent.directory}/"
        fileName = ""
        if self.parent.saveText:
            fileName = self.title + "_" + self.parent.saveText + fileType
        else:
            fileName = self.title + "_" + datetime.now().strftime("%H-%M-%S_%d-%m-%Y") + fileType
        path = directory+fileName
        logger.debug(f"Saving file to {path}")
        return path
    
    def SavePlt(self):
        current_canvas = self.notebook.getCanvas()
        
        if self.enlarged == False:
            self.btns['Enlarge'].invoke()

        path = self.saveName("figures/", ".png")
        
        quality = 2

        #Makes sure the canvas size is edited. Will edit on GUI as well until image saved
        
        current_canvas.update()

        ps = current_canvas.postscript(colormode='color', pagewidth=self.parent.figsize[0]*400*quality, pageheight=self.parent.figsize[1]*180*quality)

        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img.save(path)
            
        if self.enlarged == True:
            self.btns['Enlarge'].invoke()
        
        logger.debug(f"Saved plot as {path}")
    
    def saveWFButton(self):
        self.saveWF()
        self.setSaveWFName()
    
    def saveWF(self):               ##This method will also be run in main program on a loop
        # datatype = "pulse"
        # directory = "data"
        path = f"/home/xilinx/rfsoc-pydaq/data/{self.parent.datatype}/{self.parent.directory}/dummy.csv"
        
        data = list(zip(self.notebook.waveform.timelist, self.notebook.waveform.waveform))
        
        # data = list(zip(np.arange(len(self.waveForm))/self.sampleRate, self.waveForm))
        
        with open(path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)  
        logger.debug("Waveform data saved")
        return 'Saved Waveform'
    
    
    def setSaveWFName(self):        ##This saves the waveframe with the appropriate name, more like save waveform to name
        # datatype = "pulse"
        # directory = "data"
        pathTemp = f"/home/xilinx/rfsoc-pydaq/data/{self.parent.datatype}/{self.parent.directory}/dummy.csv"
        with open(pathTemp, 'r') as temp_file:
            temp_data = temp_file.readlines()
            
        path = self.saveName(".csv")

        with open(path, 'w', newline='') as new_file:
            new_file.writelines(temp_data)

        # Clear temp.csv
        open(pathTemp, 'w').close()
    
    #Size
    def enlargeButton(self):
        # self.parent.oneFrame(self.index)
        
        #Reset to normal
        if self.btns['Enlarge'].config('relief')[-1] == 'sunken':
            print("Reseting")
            
            self.notebook.ShrinkNotebook()
            
            self.parent.resetFrames()
            
            self.btns['Enlarge'].config(relief="raised")
            
            self.enlarged = False
            
            for waveframe in self.parent.waveframes:
                waveframe.setPlot(True)
            
        #Enlarge this frame
        else:
            print("Enlarging")
            
            self.parent.oneFrame(self.index)
            
            self.btns['Enlarge'].config(relief="sunken")
            
            self.notebook.EnlargeNoteBook()
            
            self.enlarged = True
            
            for waveframe in self.parent.waveframes:
                if waveframe.index != self.index:
                    waveframe.setPlot(False)
            
        logger.debug("Updated the canvas size")
        return 'Updated canvas size' 
    
    #plot?
    def setPlot(self, choice):
        self.toPlot = choice
        if choice == True:
            self.btns['Plot'].config(relief="raised")
        else:
            self.btns['Plot'].config(relief="sunken")
            
    def plotButton(self):        
        if self.btns['Plot'].config('relief')[-1] == 'sunken':
            self.btns['Plot'].config(relief="raised")
            self.toPlot = True
            # for widget in self.parent.winfo_children():
            #     print(widget.index)
        else:
            self.btns['Plot'].config(relief="sunken")
            self.toPlot = False
            
        logger.debug(f"Not plotting frame {self.title}")
        return f'Not plotting frame {self.title}'   
    
if __name__ == "__main__":

    from Waveframes import Waveframes
    
    root = tk.Tk()
    
    numChannels = 1

    setofframes = Waveframes(root, numChannels)
    
    for i in range(numChannels):
        setofframes.addWaveframe(Waveframe(setofframes, i, str(i)))
    
    
    setofframes.pack()
    setofframes.packFrames()
    
    root.mainloop()