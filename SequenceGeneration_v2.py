import numpy as np
from operator import itemgetter, attrgetter
from itertools import groupby
import matplotlib.pyplot as plt

import logging


log = logging.getLogger(__name__)

class Pulse:
	'''
	Parent class for any DAC or ADC event.
	'''

	#initializing the array storing instances of the class Pulse
	objs = []

	def __init__(self, t_init, t_duration, channel, parent):

		#adding the new instance to the objs array
		Pulse.objs.append(self)
		#initializing the object attribute
		#initial time with respect to the parent pulse end
		self.t_init = t_init
		self.t_duration = t_duration
		self._t_abs=None
		self.channel = channel
		#parent is an attribute allowing to define a pulse relatively to an
		#other pulse (timewise)
		#type : None if no parent (root event)
		self.parent = parent




	@classmethod
	def absolute_init_time(cls):
		'''
		Class method returning the initial time of each instance of the class.
		Pulse with respect to the beginning of the sequence (take adventage of
		the parent attribure).
		'''
		for obj in cls.objs:

			#initialize absolute time and parent
			t_abs=obj.t_init
			parent=obj.parent

			#going up the the hierarchy tree and incrementing the time
			#untill we reach a root event (type(parent) : None)
			while parent is not None:

				#the initial time a child pulse is define with respect to the
				#initial time of the parent pulse

				#TODO : permit to define the child pulse with respect to the
				#begining of the parent pulse
				t_abs+=parent.t_init + parent.t_duration
				#defining from begining

				#new parent
				parent=parent.parent

			#store the absolute time
			obj._t_abs=t_abs


	@classmethod
	def sort_and_groupby_timewise(cls):
		'''
		Method to sort ADC and DAC events timewise and grouping simultaneous
		events.
		'''
		cls.absolute_init_time()

		#initializing the list containing groups of simultaneous events
		groups=[]

		#sort the Pulse instances timewise
		new=sorted(cls.objs , key=attrgetter('_t_abs'))
		#group by absolute initial time
		for _ , g in groupby(new, key=attrgetter('_t_abs')):

			groups.append(list(g))

		return groups


	@classmethod
	def generate_sequence_and_DAC_memory(cls,nb_loop,acq_mode,mix_freq):
		'''
		Method to generate the SCPI command for filling the DAC memory and
		the sequence memory based on the instances of the Pulse class.
		
		TODO : account for simultaneous events.
		'''

		sorted_seq=np.array(cls.sort_and_groupby_timewise())
		# print(sorted_seq)

		Tseq=max([max([p[i]._t_abs + p[i].t_duration for i in range(len(p))]) for  p in sorted_seq])
		
		# print('Tseq={}'.format(Tseq))

		#initialize the scpi command (memory adress 0 wait 44 ns and set all
		#beginiing DAC memories to 0)

		#storing the time of play of the sequence to adjust for sync with LO
		#and adjust for letting time for DAC playing all memory before starting again
		#the sequence
		N_seq_loop=1
		N_data_transfer=0


		if acq_mode=='SUM':
			acq_mode_val=286331153
			#for now we turn all ADCs to the same acquisition mode
		else:
			acq_mode_val=0

		if nb_loop==0:
			scpi_str='SEQ 0,1,10,4106,'+str(acq_mode_val)+',257,0,4105,0'
		else:
			scpi_str='SEQ 0,1,10,4106,'+str(acq_mode_val)+',257,'+str(nb_loop)+',4105,0'

		#array storing previous DAC pulses for each DAC channel to manage
		#the momort adress
		last_DAC_channel_event=[None,None,None,None,None,None,None,None]

		#TODO : get rid of the groupy method and directly loop through groupby
		#(sorted listn key)

		#go through sorted events (the sequence is ... sequential)
		for gp in sorted_seq:
			# print(last_DAC_channel_event)
			N_wait = int(round(gp[0].t_init/(4.e-9)))
			ctrl_dac_adc=0
			N_adc_duration=0

			if N_wait!=0.:
				scpi_str=scpi_str+',1,{}'.format(N_wait-1)
				N_seq_loop+=N_wait


			for obj in gp:
				#looking if the pulse is DAC or ADC
				if type(obj)==PulseGeneration:

					N_duration = int(round(obj.t_duration/(4.e-9)))	
					ctrl_dac_adc+=DAC_status([int(obj.channel[2])])
		

					#managing DAC memory adress
					if last_DAC_channel_event[int(obj.channel[2])-1]==None:
				
						obj._DAC_2D_memory=obj.send_DAC_2D_memory()

					else :
						#computing new start adress for the new wform of the DAC
						new_adress= int(round(last_DAC_channel_event[int(obj.channel[2])-1].t_duration/(4.e-9))) + 1
						# print('new_adress = {}'.format(new_adress))

						#adding delay or not
						scpi_str=scpi_str+',{},{}'.format(4096+int(obj.channel[2]),new_adress)
						N_seq_loop+=1
						
						#storing the filling DAC memory SCPI instruction as an
						#attribute of the PulseGeneration object
						obj._DAC_2D_memory=obj.send_DAC_2D_memory(new_adress)

					#updating last event of the DAC
					last_DAC_channel_event[int(obj.channel[2])-1]=obj

				elif type(obj)==PulseReadout:

					ctrl_dac_adc+=ADC_status([int(obj.channel[2])])

					#header 8 point of 2 bytes
					#data transfer speed is 100 Mo/s max (doc specify to verify)
					t_data_transfer=16./(100.e6)
					N_data_transfer+=int(round(t_data_transfer/(4.e-9)))

					#TODO : take decimation into account
					#       if deficamtion divide N_acq by decimation facotr
					N_acq = int(round(obj.t_duration/(0.5e-9)))

					N_temp=int(round(obj.t_duration/(4e-9)))
					if N_temp > N_adc_duration:
						N_adc_duration=N_temp

					#data is 2 octet per point in raw mode
					if acq_mode is 'RAW':
						t_data_transfer=2.*N_acq/100.e6
						N_data_transfer+=int(round(t_data_transfer/(4.e-9)))

					if acq_mode is 'SUM':
						#in sum mode 64 bits for I and 64 bits for Q
						#ie 4*2 bytes I 4*2 bytes Q
						t_data_transfer=16./(100.e6)
						N_data_transfer+=int(round(t_data_transfer/(4.e-9)))


					scpi_str=scpi_str+',{},{}'.format(4106+int(obj.channel[2]),N_acq)
					
					N_seq_loop+= 1

			if N_adc_duration!=0:

				scpi_str=scpi_str+',4096,{},1,{}'.format(ctrl_dac_adc,N_adc_duration-1)
				N_seq_loop+= 1 + N_adc_duration

			else:
				
				scpi_str=scpi_str+',4096,{}'.format(ctrl_dac_adc)
				N_seq_loop+= 1

		
		N_add=0
		N_seq_loop+=3 #end of loop and wait at the end for adjustment
		# print('N_seq_loop={}'.format(N_seq_loop))

		if N_seq_loop*4.e-9 < Tseq:

			N_add=int(round((Tseq-N_seq_loop*4.e-9)/4.e-9))
			N_seq_loop+=N_add

		# print('N_add={}'.format(N_add))

		N_data_transfer=N_data_transfer*10
		N_seq_loop = N_seq_loop + N_data_transfer*10

		# print('N_seq_loop={}'.format(N_seq_loop))
		# N_seq_loop = N_seq_loop

		# print('N_data_transfer={}'.format(N_data_transfer))

		if mix_freq!=0.:

			N_mix=int(round(1./(4.e-9 * mix_freq)))
			N_add +=(N_mix -  N_seq_loop % N_mix) #+ N_mix*1000  #### 25 points of wait correspond to 1 us acquisition time
			N_seq_loop+=(N_mix -  N_seq_loop % N_mix) #+ N_mix*1000

		# print('N_add={}'.format(N_add))

		#16 working
		scpi_str=scpi_str+',1,{},513,0'.format(N_add+N_data_transfer)

		# scpi_str=scpi_str+',1,{},513,0'.format(1000000-5)

		# print('N_seq_loop={}'.format(N_seq_loop))
		# print('t_seq_loop={} s'.format(N_seq_loop*4.e-9))
	

		# print(scpi_str)
		return scpi_str


