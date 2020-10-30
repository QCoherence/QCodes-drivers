import time
import numpy as np
import sys
import struct
import ctypes  # only for DLL-based instrument

import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
                    ManualParameter, MultiParameter,
                    validators as vals)
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter

import SequenceGeneration_v2 as sqg
from qcodes.utils.delaykeyboardinterrupt import DelayedKeyboardInterrupt



class RAW(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._channel = self._instrument._adc_channel

    def get_raw(self):
        time.sleep(0.2)

        dataI, dataQ = self._instrument._parent.get_single_readout_pulse()

        print(self._channel)
        if self._channel in np.arange(1,9):
            data_ret = dataI[self._channel-1]
        else:
            print('Wrong parameter.')

        return data_ret

class RAW_ALL(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_raw(self):
        time.sleep(0.2)

        dataI, dataQ = self._instrument.get_readout_pulse()

        data_ret = dataI

        return data_ret

class IQINT(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._channel = self._instrument._adc_channel

    def get_raw(self):
        time.sleep(0.2)

        dataI, dataQ = self._instrument._parent.get_single_readout_pulse()

        print(self._channel)
        if self._channel in np.arange(1,9):
            data_retI = dataI[self._channel-1]
            data_retQ = dataQ[self._channel-1]
        else:
            print('Wrong parameter.')

        return data_retI, data_retQ

class IQINT_ALL(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def get_raw(self):
        time.sleep(0.2)

        data_retI, data_retQ = self._instrument.get_readout_pulse()

        return data_retI, data_retQ


class IQINT_AVG(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._channel = self._instrument._adc_channel

    def get_raw(self):
        time.sleep(0.2)

        dataI, dataQ = self._instrument._parent.get_single_readout_pulse()

        print(self._channel)
        if self._channel in np.arange(1,9):
            data_retI = np.mean(dataI[self._channel-1])
            data_retQ = np.mean(dataQ[self._channel-1])
        else:
            print('Wrong parameter.')

        return data_retI, data_retQ



#TODO : add the different results we would return
class AcqChannel(InstrumentChannel):

    #initializing the array storing channel instances
    objs = []

    def __init__(self, parent: 'RFSoC', name: str, channel: int):

        """
        Args:
            parent: Instrument that this channel is bound to.
            name: Name to use for this channel.
            channel: channel on the card to use
        """
        if channel not in np.arange(1,9):
            raise ValueError('channel number must be in between 1 and 8')

        self._adc_channel = channel

        super().__init__(parent, name)

        AcqChannel.objs.append(self)

        self.add_parameter(name='status',
                           label = 'ADC{} status'.format(self._adc_channel),
                           set_cmd='ADC:ADC{} {}'.format(self._adc_channel,'{:d}'),
                           val_mapping={'ON': 1, 'OFF': 0},
                           initial_value='OFF'
                           )

        #TODO : add allowed values of decimation and mixer frea
        self.add_parameter(name='decfact',
                           label='ADC{} decimation factor'.format(self._adc_channel),
                           #the decimation works by tiles of two adcs
                           set_cmd='ADC:TILE{}:DECFACTOR {}'.format((self._adc_channel-1)//2,'{:d}'),

                           )

        self.add_parameter(name='fmixer',
                           label = 'ADC{} mixer frequency'.format(self._adc_channel),
                           set_cmd='ADC:ADC{}:MIXER {}'.format(self._adc_channel,'{:.4f}'),
                           )

        self.add_parameter(name='RAW',
                           unit='V',
                           label='Channel {}'.format(self._adc_channel),
                           channel=self._adc_channel,
                           parameter_class=RAW)

        self.add_parameter(name='IQINT',
                           unit='V',
                           label='Channel {}'.format(self._adc_channel),
                           channel=self._adc_channel,
                           parameter_class=IQINT)

        self.add_parameter(name='IQINT_AVG',
                           unit='V',
                           label='Integrated averaged I Q for channel {}'.format(self._adc_channel),
                           channel=self._adc_channel,
                           parameter_class=IQINT_AVG)
        self.status('OFF')

class RFSoC(VisaInstrument):

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__
    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every
        # response
        super().__init__(name, address, terminator='\r\n', **kwargs)

        # reset PLL
        self.reset_PLL()

        #Add the channel to the instrument
        for adc_num in np.arange(1,9):

            adc_name='ADC{}'.format(adc_num)
            adc=AcqChannel(self,adc_name,adc_num)
            self.add_submodule(adc_name, adc)

        #parameters to store the events of a sequence directly as a parameter of the instrument
        self.add_parameter('events',
                            set_cmd='{}',
                            get_parser=list,
                            initial_value=[])

        self.add_parameter('DAC_events',
                            set_cmd='{}',
                            get_parser=list,
                            initial_value=[])

        self.add_parameter('ADC_events',
                            set_cmd='{}',
                            get_parser=list,
                            initial_value=[])

        self.add_parameter('nb_measure',
                            set_cmd='{}',
                            get_parser=int,
                            initial_value = int(1))

        self.add_parameter('acquisition_mode',
                            label='ADCs acquisition mode',
                            set_cmd='{}',
                            get_parser=str,
                            vals = vals.Enum('RAW','SUM')
                            )

        self.add_parameter( name = 'output_format',
                            #Format(string) : 'BIN' or 'ASCII'
                            label='Output format',
                            vals = vals.Enum('ASCII','BIN'),
                            set_cmd='OUTPUT:FORMAT ' + '{}',
                            get_cmd='OUTPUT:FORMAT?',
                            #snapshot_get  = False,
                            get_parser=str )

        self.add_parameter(name='RAW_ALL',
                           unit='V',
                           label='Raw adc for all channel',
                           parameter_class=RAW_ALL)

        self.add_parameter(name='IQINT_ALL',
                           unit='V',
                           label='Integrated averaged I Q for all channels',
                           parameter_class=IQINT_ALL)

        #for now all mixer frequency must be multiples of the base frequency for phase matching
        self.add_parameter(name='base_fmixer',
                           unit='MHz',
                           label='Reference frequency for all mixers',
                           set_cmd='{}',
                           get_parser=float)

        # self.add_parameter(name = 'DC_offset',
        #                     unit = 'V',
        #                     label = 'DC offset list for all channels',
        #                     get_parser = list,
        #                     parameter_class = ManualParameter)


    def write_sequence_and_DAC_memory(self):

        self.log.info(__name__+ ' sending sequence'+'  \n')
        self.write(sqg.Pulse.generate_sequence_and_DAC_memory(self.nb_measure.get()-1,self.acquisition_mode.get(),self.base_fmixer.get()))

        for obj in sqg.PulseGeneration.objs:

            self.log.info(__name__+ ' sending DAC {} 2D memory'.format(obj.channel)+'  \n')
            self.write(obj._DAC_2D_memory)


    def reset_DAC_2D_memory(self, channel):
        """
            Reset the 2D memory of one DAC

            Input : - channel of the DAC we wantto reset
        """

        self.log.info(__name__+ ' reset the 2D memory of DAC channel'+ channel+'  \n')

        if channel in ['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8']:

            self.write("DAC:DATA:{}:CLEAR".format(channel))

        else:
            raise ValueError('Wrong channel value')


    def reset_all_DAC_2D_memory(self):
        """
            Reset the 2D memory of all the DACs
        """
        for channel in ['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8']:

            self.write("DAC:DATA:{}:CLEAR".format(channel))


    def reset_PLL(self):

        self.write("DAC:RELAY:ALL 0")
        self.write("PLLINIT")
        time.sleep(5)
        self.write("DAC:RELAY:ALL 1")


    def reset_output_data(self):

        self.ask('OUTPUT:DATA?')


    def adc_events(self):
        '''
        will be used to organize the data saving
        '''
        sorted_seq=np.array(sqg.Pulse.sort_and_groupby_timewise()).flatten()
        mask=[type(p) is sqg.PulseReadout for p in sorted_seq]

        sorted_adcs=sorted_seq[mask]

        #store the nb of acq point for each unique event of each channel
        length_vec=[[],[],[],[],[],[],[],[]]

        N_adc_events=len(sorted_adcs)

        #ch vec list of the order of adc ch measured in one loop of the sequence
        ch_vec=np.zeros(N_adc_events,dtype=int)

        for i in range(len(sorted_adcs)):

            length_vec[int(sorted_adcs[i].channel[2])-1].append(int(round((sorted_adcs[i].t_duration)/0.5e-9)))

            ch_vec[i]=int(sorted_adcs[i].channel[2])-1

        return(length_vec,ch_vec)




    def get_readout_pulse(self):

        '''

         This function reformat the data without looping over all the headers by trusting that 
         what we set is what we get.
         It also assumes that within a sequence every ADC pulses have the same length.

        '''

        self.reset_output_data()

        #for now we consider only the one same type of acq on all adc
        mode=self.acquisition_mode.get()

        nb_measure=self.nb_measure.get()

        length_vec,ch_vec=self.adc_events()
        
        N_adc_events=len(ch_vec)
        N_acq=np.sum(np.sum(length_vec))
        
        #same acquisition length for all ADCs
        N_acq_single=int(round(N_acq/N_adc_events))

         
        # 8 I and Q channels
        adcdataI = [[],[],[],[],[],[],[],[]]
        adcdataQ = [[],[],[],[],[],[],[],[]]

        tstart = time.perf_counter()
        tick = 0.1
        duree = 2

        rep=[]
        count_meas=0

        if mode=='SUM':

            self.write("SEQ:START")
            time.sleep(0.1)

            while count_meas==0:

                r = self.ask('OUTPUT:DATA?')

                if len(r)>1:
                    rep = rep+r
                    #to modify manually depending on what we

                    # count_meas+=len(r)//(16*N_adc_events)


                elif r==[3338]:

                    # count_meas=nb_measure
                    count_meas=1

        if mode=='RAW':

            self.write("SEQ:START")
            time.sleep(0.1)


            while count_meas==0:

                r = self.ask('OUTPUT:DATA?')

                if len(r)>1:
                    print(len(r))
                    rep = rep+r
                    #to modify manually depending on what we
                    #TODO : figure a way to do it auto depending on the adcs ons and their modes
                    #now for 1 ADC in accum
                    # count_meas+=len(r)//16
                    # count_meas+=len(r)//((8+N_acq))


                elif r==[3338]:

                    # count_meas=nb_measure
                    count_meas=1


        # while time.perf_counter()<(tstart+duree):

        #     time.sleep(tick)
        #     r = self.ask('OUTPUT:DATA?')
        #     if len(r)>1:
        #         rep = rep+r

        self.write("SEQ:STOP")
        #we ask for last packet and add it
        r = self.ask('OUTPUT:DATA?')
        if len(r)>1:
                rep = rep+r

        rep=np.array(rep,dtype=int)
        #data decoding
        if mode is 'RAW':

            # removing headers

            mask = np.ones(len(rep), dtype=bool) #initialize array storing which items to keep

            starts = np.arange(0, len(rep), N_acq_single + 8)
            # print(starts)
            indices=np.arange(8) + starts[:,np.newaxis] #indeces of headers datapoints
            indices=indices.flatten()
            # print(indices)
            mask[indices]=False

            res=np.right_shift(rep[mask],4)*(2*0.3838e-3)

            res=np.split(res,nb_measure)

            res=np.mean(res,axis=0)

            res=np.split(res,N_adc_events)

            for i in range(len(ch_vec)):

                adcdataI[ch_vec[i]].append(res[i])


        if mode is 'SUM':

            # removing headers

            mask = np.ones(len(rep), dtype=bool) #initialize array storing which items to keep

            starts = np.arange(0, len(rep), 8 + 8)

            indices=np.arange(8) + starts[:,np.newaxis] #indices of headers datapoints
            indices=indices.flatten()

            mask[indices]=False

            res=rep[mask]

            print('len(res)={}'.format(len(res)))

            #format for unpacking
            fmt='q'*nb_measure
       
            for i in range(len(ch_vec)):

                maskI= np.zeros(len(res), dtype=bool) #initialize array storing which items to keep
                maskQ= np.zeros(len(res), dtype=bool) #initialize array storing which items to keep

                starts= np.arange(8*i,len(res), len(ch_vec)*8 )

                indicesI=np.arange(4) + starts[:,np.newaxis]
                
                indicesI=indicesI.flatten()

                indicesQ=np.arange(4) + starts[:,np.newaxis] 
                indicesQ=indicesQ.flatten() + 4    

                maskI[indicesI]=True
                maskQ[indicesQ]=True

                newI=res[maskI].astype('int16').tobytes()
                newQ=res[maskQ].astype('int16').tobytes()

                print('len(newI)={}'.format(len(newI)))
                print('len(newQ)={}'.format(len(newQ)))

                newI=np.array(struct.unpack(fmt,newI))*(2*0.3838e-3)/(N_acq_single*2*8)
                newQ=np.array(struct.unpack(fmt,newQ))*(2*0.3838e-3)/(N_acq_single*2*8)
                # newI=np.array(struct.unpack(fmt,newI))/(N_acq_single*2)
                # newQ=np.array(struct.unpack(fmt,newQ))/(N_acq_single*2)
              

                adcdataI[ch_vec[i]].append(newI)
                adcdataQ[ch_vec[i]].append(newQ)
              

        return adcdataI,adcdataQ


    def ask_raw(self, cmd: str) -> str:
            """
            Overwriting the ask_ray qcodes native function to query binary
            Low-level interface to ``visa_handle.ask``.
            Args:
                cmd: The command to send to the instrument.
            Returns:
                str: The instrument's response.
            """
            with DelayedKeyboardInterrupt():
                keep_trying = True
                count = 0
                while keep_trying:
                    count += 1
                    self.visa_log.debug(f"Querying: {cmd}")
                    try:
                        response = self.visa_handle.query_binary_values(cmd, datatype="h", is_big_endian=True)
                        self.visa_log.debug(f"Response: {response}")
                    except:
                        response = 'ERR'
                    if response != 'ERR' and response != [3338]:
                        keep_trying = False
                    if count>10:
                        keep_trying = False

            return response



    def get_readout_pulse_loop(self):
            '''
            This function uses loop over all the data array to read the dsp type and parameters
            If the regular fast decoding behaviour is weird check using this function
            Very long for high nb of measurements 
            '''
            self.reset_output_data()

            #for now we consider only the one same type of acq on all adc
            mode=self.acquisition_mode.get()

            ch_vec,length_vec=self.adc_events()

            N_adc_events=len(ch_vec)

            N_acq=np.sum(np.sum(length_vec))

            # print('N_acq={}'.format(N_acq))

            # 8 I and Q channels
            adcdataI = [[],[],[],[],[],[],[],[]]
            adcdataQ = [[],[],[],[],[],[],[],[]]

            tstart = time.perf_counter()
            tick = 0.1
            duree = 2

            rep=[]
            count_meas=0

            if mode=='SUM':

                self.write("SEQ:START")
                time.sleep(0.1)

                while count_meas<self.nb_measure.get():

                    r = self.ask('OUTPUT:DATA?')

                    if len(r)>1:
                        rep = rep+r
                        #to modify manually depending on what we

                        count_meas+=len(r)//(16*N_adc_events)


                    elif r==[3338]:

                        count_meas=self.nb_measure.get()

            if mode=='RAW':

                self.write("SEQ:START")
                time.sleep(0.1)

                # print(self.nb_measure.get())
                while count_meas<self.nb_measure.get():

                    r = self.ask('OUTPUT:DATA?')

                    if len(r)>1:
                        # print(len(r))
                        rep = rep+r
                        #to modify manually depending on what we
                        #TODO : figure a way to do it auto depending on the adcs ons and their modes
                        #now for 1 ADC in accum
                        # count_meas+=len(r)//16
                        count_meas+=len(r)//((8+N_acq))


                    elif r==[3338]:

                        count_meas=self.nb_measure.get()



            # while time.perf_counter()<(tstart+duree):

            #     time.sleep(tick)
            #     r = self.ask('OUTPUT:DATA?')
            #     if len(r)>1:
            #         rep = rep+r

            self.write("SEQ:STOP")
            #we ask for last packet and add it
            r = self.ask('OUTPUT:DATA?')
            if len(r)>1:
                    rep = rep+r

            # data decoding
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
                # print("Channel={}; N={}; DSP_type={}; TimeStamp={}; Np_Cont={}; Delta_TimeStamp={}".format(V,N,DSPTYPE,TS,NpCont,TS-TSMEM))

                TSMEM=TS

                iStart=i+8
                # if not in continuous acq mode
                if ((DSPTYPE &  0x2)!=2):
                    # raw adcdata for each Np points block
                    if ((DSPTYPE  &  0x1)==0):
                        Np=N
                        adcdataI[V]=np.concatenate((adcdataI[V], np.right_shift(rep[iStart:iStart+Np],4)*0.3838e-3))

                    #in the accumulation mode, only 1 I and Q point even w mixer OFF
                    #mixer ON or OFF
                    if ((DSPTYPE  & 0x01)==0x1):
                        Np=8
                        D=np.array(rep[iStart:iStart+Np])
                        X = D.astype('int16').tobytes()

                        #I  dvided N and 2 bcse signed 63 bits aligned to the left
                        I=  struct.unpack('q',X[0:8])[0]*(0.3838e-3)/(N*2)
                        Q=  struct.unpack('q',X[8:16])[0]*(0.3838e-3)/(N*2)

                        #print the point
                        # print("I/Q:",I,Q,"Amplitude:",np.sqrt(I*I+Q*Q),"Phase:",180*np.arctan2(I,Q)/np.pi)

                        adcdataI[V]=np.append(adcdataI[V], I)
                        adcdataQ[V]=np.append(adcdataQ[V], Q)


                #in our case we dont need the continuous mode for now
                # continuoous acquisition mode with accumulation (reduce the flow of data)
                elif ((DSPTYPE &  0x3)==0x3):
                    # mixer OFF : onlyI @2Gs/s or 250Ms/s
                    if ((DSPTYPE  & 0x20)==0x0):
                        # points are already averaged in the PS part
                        # format : 16int
                        Np = NpCont
                        adcdataI[V]=np.concatenate((adcdataI[V], np.right_shift(rep[iStart:iStart+Np],4)*0.3838e-3))

                    # mixer ON : I and Q present
                    elif ((DSPTYPE  & 0x20)==0x20):
                        Np = NpCont
                        adcdataI[V]=np.concatenate((adcdataI[V],np.right_shift(rep[iStart:Np:2],4)*0.3838e-3))
                        adcdataQ[V]=np.concatenate((adcdataQ[V], np.right_shift(rep[iStart+1:Np:2],4)*0.3838e-3))


                i = iStart+Np # index of the new data block, new header

            # print("********************************************************************")
            # print(len(rep),"Pts treated in ",time.perf_counter()-tstart,"seconds")
            # print("********************************************************************")

            #reshaping results

            if mode=='SUM':

                adcdataI=[np.array(adcdataI[v]).reshape(self.nb_measure.get(),len(length_vec[v])).T for v in range(8)]
                adcdataQ=[np.array(adcdataQ[v]).reshape(self.nb_measure.get(),len(length_vec[v])).T for v in range(8)]


            if mode=='RAW':

                adcdataI=[np.array(adcdataI[v]).reshape(self.nb_measure.get(),np.sum(length_vec[v],dtype=int)) for v in range(8)]

                # adcdataI=[np.array(adcdataI[v]).reshape(self.nb_measure.get(),np.sum(np.sum(ch[v],dtype=int))) for v in range(8)]
                adcdataI=[np.mean(adcdataI[v],axis=0) for v in range(8)]

                adcdataI=np.array([np.split(adcdataI[v],[sum(length_vec[v][0:i+1]) for i in range(len(length_vec[v]))]) for v in range(8)])

            return adcdataI,adcdataQ


    # def get_single_readout_pulse(self):

    #     self.reset_output_data()

    #     print(self.ADC_events.get())

    #     if len(self.ADC_events.get())>1:

    #         raise ValueError('Need only one readout pulse in the sequence for this function')

    #     else :

    #         readout=self.ADC_events.get()[0]

    #     #pick up the parameters of the wanted ADC
    #     ch=readout.channel
    #     ch_obj=getattr(self,'ADC'+ch[2])

    #     fmix=ch_obj.fmixer.get()
    #     decfactor=ch_obj.decfact.get()
    #     mode=self.acquisition_mode.get()

    #     N_acq=int((readout.t_duration)/0.5e-9)
    #     #Ethernet data transfer
    #     t_wait=(N_acq)*16.e-9
    #     N_wait=int((t_wait)/0.5e-9)

    #     # 8 I and Q channels
    #     adcdataI = [[],[],[],[],[],[],[],[]]
    #     adcdataQ = [[],[],[],[],[],[],[],[]]


    #     tick = 0.1
    #     duree = 2

    #     print('mode is {}'.format(mode))
    #     count_meas=0
    #     print('count_meas={}'.format(count_meas))
    #     rep=[]

    #     if mode=='SUM':

    #         self.write("SEQ:START")
    #         time.sleep(0.1)

    #         while count_meas is not 1:

    #             r = self.ask('OUTPUT:DATA?')

    #             if len(r)>1:
    #                 rep = rep+r
    #                 #to modify manually depending on what we
    #                 #TODO : figure a way to do it auto depending on the adcs ons and their modes
    #                 #now for 1 ADC in accum

    #             elif r==[3338]:

    #                 count_meas=1

    #     if mode=='RAW':

    #         self.write("SEQ:START")
    #         time.sleep(0.1)


    #         while count_meas is not 1:

    #             r = self.ask('OUTPUT:DATA?')

    #             if len(r)>1:
    #                 print(len(r))
    #                 rep = rep+r
    #                 #to modify manually depending on what we
    #                 #TODO : figure a way to do it auto depending on the adcs ons and their modes
    #                 #now for 1 ADC in accum

    #             elif r==[3338]:
    #                 count_meas=1



    #     # while time.perf_counter()<(tstart+duree):

    #     #     time.sleep(tick)
    #     #     r = self.ask('OUTPUT:DATA?')
    #     #     if len(r)>1:
    #     #         rep = rep+r

    #     self.write("SEQ:STOP")
    #     #we ask for last packet and add it
    #     r = self.ask('OUTPUT:DATA?')
    #     if len(r)>1:
    #             rep = rep+r

    #     # data decoding
    #     tstart = time.perf_counter()
    #     i=0
    #     TSMEM=0
    #     while (i + 8 )<= len(rep) : # at least one header left

    #         entete = np.array(rep[i:i+8])
    #         X =entete.astype('int16').tobytes()
    #         V = X[0]-1 # channel (1 to 8)
    #         DSPTYPE = X[1]
    #         #N does not have the same meaning depending on DSTYPE
    #         N = struct.unpack('I',X[2:6])[0]
    #         #number of acquisition points in continuous
    #         #depends on the point length
    #         NpCont = X[7]*256 + X[6]
    #         TS= struct.unpack('Q',X[8:16])[0]

    #         # print the header for each packet
    #         # print("Channel={}; N={}; DSP_type={}; TimeStamp={}; Np_Cont={}; Delta_TimeStamp={}".format(V,N,DSPTYPE,TS,NpCont,TS-TSMEM))

    #         TSMEM=TS

    #         iStart=i+8
    #         # if not in continuous acq mode
    #         if ((DSPTYPE &  0x2)!=2):
    #             # raw adcdata for each Np points block
    #             if ((DSPTYPE  &  0x1)==0):
    #                 Np=N
    #                 adcdataI[V]=np.concatenate((adcdataI[V], np.right_shift(rep[iStart:iStart+Np],4)*0.3838e-3))

    #             #in the accumulation mode, only 1 I and Q point even w mixer OFF
    #             #mixer ON or OFF
    #             if ((DSPTYPE  & 0x01)==0x1):
    #                 Np=8
    #                 D=np.array(rep[iStart:iStart+Np])
    #                 X = D.astype('int16').tobytes()

    #                 #I  dvided N and 2 bcse signed 63 bits aligned to the left
    #                 I=  struct.unpack('q',X[0:8])[0]*(0.3838e-3)/(N*2)
    #                 Q=  struct.unpack('q',X[8:16])[0]*(0.3838e-3)/(N*2)

    #                 #print the point
    #                 # print("I/Q:",I,Q,"Amplitude:",np.sqrt(I*I+Q*Q),"Phase:",180*np.arctan2(I,Q)/np.pi)

    #                 adcdataI[V]=np.append(adcdataI[V], I)
    #                 adcdataQ[V]=np.append(adcdataQ[V], Q)

    #         # continuoous acquisition mode with accumulation (reduce the flow of data)
    #         elif ((DSPTYPE &  0x3)==0x3):
    #             # mixer OFF : onlyI @2Gs/s or 250Ms/s
    #             if ((DSPTYPE  & 0x20)==0x0):
    #                 # points are already averaged in the PS part
    #                 # format : 16int
    #                 Np = NpCont
    #                 adcdataI[V]=np.concatenate((adcdataI[V], np.right_shift(rep[iStart:iStart+Np],4)*0.3838e-3))

    #             # mixer ON : I and Q present
    #             elif ((DSPTYPE  & 0x20)==0x20):
    #                 Np = NpCont
    #                 adcdataI[V]=np.concatenate((adcdataI[V],np.right_shift(rep[iStart:Np:2],4)*0.3838e-3))
    #                 adcdataQ[V]=np.concatenate((adcdataQ[V], np.right_shift(rep[iStart+1:Np:2],4)*0.3838e-3))


    #         i = iStart+Np # index of the new data block, new header

    #     print("********************************************************************")
    #     print(len(rep),"Pts treated in ",time.perf_counter()-tstart,"seconds")
    #     print("********************************************************************")


    #     return adcdataI,adcdataQ
