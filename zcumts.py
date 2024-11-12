from pynq import Overlay, GPIO, MMIO
import time
import os
import subprocess
import zcurfclk
import numpy as np

class zcuMTS(Overlay):
    def __init__(self, bitfile_name='zcu111_top.bit', **kwargs):

        # Check whether zocl is working
        output = subprocess.check_output(['lsmod'])
        if b'zocl' in output:
            rmmod_output = subprocess.run(['rmmod', 'zocl'])
            assert rmmod_output.returncode == 0, "Could not restart zocl. Please Shutdown All Kernels and then restart"
            modprobe_output = subprocess.run(['modprobe', 'zocl'])
            assert modprobe_output.returncode == 0, "Could not restart zocl. It did not restart as expected"
        else:
            modprobe_output = subprocess.run(['modprobe', 'zocl'])
            assert modprobe_output.returncode == 0, "Could not restart ZOCL!"

        # Setup up firmware

        zcurfclk.set_rf_clks(lmkfn='ZCU111_LMK_24.txt',lmxfn='ZCU111_LMX.txt')

        self.gpio_trig = GPIO(GPIO.get_gpio_pin(0), 'out')
        self.gpio_done = [ GPIO(GPIO.get_gpio_pin(8), 'in'),
                           GPIO(GPIO.get_gpio_pin(9), 'in'),
                           GPIO(GPIO.get_gpio_pin(10), 'in'),
                           GPIO(GPIO.get_gpio_pin(11), 'in'),
                           GPIO(GPIO.get_gpio_pin(12), 'in'),
                           GPIO(GPIO.get_gpio_pin(13), 'in'),
                           GPIO(GPIO.get_gpio_pin(14), 'in'),
                           GPIO(GPIO.get_gpio_pin(15), 'in') ]

        super().__init__(resolve_binary_path(bitfile_name), **kwargs)

        self.dbg = self.debug_bridge_0

        self.adcIP = ["adc_cap_0/axi_bram_ctrl_0", 
                      "adc_cap_1/axi_bram_ctrl_0", 
                      "adc_cap_2/axi_bram_ctrl_0", 
                      "adc_cap_3/axi_bram_ctrl_0"]
        
        self.adc_memory = []
        
    def init_adc_memory(self, channels, range = None):
        for i, channel in enumerate(channels):
            if channel != None and channel != "":
                self.adc_memory.append(self.memdict_to_view(ip = self.adcIP[i], range = range))
            else:
                self.adc_memory.append(None)
    
    def memdict_to_view(self, ip, dtype='int16', range = None):
        """ Configures access to internal memory via MMIO"""
        baseAddress = self.mem_dict[ip]["phys_addr"]
        mem_range = self.mem_dict[ip]["addr_range"] #range if range is not None else self.mem_dict[ip]["addr_range"]
        ipmmio = MMIO(baseAddress, mem_range)
        return ipmmio.array[0:ipmmio.length].view(dtype)
    
    # pointless
    def verify_clock_tree(self):
        return True

    # THIS DOES NOTHING FOR NOW
    def sync_tiles(self, dacTarget=-1, adcTarget=-1):
        return

    # THIS DOES NOTHING FOR NOW
    def init_tile_sync(self):
        return
    
    def internal_capture(self, buf):
        if not np.issubdtype(buf.dtype, np.int16):
            raise Exception("buffer not defined or np.int16")
        
        self.gpio_trig.write(1)
        self.gpio_trig.write(0)
        for i in range(4):
            if self.adc_memory[i] is not None:
                buf[i] = np.copy(self.adc_memory[i][0:len(buf[i])])
            
def resolve_binary_path(bitfile_name):
    """ this helper function is necessary to locate the bit file during overlay loading"""
    MODULE_PATH = '/home/xilinx/python/'
    if os.path.isfile(bitfile_name):
        return bitfile_name
    elif os.path.isfile(os.path.join(MODULE_PATH, bitfile_name)):
        return os.path.join(MODULE_PATH, bitfile_name)
    else:
        raise FileNotFoundError(f'Cannot find {bitfile_name}.')
    