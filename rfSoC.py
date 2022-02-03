# rfSoC driver with inbuilt pulse-generation
# Recommended practice is to add pulses to parameter snaps.
#                                        			-- Arpit





import time
import datetime
import numpy as np
import sys
import struct
import ctypes  # only for DLL-based instrument
import pickle as pk

import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter,
					validators as vals)
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter

import SequenceGeneration_v2 as sqg
from qcodes.utils.delaykeyboardinterrupt import DelayedKeyboardInterrupt
from qcodes.utils.validators import Numbers, Arrays

import plotly.express as px
import pandas as pd
from IPython.display import display, HTML
from ipywidgets import IntProgress
import matplotlib.pyplot as plt

import functools
import operator
from itertools import chain

sys.path.append('C:\\QCodes drivers and scripts\\Scripts\\Arpit\\Modules')
from progress_barV2 import bar

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


class ADC_power(Parameter):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def get_raw(self):

		time.sleep(0.2)

		data_retI, data_retQ = self._instrument.get_readout_pulse()#.get_readout_pulse() ###### Martina 08/11/2020

		Sq_I_list = [[],[],[],[],[],[],[],[]]
		Sq_Q_list = [[],[],[],[],[],[],[],[]]
		Pow = [[],[],[],[],[],[],[],[]]

		for i in range(8):

			if len(data_retI[i])>0:

				for j in range(len(data_retI[i])):

					if len(data_retI[i][j])>0:

						Sq_I_list[i].append(np.mean(data_retI[i][j]**2))
						Sq_Q_list[i].append(np.mean(data_retQ[i][j]**2))
								
		for i in range(8):
			
			Pow[i] = (np.array(Sq_I_list[i]) + np.array(Sq_Q_list[i]))/(50*2)	# RMS power

		return Pow


