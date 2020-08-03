from driver_rfsoc import RFSoC
import SequenceGeneration as sqg

rfsoc = RFSoC('RFSoC', 'TCPIP::{}::{}::SOCKET'.format('192.168.0.123',5001))


freq=10.e6
amp=1.
pulse_duration=1.e-6
delay=0.

param=[freq,amp,pulse_duration,delay]

pulse_DAC1=sqg.PulseGeneration(0,5.e-6,'CH1','SIN',param,False)
pulse_DAC2=sqg.PulseGeneration(0,50.e-6,'CH3','SIN', param, False, master=pulse_DAC1)

rfsoc.reset_all_DAC_2D_memory()
rfsoc.send_all_2D_memory()

del rfsoc