class PulseGeneration(Pulse):
	'''
	Child class of the Pulse class for DAC events
	'''
	objs=[]

	def __init__(self, t_init, t_duration, channel, wform, params, CW_mode=False, DC_offset=0, parent=None):

		super().__init__(t_init, t_duration, channel, parent)
		PulseGeneration.objs.append(self)
		self.wform = wform
		self.params = params
		self.CW_mode = CW_mode
		self.DC_offset = DC_offset

	#overwritting the __repr__ native method for nice display of the object
	def __repr__(self):

		return('Pulse(DAC {}, t_abs={} s,  t_init={} s, t_duration={} s, waveform : {}, params={}, CW_mode={}'.format(
				self.channel, self._t_abs, self.t_init, self.t_duration, self.wform, self.params, self.CW_mode))


	def fill_2D_memory(self,trigger=None):
		'''
		Generate a 2D memory for the DAC.
		First version with NO repetion of chunks of 8 values.

		TODO : add ramp, square, etc...
		'''

		#check waveform
		if self.wform=='SIN':
			###### TO DO add the phase ()
			# freq, amplitude= self.params
			freq, amplitude, phase = self.params ### ME (phase must be given in degrees)
			#size of the memory is 65536 and the time step of the DACS is 500 ps

			#control parameters of the wform
			#TODO : move those control to the init of the PulseGeneration object

			# if freq > 1./0.5e-9 or amplitude > 2 or self.t_duration > 64.e-6:
			if freq > 1./0.5e-9 or amplitude > 2 or self.t_duration > 64.e-6 or phase > 360 or phase < 0: ### ME
				raise ValueError('One of the parameters is not correct')

			else :
				if freq > 1./(4.*0.5e-9):
				    log.Warning('Warning : bellow 4 points per period, the signal might be unstable.')

			# DAC values are coded on signed 14 bits = +/- 8192
			DAC_amplitude = amplitude * 8192/0.926
			phase_rad = phase*2*np.pi/360 ### ME

			N_point = int(round(self.t_duration/0.5e-9))
			n_oscillation = freq*self.t_duration
			t = np.linspace(0, 2 * np.pi,N_point)

			# table = (self.DC_offset* 8192/0.926) + DAC_amplitude*np.concatenate((np.sin(n_oscillation*t),np.zeros(N_point%8)))

			table = (self.DC_offset* 8192/0.926) + DAC_amplitude*np.concatenate((np.sin(n_oscillation*t + phase_rad),np.zeros(N_point%8))) ### ME
			# plt.plot(t, table)
			# adding zeros at the end so that N_point_tot is dividable by 8
			# because the table is to be divided in chunks of 8 values

			#reshaping +andadding initialized values for trigger and repetition
			#number

			table=table.reshape(int(round(table.shape[0]/8.)),8)
			memory_table=np.concatenate((table,np.zeros((table.shape[0],1)),np.zeros((table.shape[0],2))),axis=1)

			# the triggers of one channel are stored in a tuple
			# the tuple is composed of couples of string for the trigger val
			# and float for the time at wich a trigger is set
			# by default trigger is set to none and all trigger is set to 0

			#TODO : made before coding the class. Maybe put the trigger as an
			#       attribute of the PulseGeneration class.

			#triggers not used or tested so far
			if trigger is None:
			    return memory_table.reshape((1,memory_table.shape[0]*memory_table.shape[1]))[0]

			else :
			    for trig in trigger :
			        trig_name=trig[0]
			        trig_time=trig[1]
			        trig_row_index=int(round(trig_time/(0.5e-9 * 8)))

			        if trig_name=='TRIG1':
			            memory_table[trig_row_index,-1]=1.

			        elif trig_name=='TRIG2':
			            memory_table[trig_row_index,-2]=1.

			        elif trig_name=='BOTH':
			            memory_table[trig_row_index,-1]=1.
			            memory_table[trig_row_index,-2]=1.

			        else :
			            raise ValueError('Wrong trigger value')

			    return memory_table.reshape((1,memory_table.shape[0]*memory_table.shape[1]))[0]



			#check waveform
		if self.wform=='SIN+SIN':

			freq1, amp1, phase1, freq2, amp2, phase2 = self.params ### phases must be given in degrees

			#size of the memory is 65536 and the time step of the DACS is 500 ps

			#control parameters of the wform
			#TODO : move those control to the init of the PulseGeneration object

			if freq1 > 1./0.5e-9 or freq1 > 1./0.5e-9 or amp1 + amp2 > .926 or self.t_duration > 64.e-6:
				raise ValueError('One of the parameters is not correct')
			elif  phase1 > 360 or phase1 < 0 or phase2 > 360 or phase2 < 0: ### ME
				raise ValueError('One of the phase parameters is not correct') ### ME

			else :
				if freq1 > 1./(4.*0.5e-9) or freq2 > 1./(4.*0.5e-9):
				    log.Warning('Warning : bellow 4 points per period, the signal might be unstable.')

			# DAC values are coded on signed 14 bits = +/- 8192
			DAC_amp1 = amp1 * 8192/0.926
			DAC_amp2 = amp2 * 8192/0.926
			phase_rad1 = phase1*2*np.pi/360 ### ME
			phase_rad2 = phase2*2*np.pi/360 ### ME

			N_point = int(round(self.t_duration/0.5e-9))
			n_oscillation1 = freq1*self.t_duration
			n_oscillation2 = freq2*self.t_duration
			t = np.linspace(0, 2 * np.pi,N_point)

			table1=DAC_amp1*np.concatenate((np.sin(n_oscillation1*t + phase_rad1),np.zeros(N_point%8)))
			table2=DAC_amp2*np.concatenate((np.sin(n_oscillation2*t + phase_rad2),np.zeros(N_point%8)))

			table = table1 + table2
			# print(table)
			# adding zeros at the end so that N_point_tot is dividable by 8
			# because the table is to be divided in chunks of 8 values

			#reshaping +andadding initialized values for trigger and repetition
			#number

			table=table.reshape(int(round(table.shape[0]/8.)),8)
			memory_table=np.concatenate((table,np.zeros((table.shape[0],1)),np.zeros((table.shape[0],2))),axis=1)

			# the triggers of one channel are stored in a tuple
			# the tuple is composed of couples of string for the trigger val
			# and float for the time at wich a trigger is set
			# by default trigger is set to none and all trigger is set to 0

			#TODO : made before coding the class. Maybe put the trigger as an
			#       attribute of the PulseGeneration class.

			#triggers not used or tested so far
			if trigger is None:
			    return memory_table.reshape((1,memory_table.shape[0]*memory_table.shape[1]))[0]

			else :
			    for trig in trigger :
			        trig_name=trig[0]
			        trig_time=trig[1]
			        trig_row_index=int(round(trig_time/(0.5e-9 * 8)))

			        if trig_name=='TRIG1':
			            memory_table[trig_row_index,-1]=1.

			        elif trig_name=='TRIG2':
			            memory_table[trig_row_index,-2]=1.

			        elif trig_name=='BOTH':
			            memory_table[trig_row_index,-1]=1.
			            memory_table[trig_row_index,-2]=1.

			        else :
			            raise ValueError('Wrong trigger value')

			    return memory_table.reshape((1,memory_table.shape[0]*memory_table.shape[1]))[0]




	def send_DAC_2D_memory(self,adress=0):

		"""
		Send the waveform to the DAC memory

		Input : beginning adress for the memory

		Output : SCPI command
		"""
		# convert the element of table_bit to int and then to string for sending
		# then forming a whole string with values separated by commas by using
		# the join method

		table=self.fill_2D_memory()
		table_bit=(table.astype(int)).astype(str)
		separator = ','
		table_bit = separator.join(table_bit)

		#managing the beginning adress of the memory depending on the mode
		#(CW or pulse)
		if self.channel in ['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8']:

			#fill the end of the memory for the CW mode
			if self.CW_mode == False:
				return 'DAC:DATA:'+self.channel+' '+str(adress)+','+table_bit+','+'0,0,0,0,0,0,0,0,0,0,16383'

			else:
				new_adress = int(round(16384 - self.t_duration/(4.e-9)))

				return 'DAC:DATA:'+self.channel+' '+str(new_adress)+','+table_bit

		else:
			raise ValueError('Wrong channel value')



