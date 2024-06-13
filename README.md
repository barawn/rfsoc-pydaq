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

## New, most usable version yet!!!

One should run with root. Can use sudo -i to get to root.

Running app.py, will launch the TKinter GUI with the RFSoC_Daq class embedded.

This is the super Daq class that contains all the useful basics for all firmware overlays loaded into the daq.dev

The Daq class will store the Waveframes class that holds multiple Waveframe classes. These waveframe classes store the core GUI of the DAQ. The waveframe most importantly contains a tk.Notebook class called Notebook which will automatically manage, pack and dipslay plots that it gets from the PlotDipslay class that holds plots from the PlotsCanvas class (also in PlotDisplay.py). The managing of the waveform data is managed within Waveform class.

### You the User!

Ideally the only parts of the main program you should be editing is PlotCanvas, to add new plot method, and Waveform (though I am tempted to have this be a superclass that particular firmware/testing type directories have a derived class within), to add new data analyse techniques (this is were the FFT and etc are done)

To use RFSoC-PyDAQ for you're own purposes:
* Choose/make a directory for you intended purpose (say AGC)
* Make a derived class of RFSoC_Daq (called name_Daq) to house core methods (such as runAGC unique to testing AGC firmware)
* Maybe make another derived class of e.g. AGC_Daq called name_Test. This can store new unproven methods and leave a nice clean python file to edit on emacs locally on the FPGA if say you don't have you FPGA connected to the labnetwork/internet. 
* If you feel the plots are not adequete for your task add a derived Notebook class that can add more plots to your Daq GUI. (New plots will need to be added as a method to PlotCanvas). You would only need to override the plot method in the derived Notebook. The rest is just general canvas managment stuff

One can also override methods from RFSoC_Daq such as: 
* Having the load method automatically load the appropriate overlay
* StartWaveFrames method have the modules own notebook loaded
* Have acquire automatically format ADC buffer data
* More idk

Oh yeah and you will have to edit the config file and add to the method getDaq in app.py if you are adding two much stuff

### What this assumes

* That you save data in /home/xilinx/data
* That your loading overlay


### Current issues

* Since moving everything around a tonne the scrolled log no longer works. Log inputs still put in terminal but needs to be fixed.

* Since I wrote this on my laptop and the OSU ZCU-111 doesn't have internet some troubleshooting to actually make this work on an FPGA might have slipped through when testing on the OSU zcu-111 and not be added to the git repo from my laptop. Also some methods or implementation won't be in the repo. Also certain save methods that previous worked have not been retested. Will have to wait to test on fully connected to lab-network and internet UCL zcu-111 to properly test the migration of all features. What I'm trying to say is the thing works but some auxillary functionality isn't fully tested yet