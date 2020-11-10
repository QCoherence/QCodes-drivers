import time
import datetime
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
from qcodes.utils.validators import Numbers, Arrays

import logging
log = logging.getLogger(__name__)





class GeneratedSetPoints(Parameter):
	"""
	A parameter that generates a setpoint array from start, stop and num points
	parameters.
	"""
	def __init__(self, startparam, stopparam, numpointsparam, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._startparam = startparam
		self._stopparam = stopparam 
		self._numpointsparam = numpointsparam

	def get_raw(self):
		return np.linspace(self._startparam(), self._stopparam() -1,
							  self._numpointsparam())


class RAW(Parameter):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._channel = self._instrument._adc_channel

	def get_raw(self):
		time.sleep(0.2)

		dataI, dataQ = self._instrument._parent.get_single_readout_pulse()

		# print(self._channel)
		if self._channel in np.arange(1,9):
			data_ret = dataI[self._channel-1]
		else:
			log.warning('Wrong parameter.')

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

		# print(self._channel)
		if self._channel in np.arange(1,9):
			data_retI = dataI[self._channel-1]
			data_retQ = dataQ[self._channel-1]
		else:
			log.warning('Wrong parameter.')

		return data_retI, data_retQ


class IQINT_ALL(Parameter):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


	def get_raw(self):
		time.sleep(0.2)

		data_retI, data_retQ = self._instrument.get_readout_pulse()

		return data_retI, data_retQ


class IQINT_ALL_read_header(Parameter):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


	def get_raw(self):
		time.sleep(0.2)

		data_retI, data_retQ = self._instrument.get_readout_pulse()

		return data_retI, data_retQ


class IQINT_AVG(Parameter): 

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def get_raw(self):

		time.sleep(0.2)

		data_retI, data_retQ = self._instrument.get_readout_pulse()#.get_readout_pulse() ###### Martina 08/11/2020

		Sq_I = [[],[],[],[],[],[],[],[]]
		Sq_Q = [[],[],[],[],[],[],[],[]]

		Sq_I_list = [[],[],[],[],[],[],[],[]]
		Sq_Q_list = [[],[],[],[],[],[],[],[]]

		for i in range(8):

			if len(data_retI[i])>0:

				for j in range(len(data_retI[i])):

					if len(data_retI[i][j])>0:

						Sq_I[i] = np.append(Sq_I[i],np.mean(data_retI[i][j]))
						Sq_Q[i] = np.append(Sq_Q[i],np.mean(data_retQ[i][j]))
						Sq_I_list[i].append(np.mean(data_retI[i][j]))
						Sq_Q_list[i].append(np.mean(data_retQ[i][j]))
								
		for i in range(8):
			
			Sq_I[i] = np.array(Sq_I_list[i])
			Sq_Q[i] = np.array(Sq_Q_list[i])

		return Sq_I,Sq_Q


class ADC_power(ParameterWithSetpoints):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def get_raw(self):

		Sq_I = [[],[],[],[],[],[],[],[]]
		Sq_Q = [[],[],[],[],[],[],[],[]]
		PSD = [[],[],[],[],[],[],[],[]]

		time.sleep(0.2)

		data_retI, data_retQ = self._instrument.get_readout_pulse()

		for i in range(8):

			if len(data_retI[i])>0:

				Sq_I[i] = data_retI[i][0]**2
				Sq_Q[i] = data_retQ[i][0]**2

				PSD[i] = [np.mean(Sq_I[i]+Sq_Q[i])/50]

		for i in range(8):

			if len(PSD[i]) == 0:

				PSD[i] = 0

			else:

				PSD[i] = PSD[i][0]

		return np.array(PSD)











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
						   initial_value='OFF',
						   snapshot_value = False
						   )

		#TODO : add allowed values of decimation and mixer frea
		self.add_parameter(name='decfact',
						   label='ADC{} decimation factor'.format(self._adc_channel),
						   #the decimation works by tiles of two adcs
						   set_cmd='ADC:TILE{}:DECFACTOR {}'.format((self._adc_channel-1)//2,'{:d}'),
						   snapshot_value = False
						   )

		self.add_parameter(name='fmixer',
						   label = 'ADC{} mixer frequency'.format(self._adc_channel),
						   set_cmd='ADC:ADC{}:MIXER {}'.format(self._adc_channel,'{:.4f}'),
						   get_parser = self.MHz_to_Hz,
						   set_parser = self.Hz_to_MHz,
						   snapshot_value = False
						   )

		self.add_parameter(name='RAW',
						   unit='V',
						   label='Channel {}'.format(self._adc_channel),
						   channel=self._adc_channel,
						   parameter_class=RAW,
						   snapshot_value = False
						   )

		self.add_parameter(name='IQINT',
						   unit='V',
						   label='Channel {}'.format(self._adc_channel),
						   channel=self._adc_channel,
						   parameter_class=IQINT,
						   snapshot_value = False)

		self.add_parameter(name='IQINT_AVG',
						   unit='V',
						   label='Integrated averaged I Q for channel {}'.format(self._adc_channel),
						   channel=self._adc_channel,
						   parameter_class=IQINT_AVG,
						   snapshot_value = False)
		self.status('OFF')

	def MHz_to_Hz(self,value):
		return value*1e6

	def Hz_to_MHz(self,value):
		return value*1e-6

class RFSoC(VisaInstrument):

	# all instrument constructors should accept **kwargs and pass them on to
	# super().__init__
	def __init__(self, name, address, **kwargs):
		# supplying the terminator means you don't need to remove it from every
		# response
		super().__init__(name, address, terminator='\r\n', **kwargs)

		# reset PLL
		# self.reset_PLL()

		self.dummy_array_size_8 = 8

		#Add the channel to the instrument
		for adc_num in np.arange(1,9):

			adc_name='ADC{}'.format(adc_num)
			adc=AcqChannel(self,adc_name,adc_num)
			self.add_submodule(adc_name, adc)

		#parameters to store the events of a sequence directly as a parameter of the instrument
		self.add_parameter('events',
							get_parser=list,
							initial_value=[],
							parameter_class=ManualParameter)

		self.add_parameter('DAC_events',
							get_parser=list,
							initial_value=[],
							parameter_class=ManualParameter)

		self.add_parameter('ADC_events',
							get_parser=list,
							initial_value=[],
							parameter_class=ManualParameter)

		self.add_parameter('nb_measure',
							get_parser=int,
							initial_value = int(1),
							parameter_class=ManualParameter)

		self.add_parameter('acquisition_mode',
							label='ADCs acquisition mode',
							get_parser=str,
							vals = vals.Enum('RAW','SUM'),
							parameter_class=ManualParameter
							)

		self.add_parameter( name = 'output_format',
							#Format(string) : 'BIN' or 'ASCII'
							label='Output format',
							vals = vals.Enum('ASCII','BIN'),
							set_cmd='OUTPUT:FORMAT ' + '{}',
							get_cmd='OUTPUT:FORMAT?',
							#snapshot_get  = False,
							get_parser=str,
							snapshot_value = False)

		self.add_parameter(name='RAW_ALL',
						   unit='V',
						   label='Raw adc for all channel',
						   parameter_class=RAW_ALL,
						   snapshot_value = False)

		self.add_parameter(name='IQINT_ALL',
						   unit='V',
						   label='Integrated I Q for all channels',
						   parameter_class=IQINT_ALL,
						   snapshot_value = False)

		self.add_parameter(name='IQINT_ALL_read_header',
						   unit='V',
						   label='Integrated I Q for all channels with header check',
						   parameter_class=IQINT_ALL_read_header,
						   snapshot_value = False)

		self.add_parameter(name='IQINT_AVG',
						   unit='V',
						   label='Integrated averaged I Q for all channels',
						   parameter_class=IQINT_AVG,
                           vals=Arrays(shape=(2, 8, 2)), ### ME
						   snapshot_value = False)

		self.add_parameter('channel_axis',
							unit = 'channel index',
							label = 'Channel index axis for ADC power mode',
							parameter_class = GeneratedSetPoints,
							startparam = self.int_0,
							stopparam = self.int_8,
							numpointsparam = self.int_8,
							snapshot_value = False,
							vals=Arrays(shape=(self.dummy_array_size_8,))
							)

		self.add_parameter(name='ADC_power',
						   unit='W',
						   setpoints=(self.channel_axis,),
						   label='Array of incident power on ADC channels, (works only in single pulse sequence)',
						   parameter_class=ADC_power,
						   vals=Arrays(shape=(self.dummy_array_size_8,)),
						   snapshot_value = False)

		#for now all mixer frequency must be multiples of the base frequency for phase matching
		self.add_parameter(name='base_fmixer',
						   unit='Hz',
						   label='Reference frequency for all mixers',
						   get_parser=float,
						   parameter_class=ManualParameter,
						   snapshot_value = False)

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
		sorted_seq=np.array(sqg.Pulse.sort_and_groupby_timewise())
		
		# sorted_seq=np.array(sqg.Pulse.sort_and_groupby_timewise()).flatten()
		sorted_seq=np.concatenate( sorted_seq, axis=0 )
		# print('sorted_seq={}'.format(sorted_seq))

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
		 This function reformat the data reading the header contents.
		'''

		self.reset_output_data()
		mode = self.acquisition_mode()
		nb_measure = self.nb_measure()
		length_vec,ch_vec = self.adc_events()
		N_adc_events = len(ch_vec)
		n_pulses = len(length_vec[0])
		
		if mode == 'SUM':
			'''
				Get data
			'''
			N_acq = np.sum(np.sum(length_vec))

			data_unsorted = []
			count_meas = 0
			empty_packet_count = 0

			self.write("SEQ:START")
			time.sleep(0.1)

			while (count_meas//(16*N_adc_events))<self.nb_measure.get():

				r = self.ask('OUTPUT:DATA?')

				if r == 'ERR':

					log.error('rfSoC: Instrument returned ERR!')

					# reset measurement
					data_unsorted = []
					count_meas = 0
					empty_packet_count = 0
					self.write("SEQ:STOP")
					time.sleep(2)
					while True:
						junk = self.ask('OUTPUT:DATA?')
						# print(junk)
						time.sleep(0.1)
						if junk == [3338]:
							break
					junk = []
					self.write("SEQ:START")
					time.sleep(0.1)

					continue

				elif len(r)>1:

					empty_packet_count = 0
					# print(datetime.datetime.now())
					data_unsorted = data_unsorted+r
					# print(datetime.datetime.now(),'\n')
					count_meas+=len(r)


				elif r == [3338]:

					empty_packet_count += 1
					time.sleep(0.5)

				if empty_packet_count>20:

					log.warning('Data curruption: rfSoC did not send all data points({}).'.format(count_meas//(16*N_adc_events)))
					
					# reset measurement
					data_unsorted = []
					count_meas = 0
					empty_packet_count = 0
					self.write("SEQ:STOP")
					time.sleep(2)
					while True:
						junk = self.ask('OUTPUT:DATA?')
						# print(junk)
						time.sleep(0.1)
						if junk == [3338]:
							break
					junk = []
					self.write("SEQ:START")
					time.sleep(0.1)

					continue

			self.write("SEQ:STOP")

			'''
				Process data
			'''

			data_unsorted = np.array(data_unsorted,dtype=int)

			raw_IQ_data_dump_header = data_unsorted.reshape(int(len(data_unsorted)/8),8)[0::2]
			raw_I_data_dump_data = data_unsorted.reshape(int(len(data_unsorted)/8),8)[1::2][:,0:4]
			raw_Q_data_dump_data = data_unsorted.reshape(int(len(data_unsorted)/8),8)[1::2][:,4:8]

			ch_num = (raw_IQ_data_dump_header%256).T[0]
			num_points = (raw_IQ_data_dump_header).T[1]+256*(raw_IQ_data_dump_header).T[2]
			ch_1 = ch_num*(ch_num == np.ones(len(ch_num)))
			ch_2 = ch_num*(ch_num == 2*np.ones(len(ch_num)))/2
			ch_3 = ch_num*(ch_num == 3*np.ones(len(ch_num)))/3
			ch_4 = ch_num*(ch_num == 4*np.ones(len(ch_num)))/4
			ch_5 = ch_num*(ch_num == 5*np.ones(len(ch_num)))/5
			ch_6 = ch_num*(ch_num == 6*np.ones(len(ch_num)))/6
			ch_7 = ch_num*(ch_num == 7*np.ones(len(ch_num)))/7
			ch_8 = ch_num*(ch_num == 8*np.ones(len(ch_num)))/8

			#data conversion
			I_all_data = 2 + np.frombuffer(raw_I_data_dump_data.astype('int16').tobytes(), dtype=np.longlong)*(0.3838e-3/16)/num_points
			Q_all_data = 2 + np.frombuffer(raw_Q_data_dump_data.astype('int16').tobytes(), dtype=np.longlong)*(0.3838e-3/16)/num_points

			I_all_data*ch_1

			I = [np.split((I_all_data*ch_1)[I_all_data*ch_1!=0]-2,n_pulses),
				 np.split((I_all_data*ch_2)[I_all_data*ch_2!=0]-2,n_pulses),
				 np.split((I_all_data*ch_3)[I_all_data*ch_3!=0]-2,n_pulses),
				 np.split((I_all_data*ch_4)[I_all_data*ch_4!=0]-2,n_pulses),
				 np.split((I_all_data*ch_5)[I_all_data*ch_5!=0]-2,n_pulses),
				 np.split((I_all_data*ch_6)[I_all_data*ch_6!=0]-2,n_pulses),
				 np.split((I_all_data*ch_7)[I_all_data*ch_7!=0]-2,n_pulses),
				 np.split((I_all_data*ch_8)[I_all_data*ch_8!=0]-2,n_pulses)]
			Q = [np.split((Q_all_data*ch_1)[Q_all_data*ch_1!=0]-2,n_pulses),
				 np.split((Q_all_data*ch_2)[Q_all_data*ch_2!=0]-2,n_pulses),
				 np.split((Q_all_data*ch_3)[Q_all_data*ch_3!=0]-2,n_pulses),
				 np.split((Q_all_data*ch_4)[Q_all_data*ch_4!=0]-2,n_pulses),
				 np.split((Q_all_data*ch_5)[Q_all_data*ch_5!=0]-2,n_pulses),
				 np.split((Q_all_data*ch_6)[Q_all_data*ch_6!=0]-2,n_pulses),
				 np.split((Q_all_data*ch_7)[Q_all_data*ch_7!=0]-2,n_pulses),
				 np.split((Q_all_data*ch_8)[Q_all_data*ch_8!=0]-2,n_pulses)]

		elif mode == 'RAW':

			# '''
			# 	Get data
			# '''
			# N_acq = np.sum(np.sum(length_vec))

			# data_unsorted = []
			# count_meas = 0
			# empty_packet_count = 0

			# self.write("SEQ:START")
			# time.sleep(0.1)

			# while (count_meas//(16*N_adc_events))<self.nb_measure.get():

			# 	r = self.ask('OUTPUT:DATA?')

			# 	if r == 'ERR':

			# 		log.error('rfSoC: Instrument returned ERR!')

			# 		# reset measurement
			# 		data_unsorted = []
			# 		count_meas = 0
			# 		empty_packet_count = 0
			# 		self.write("SEQ:STOP")
			# 		time.sleep(2)
			# 		while True:
			# 			junk = self.ask('OUTPUT:DATA?')
			# 			# print(junk)
			# 			time.sleep(0.1)
			# 			if junk == [3338]:
			# 				break
			# 		junk = []
			# 		self.write("SEQ:START")
			# 		time.sleep(0.1)

			# 		continue

			# 	elif len(r)>1:

			# 		empty_packet_count = 0
			# 		# print(datetime.datetime.now())
			# 		data_unsorted = data_unsorted+r
			# 		# print(datetime.datetime.now(),'\n')
			# 		count_meas+=len(r)


			# 	elif r == [3338]:

			# 		empty_packet_count += 1
			# 		time.sleep(0.5)

			# 	if empty_packet_count>20:

			# 		log.warning('Data curruption: rfSoC did not send all data points({}).'.format(count_meas//(16*N_adc_events)))
					
			# 		# reset measurement
			# 		data_unsorted = []
			# 		count_meas = 0
			# 		empty_packet_count = 0
			# 		self.write("SEQ:STOP")
			# 		time.sleep(2)
			# 		while True:
			# 			junk = self.ask('OUTPUT:DATA?')
			# 			# print(junk)
			# 			time.sleep(0.1)
			# 			if junk == [3338]:
			# 				break
			# 		junk = []
			# 		self.write("SEQ:START")
			# 		time.sleep(0.1)

			# 		continue

			# self.write("SEQ:STOP")


			self.reset_output_data()

			#for now we consider only the one same type of acq on all adc
			mode=self.acquisition_mode.get()

			length_vec,ch_vec=self.adc_events()

			N_adc_events=len(ch_vec)

			N_acq=np.sum(np.sum(length_vec))

			adcdataI = [[],[],[],[],[],[],[],[]]
			adcdataQ = [[],[],[],[],[],[],[],[]]

			rep=[]
			count_meas=0

			empty_packet_count = 0

			self.write("SEQ:START")
			time.sleep(0.1)

			print(self.nb_measure.get())
			while count_meas<self.nb_measure.get():

				r = self.ask('OUTPUT:DATA?')

				if len(r)>1:
					print(len(r))
					rep = rep+r
					#to modify manually depending on what we
					#TODO : figure a way to do it auto depending on the adcs ons and their modes
					#now for 1 ADC in accum
					# count_meas+=len(r)//16
					count_meas+=len(r)//((8+N_acq))


				elif r==[3338]:

					count_meas=self.nb_measure.get()

			self.write("SEQ:STOP")

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
						# mod div by 4 to fix amplitude -Arpit, Martina
						I=  struct.unpack('q',X[0:8])[0]*(0.3838e-3)/(N*2*4)
						Q=  struct.unpack('q',X[8:16])[0]*(0.3838e-3)/(N*2*4)

						# print the point
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

			adcdataI=[np.array(adcdataI[v]).reshape(self.nb_measure.get(),np.sum(length_vec[v],dtype=int)) for v in range(8)]

			# adcdataI=[np.array(adcdataI[v]).reshape(self.nb_measure.get(),np.sum(np.sum(ch[v],dtype=int))) for v in range(8)]
			adcdataI=[np.mean(adcdataI[v],axis=0) for v in range(8)]

			adcdataI=np.array([np.split(adcdataI[v],[sum(length_vec[v][0:i+1]) for i in range(len(length_vec[v]))]) for v in range(8)])


			I,Q = adcdataI,adcdataQ



		else:

			log.error('rfSoC: Instrument mode not recognized.')

		return I,Q




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


	def int_0(self):
		return 0

	def int_8(self):
		return 8

	def get_idn(self):
		return {'vendor': 'Quantum Coherence Team', 'model': 'rfSoC gen01',
				'serial': 'NA', 'firmware': None}