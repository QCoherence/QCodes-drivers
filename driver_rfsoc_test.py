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

#uncomment the following lines when first booting the RFSoC

# rfsoc.write("DAC:RELAY:ALL 0")
# rfsoc.write("PLLINIT")
# time.sleep(5)
# rfsoc.write("DAC:RELAY:ALL 1")


#make sure that no Pulses are defined at the beginning

for inst in sqg.Pulse.objs:
	del inst

#reset the DAC memories
rfsoc.reset_all_DAC_2D_memory()

#define parameters of pulses we want to play
freq1=2.e6
amp1=.7
param1=[freq1,amp1]

freq2=15.e6
amp2=0.5
param2=[freq2,amp2]

#instantiation of pulses
pulse1_DAC1=sqg.PulseGeneration(1e-6,4.e-6,'CH2','SIN',param1,CW_mode=False)
pulse2_DAC1=sqg.PulseGeneration(2.e-6,2.e-6,'CH2','SIN', param2, CW_mode=False, parent=pulse1_DAC1)

pulse_ADC=sqg.PulseReadout(0.,10.e-6,'CH2')

#sending sequence and DAC memories based on the Pulse instances
rfsoc.write_sequence_and_DAC_memory()

#data acquisition
rfsoc.write("OUTPUT:FORMAT BIN")

rep = rfsoc.ask('OUTPUT:DATA?')

tstart = time.perf_counter()
tick = 0.1
duree = 2
rep=[]

#ADC parameters
rfsoc.write("ADC:ADC2:MIXER 0.0")
rfsoc.write("ADC:TILE0:DECFACTOR 1")
rfsoc.write("ADC:ADC2 1")

# beginning of the sequence
rfsoc.write("SEQ:START")
time.sleep(2)
while time.perf_counter()<(tstart+duree):

    time.sleep(tick)
    r = rfsoc.ask('OUTPUT:DATA?')
    if len(r)>1:
        rep = rep+r

rfsoc.write("SEQ:STOP")

# we ask the last packet and add it to the previous
r = rfsoc.ask('OUTPUT:DATA?')
if len(r)>1:
    rep = rep+r

#TODO get a function for data decoding

# data decoding
# 8 I and Q channels
adcdataI = [[],[],[],[],[],[],[],[]]
adcdataQ = [[],[],[],[],[],[],[],[]]
#tsdata= [[],[],[],[],[],[],[],[]]

tstart = time.perf_counter()

i=0
TSMEM=0
while (i + 8 )<= len(rep) : # at least one header left

    entete = np.array(rep[i:i+8])
    X =entete.astype('int16').tobytes()
    V = X[0]-1 # channel (1 to 8)
    DSPTYPE = X[1]
	#N does not have the same meaning depending on DSTYPE
    N = struct.unpack('I',X[2:6])[0]
	#number of acquisition points in continuous
	#depends on the point length
    NpCont = X[7]*256 + X[6]
    TS= struct.unpack('Q',X[8:16])[0]

    # print the header for each packet
    print("Channel={}; N={}; DSP_type={}; TimeStamp={}; Np_Cont={}; Delta_TimeStamp={}".format(V,N,DSPTYPE,TS,NpCont,TS-TSMEM))

    TSMEM=TS

    iStart=i+8
    # if not in continuous acq mode
    if ((DSPTYPE &  0x2)!=2):
        # raw adcdata for each Np points block
        if ((DSPTYPE  &  0x1)==0):
            Np=N
            adcdataI[V]=np.concatenate((adcdataI[V], rep[iStart:iStart+Np]))

		#in the accumulation mode, only 1 I and Q point even w mixer OFF
		#mixer ON or OFF
        if ((DSPTYPE  & 0x01)==0x1):
            Np=8
            D=np.array(rep[iStart:iStart+Np])
            X = D.astype('int16').tobytes()

            #I  dvided N and 2 bcse signed 63 bits aligned to the left
            I=  struct.unpack('q',X[0:8])[0]/(N*2)
            Q=  struct.unpack('q',X[8:16])[0]/(N*2)

            #print the point
            print("I/Q:",I,Q,"Amplitude:",np.sqrt(I*I+Q*Q),"Phase:",180*np.arctan2(I,Q)/np.pi)

            adcdataI[V]=np.append(adcdataI[V], I)
            adcdataQ[V]=np.append(adcdataQ[V], Q)

    # continuoous acquisition mode with accumulation (reduce the flow of data)
    elif ((DSPTYPE &  0x3)==0x3):
        # mixer OFF : onlyI @2Gs/s or 250Ms/s
        if ((DSPTYPE  & 0x20)==0x0):
            # points are already averaged in the PS part
            # format : 16int
            Np = NpCont
            adcdataI[V]=np.concatenate((adcdataI[V], rep[iStart:iStart+Np]))

        # mixer ON : I and Q present
        elif ((DSPTYPE  & 0x20)==0x20):
            Np = NpCont
            adcdataI[V]=np.concatenate((adcdataI[V], rep[iStart:Np:2]))
            adcdataQ[V]=np.concatenate((adcdataQ[V], rep[iStart+1:Np:2]))


    i = iStart+Np # index of the new data block, new header

# buffer treatment time
print("********************************************************************")
print(len(rep),"Pts treated in ",time.perf_counter()-tstart,"seconds")
print("********************************************************************")

#plotting
plt.figure(figsize=(16,8))
plt.plot(0.5e-3*np.arange(len(adcdataI[1])),adcdataI[1])
# plt.plot(adcdataI[1])
plt.show()
