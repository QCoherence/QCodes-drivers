# Last updated on 3 Mar 2020
#                     -- Arpit


import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter,
					validators as vals)
from qcodes.instrument.channel import InstrumentChannel



class RS_FSQ(VisaInstrument): 
	
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
							set_cmd=':BANDwidth:RESolution ' + '{:.12f}',
							get_cmd=':BANDwidth:RESolution?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'video_BW',  
							label = 'Video bandwidth',
							vals = vals.Numbers(1,30e6),
							unit   = 'Hz',
							set_cmd=':BANDwidth:VIDeo ' + '{:.12f}',
							get_cmd=':BANDwidth:VIDeo?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'sweep_time',  
							label = 'Sweep time',
							vals = vals.Numbers(1e-6,16e3),
							unit   = 's',
							set_cmd=' ' + '{:.12f}',
							get_cmd='?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'input_att',  
							label = 'Input attenuation',
							vals = vals.Numbers(0,50),
							unit   = 'dB',
							set_cmd=' ' + '{:.12f}',
							get_cmd='?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'input_att_mode',  
							label = 'Input attenuation mode',
							vals = vals.Enum('auto','man'),
							unit   = 'NA',
							set_cmd=' ' + '{:.12f}',
							get_cmd='?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'center_freq',  
							label = 'Center Frequency',
							vals = vals.Numbers(20,26.5e9),
							unit   = 'Hz',
							set_cmd=' ' + '{:.12f}',
							get_cmd='?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'averages',  
							label = 'Averages',
							vals = vals.Numbers(20,26.5e9),
							unit   = 'NA',
							set_cmd=' ' + '{:.12f}',
							get_cmd='?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'numpoints',  
							label = '',
							vals = vals.Numbers(20,26.5e9),
							unit   = '',
							set_cmd=' ' + '{:.12f}',
							get_cmd='?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'span',  
							label = 'Span',
							vals = vals.Numbers(20,26.5e9),
							unit   = 'Hz',
							set_cmd=' ' + '{:.12f}',
							get_cmd='?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'average_type',  
							label = 'Average type',
							vals = vals.Enum('rms','log','scalar'),
							unit   = 'NA',
							set_cmd=' ' + '{:.12f}',
							get_cmd='?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.connect_message()


def set_screen(screen):
	ret='Active screen set to '+screen
	if screen=='A':
		sense_num=1
	elif screen=='B':
		sense_num=2
	else:
		ret='Error: not able to recognize screen id.'
	return ret
