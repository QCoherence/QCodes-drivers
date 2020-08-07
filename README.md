# RFSoC QCoDeS driver development

This repository is dedicated to the devolopment of a QCoDeS driver for the ADC/DAC instrument developped at Institut Néel based on Xilinx RFSoC.

### Zynq UltraScale+ RFSoC : 

https://www.xilinx.com/products/silicon-devices/soc/rfsoc.html


### QCoDeS Python package : 

Qcodes is a Python-based data acquisition framework for physics experiments !
https://qcodes.github.io/Qcodes/

## Driver :

So far the driver uses the *SequenceGenerator.py* module as well as the *driver_rfsoc.py* file. The *driver_rfsoc_test.py* is used to test the driver.
Some scripts for testing the card without using te driver can be found in the test/ADC-tests branch