class PulseReadout(Pulse):
	'''
	Child class of the Pulse class for ADC events
	'''
	objs=[]

	def __init__(self,t_init, t_duration, channel, parent=None):

		super().__init__(t_init, t_duration, channel, parent)
		PulseReadout.objs.append(self)

	def __repr__(self):

		return('Pulse(ADC {}, t_abs={} s,  t_init={} s, t_duration={} s'.format(
				self.channel, self._t_abs, self.t_init, self.t_duration))



def ADC_status(ADC_list):
	'''
	Convert the ADC channel numbers to the CTRL_DAC&ADC data value of the
	sequenceur.
	'''
	dec=0

	for ADCnum in ADC_list:
		dec+=2**(ADCnum+23)

	return dec

def DAC_status(DAC_list):
	'''
	Convert the DAC channel numbers to the CTRL_DAC&ADC data value of the
	sequenceur.
	'''
	dec=0

	for DACnum in DAC_list:
		dec+= 2**(3*DACnum - 3) + 2**(3*DACnum - 2) + 0*2**(3*DACnum - 1)

	return dec


def ADC_DAC_status(DAC_list, ADC_list):
	'''
	Convert both DAC and ADC channel numbers to the CTRL_DAC&ADC data value of
	the sequenceur.
	'''
	return str(int(DAC_status(DAC_list))+int(ADC_status(ADC_list)))

