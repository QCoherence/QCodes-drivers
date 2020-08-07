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

rfsoc.write("ADC:ADC2:MIXER 25.0")
rfsoc.write("ADC:TILE0:DECFACTOR 1")

#generating and loading sequence

chunck_duration=1.e-6

ADCs=[1]
DACs=[]
ctrl_dac_adc=mem.ADC_DAC_status(DACs,ADCs)

N_acq=int((chunck_duration)/0.5e-9)


print("********************************************************************")
print("Number of acq points = {}".format(N_acq))
print("********************************************************************")

# print(ctrl_dac_adc)

seq="SEQ 0,1,10,4115,"+str(N_acq)+",4096,"+str(ctrl_dac_adc)+",1,25000000,3,2"
rfsoc.write(seq)

#acquisition

rfsoc.write("OUTPUT:FORMAT BIN")

rep = rfsoc.query_binary_values('OUTPUT:DATA?', datatype="h", is_big_endian=True)

tstart = time.perf_counter()
tick = 0.5
duree = 0.1
rep=[]

rfsoc.write("ADC:ADC1 1")

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
