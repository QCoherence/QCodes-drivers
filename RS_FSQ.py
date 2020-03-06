# Last updated on 3 Mar 2020
#                     -- Arpit


import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter,
					validators as vals)
from qcodes.instrument.channel import InstrumentChannel



from time import sleep






class RS_FSQ(VisaInstrument): 

	sense_num=1
	
	"""
	QCoDeS driver for the R&S FSQ Signal Analyser
	"""
	
	# all instrument constructors should accept **kwargs and pass them on to
	# super().__init__

	def __init__(self, name, address, **kwargs):
		# supplying the terminator means you don't need to remove it from every response
		super().__init__(name, address, terminator='\n', **kwargs)

		self.add_parameter( name = 'res_BW',  
							label = 'Resolution bandwidth',
							vals = vals.Numbers(10,50e6),
							unit   = 'Hz',
							set_cmd='SENSe'+str(self.sense_num)+':BANDwidth:RESolution ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':BANDwidth:RESolution?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'video_BW',  
							label = 'Video bandwidth',
							vals = vals.Numbers(1,30e6),
							unit   = 'Hz',
							set_cmd='SENSe'+str(self.sense_num)+':BANDwidth:VIDeo ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':BANDwidth:VIDeo?'
							# set_parser =self.,
							# get_parser=self.
							)

		# self.add_parameter( name = 'sweep_time',  
		# 					label = 'Sweep time',
		# 					vals = vals.Numbers(1e-6,16e3),
		# 					unit   = 's',
		# 					set_cmd='SENSe'+str(self.sense_num)+'SWEep:TIME ' + '{:.12f}',
		# 					get_cmd='SENSe'+str(self.sense_num)+'SWEep:TIME?'
		# 					# set_parser =self.,
		# 					# get_parser=self.
		# 					)

		self.add_parameter( name = 'input_att',  
							label = 'Input attenuation',
							vals = vals.Numbers(0,50),
							unit   = 'dB',
							set_cmd='SENSe'+str(self.sense_num)+':POWer:RF:ATTenuation ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':POWer:RF:ATTenuation?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'input_att_mode',  
							label = 'Input attenuation mode',
							vals = vals.Enum('auto','man'),
							unit   = 'NA',
							set_cmd='SENSe'+str(self.sense_num)+':POWer:RF:ATTenuation:AUTO ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':POWer:RF:ATTenuation:AUTO?',
							set_parser =self.caps,
							get_parser=self.caps_dag
							)

		self.add_parameter( name = 'center_freq',  
							label = 'Center Frequency',
							vals = vals.Numbers(20,26.5e9),
							unit   = 'Hz',
							set_cmd='SENSe'+str(self.sense_num)+':FREQuency:CENTer ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':FREQuency:CENTer?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'averages',  
							label = 'Averages',
							vals = vals.Numbers(20,26.5e9),
							unit   = 'NA',
							set_cmd='SENSe'+str(self.sense_num)+':AVERage:COUNt ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':AVERage:COUNt?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'num_points',  
							label = '',
							vals = vals.Numbers(20,26.5e9),
							unit   = '',
							set_cmd='SENSe'+str(self.sense_num)+':SWEep:POINts ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':SWEep:POINts?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'span',  
							label = 'Span',
							vals = vals.Numbers(20,26.5e9),
							unit   = 'Hz',
							set_cmd='SENSe'+str(self.sense_num)+':FREQuency:SPAN ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':FREQuency:SPAN?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'average_type',  
							label = 'Average type',
							vals = vals.Enum('rms','log','scalar'),
							unit   = 'NA',
							set_cmd='SENSe'+str(self.sense_num)+':AVERage:TYPE ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':AVERage:TYPE?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.connect_message()

	def get_trace(self):
		self.write('*CLS')
		self.write(':INIT:CONT OFF')
		self.write(':INIT:IMMediate;*OPC')
		while self.ask('*ESR?') == '0': 
		    sleep(1) # we wait until the register is 1
		datastr = self.ask(':TRAC? TRACE'+str(1))
		datalist = datastr.split(",")
		dataflt = []
		for val in datalist:
		    dataflt.append(float(val))
		return dataflt

	def caps(string):
		return string.upper()

	def caps_dag(string):
		return string.lower()


	# Functions fordebugging
	def deb_ask(self,question):
		ret = self.ask(question)
		return ret

	def deb_say(self,direction):
		self.write(direction)
		return 0



	# Nor working yet
	def set_screen(self,screen):
		if screen=='A':
			self.sense_num=1
			ret='Active screen set to '+screen
		elif screen=='B':
			self.sense_num=2
			ret='Active screen set to '+screen
		else:
			ret='Error: not able to recognize screen id.'
		return ret