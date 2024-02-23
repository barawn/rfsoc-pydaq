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
* the bitstream and HWH that overlay will load. The bitstream should be referenced by _default_ in the Python overlay (see the examples) and the ``.hwh`` needs to be the same name as the bitstream (``my_bitstream.bit`` needs ``my_bitstream.hwh``)
* any additional Python modules/files (e.g. clock programming). Generally just copy the python directory entirely and grab the bitstream/HWH from the hardware export (XSA) from "Export->Hardware". __XSA files are zip files__ , you can pull the files out from there.

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

