import numpy as np
from operator import itemgetter, attrgetter
from itertools import groupby



class Pulse:

	objs = []

	def __init__(self, t_init, t_duration, channel, parent):

		Pulse.objs.append(self)
		self.t_init = t_init
		self.t_duration = t_duration
		self._t_abs=None
		self.channel = channel
		self.parent = parent


	def is_absolute_parent(self):
		if self.parent is None :
			return True
		else :
			return False


	@classmethod
	def absolute_init_time(cls):

		for obj in cls.objs:

			t_abs=obj.t_init
			parent=obj.parent

			while parent is not None:

				t_abs+=parent.t_init + parent.t_duration
				parent=parent.parent

			obj._t_abs=t_abs


	@classmethod
	def sort_and_groupby_timewise(cls):
		'''
			sort ADC and DAC events timewise and grouping simultaneous events
		'''
		cls.absolute_init_time()

		groups=[]
		new=sorted(cls.objs , key=attrgetter('_t_abs'))

		for _ , g in groupby(new, key=attrgetter('_t_abs')):

			groups.append(list(g))

		return groups
		
		
	@classmethod
	def generate_sequence_and_DAC_memory(cls):
		'''
		ATM this method doesnt account for simultaneous events
		'''
		scpi_str='SEQ 0,1,10,4105,0'

		last_DAC_channel_event=[None,None,None,None,None,None,None,None]

		#TODO : get rid of the groupy method and directly loop through groupby(sorted listn key)

		for gp in cls.sort_and_groupby_timewise():
			for obj in gp:

				print(type(obj))

				ctrl_dac_adc=DAC_status([int(obj.channel[2])])

				if type(obj)==PulseGeneration:
					
					N_wait = int(round(obj.t_init/(4.e-9)))
					N_duration = int(round(obj.t_duration/(4.e-9)))

					
					if last_DAC_channel_event[int(obj.channel[2])-1]==None:

						if N_wait!=0.:

							scpi_str=scpi_str+',1,{},4096,{},1,{}'.format(N_wait,ctrl_dac_adc,N_duration)

						else :

							scpi_str=scpi_str+',4096,{},1,{}'.format(ctrl_dac_adc,N_duration)

						obj._DAC_2D_memory=obj.send_DAC_2D_memory()


					else :


						new_adress= int(round(last_DAC_channel_event[int(obj.channel[2])-1].t_duration/(4.e-9))) + 1

						# print('new_adress = {}'.format(new_adress))

						if N_wait!=0.:

							scpi_str=scpi_str+',{},{},1,{},4096,{},1,{}'.format(4096+int(obj.channel[2]),new_adress,N_wait-1,ctrl_dac_adc,N_duration-1)

						else :

							scpi_str=scpi_str+',{},{},4096,{},1,{}'.format(4096+int(obj.channel[2]),new_adress,ctrl_dac_adc,N_duration-1)

						obj._DAC_2D_memory=obj.send_DAC_2D_memory(new_adress)


					last_DAC_channel_event[int(obj.channel[2])-1]=obj




				elif type(obj)==PulseReadout:

					N_wait = int(round(obj.t_init/(4.e-9)))
					N_acq = int(round(obj.t_duration/(0.5e-9)))
					ctrl_dac_adc=ADC_status([int(obj.channel[2])])

					scpi_str=scpi_str+',{},{},1,{},4096,{}'.format(4106+int(obj.channel[2]),N_acq,N_wait,ctrl_dac_adc)

		#TODO figure out the bus error when removing the 1 2500000000
		return scpi_str+',1,2500000000'