#Testing the module

if __name__=="__main__":
	from driver_rfsoc import RFSoC
	try:
		rfsoc = RFSoC('RFSoC', 'TCPIP::{}::{}::SOCKET'.format('192.168.0.123',5001))

	except KeyError as er:

		RFSoC.close_all() #Disconnect and irreversibly tear down the instrument
		rfsoc = RFSoC('RFSoC', 'TCPIP::{}::{}::SOCKET'.format('192.168.0.123',5001))

	Pulse.objs=[]
	PulseGeneration.objs=[]
	PulseReadout.objs=[]

	rfsoc.ADC2.decfact(8)

	chunck_duration=1.e-6 #length of acquisition pulse

	if rfsoc.ADC2.decfact.get()  is 8 :
		chunck_duration_ADC=chunck_duration/ 8

	elif rfsoc.ADC2.decfact.get() is not 1:
		raise ValueError('Invalid decimation factor')
	else:
		chunck_duration_ADC=chunck_duration

	freq1=4.e6
	amp1=.8
	param1=[freq1,amp1]

	pulse_DAC1=PulseGeneration(0.,chunck_duration*3,'CH2','SIN',param1,CW_mode=False)
	pulse_ADC2=PulseReadout(1.e-6,chunck_duration_ADC,'CH2')


	Pulse.absolute_init_time()


	sorted_objs=Pulse.sort_and_groupby_timewise()


	# print('Sorted list of pulse instances grouped by absolute initial time')
	# print(sorted_objs)
