import pyvisa
import time
import numpy as np
from numpy.fft import fft
import matplotlib.pyplot as plt
import struct
import math
from driver_rfsoc import RFSoC
import SequenceGeneration as sqg

rfsoc = RFSoC('RFSoC', 'TCPIP::{}::{}::SOCKET'.format('192.168.0.123',5001))

rfsoc.write("SEQ:STOP")

# rfsoc.write("DAC:RELAY:ALL 0")
# rfsoc.write("PLLINIT")
# time.sleep(5)
# rfsoc.write("DAC:RELAY:ALL 1")


for inst in sqg.Pulse.objs:
	del inst

rfsoc.reset_all_DAC_2D_memory()

freq=0.5e6
amp=1.


param=[freq,amp]

pulse1_DAC1=sqg.PulseGeneration(2.e-6,4.e-6,'CH2','SIN',param,CW_mode=False)
# pulse2_DAC1=sqg.PulseGeneration(2.e-6,3.e-6,'CH2','SIN', [freq,amp,10.e-6,delay], CW_mode=False, parent=pulse1_DAC1)


rfsoc.write_sequence_and_DAC_memory()
print(sqg.Pulse.generate_sequence_and_DAC_memory())      

rfsoc.write("SEQ:START")