class ADC_power_dBm(Parameter):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def get_raw(self):

		time.sleep(0.2)

		data_retI, data_retQ = self._instrument.get_readout_pulse()#.get_readout_pulse() ###### Martina 08/11/2020

		Sq_I_list = [[],[],[],[],[],[],[],[]]
		Sq_Q_list = [[],[],[],[],[],[],[],[]]
		Pow = [[],[],[],[],[],[],[],[]]

		for i in range(8):

			if len(data_retI[i])>0:

				for j in range(len(data_retI[i])):

					if len(data_retI[i][j])>0:

						Sq_I_list[i].append(np.mean(data_retI[i][j]**2))
						Sq_Q_list[i].append(np.mean(data_retQ[i][j]**2))
								
		for i in range(8):
			
			Pow[i] = 10*np.log10(1e3*(np.array(Sq_I_list[i]) + np.array(Sq_Q_list[i]))/(50*2))		# RMS power

		return Pow












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
						   # get_parser = self.MHz_to_Hz,
						   # set_parser = self.Hz_to_MHz,
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

		self.sampling_rate = 2e9
		self.FPGA_clock = 250e6
		self.DAC_amplitude_calib = [1.08,1.08,1.08,1.08,1.08,1.08,1.08,1.08]

		self.pulses = pd.DataFrame()
		self.ADC_ch_active = np.zeros(8)
		self.length_vec = [[],[],[],[],[],[],[],[]]
		self.ch_vec = []

		self.display_sequence = True
		self.display_IQ_progress = True
		self.debug_mode = False
		self.debug_mode_plot_waveforms = False
		self.debug_mode_waveform_string = False

		self.raw_dump_location = "C:/Data_tmp"

		#Add the channels to the instrument
		for adc_num in np.arange(1,9):
			adc_name='ADC{}'.format(adc_num)
			adc=AcqChannel(self,adc_name,adc_num)
			self.add_submodule(adc_name, adc)


		self.add_parameter('sequence_str',
							get_parser=str,
							initial_value='',
							parameter_class=ManualParameter)

		self.add_parameter('n_rep',
							get_parser=int,
							initial_value = int(1),
							parameter_class=ManualParameter)

		self.add_parameter('acquisition_mode',
							label='ADCs acquisition mode',
							get_parser=str,
							vals = vals.Enum('RAW','IQ'),
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
						   vals=Arrays(shape=(8, 2, self.n_rep)), ### ME
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
						   vals=Arrays(shape=(2, 8, 2, self.n_rep)), ### ME
						   snapshot_value = False)

		self.add_parameter(name='IQINT_two_mode_squeezing',
						   unit='V',
						   label='Integrated I Q for 2 channels with header check',
						   parameter_class = ManualParameter,
						   vals=Arrays(shape=(2, 2, 2, self.n_rep)), ### ME
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
						   label='Array of incident power on ADC channels',
						   parameter_class=ADC_power,
						   vals=Arrays(shape=(self.dummy_array_size_8,)),
						   # vals=Arrays(shape=(self.dummy_array_size_8,)),
						   snapshot_value = False)

		self.add_parameter(name='ADC_power_dBm',
						   unit='dBm',
						   label='Array of incident power on ADC channels',
						   parameter_class=ADC_power_dBm,
						   vals=Arrays(shape=(self.dummy_array_size_8,)),
						   snapshot_value = False)

		#for now all mixer frequency must be multiples of the base frequency for phase matching
		self.add_parameter(name='freq_sync',
						   unit='Hz',
						   label='Reference frequency for synchronizing pulse repetition',
						   get_parser=float,
						   parameter_class=ManualParameter,
						   snapshot_value = False)


	

	def process_sequencing(self):

		log.info('Started sequence processing'+'  \n')

		n_rep = self.n_rep()
		pulses_raw_df = self.pulses

		if len(set(pulses_raw_df['label'])) < len(pulses_raw_df['label']):

			log.error('Duplicate Labels: Labels need to be unique for consistent identification of pulse hierarchy.')

		pulses_raw_df.set_index('label', inplace = True)

		if self.debug_mode:

			display(pulses_raw_df)

		resolve_hierarchy = True
		while resolve_hierarchy:

			for index, row in pulses_raw_df.iterrows():

				if row['parent'] != None:

					if pulses_raw_df.loc[row['parent']]['parent'] == None:

						pulses_raw_df.loc[index,'start'] = pulses_raw_df.loc[index,'start'] +  pulses_raw_df.loc[row['parent']]['start'] + pulses_raw_df.loc[row['parent']]['length']
						pulses_raw_df.loc[index,'parent'] = None
			
			resolve_hierarchy = False
			for val in pulses_raw_df['parent']:
				if val != None:
					resolve_hierarchy = True

		if self.debug_mode:

			print('Hierarchy resolution...')
			display(pulses_raw_df)

		pulses_df = pd.DataFrame()
		time_ADC = [0,0,0,0,0,0,0,0]
		time_DAC = [0,0,0,0,0,0,0,0]
		length_vec = [[],[],[],[],[],[],[],[]]
		ch_vec = []
		wait_color_count = int("D3D3D3", 16)
		DAC_color_count = int("306cc7", 16)
		ADC_color_count = int("db500b", 16)
		color_dict = {}
		termination_time = 0

		tmp_df = pulses_raw_df.loc[pulses_raw_df['module'] == 'ADC']
		for index, row in tmp_df.iterrows():
			
			if row['start'] > time_ADC[int(row['channel'])-1]:
				
				label = 'wait' + str(wait_color_count-int("D3D3D3", 16)+1)
				start = time_ADC[int(row['channel'])-1]
				stop = row['start']
				time = row['start'] - time_ADC[int(row['channel'])-1]
				module = row['module']
				Channel = 'ADC ch' + str(int(row['channel']))
				mode = 'wait'
				color = wait_color_count
				wait_color_count += 1
				color_dict[str(color)] = '#{0:06X}'.format(color)
				param = row['param']
				ch_num = row['channel']
				
				pulses_df = pulses_df.append(dict(label=label, start=start, stop=stop, time=time, module=module , Channel=Channel, mode=mode, color=str(color), param=param, ch_num=ch_num), ignore_index=True)
			
			label = index
			start = row['start']
			stop = row['start'] + row['length']
			time = row['length']
			module = row['module']
			Channel = 'ADC ch' + str(int(row['channel']))
			mode = row['mode']
			color = ADC_color_count
			ADC_color_count += 1
			color_dict[str(color)] = '#{0:06X}'.format(color)
			param = row['param']
			ch_num = row['channel']

			pulses_df = pulses_df.append(dict(label=label, start=start, stop=stop, time=time, module=module , Channel=Channel, mode=mode, color=str(color), param=param, ch_num=ch_num), ignore_index=True)

			length_vec[int(row['channel'])-1].append(int(time*1e-6*self.sampling_rate))
			ch_vec.append(int(row['channel'])-1)
			
			time_ADC[int(row['channel'])-1] = stop
			
			if stop>termination_time:
				
				termination_time = stop
			
		tmp_df = pulses_raw_df.loc[pulses_raw_df['module'] == 'DAC']
		for index, row in tmp_df.iterrows():
			
			if row['start'] > time_DAC[int(row['channel'])-1]:
				
				label = 'wait' + str(wait_color_count-int("D3D3D3", 16)+1)
				start = time_DAC[int(row['channel'])-1]
				stop = row['start']
				time = row['start'] - time_DAC[int(row['channel'])-1]
				module = row['module']
				Channel = 'DAC ch' + str(int(row['channel']))
				mode = 'wait'
				color = wait_color_count
				wait_color_count += 1
				color_dict[str(color)] = '#{0:06X}'.format(color)
				param = row['param']
				ch_num = row['channel']
				
				pulses_df = pulses_df.append(dict(label=label, start=start, stop=stop, time=time, module=module , Channel=Channel, mode=mode, color=str(color), param=param, ch_num=ch_num), ignore_index=True)
			
			label = index
			start = row['start']
			stop = row['start'] + row['length']
			time = row['length']
			module = row['module']
			Channel = 'DAC ch' + str(int(row['channel']))
			mode = row['mode']
			color = DAC_color_count
			DAC_color_count += 1
			color_dict[str(color)] = '#{0:06X}'.format(color)
			param = row['param']
			ch_num = row['channel']

			pulses_df = pulses_df.append(dict(label=label, start=start, stop=stop, time=time, module=module , Channel=Channel, mode=mode, color=str(color), param=param, ch_num=ch_num), ignore_index=True)
			
			time_DAC[int(row['channel'])-1] = stop
			
			if stop>termination_time:
				
				termination_time = stop
	
		for ch in range(1,9):
			
			if termination_time>time_ADC[ch-1] and time_ADC[ch-1]>0:
				
				label = 'wait' + str(wait_color_count-int("D3D3D3", 16)+1)
				start = time_ADC[ch-1]
				stop = termination_time
				time = stop - start
				module = 'ADC'
				Channel = 'ADC ch' + str(ch)
				mode = 'wait'
				color = wait_color_count
				wait_color_count += 1
				color_dict[str(color)] = '#{0:06X}'.format(color)
				param = row['param']
				ch_num = ch
				
				pulses_df = pulses_df.append(dict(label=label, start=start, stop=stop, time=time, module=module , Channel=Channel, mode=mode, color=str(color), param=param, ch_num=ch_num), ignore_index=True)
				
		for ch in range(1,9):
			
			if termination_time>time_DAC[ch-1] and time_DAC[ch-1]>0:
				
				label = 'wait' + str(wait_color_count-int("D3D3D3", 16)+1)
				start = time_DAC[ch-1]
				stop = termination_time
				time = stop - start
				module = 'DAC'
				Channel = 'DAC ch' + str(ch)
				mode = 'wait'
				color = wait_color_count
				wait_color_count += 1
				color_dict[str(color)] = '#{0:06X}'.format(color)
				param = row['param']
				ch_num = ch
				
				pulses_df = pulses_df.append(dict(label=label, start=start, stop=stop, time=time, module=module , Channel=Channel, mode=mode, color=str(color), param=param, ch_num=ch_num), ignore_index=True)

		if self.display_sequence:

			fig = px.bar(pulses_df, x="time", y="Channel", color='color', orientation='h', text="label",
						 color_discrete_map=color_dict,
						 hover_data=["start","stop"],
						 height=300,
						 title='pulse sequence')
			fig.update_layout(showlegend=False) 
			fig.show()

		self.length_vec = length_vec
		self.ch_vec = ch_vec

		event_time_list = list(dict.fromkeys(pulses_df['start']))
		event_time_list.sort()

		termination_time = np.max(pulses_df['stop'])

		if self.debug_mode:

			display(pulses_df)
			display(pulses_df.sort_values('start'))

			print('Events detected at: ',event_time_list)

			print('Termination of sequence detected at : ',termination_time)

		global_sequence = np.array([])
		event_time_prev = 0
		DAC_pulses_array = [np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),np.array([]),np.array([])]
		DAC_pulses_pointer = [[],[],[],[],[],[],[],[]]
		ADC_state = np.array([0,0,0,0,0,0,0,0])
		self.ADC_ch_active = np.array([0,0,0,0,0,0,0,0])
		n_clock_cycles = 0
		n_clock_cycles_global = 0


		for event_time in event_time_list:
			
			# adding wait till this event
			if event_time>0:
				
				global_sequence = np.append(global_sequence,1)
				global_sequence = np.append(global_sequence,int((event_time-event_time_prev)*250)-1)
				n_clock_cycles_global = n_clock_cycles_global + int((event_time-event_time_prev)*250)

				if self.debug_mode:

					print('adding wait till this event')
					print(1,int((event_time-event_time_prev)*250)-1)
				
			n_clock_cycles = 0
			event_time_prev = event_time
			tmp_df = pulses_df.loc[pulses_df['start'] == event_time]
			tmp_df = tmp_df.sort_values(by='module', ascending=False)
			
			
			for index, row in tmp_df.iterrows():
				
				if self.debug_mode:

					print(event_time,row['mode'], row['label'])

				ch_num = int(row['ch_num'])

				if row['module'] == 'DAC':
						
					if row['mode'] != 'wait':
						
						# generate sequence and add to corresponding channel
						SCPI_command = self.pulse_gen_SCPI(row['mode'],row['param'],row['time'],ch_num)
						
						# adding pointer for this pulse
						pulse_addr = int(len(DAC_pulses_array[ch_num-1])/11)
						DAC_pulses_pointer[ch_num-1].append(pulse_addr)
						
						# adding pulse to waveform
						DAC_pulses_array[ch_num-1] = np.append(DAC_pulses_array[ch_num-1],SCPI_command)
						
						# adding sequencer command to point to address of this pulse
						n_clock_cycles += 1
						global_sequence = np.append(global_sequence,4096+ch_num)
						global_sequence = np.append(global_sequence,pulse_addr)

						if self.debug_mode:

							print('adding sequencer command to point to address of this pulse')
							print(4096+ch_num,pulse_addr)
						
						# adding sequencer command to start output
						n_clock_cycles += 1
						bin_trig_cmd = ''.join(ADC_state.astype(str))
						for i in [8,7,6,5,4,3,2,1]:
							if i == ch_num:
								bin_trig_cmd += '011'
							else:
								bin_trig_cmd += '000'
						global_sequence = np.append(global_sequence,4096)
						global_sequence = np.append(global_sequence,int(bin_trig_cmd,2))

						if self.debug_mode:

							print('adding sequencer command to start output')
							print(4096,int(bin_trig_cmd,2))
						
					elif row['mode'] == 'wait':
						
						# adding sequencer command to stop output
						n_clock_cycles += 1
						bin_trig_cmd = ''.join(ADC_state.astype(str))
						for i in [8,7,6,5,4,3,2,1]:
							if i == ch_num:
								bin_trig_cmd += '001'
							else:
								bin_trig_cmd += '000'
						global_sequence = np.append(global_sequence,4096)
						global_sequence = np.append(global_sequence,int(bin_trig_cmd,2))

						if self.debug_mode:

							print('adding sequencer command to stop output')
							print(4096,int(bin_trig_cmd,2))
						
					else:
						
						log.error('Wrong pulse mode: ',event_time,row['mode'], row['label'])
						
				if row['module'] == 'ADC':
					
					if row['mode'] != 'wait':
						
						# adding sequencer command to set acq points
						n_clock_cycles += 1
						global_sequence = np.append(global_sequence,4106+ch_num)
						global_sequence = np.append(global_sequence,int(row['time']*1e-6*self.sampling_rate))

						if self.debug_mode:

							print('adding sequencer command to set acq points')
							print(4106+ch_num,int(row['time']*1e-6*self.sampling_rate))
						
						# adding sequencer command to start acq
						n_clock_cycles += 1
						ADC_state[7-(ch_num-1)] = 1
						self.ADC_ch_active[ch_num-1] = 1
						bin_trig_cmd = ''.join(ADC_state.astype(str))+'000000000000000000000000'
						global_sequence = np.append(global_sequence,4096)
						global_sequence = np.append(global_sequence,int(bin_trig_cmd,2))

						if self.debug_mode:

							print('adding sequencer command to start acq')
							print(4096,int(bin_trig_cmd,2))
						
					elif row['mode'] == 'wait':
						
						# adding sequencer command to stop acq
						n_clock_cycles += 1
						ADC_state[7-(ch_num-1)] = 0
						bin_trig_cmd = ''.join(ADC_state.astype(str))+'000000000000000000000000'
						global_sequence = np.append(global_sequence,4096)
						global_sequence = np.append(global_sequence,int(bin_trig_cmd,2))

						if self.debug_mode:

							print('adding sequencer command to stop acq')
							print(4096,int(bin_trig_cmd,2))
						
					else:
						
						log.error('Wrong pulse mode: ',event_time,row['mode'], row['label'])
						
			n_clock_cycles_global += n_clock_cycles
				
		#terminate the sequence
		global_sequence = np.append(global_sequence,1)
		global_sequence = np.append(global_sequence,int((termination_time-event_time_prev)*250)-1)
		n_clock_cycles_global = n_clock_cycles_global + int((termination_time-event_time_prev)*250)
		global_sequence = np.append(global_sequence,4096)
		global_sequence = np.append(global_sequence,0)
		n_clock_cycles_global += 1

		if self.acquisition_mode() == 'RAW':
			acq_mode = 0
		elif self.acquisition_mode() == 'IQ':
			acq_mode = 286331153
		else:
			log.error('Invalid acquisition mode\n')
			
		period_sync = int(self.FPGA_clock/self.freq_sync())
		wait_sync = period_sync-(n_clock_cycles_global%period_sync)-1 -2 #(2 clock cycles for jump)

		global_sequence_str = 'SEQ 0,1,9,4106,' + str(acq_mode) + ',257,' + str(int(n_rep-1)) + ',' + ','.join((global_sequence.astype(int)).astype(str)) + ',1,' + str(wait_sync) + ',513,0,0,0'

		# just to keep in log
		self.sequence_str = global_sequence_str

		if self.debug_mode:

			print('Sequence programmer command: ',global_sequence_str)

		for i in range(8):

			if len(DAC_pulses_array[i])>0:

				self.write('DAC:DATA:CH{}:CLEAR'.format(str(i+1)))

				if self.debug_mode and self.debug_mode_plot_waveforms:

					fig = plt.figure(figsize=(8,5))
					plt.plot(range(len(DAC_pulses_array[i])),DAC_pulses_array[i])
					plt.grid()
					plt.legend(fontsize = 14)
					plt.show()

				DAC_SCPI_cmd = 'DAC:DATA:CH' + str(i+1) + ' 0,' + ','.join((DAC_pulses_array[i].astype(int)).astype(str)) + ',0,0,0,0,0,0,0,0,0,0,16383'

				if self.debug_mode and self.debug_mode_waveform_string:

					print('DAC sequence for CH '+str(i+1)+': ',DAC_SCPI_cmd)

				log.info('Writing waveform for CH'+str(i+1)+'  \n')
				self.write(DAC_SCPI_cmd)

		log.info('Writing global sequence' + '\n')
		self.write(global_sequence_str)

		log.info('Waveform and sequence processing complete' + '\n')
	


	def pulse_gen_SCPI(self,mode,param,duration,ch):
	
		period = 1./self.sampling_rate
		time_vec = np.arange(period,duration*1e-6+period/2,period)
		
		if mode == 'sin+sin':
			
			wavepoints1 = (2**13)*self.DAC_amplitude_calib[ch-1]*param['amp1']*np.sin(-param['phase_offset1'] + 2*np.pi*param['freq1']*1e6*time_vec)
			wavepoints2 = (2**13)*self.DAC_amplitude_calib[ch-1]*param['amp2']*np.sin(-param['phase_offset2'] + 2*np.pi*param['freq2']*1e6*time_vec)
			
			wavepoints = (2**13)*self.DAC_amplitude_calib[ch-1]*param['dc_offset'] + wavepoints1 + wavepoints2
			
			if self.debug_mode and self.debug_mode_plot_waveforms:
				print('plot of sinsin mode 1')
				fig = plt.figure(figsize=(8,5))
				plt.plot(time_vec,wavepoints1)
				plt.grid()
				plt.show()
				print('plot of sinsin mode 2')
				fig = plt.figure(figsize=(8,5))
				plt.plot(time_vec,wavepoints2)
				plt.grid()
				plt.show()
				print('plot of sinsin mode total')
				fig = plt.figure(figsize=(8,5))
				plt.plot(time_vec,wavepoints)
				plt.grid()
				plt.show()
				
				
			
		elif mode == 'sin':
			
			wavepoints = (2**13)*self.DAC_amplitude_calib[ch-1]*param['dc_offset'] + (2**13)*self.DAC_amplitude_calib[ch-1]*param['amp']*np.sin(-param['phase_offset'] + 2*np.pi*param['freq']*1e6*time_vec)
			
			if self.debug_mode and self.debug_mode_plot_waveforms:
				print('plot of sin mode')
				fig = plt.figure(figsize=(8,5))
				plt.plot(time_vec,wavepoints)
				plt.grid()
				plt.legend(fontsize = 14)
				plt.show()
			
			
			
		else:
			
			log.error('Wrong waveform mode: ',mode)
		
		
		
		# adding zeros to make length multiple of 8
		wavepoints = np.append(wavepoints,np.zeros(len(time_vec)%8))

		trig_rep_len = int(len(wavepoints)/8)
		# adding trigger vectors
		wavepoints = np.concatenate((wavepoints.reshape(trig_rep_len,8), np.array(np.zeros(trig_rep_len))[:,None]),axis=1)
		wavepoints = np.concatenate((wavepoints, np.array(np.zeros(trig_rep_len))[:,None]),axis=1)

		# adding repetation (0 for once)
		wavepoints = np.concatenate((wavepoints, np.array(np.zeros(trig_rep_len))[:,None]),axis=1)

		# convert to 1D array 
		wavepoints = wavepoints.reshape(1,len(wavepoints)*len(wavepoints[0]))
		
		return wavepoints[0]




	def reset_PLL(self):

		self.write("DAC:RELAY:ALL 0")
		self.write("PLLINIT")
		time.sleep(5)
		self.write("DAC:RELAY:ALL 1")


	def reset_output_data(self):

		self.ask('OUTPUT:DATA?')




	def get_readout_pulse(self):
		'''
		 This function reformat the data reading the header contents.
		'''

		self.reset_output_data()
		mode = self.acquisition_mode()
		n_rep = self.n_rep()
		length_vec = self.length_vec
		ch_vec = self.ch_vec
		N_adc_events = len(ch_vec)
		n_pulses = len(length_vec[0])

		ch_active = self.ADC_ch_active
		
		if mode == 'IQ':
			'''
				Get data
			'''

			data_unsorted = {}
			count_meas = 0
			empty_packet_count = 0
			run_num = 0

			self.write("SEQ:START")
			time.sleep(0.1)

			getting_valid_dataset = True

			if self.display_IQ_progress:

				self.display_IQ_progress_bar = IntProgress(min=0, max=self.n_rep.get()) # instantiate the bar
				display(self.display_IQ_progress_bar) # display the bar

			while getting_valid_dataset:

				while (count_meas//(16*N_adc_events))<self.n_rep.get():

					a = datetime.datetime.now()

					r = self.ask('OUTPUT:DATA?')

					b = datetime.datetime.now()
					# print('\nget data: ',b-a)

					if r == 'ERR':

						log.error('rfSoC: Instrument returned ERR!')

						# reset measurement
						data_unsorted = {}
						count_meas = 0
						empty_packet_count = 0
						run_num = 0
						self.write("SEQ:STOP")
						time.sleep(2)
						while True:
							junk = self.ask('OUTPUT:DATA?')
							# print(junk)
							time.sleep(0.1)
							if junk == [3338] or junk == [2573]:
								break
						junk = []
						self.write("SEQ:START")
						time.sleep(0.1)

						continue

					elif len(r)>1:

						a = datetime.datetime.now()
						empty_packet_count = 0
						data_unsorted['{}'.format(run_num)] = r
						r_size = len(r)
						count_meas += r_size
						if self.display_IQ_progress:
							self.display_IQ_progress_bar.value = count_meas//(16*N_adc_events)
						run_num += 1
						b = datetime.datetime.now()
						# print('end storing: ',b-a)

						time.sleep(0.01)


					elif r == [3338] or r == [2573]: # new empty packet?

						# log.warning('Received empty packet.')
						empty_packet_count += 1
						time.sleep(0.1)

					if empty_packet_count>20:

						log.error('Data curruption: rfSoC did not send all data points({}/'.format(count_meas//(16*N_adc_events))+str(self.n_rep.get())+').')
						
						# reset measurement
						data_unsorted = {}
						count_meas = 0
						empty_packet_count = 0
						run_num = 0
						self.write("SEQ:STOP")
						time.sleep(2)
						while True:
							junk = self.ask('OUTPUT:DATA?')
							# print(junk)
							time.sleep(0.1)
							if junk == [3338] or junk == [2573]:
								break
						junk = []
						self.write("SEQ:START")
						time.sleep(0.1)

						continue

				if count_meas//(16*N_adc_events) == self.n_rep.get():

					getting_valid_dataset = False

				else:

					log.error('Data curruption: rfSoC did not send all data points({}/'.format(count_meas//(16*N_adc_events))+str(self.n_rep.get())+').')

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
						if junk == [3338] or junk == [2573]:
							break
					junk = []
					self.write("SEQ:START")
					time.sleep(0.1)

			self.write("SEQ:STOP")

			'''
				Process data
			'''

			# data_unsorted = list(chain.from_iterable(data_unsorted.values()))
			data_unsorted = functools.reduce(operator.iconcat, list(data_unsorted.values()), [])
			data_unsorted = np.array(data_unsorted,dtype=int)

			# separate header from IQ data
			raw_IQ_data_dump_header = data_unsorted.reshape(int(len(data_unsorted)/8),8)[0::2]
			raw_I_data_dump_data = data_unsorted.reshape(int(len(data_unsorted)/8),8)[1::2][:,0:4]
			raw_Q_data_dump_data = data_unsorted.reshape(int(len(data_unsorted)/8),8)[1::2][:,4:8]

			# extract channel number from first byte of header
			ch_num = (raw_IQ_data_dump_header%256).T[0]

			# extract number of accumulated points for normalization from 3rd to 6th byte of header 
			num_points = np.frombuffer(np.stack((raw_IQ_data_dump_header.T[1], raw_IQ_data_dump_header.T[2]), axis=1).astype('int16').tobytes(), dtype=np.long)

			# vectors indicating channel that the data originated from 
			ch_1 = ch_num*(ch_num == np.ones(len(ch_num)))
			ch_2 = ch_num*(ch_num == 2*np.ones(len(ch_num)))/2
			ch_3 = ch_num*(ch_num == 3*np.ones(len(ch_num)))/3
			ch_4 = ch_num*(ch_num == 4*np.ones(len(ch_num)))/4
			ch_5 = ch_num*(ch_num == 5*np.ones(len(ch_num)))/5
			ch_6 = ch_num*(ch_num == 6*np.ones(len(ch_num)))/6
			ch_7 = ch_num*(ch_num == 7*np.ones(len(ch_num)))/7
			ch_8 = ch_num*(ch_num == 8*np.ones(len(ch_num)))/8

			# data conversion form four 16 bit integers to one 64 bit longlong (*(0.3838e-3/16))
			I_all_data = 2 + np.frombuffer(raw_I_data_dump_data.astype('int16').tobytes(), dtype=np.longlong)*0.3838e-3/(16*num_points)
			Q_all_data = 2 + np.frombuffer(raw_Q_data_dump_data.astype('int16').tobytes(), dtype=np.longlong)*0.3838e-3/(16*num_points)

			I = [((I_all_data*ch_1)[I_all_data*ch_1!=0]-2).reshape(n_rep*ch_active[0],n_pulses).T,
				 ((I_all_data*ch_2)[I_all_data*ch_2!=0]-2).reshape(n_rep*ch_active[1],n_pulses).T,
				 ((I_all_data*ch_3)[I_all_data*ch_3!=0]-2).reshape(n_rep*ch_active[2],n_pulses).T,
				 ((I_all_data*ch_4)[I_all_data*ch_4!=0]-2).reshape(n_rep*ch_active[3],n_pulses).T,
				 ((I_all_data*ch_5)[I_all_data*ch_5!=0]-2).reshape(n_rep*ch_active[4],n_pulses).T,
				 ((I_all_data*ch_6)[I_all_data*ch_6!=0]-2).reshape(n_rep*ch_active[5],n_pulses).T,
				 ((I_all_data*ch_7)[I_all_data*ch_7!=0]-2).reshape(n_rep*ch_active[6],n_pulses).T,
				 ((I_all_data*ch_8)[I_all_data*ch_8!=0]-2).reshape(n_rep*ch_active[7],n_pulses).T]
			Q = [((Q_all_data*ch_1)[Q_all_data*ch_1!=0]-2).reshape(n_rep*ch_active[0],n_pulses).T,
				 ((Q_all_data*ch_2)[Q_all_data*ch_2!=0]-2).reshape(n_rep*ch_active[1],n_pulses).T,
				 ((Q_all_data*ch_3)[Q_all_data*ch_3!=0]-2).reshape(n_rep*ch_active[2],n_pulses).T,
				 ((Q_all_data*ch_4)[Q_all_data*ch_4!=0]-2).reshape(n_rep*ch_active[3],n_pulses).T,
				 ((Q_all_data*ch_5)[Q_all_data*ch_5!=0]-2).reshape(n_rep*ch_active[4],n_pulses).T,
				 ((Q_all_data*ch_6)[Q_all_data*ch_6!=0]-2).reshape(n_rep*ch_active[5],n_pulses).T,
				 ((Q_all_data*ch_7)[Q_all_data*ch_7!=0]-2).reshape(n_rep*ch_active[6],n_pulses).T,
				 ((Q_all_data*ch_8)[Q_all_data*ch_8!=0]-2).reshape(n_rep*ch_active[7],n_pulses).T]

		elif mode == 'RAW':


			self.reset_output_data()

			#for now we consider only the one same type of acq on all adc
			mode=self.acquisition_mode.get()

			N_adc_events=len(ch_vec)

			N_acq=np.sum(np.sum(length_vec))

			getting_valid_dataset = True

			while getting_valid_dataset:

				adcdataI = [[],[],[],[],[],[],[],[]]
				adcdataQ = [[],[],[],[],[],[],[],[]]

				rep=[]

				keep_trying = True
				empty_packet_count = 0

				self.write("SEQ:START")
				time.sleep(0.1)

				while keep_trying:

					r = self.ask('OUTPUT:DATA?')

					if r == 'ERR':

						log.error('rfSoC: Instrument returned ERR!')

						# reset measurement
						rep = []
						empty_packet_count = 0
						self.write("SEQ:STOP")
						time.sleep(2)
						while True:
							junk = self.ask('OUTPUT:DATA?')
							# print(junk)
							time.sleep(0.1)
							if junk == [3338] or junk == [2573]:
								break
						junk = []
						self.write("SEQ:START")
						time.sleep(0.1)

						continue

					if len(r)>1:

						rep = rep+r

					elif r==[3338] or r==[2573]:

						empty_packet_count += 1
						time.sleep(0.1)

						if empty_packet_count>10:

							keep_trying = False

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

				points_rec = 0
				points_expected = 0

				for index in range(8):

					if len(adcdataI[index]) > 0:

						points_rec += adcdataI[index].size

					points_expected += int(self.n_rep() * np.sum(length_vec[index],dtype=int))

				if points_rec == points_expected:

					getting_valid_dataset = False

					adcdataI=[np.array(adcdataI[v]).reshape(self.n_rep.get(),np.sum(length_vec[v],dtype=int)) for v in range(8)]

					# adcdataI=[np.array(adcdataI[v]).reshape(self.n_rep.get(),np.sum(np.sum(ch[v],dtype=int))) for v in range(8)]
					adcdataI=[np.mean(adcdataI[v],axis=0) for v in range(8)]

					adcdataI=np.array([np.split(adcdataI[v],[sum(length_vec[v][0:i+1]) for i in range(len(length_vec[v]))]) for v in range(8)])

					I,Q = adcdataI,adcdataQ

				else:

					log.error('Data curruption: rfSoC did not send all data points({}/'.format(points_rec)+str(points_expected)+').')

					# adcdataI=[np.mean(adcdataI[v],axis=0) for v in range(8)]

					# adcdataI=np.array([np.split(adcdataI[v],[sum(length_vec[v][0:i+1]) for i in range(len(length_vec[v]))]) for v in range(8)])

					I,Q = adcdataI,adcdataQ
					print(I,Q)

		else:

			log.error('rfSoC: Instrument mode not recognized.')

		return I,Q



	def dump_raw_readout_pulse(self):
		'''
		 This function dumps raw data to drive to avoid RAM clogging.
		'''
		self.reset_output_data()
		mode = self.acquisition_mode()
		n_rep = self.n_rep()
		length_vec = self.length_vec
		ch_vec = self.ch_vec
		N_adc_events = len(ch_vec)
		n_pulses = len(length_vec[0])
		location = self.raw_dump_location

		ch_active = self.ADC_ch_active
		
		if mode == 'IQ':
			'''
				Get data
			'''

			count_meas = 0
			empty_packet_count = 0
			run_num = 0

			self.write("SEQ:START")
			time.sleep(0.1)

			getting_valid_dataset = True

			if self.display_IQ_progress:

				self.display_IQ_progress_bar = IntProgress(min=0, max=self.n_rep.get()) # instantiate the bar
				display(self.display_IQ_progress_bar) # display the bar

			while getting_valid_dataset:

				while (count_meas//(16*N_adc_events))<self.n_rep.get():

					a = datetime.datetime.now()

					r = self.ask('OUTPUT:DATA?')

					b = datetime.datetime.now()
					# print('\nget data: ',b-a)

					if r == 'ERR':

						log.error('rfSoC: Instrument returned ERR!')

						# reset measurement
						count_meas = 0
						empty_packet_count = 0
						run_num = 0
						self.write("SEQ:STOP")
						time.sleep(2)
						while True:
							junk = self.ask('OUTPUT:DATA?')
							# print(junk)
							time.sleep(0.1)
							if junk == [3338] or junk == [2573]:
								break
						junk = []
						self.write("SEQ:START")
						time.sleep(0.1)

						continue

					elif len(r)>1:

						a = datetime.datetime.now()
						empty_packet_count = 0
						r_size = len(r)
						pk.dump(r, open(location+"/raw_"+str(run_num)+".pkl","wb"))
						count_meas += r_size
						if self.display_IQ_progress:
							self.display_IQ_progress_bar.value = count_meas//(16*N_adc_events)
						run_num += 1
						b = datetime.datetime.now()
						# print('end storing: ',b-a)

						time.sleep(0.01)


					elif r == [3338] or r == [2573]: # new empty packet?

						# log.warning('Received empty packet.')
						empty_packet_count += 1
						time.sleep(0.1)

					if empty_packet_count>20:

						log.error('Data curruption: rfSoC did not send all data points({}/'.format(count_meas//(16*N_adc_events))+str(self.n_rep.get())+').')
						
						# reset measurement
						count_meas = 0
						empty_packet_count = 0
						run_num = 0
						self.write("SEQ:STOP")
						time.sleep(2)
						while True:
							junk = self.ask('OUTPUT:DATA?')
							# print(junk)
							time.sleep(0.1)
							if junk == [3338] or junk == [2573]:
								break
						junk = []
						self.write("SEQ:START")
						time.sleep(0.1)

						continue

				if count_meas//(16*N_adc_events) == self.n_rep.get():

					getting_valid_dataset = False

				else:

					log.error('Data curruption: rfSoC did not send all data points({}/'.format(count_meas//(16*N_adc_events))+str(self.n_rep.get())+').')

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
						if junk == [3338] or junk == [2573]:
							break
					junk = []
					self.write("SEQ:START")
					time.sleep(0.1)

			self.write("SEQ:STOP")

		return run_num


	def transfer_speed(self, block_size=100):

		block_n = int(block_size/10)
		a = datetime.datetime.now()
		for i in bar(range(block_n)):

			data = self.ask('OUTPUT:DATATEST?')

		b = datetime.datetime.now()
		del_t = (b-a).seconds
		speed = round(10*block_n/del_t,2)
		event_rate = round(1000*speed/32,2)
		pulse_length = round(1000/event_rate,2)
		print('Transfer speed: '+str(speed)+' MBps')
		print('Event rate: '+str(event_rate)+' K/s')
		print('Minimum size of one ADC pulse: '+str(pulse_length)+' us per active channel')




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
						response = self.visa_handle.query_binary_values(cmd, datatype="h", is_big_endian=False)
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