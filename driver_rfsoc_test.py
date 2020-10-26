import pyvisa
import time
import numpy as np
from numpy.fft import fft
import matplotlib.pyplot as plt
import struct
import math
from driver_rfsoc_channel import RFSoC
import SequenceGeneration as sqg

rfsoc = RFSoC('RFSoC', 'TCPIP::{}::{}::SOCKET'.format('192.168.0.123',5001))

rfsoc.write("SEQ:STOP")

#uncomment the following lines when first booting the RFSoC

# rfsoc.reset_PLL()

#make sure that no Pulses are defined at the beginning

rfsoc.reset_sequence()

#reset the DAC memories
rfsoc.reset_all_DAC_2D_memory()

#define parameters of pulses we want to play
freq1=4.e6
amp1=1.
param1=[freq1,amp1]

freq2=1.e6
amp2=0.5
param2=[freq2,amp2]

#instantiation of pulses
pulse1_DAC1=sqg.PulseGeneration(0.5e-6,4.e-6,'CH2','SIN',param1,CW_mode=False)
# pulse2_DAC1=sqg.PulseGeneration(2.e-6,2.e-6,'CH2','SIN', param2, CW_mode=False, parent=pulse1_DAC1)

#factor 8 to reduce number of points for decimation 
pulse_ADC=sqg.PulseReadout(1.e-6 / 8,6.e-6 / 8,'CH2','RAW')

#nb of measures
rfsoc.nb_measure(20)

#sending sequence and DAC memories based on the Pulse instances
rfsoc.write_sequence_and_DAC_memory()

#data acquisition
rfsoc.write("OUTPUT:FORMAT BIN")

rfsoc.reset_output_data()

#ADC parameters
# rfsoc.write("ADC:ADC2:MIXER 0.0")
# rfsoc.write("ADC:TILE0:DECFACTOR 8")
rfsoc.ADC2.fmixer(0.0)
rfsoc.ADC2.decfact(8)
rfsoc.ADC2.status("on")

adcdataI, adcdataQ = rfsoc.run_and_get_data()

#plotting
plt.figure(figsize=(16,8))
plt.plot(0.5e-3*np.arange(len(adcdataI[1])),adcdataI[1])
# plt.plot(adcdataI[1])
plt.show()