class PulseGeneration(Pulse):

	objs=[]

	def __init__(self, t_init, t_duration, channel, wform, params, CW_mode=False, parent=None):

		super().__init__(t_init, t_duration, channel, parent)
		PulseGeneration.objs.append(self)
		self.wform = wform
		self.params = params
		self.CW_mode = CW_mode

	def __repr__(self):

		return('Pulse(DAC {}, t_abs={} s,  t_init={} s, t_duration={} s, waveform : {}, params={}, CW_mode={}'.format(
				self.channel, self._t_abs, self.t_init, self.t_duration, self.wform, self.params, self.CW_mode))

	def fill_2D_memory(self,trigger=None):
		"""
		Fill a 2D memory.
		First version with 1 repetion of chunks of 8 values.
		Input:
		    function(string): name of the function
		    parameters(float): vector of parameters characterizing the function:
		    freq (Hz), Amplitude (from 0 to 1), pulse_duration (s), delay (s)
		Output:
		    the 2D table (int)
		"""
		if self.wform=='SIN':

			freq, amplitude = self.params

			# the size of the memory is 65536 and the time step pf the DACS is
			# 500 ps
			if freq > 1./0.5e-9 or amplitude > 1 or self.t_duration > 64.e-6:

				raise ValueError('One of the parameters is not correct')

			else :

				if freq > 1./(4.*0.5e-9):

				    print('Warning : bellow 4 points per period, the signal might be unstable.')

			DAC_amplitude = amplitude * 8192 # DAC values are coded on signed 14 bits = +/- 8192

			N_point = int(round(self.t_duration/0.5e-9))

			n_oscillation = freq*self.t_duration

			t = np.linspace(0, 2 * np.pi,N_point)

			table=DAC_amplitude*np.concatenate((np.sin(n_oscillation*t),np.zeros(N_point%8)))

			# we add zeros at the end so that N_point_tot is dividable by 8
			# because the tible is to be divided in chunks of 8 values

			table=table.reshape(int(round(table.shape[0]/8.)),8)
			memory_table=np.concatenate((table,np.zeros((table.shape[0],1)),np.zeros((table.shape[0],2))),axis=1)

			# the triggers of one channel are stored in a tuple
			# the tuple is composed of couples of string for the trigger val
			# and float for the time at wich a trigger is set
			# by default trigger is set to none and all trigger is set to 0

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
		#THIS FUNCTION CAN BE WRITTEN IN A NICER MANNER USING ARGS AND KWARGS
		#BCSE DURATION AND MODE ARE  SYSTEMATICALLY USED

		"""
			Send a 2D memory to one of the DAC chanels
			Input : - table (float): table to be sent
			        - channel(string): channel in which to table in sent
			        - adress(string): adress in the table of the DAC at which
			                          we start to write
		"""
		# self.log.info(__name__+ ' Send the 2D memory to DAC'+ channel+'  \n')
		# convert the element of table_bit to int and then to string for sending
		# then forming a whole string with values separated by commas by using
		# the join method

		table=self.fill_2D_memory()
		table_bit=(table.astype(int)).astype(str)
		separator = ','
		table_bit = separator.join(table_bit)

		if self.channel in ['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8']:

			if self.CW_mode == False:

				return 'DAC:DATA:'+self.channel+' '+str(adress)+','+table_bit+','+'0,0,0,0,0,0,0,0,0,0,16383'

			else:

				new_adress = int(round(16384 - self.t_duration/(4.e-9)))

				return 'DAC:DATA:'+self.channel+' '+str(new_adress)+','+table_bit

		else:

			raise ValueError('Wrong channel value')



class PulseReadout(Pulse):

	objs=[]

	def __init__(self,t_init, t_duration, channel, parent=None):

		super().__init__(t_init, t_duration, channel, parent)
		PulseReadout.objs.append(self)

	def __repr__(self):

		return('Pulse(ADC {}, t_abs={} s,  t_init={} s, t_duration={} s'.format(
				self.channel, self._t_abs, self.t_init, self.t_duration))



def ADC_status(ADC_list):

    dec=0

    for ADCnum in ADC_list:
        dec+=2**(ADCnum+23)

    return str(dec)

def DAC_status(DAC_list):

    dec=0

    for DACnum in DAC_list:
        dec+= 2**(3*DACnum - 3) + 2**(3*DACnum - 2) + 0*2**(3*DACnum - 1)

    return str(dec)


def ADC_DAC_status(DAC_list, ADC_list):

    return str(DAC_status(DAC_list)+ADC_status(ADC_list))


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
	