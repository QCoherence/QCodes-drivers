import numpy as np
from operator import itemgetter, attrgetter
from itertools import groupby

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
	def generate_sequence_and_DAC_memory(cls):
		'''
		Method to generate the SCPI command for filling the DAC memory and
		the sequence memory based on the instances of the Pulse class.

		TODO : account for simultaneous events.
		'''
		#initialize the scpi command (memory adress 0 wait 44 ns and set all
		#beginiing DAC memories to 0)
		scpi_str='SEQ 0,1,10,4105,0'

		#array storing previous DAC pulses for each DAC channel to manage
		#the momort adress
		last_DAC_channel_event=[None,None,None,None,None,None,None,None]

		#TODO : get rid of the groupy method and directly loop through groupby
		#(sorted listn key)

		#go through sorted events (the sequence is ... sequential)
		for gp in cls.sort_and_groupby_timewise():
			for obj in gp:
				#looking if the pulse is DAC or ADC
				if type(obj)==PulseGeneration:

					#computing the data for the CTRL_DAC&ADC seq instr
					ctrl_dac_adc=DAC_status([int(obj.channel[2])])

					#computing the steps to wait
					N_wait = int(round(obj.t_init/(4.e-9)))
					N_duration = int(round(obj.t_duration/(4.e-9)))

					#managing DAC memory adress
					if last_DAC_channel_event[int(obj.channel[2])-1]==None:
						#adding delay or not
						if N_wait!=0.:
							scpi_str=scpi_str+',1,{},4096,{},1,{}'.format(N_wait,ctrl_dac_adc,N_duration)

						else :
							scpi_str=scpi_str+',4096,{},1,{}'.format(ctrl_dac_adc,N_duration)

						obj._DAC_2D_memory=obj.send_DAC_2D_memory()

					else :
						#computing new start adress for the new wform of the DAC
						new_adress= int(round(last_DAC_channel_event[int(obj.channel[2])-1].t_duration/(4.e-9))) + 1
						# print('new_adress = {}'.format(new_adress))

						#adding delay or not
						if N_wait!=0.:
							scpi_str=scpi_str+',{},{},1,{},4096,{},1,{}'.format(4096+int(obj.channel[2]),new_adress,N_wait-1,ctrl_dac_adc,N_duration-1)

						else :
							scpi_str=scpi_str+',{},{},4096,{},1,{}'.format(4096+int(obj.channel[2]),new_adress,ctrl_dac_adc,N_duration-1)

						#storing the filling DAC memory SCPI instruction as an
						#attribute of the PulseGeneration object
						obj._DAC_2D_memory=obj.send_DAC_2D_memory(new_adress)

					#updating last event of the DAC
					last_DAC_channel_event[int(obj.channel[2])-1]=obj

				elif type(obj)==PulseReadout:

					N_wait = int(round(obj.t_init/(4.e-9)))
					#TODO : take decimation into account
					#       if deficamtion divide N_acq by decimation facotr
					N_acq = int(round(obj.t_duration/(0.5e-9)))

					ctrl_dac_adc=ADC_status([int(obj.channel[2])])

					scpi_str=scpi_str+',{},{},1,{},4096,{}'.format(4106+int(obj.channel[2]),N_acq,N_wait,ctrl_dac_adc)

		#TODO figure out the bus error when removing the 1 2500000000

		seq = scpi_str+',1,2500000000'
		print(seq)
		return seq


class PulseGeneration(Pulse):
	'''
	Child class of the Pulse class for DAC events
	'''
	objs=[]

	def __init__(self, t_init, t_duration, channel, wform, params, CW_mode=False, parent=None):

		super().__init__(t_init, t_duration, channel, parent)
		PulseGeneration.objs.append(self)
		self.wform = wform
		self.params = params
		self.CW_mode = CW_mode

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

			freq, amplitude = self.params

			#size of the memory is 65536 and the time step of the DACS is 500 ps

			#control parameters of the wform
			#TODO : move those control to the init of the PulseGeneration object

			if freq > 1./0.5e-9 or amplitude > 1 or self.t_duration > 64.e-6:
				raise ValueError('One of the parameters is not correct')

			else :
				if freq > 1./(4.*0.5e-9):
				    print('Warning : bellow 4 points per period, the signal might be unstable.')

			# DAC values are coded on signed 14 bits = +/- 8192
			DAC_amplitude = amplitude * 8192

			N_point = int(round(self.t_duration/0.5e-9))
			n_oscillation = freq*self.t_duration
			t = np.linspace(0, 2 * np.pi,N_point)

			table=DAC_amplitude*np.concatenate((np.sin(n_oscillation*t),np.zeros(N_point%8)))

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

	def __init__(self,t_init, t_duration, channel, mode, parent=None):

		super().__init__(t_init, t_duration, channel, parent)
		PulseReadout.objs.append(self)

		if mode not in ['RAW','SUM']:
			raise ValueError('ADC mode must be either "RAW" or "SUM"')
		else:
			PulseReadout.mode=mode

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

	return str(dec)

def DAC_status(DAC_list):
	'''
	Convert the DAC channel numbers to the CTRL_DAC&ADC data value of the
	sequenceur.
	'''
	dec=0

	for DACnum in DAC_list:
		dec+= 2**(3*DACnum - 3) + 2**(3*DACnum - 2) + 0*2**(3*DACnum - 1)

	return str(dec)


def ADC_DAC_status(DAC_list, ADC_list):
	'''
	Convert both DAC and ADC channel numbers to the CTRL_DAC&ADC data value of
	the sequenceur.
	'''
	return str(DAC_status(DAC_list)+ADC_status(ADC_list))

#Testing the module

if __name__=="__main__":

	freq=10.e6
	amp=1.
	pulse_duration=1.e-6
	delay=0.

	freq1=2.e6
	amp1=1.
	param1=[freq1,amp1]

	freq2=5.e6
	amp2=0.5
	param2=[freq2,amp2]

	pulse1_DAC1=PulseGeneration(1e-6,4.e-6,'CH2','SIN',param1,CW_mode=False)
	pulse2_DAC1=PulseGeneration(2.e-6,2.e-6,'CH2','SIN', param2, CW_mode=False, parent=pulse1_DAC1)
	pulse1_DAC4=PulseGeneration(.5e-6,2.e-6,'CH4','SIN', param2, CW_mode=False, parent=pulse1_DAC1)
	pulse1_ADC1=PulseReadout(1e-6,9.e-6,'CH1')

	Pulse.absolute_init_time()

	# print('pulse 1 abosolute time : {} s'.format(pulse1_DAC1._t_abs))
	# print('pulse 2 abosolute time : {} s'.format(pulse2_DAC1._t_abs))
	# print('pulse 3 abosolute time : {} s'.format(pulse1_DAC4._t_abs))


	sorted_objs=Pulse.sort_and_groupby_timewise()


	print('Sorted list of pulse instances grouped by absolute initial time')
	print(sorted_objs)
