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

## Running

RFSoC-PyDaq has been altered.

Since all the overlays where all the same, zcumts will be exlcusively used, but the bitfile name will changed. The zcumts.py is also included.

All bit streams are expected to be written in the form zcu111_<name of bit file>.bit . Now that I think about it, some people may not be using the zcu111 development board so ~2 lines will have to be alterred for that purpose.

The overlay is what actually connects to the FPGA and writes the firmware, standard, agc, biquad, etc.

To run rfsoc-pydaq, you need to have a directory which contains
* the Python overlay describing the firmware you're using (e.g. ``zcumts.py``) and anything else it needs.
* the bitstream and HWH that overlay will load.

To run the overlay one needs to be in root access. Therefore I'd suggest running terminal_setup.sh and navigate to your local rfsoc-pydaq directory

`./terminal_setup.sh`

This should also setup environmental requiremnts to run any TKinter GUI

From here simply
`python Daq_of_somekind.py`
and it should run fine


## Key Differences
* The daq module is simply seperate from any GUI
* The GUI now emulates a oscilloscope
* I broke the logger but fixed it here (worth mentioning)
* Only one overlay, now input bitstream name


## Basic Structure
* A daq is defined by
* * It's bitstream
* * The number of samples (maximum 2^14) taken per internal capture
* * The channel names
* Bitsteam name can be changed for the basic daq but firmware specific daqs like biquad_daq will automatically run the biquad firmware. I had called mine zcu111_iir.bit so this might have to be altered
* Number of samples can be changed at any time, however when the overlay is loaded, the adc memory will be defined by current value and will act as a maximum sample size. This was done since the biquad is limited to ~900 samples and the adc memory storing ~16,000 was a bit of a waste. Once loaded the adc memory size is not dynamic. Adc memory is passed to an adc buffer (whose size is the sample size). This is the raw adc output which is the wrong bit width.
* Channel names should be a size 4 array of strings or None. None means the daq will effectively and permanently (in the class instance) ignore that channel. For instance only the first two output channels do anything anyway. Otherwise the names are used to tag the waveforms and label plots.
* Waveform Class(es):
The waveform class takes the corrected bit width of the adc output. Any waveform instance has access to useful methods, particularly containing to fourier transforms and the biquad_daqs waveforms automatically size to the ~64 clock gated output. All 4 waveform instances are stored in the field waveforms as an array of class instances
* Internal captures will update channel waveform instances and in the GUI update the plots
* The daq has two class instances at it's disposal
* * self.dev which is the zcuMTS instance that communicates directly with the daq.
* * self.sdv which is a serial cobs device instance which is used to read and write directly with the firmware (setting biquad parameters)
* There is a basic App_GUI.py class that handles all the basic GUI elements required for all Daq_app's. This should be instantiated within a Daq_app class constructor
* Daq_app's inherit from there 'mother-daq' and should only implement app_GUI and specific GUI elements (such as setting biquad parameters)

## Using RFSoC's GUI
The GUI consists of 4 elements
* Oscilloscope
* * Display
* * Settings (which includes the DAQ settings)
* Console
* Log

For this general Daq one must load a bitstream with the load button (default zcu111_top.bit). Afterwards load functionality will disappear because two overlays can't be used at once and you can't restart zocl whilst an overlay is running

One can toggle what channels they want plotting. All data is taking regardless. If you toggle a field and want it reflected in the plots press update.

Pressing Acquire will update the waveform instances, update the plot setting and plot the new waveforms

Within the console the daq (whichever one is using) is called daq. Here one can access daq.dev, write using daq.sdv.write and access the waveforms

The log is mainly here to confirm user inputs

![Screenshot of RFSoC-PyDaq Running](https://github.com/pueo-pynq/rfsoc-pydaq/blob/rework/images/PyDaq.png)


# AGC

The agc runs like the basic daq but only the first two channels will run anything (agc output, raw input)

The main parameters that change in the agc are it's scaling (0x10) and offest (0x14) which are daq properties .scaling and .offset. The agc must be loaded in and applied before it can work (automatically done setting paramters) and then run. This comes from the run_AGC method and the imaginatively named AGC button in the GUI. 

Within the GUI pressing start_PID_Loop will start the active gain control so any inputs have the same amplitude. This should not freeze the rest of the GUI. My FPGA's physical output isn't currently working but this worked last time I ran it through an actual oscilloscope. One can always run the pid_loop methods within the daq.


![Screenshot of AGC-PyDaq Running](https://github.com/pueo-pynq/rfsoc-pydaq/blob/rework/images/AGC_PyDaq.png)


# Biquad

The biquad daq inherits from the biquad class as well. A sim biquad was necessary for testigng and it creates a unified method scheme. Also it handles all the biquad programming in a neat place aware for data aquisition

The biquad is defined by 4 parameters which in term calculate many coefficients. _update_coefficients must be run for the biquad to reflect changes in the coefficients. Also coefficient calculation as been simplified under the assumption of 8 samples per clock. If this changes this will have to reflect those changes. You can also set these coefficients directly

The biquad has 4 sections to run

* Running the zero fir
* Running the pole fir
* Running the pole iir
* Running the incremental (the firmware doens't exist yet but the Daq is setup for when it does)

All these will need to be run to get the expected output

Worth noting the filtered waveform may be configured to 64 clocks which will cut off additional waveform generated from the iir. This can be edited.

![Screenshot of Biquad-PyDaq Running](https://github.com/pueo-pynq/rfsoc-pydaq/blob/rework/images/Biquad_PyDaq.png)