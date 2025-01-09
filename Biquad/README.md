# RFSoC-PyDaq Biquad modules

How the biquad app runs is detailed in the rfsoc-pydaq's readme. This goes into the details about how the python script runs the biquad and also how to run the simulated biquad.

Firstly I did some inheritance stuff which streamlined the code but for some reason more imports need to be explicitly mentioned in jupyter lab.

```python
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))

from RFSoC_Daq import RFSoC_Daq
from Biquad import Biquad
from SimBiquad import SimBiquad
from Biquad_Daq import Biquad_Daq
from Filter import Filter
from Transfer import Transfer
```

## Biquad overview

The biquad has 4 input parameters
- A, effectively a gain coefficient for a notch filter
- B, for a notch filter defined by A and the notch frequency
- P, the strength of the pole
- theta, the pole frequency

P and theta are then used to calculate a number of coefficients and are never used directly.

- Xn's
- Cross links
- Matrix coefficients
- Pole different equation coeffients

Each coefficient is set to zero by default but by writing the coefficients to the firmware the biquad will run that filter until re-written.

The biquad effectively has 5 parts:

- Zero FIR (A, B)
- First Pole FIR (Xn's), (Implemented with the Full pole FIR)
- Pole FIR (Cross Links)
- Pole IIR (Pole Matrix)
- Incremental (Pole Difference equation coefficients), (Firmware not ready and won't work if you try to run in).

The biquads input (and by extension output) is gated to 64 clocks. The current IIR implementations input gate starts at clock 35 and the output starts at clock 53.

## Biquad super class

Every biquad inherits from the biquad superclass Biquad.py. This was meant to be abract by my word did we get a lot of inheritance problems due to meta classes.

The properties are the 4 input parameters of the biquad.

One can update all the coefficients with `_update_coefficients()`, however, coefficients can be updated individually if need be. The calculation of the coefficients has been simplified given the number of samples per clock is 8. Coefficients are only updated automatically if one sets the parameters using `update_params`.

The `calc_q_format(m, n)` can convert data into the chosen Q format.

To make any biquad work one must use the run_ methods

For the biquad DAQ this will write the coefficients to the biquad and you are all set. For the simulation this will simulate that part of the biquad.

## Using the DAQ Biquad

The DAQ biqaud inherits from the RFSoC_DAQ class and the methods to capture data are widely the same.

For the DAQ this might look something like

```python
daq.update_params(**filter.get_params())

daq.generate_waveforms()

daq_output = daq.extract_biquad()
daq_input = daq.extract_raw()
```

The difference between `generate_waveforms()` and `update_waveforms()` is that generate_waveforms re-writes coefficients to the daq. Use generate_waveforms when you are changing the biquads settings. Otherwise update_waveforms is more efficient.

## Using the Simulated Biquad

The DAQ biquad is gated. Due to the fact there is atleast 2 empty clocks at the start and end of each input the simulation hasn't been edited to treat the 'first clock' differently. If you input an array without this buffer it will loop round and use the final two clocks as the previous two clocks. This is not a problem when running along side the DAQ but may be an issue when running the simulation by itself. 

### Use along side DAQ

- Set the data as the DAQs input
- Ensure coefficients have been quantised properly
- Run the simulation
- Extract the data (this is automatically sized to the gate)

Example use:

```python
sim.update_params(**filter.get_params())
sim.data = daq.adcBuffer[0] >> 4
sim.quantise_coeffs()

sim.run_IIR()

sim_output = sim.extract_biquad()
```

### For seperate use

One could always change the simulation to treat the first 2 clocks differently but at the moment one needs a buffer. One should probably also use the waveform type Waveform instead of SimFilter, which is very hardcoded for use with DAQ internal capture inputs. Setting data resets all the intermediate calculations required for the simulation.

Example:
```python
buffer = 5
data = np.zeros((clock_num+buffer) * 8)
data[buffer*8 : (clock_num+buffer)*8] = input_data
biquad.data = data

biquad.run_Biquad()
biquad.extract_biquad(buffer=5)
```

## Filter Class

The filter class is for a notch filter. The biquad firmware is for a notch filter but without appropriate inputs it won't work as one. All instances of the filter class are notch filter's. One simply sets the notch frequency and the quality and the Filter class will use scipy.signal.iirnotch to give a notch filter.

Why the filter. The filter is hard coded so the output parameters will always be a notch filter. Editing a coefficients will still lead to a notch filter. For instances changing A will change B automatically keeping the notch at the same frequency. This will just change the amount of the gain the biquad provides. Or, one can change theta (pole frequency) and P to change the shape of the biquads frequency response. 
The Filter class can also output all the filter data conveniently (worth leaving out of the biquad stuff).

Use of the Filter class:

```python
filter.calc_params(460, 30)
daq.update_params(**filter.get_params())
```