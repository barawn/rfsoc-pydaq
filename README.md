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

DisplayFrame:
* Notebooks can plot the raw wavefrom but also the frequency fft and very rudamentary fitted plot (looks worse in photo due to putting low frequency through high frequency balun, so small signal).
* The plots have labels, legends and potentially stats boxes.
* Each Notebook comes with 4 buttons. SaveWF saves the data to a csv file, SavePlt saves the canvas (very slow in TKinter, this enlarges the frame and then resets), Enlarge is a toggle that enlarges the specified Notebook and blocks other canvases from plotting and 'Plot?' toggles whether the notebook plots.

buttonFrame:
* No real change but now automatically loads in zcuMTS.

toggleFrame:
* This toggles whether the frequency fft and Fitted curve should be plotted, these can ~double the Acquire time.

submitFrame:
* You can change the sample size, only exponents of two since a lot of different inputs of 2 lead to pretty hard crashes (max 14). Don't know why but odd exponents seem to work better.
* Set the file name to save to. Files are saved automatically starting with the full channel name. Afterwards either the date horribly formatted or whatever is typed here. If this is falsey it will go back to the awkward time naming. This name will be for all Notebooks
* Can now press enter to submit the field 

consoleFrame:
* A few new built in methods in the RFSoC_Daq can be accessed here. Most useful ones are automatically run for display

logFrame:
* Many new features will give a log output but some will only do this in the terminal you run ./run-rfsoc-pydaq.sh