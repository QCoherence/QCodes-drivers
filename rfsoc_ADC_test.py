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

rfsoc.write("ADC:ADC2:MIXER 0.")
rfsoc.write("ADC:TILE0:DECFACTOR 1")

#generating and loading sequence

chunck_duration=10.e-6

ADCs=[1]
DACs=[]
ctrl_dac_adc=mem.ADC_DAC_status(DACs,ADCs)

N_acq=int((chunck_duration)/0.5e-9)


print("********************************************************************")
print("Number of acq points = {}".format(N_acq))
print("********************************************************************")

# print(ctrl_dac_adc)

#mode brute ADC2
seq="SEQ 0,1,10,4115,"+str(N_acq)+",4096,"+str(ctrl_dac_adc)+",1,25000000,3,2"
rfsoc.write(seq)

#acquisition

rfsoc.write("OUTPUT:FORMAT BIN")

rep = rfsoc.query_binary_values('OUTPUT:DATA?', datatype="h", is_big_endian=True)

tstart = time.perf_counter()
tick = 0.01
duree = 2
rep=[]

rfsoc.write("ADC:ADC1 1")

# c'est parti pour la durée
rfsoc.write("SEQ:START")
time.sleep(2)
while time.perf_counter()<(tstart+duree):

    time.sleep(tick)
    r = rfsoc.query_binary_values('OUTPUT:DATA?', datatype="h", is_big_endian=True)
    if len(r)>1:
        rep = rep+r

rfsoc.write("SEQ:STOP")

# on demande le dernier paquet et on l'ajoute au précédent
r = rfsoc.query_binary_values('OUTPUT:DATA?', datatype="h", is_big_endian=True)
if len(r)>1:
    rep = rep+r


# decodage des données
# 8 places pour les 8 voies en I & Q
adcdataI = [[],[],[],[],[],[],[],[]]
adcdataQ = [[],[],[],[],[],[],[],[]]
#tsdata= [[],[],[],[],[],[],[],[]]

tstart = time.perf_counter()

i=0
TSMEM=0
while (i + 8 )<= len(rep) : # reste au moins 1 entete

    entete = np.array(rep[i:i+8])
    X =entete.astype('int16').tobytes()
    V = X[0]-1 # voie (1 à 8)
    DSPTYPE = X[1]
    # N n'a pas la meme signification en fonction de DSPTYPE
    N = struct.unpack('I',X[2:6])[0]
    NpCont = X[7]*256 + X[6] # nbre de point si Acquisition en continu, attention relatif à la taille des pts
    TS= struct.unpack('Q',X[8:16])[0]

    # affiche les données de l'entête pour chaque paquet
    print("********************************************************************")
    print("Channel={}; N={}; DSP_type={}; TimeStamp={}; Np_Cont={}; Delta_TimeStamp={}".format(V,N,DSPTYPE,TS,NpCont,TS-TSMEM))
    print("********************************************************************")
    TSMEM=TS

    iStart=i+8
    # si on est pas dans le mode d'acquisition en continu
    if ((DSPTYPE &  0x2)!=2):
        # adcdata brute par bloc de Np points
        if ((DSPTYPE  &  0x1)==0):
            Np=N
            adcdataI[V]=np.concatenate((adcdataI[V], rep[iStart:iStart+Np]))

        # dans le cas du mode accumulation, il y a 1 un seul point I et Q même si le mixer est OFF
        # ce n'est pas du tout optimisé mais on récupère la somme complète
        # mixer ON ou OFF
        if ((DSPTYPE  & 0x01)==0x1):
            Np=8
            D=np.array(rep[iStart:iStart+Np])
            X = D.astype('int16').tobytes()
            # I divisé par N et par 2 car 63 bits alignés à gauche
            I=  struct.unpack('q',X[0:8])[0]/(N*2)
            Q=  struct.unpack('q',X[8:16])[0]/(N*2)
            # on affiche le point
            print("********************************************************************")
            print("I/Q:",I,Q,"Amplitude:",np.sqrt(I*I+Q*Q),"Phase:",180*np.arctan2(I,Q)/np.pi)
            print("********************************************************************")
            adcdataI[V]=np.append(adcdataI[V], I)
            adcdataQ[V]=np.append(adcdataQ[V], Q)

    # mode d'acquition en continu et donc accumulé (pour réduire le débit)
    elif ((DSPTYPE &  0x3)==0x3):
        # mixer OFF : que des I @2Gs/s ou 250Ms/s
        if ((DSPTYPE  & 0x20)==0x0):
            # les pts sont déjà moyennés dans la partie PS
            # ils arrivent au format 16 bits entiers
            Np = NpCont
            adcdataI[V]=np.concatenate((adcdataI[V], rep[iStart:iStart+Np]))

        # mixer ON : I et Q présent
        elif ((DSPTYPE  & 0x20)==0x20):
            Np = NpCont
            adcdataI[V]=np.concatenate((adcdataI[V], rep[iStart:Np:2]))
            adcdataQ[V]=np.concatenate((adcdataQ[V], rep[iStart+1:Np:2]))


    i = iStart+Np # index des prochaines données, nouvel entete...

# temps de traitement du buffer
print("********************************************************************")
print(len(rep),"Pts traités en ",time.perf_counter()-tstart,"secondes")
print("********************************************************************")

# pour le signal ADC ou I
plt.figure()
plt.plot(0.5e-3*np.arange(len(adcdataI[0])),adcdataI[0])
# plt.plot(adcdataI[1])
plt.show()


