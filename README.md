# RFSoC-PyDaq

This is a work-in-progress simple data acquisition system for an
RFSoC system built up from Pynq. Instead of Jupyter notebooks,
we use straight Python, Matplotlib, and Tkinter.

The proper Pynq repository itself does not do a very good job
of attempting to maintain straight Python compatibility. There's
a fork at

https://github.com/barawn/RFSoC-PYNQ-OSU

which attempts to track/fix those issues, but please read the README
there because the build system is disaster upon disaster.

## Screenshot

![Screenshot of RFSoC-PyDaq Running](https://github.com/pueo-pynq/rfsoc-pydaq/blob/main/rfsoc-pydaq-screenshot.png)

## Running

To run rfsoc-pydaq, you need to have a directory which contains
* the Python overlay describing the firmware you're using (e.g. ``zcumts.py``) and anything else it needs. These are usually in the ``python/`` subdirectory.
* the bitstream and HWH that overlay will load.

Launch rfsoc-pydaq. Click the "Load" button and navigate to the directory containing the Python overlay. Select the Python overlay and click Open. This may take a moment,
as it's loading the bitstream and likely configuring clocks.

You can now click "Acquire" to view the ADC inputs of the RFSoC. You can interact with the RFSoC overlay via the Python console: it is called ``daq.dev``. You can
also see the data in the buffer directly in the Python console - it is called ``daq.adcBuffer``. You can plot custom details from that buffer in the User frame
via ``daq.wf[<channel number>].figs['user'].add_subplot(111).plot(<custom data output>)``. In addition, you can create a custom user callback which will _always_ plot
what you're doing in the User frame by passing a function to ``daq.wf[<channel number>].set_user_callback()``. The user callback will be called with the data
(now just a single array, since it's a single channel), the figure, and the canvas.

You can change what the buttons do by accessing ``buttons['Load']``, ``buttons['Acquire']`` and ``buttons['User']``.

## Subdirectory stuff

The app itself consists of a few features that I haven't seen fully
embedded into a Python module yet.

* A Python interactive console inside a Tk widget (pyconsole dir).
  Not perfect yet, but usable. Allows building up auxiliary scripts
  to modify the way the DAQ behaves.

* A logging frame to capture output.

* A tabbed plotting canvas (in progress)

## Stuff I added

![Screenshot of RFSoC-PyDaq Running](https://github.com/pueo-pynq/rfsoc-pydaq/blob/Hugo/pydaqimage.png)

### Features:
StartUp:
* One can run rfsoc-pydaq from anywhere start location (obviously with the appropriate path)
* It will automatically load the zcu bitstream upon startup
* The Frame sizing should be automatic but this has only been tested on a limited displays

MainButtons:
* I do not know if load works if something is automatically loaded
* The Acquire hotkey (F5) or button will run an internal capture
* User doesn't do anythinf
* I couldn't get restart to work, so it doesn't do anything
* Save will save 100 waveforms of the 1st packed Waveframe display. It will plot 1.

ExtraButtons:
* Freq/Fit toggle buttons toggle whether after an internal capture the Frequnecy spectrum FFT and Sine Curve Fit is plotted. This (especially the fit) make running the acquire method take much longer. (Plotting in TKinter is the most time consuming process)

* Set SampleSize allows you to change the sample size as 2^(2 to 14). 
* Set Filename allows you to change the name of the file to be saved. This should be global to the GUI. The pathing may be different depending on the save method. To save say 200_100 you'd have to type "200_100". The scrolled log should output the change

### Waveform:
This was just an easier way of being able to do anything with the ADC buffer data from an internal capture. Each Internal capture will create a Waveform instance. 

This is full of mainly pointless methods. Since most of this should be done in subsequent analysis I've done the terrible practice of initialising instance variables within methods, since an individual waveform instance is unlikley to be running multiple methods and doesn't need all the bloat of unnessasary instance variables.

This is where all of handling of the ADC buffer data should be handled

### Waveframes:
This is a colllection of individual Waveframe. It's main job is just to handle the packing of a Waveframe and store variables that should be the same for each WaveFrame such as the same name


#### Waveframe
This is where the recorded data is displayed. Each Waveframe is made up of a Notebook and a button frame.

#### Notebook
Notebook allows on to have multiple tabs on a display GUI. The plots are controlled by PlotDisplay and PlotCanvas

#### PlotDisplay
This is only necessary to add a canvas to the Notebook. The canvas needs to be within a frame and the frame needs to be added in a particular way. This should automatically do this

#### PlotCanvas
Populate with methods to plot whatever you want. Each individual method is for a single plot

### Waveframe button frame
* SaveWF will save the adc buffer data for that specific waveform sample from the selected ADC channel. The name is detemined by the set filename submit widget
* SavePlt will save the currently open canvas open in the notebook. So either the waveform, FFT, fit etc. To make the image better it will launch the enlarge button. This process takes way longer than one might think. Saving is clearly finised when the Waveframes are repacked as normal. This should save to a Figures directory in data directory.
* Enlarge just allows one to focus on a single channel. The other channel Waveframe instances will be unpakced and won't plot and the chosen channels display will fill the screen. If you are only using one channel this is significantly quicker.
* Plot? toggle whether you want a channels display to plot. Again plotting takes the longest time.


## Notes for the user

Most things can be accessed through the GUI. However the user currently has to change within the code:
* The number of saved waveforms (should be 100 atm)
* The saved directory of the saved waveforms

## Adding to existing
To add a new frame to notebooks
* Within the Notebook constructor add
self.what-frame-will-do_frame = PlotDisplay(self, figsize, "Name of tab in notebook", self.waveform)
* Ensure the waveform is set in method setWaveform
self.what-frame-will-do_frame.updateWaveform(self.waveform)
* Write a plot method within PlotCanvas
* Make sure that the Notebooks plot method is ammended to ensure that it is plotted


