import time
import numpy as np
import ctypes  # only for DLL-based instrument

import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
                    ManualParameter, MultiParameter,
                    validators as vals)
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter

import SequenceGeneration as sqg
from qcodes.utils.delaykeyboardinterrupt import DelayedKeyboardInterrupt
import struct


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
                           val_mapping={'on': 1, 'off': 0}
                           )

        #TODO : add allowed values of decimation and mixer frea
        self.add_parameter(name='decfact',
                           label='ADC{} decimation factor'.format(self._adc_channel),
                           #the decimation works by tiles of two adcs
                           set_cmd='ADC:TILE{}:DECFACTOR {}'.format((self._adc_channel-1)//2,'{:d}')
                           )

        self.add_parameter(name='fmixer',
                           label = 'ADC{} mixer frequency'.format(self._adc_channel),
                           set_cmd='ADC:ADC{}:MIXER {}'.format(self._adc_channel,'{:.4f}')
                           )

        self.add_parameter(name='mode',
                           label='ADC{} acquisition mode'.format(self._adc_channel),
                           vals = vals.Enum('RAW','SUM'),)




class RFSoC(VisaInstrument):

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__
    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every
        # response
        super().__init__(name, address, terminator='\r\n', **kwargs)

        #Add the channel to the instrument
        for adc_num in np.arange(1,9):

            adc_name='ADC{}'.format(adc_num)
            adc=AcqChannel(self,adc_name,adc_num)
            self.add_submodule(adc_name, adc)


        self.add_parameter('nb_measure',
                            set_cmd='{}',
                            get_parser=int,
                            initial_value = int(1))

        self.add_parameter( name = 'output_format', 
                            #Format(string) : 'BIN' or 'ASCII' 
                            label='Output format',
                            vals = vals.Enum('ASCII','BIN'),
                            set_cmd='OUTPUT:FORMAT ' + '{}',
                            get_cmd='OUTPUT:FORMAT?',
                            #snapshot_get  = False,
                            get_parser=str )


    def reset_sequence(self):
    	'''
    		Delete all instances of the Pulse class from the sqg module
    	'''
    	for inst in sqg.Pulse.objs:
    		del inst

    def write_sequence_and_DAC_memory(self):

        self.log.info(__name__+ ' sending sequence'+'  \n')
        self.write(sqg.Pulse.generate_sequence_and_DAC_memory())

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




    def ask_raw(self, cmd: str) -> str:
        """
        Overwriting the ask_raw qcodes native function to query binary

        Low-level interface to ``visa_handle.ask``.

        Args:
            cmd: The command to send to the instrument.

        Returns:
            str: The instrument's response.
        """
        with DelayedKeyboardInterrupt():
            self.visa_log.debug(f"Querying: {cmd}")
            response = self.visa_handle.query_binary_values(cmd, datatype="h", is_big_endian=True)
            self.visa_log.debug(f"Response: {response}")
        return response

    def reset_PLL(self):

    	self.write("DAC:RELAY:ALL 0")
    	self.write("PLLINIT")
    	time.sleep(5)
    	self.write("DAC:RELAY:ALL 1")

    def reset_output_data(self):

    	self.ask('OUTPUT:DATA?')

    def run_and_get_data(self):

        rep=self.ask("OUTPUT:DATA?")

        tstart = time.perf_counter()
        tick = 0.1
        duree = 2
        rep=[]

        # beginning of the sequence
        self.write("SEQ:START")
        time.sleep(2)
        while time.perf_counter()<(tstart+duree):

            time.sleep(tick)
            r = self.ask('OUTPUT:DATA?')
            if len(r)>1:
                rep = rep+r

        self.write("SEQ:STOP")

        # we ask the last packet and add it to the previous

        r = self.ask('OUTPUT:DATA?')
        if len(r)>1:
           rep = rep+r

        # data decoding
        # 8 I and Q channels
        adcdataI = [[],[],[],[],[],[],[],[]]
        adcdataQ = [[],[],[],[],[],[],[],[]]

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

        return adcdataI,adcdataQ




