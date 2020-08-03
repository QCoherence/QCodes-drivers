import numpy as np

class Pulse:

	objs = []

	def __init__(self, t_init, t_duration, channel, parent):

		Pulse.objs.append(self)
		self.t_init = t_init
		self.t_duration = t_duration
		self.channel = channel
		self.parent = parent

	def is_absolute_parent(self):
		if self.parent is None :
			return True
		else :
			return False

	@classmethod
	def generate_sequence_and_DAC_memory(cls):
		'''
		ATM this method doesnt account for simultaneous events
		'''
		scpi_str='SEQ 0,1,10,4105,0,'

		last_DAC_channel_event=[None,None,None,None,None,None,None,None]

		for obj in cls.objs:

			if type(obj)==PulseGenerate:

				N_wait = int(round(obj.t_init/(4.e-9)))
				N_duration = int(round(obj.duration/(4.e-9)))

				ctrl_dac_adc=DAC_status([int(obj.channel[2])])

				if last_DAC_channel_event[int(obj.channel[2])]==None:

					scpi_str=scpi_str+'1,{},4096,{},1,{},'.format(N_wait-1,ctrl_dac_adc,N_duration-1)

					obj._DAC_2D_memory=obj.send_2D_memory()

				else :

					new_adress= N_duration + 1
					scpi_str=scpi_str+'{},{},1,{},4096,{},1,{},'.format(4096+int(obj.channel[2]),new_adress,N_wait-1,ctrl_dac_adc,N_duration-1)

					obj._DAC_2D_memory=obj.send_2D_memory(new_adress)

				last_DAC_channel_event[int(obj.channel[2])]=obj

		if type(obj)==PulseReadout:

			N_wait = int(round(obj.t_init/(4.e-9)))
			N_acq = int(round(obj.t_duration)/(0.5e-9)
			N_duration = int(round(obj.duration/(4.e-9)))
			ctrl_dac_adc=ADC_status([int(obj.channel[2])])

			scpi_str=scpi_str+'{},{},1,{},4096,{},1,{},'.format(4106+int(obj.channel[2],N_acq,N_wait,ctrl_dac_adc,N_duration)

		return scpi_str+'1,10'


class PulseGeneration(Pulse):

	objs=[]

	def __init__(self, t_init, t_duration, channel, wform, params, CW_mode, parent=None):

		super().__init__(t_init, t_duration, channel, parent)
		PulseGeneration.objs.append(self)
		self.wform = wform
		self.params = params
		self.CW_mode = CW_mode

	def send_2D_memory(self,adress=0):

		function=self.wform
		parameters=self.params
		channel=self.channel
		CW_mode=self.CW_mode
		duration=self.t_duration

		table=fill_2D_memory(function, parameters)

		return send_DAC_2D_memory(table, channel, duration, CW_mode, adress=0)


class PulseReadout(Pulse):

	objs=[]

	def __init__(self,t_init, t_duration, channel, parent=None):

		super().__init__(t_init, t_duration, channel, parent)
		PulseReadout.objs.append(self)


def fill_2D_memory(function, parameters, trigger=('NONE')):
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
        if function=='SIN':

            freq, amplitude, pulse_duration, delay = parameters
            # the size of the memory is 65536 and the time step pf the DACS is
            # 500 ps
            if freq > 1./0.5e-9 or amplitude > 1 or pulse_duration + delay > 64.e-6:
                raise ValueError('One of the parameters is not correct')

            else :
                if freq > 1./(4.*0.5e-9):
                    print('Warning : bellow 4 points per period, the signal might be unstable.')

                DAC_amplitude = amplitude * 8192 # DAC values are coded on signed 14 bits = +/- 8192
                N_point = int(round(pulse_duration/0.5e-9))

                N_point_tot=int(round((pulse_duration+delay)/0.5e-9))

                n_oscillation = freq*pulse_duration
                t = np.linspace(0, 2 * np.pi,N_point)

                table=DAC_amplitude*np.concatenate((np.zeros(int(round(delay/0.5e-9))),np.sin(n_oscillation*t),np.zeros(N_point%8)))

                # we add zeros at the end so that N_point_tot is dividable by 8
                # because the tible is to be divided in chunks of 8 values
                table=table.reshape(int(round(table.shape[0]/8.)),8)

                memory_table=np.concatenate((table,np.zeros((table.shape[0],1)),np.zeros((table.shape[0],2))),axis=1)

                # the triggers of one channel are stored in a tuple
                # the tuple is composed of couples of string for the trigger val
                # and float for the time at wich a trigger is set
                # by default trigger is set to none and all trigger is set to 0

                if trigger == 'NONE':

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


def send_DAC_2D_memory(table, channel, duration, CW_mode, adress=0):

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
        table_bit=(table.astype(int)).astype(str)
        separator = ','
        table_bit = separator.join(table_bit)

        if channel in ['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8']:

            if CW_mode == False:
                # self.write('DAC:DATA:'+channel+' '+adress+','+table_bit)

                return 'DAC:DATA:'+channel+' '+str(adress)+','+table_bit+','+'0,0,0,0,0,0,0,0,0,0,16383'

            else:

                new_adress = int(round(16384 - duration/(4.e-9)))

                return 'DAC:DATA:'+channel+' '+str(new_adress)+','+table_bit

        else:
            raise ValueError('Wrong channel value')

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


	params=[freq,amp,pulse_duration,delay]

	DAC1=PulseGeneration(0,1.e-6,'CH1','SIN',params,CW_mode=False)
	DAC2=PulseGeneration(0,5.e-6,'CH2','SIN',params,CW_mode=True, parent=DAC1)
	ADC1=PulseReadout(0,5.e-6,'CH1', parent=DAC2)

	print(Pulse.objs)
