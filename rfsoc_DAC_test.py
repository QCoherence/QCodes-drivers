import pyvisa
import time
import numpy as np
from numpy.fft import fft
import matplotlib.pyplot as plt
import struct
import math
import DAC_memory_test as mem
#
# fileseq= open(r"E:\rfSoc_Set\test_1.scpi","r+")
# fileseq= open(r"E:\rfSoc_Set\adc1_cont.scpi","r+")
#
# seq=fileseq.read()
# fileseq.close()
rm = pyvisa.ResourceManager()
rfsoc = rm.open_resource('TCPIP::{}::{}::SOCKET'.format('192.168.0.123',5001), read_termination = '\r\n')
print(rfsoc.query("*IDN?"))

# init de la carte & synchro des ADC /DAC

rfsoc.write("SEQ:STOP")

# rfsoc.write("DAC:RELAY:ALL 0")
# rfsoc.write("PLLINIT")
# time.sleep(5)
# rfsoc.write("DAC:RELAY:ALL 1")

rfsoc.write('DAC:DATA:CH1:CLEAR')
rfsoc.write('DAC:DATA:CH2:CLEAR')

freq=1.e6
amp=1.
pulse_duration=2.e-6
delay=0.
trigger='NONE'

param=[freq,amp,pulse_duration,delay]

mem2D=mem.fill_2D_memory('SIN',param,trigger) 

serv=mem.send_DAC_2D_memory(mem2D,'CH2',pulse_duration,'CW')

rfsoc.write(serv)


adress = int(round(16384 - pulse_duration/(4.e-9)))

#CW sequence 
rfsoc.write("SEQ 0,1,10,4105,"+str(adress)+",4096,27")

# # pulses sequence
# rfsoc.write('SEQ 0,1,10,4105,0,4096,7190235,1,550,3,1')

rfsoc.write("SEQ:START")
 
