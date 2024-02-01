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

## Subdirectory stuff

The app itself consists of a few features that I haven't seen fully
embedded into a Python module yet.

* A Python interactive console inside a Tk widget (pyconsole dir).
  Not perfect yet, but usable. Allows building up auxiliary scripts
  to modify the way the DAQ behaves.

* A logging frame to capture output.

* A tabbed plotting canvas (in progress)

