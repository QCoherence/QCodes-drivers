# Last update Jan 2023
#                     -- Arpit


import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter,
					validators as vals)
from qcodes.instrument.channel import InstrumentChannel
import logging

from numpy import pi

log = logging.getLogger(__name__)






class SGS100A(VisaInstrument): 
	"""
	QCoDeS driver for the Rohde and Schwarz SGS 100A MW source
	"""
	
	# all instrument constructors should accept **kwargs and pass them on to
	# super().__init__

	def __init__(self, name, address, **kwargs):
		# supplying the terminator means you don't need to remove it from every response
		super().__init__(name, address, terminator='\n', **kwargs)

		self.add_parameter( name = 'frequency',  
							label = 'Output frequency in Hz',
							vals = vals.Numbers(100e3,20e9),
							unit   = 'Hz',
							set_cmd='frequency ' + '{:.12f}' + 'Hz',
							get_cmd='frequency?'
							)

		self.add_parameter( name = 'power',  
							label = 'Output power in dBm',
							vals = vals.Numbers(-20,25),
							unit   = 'dBm',
							set_cmd='power ' + '{:.12f}',
							get_cmd='power?',
							set_parser =self.warn_over_range
							)

		self.add_parameter( name = 'phase',  
							label = 'Output phase in Rad',
							vals = vals.Numbers(-2*pi,2*pi),
							unit   = 'Rad',
							set_cmd='phase ' + '{:.12f}',
							get_cmd='phase?',
							set_parser =self.rad_to_deg,
							get_parser=self.deg_to_rad
							)

		self.add_parameter( name = 'status',  
							label = 'Output on/off',
							vals = vals.Enum('on','off'),
							unit   = 'NA',
							set_cmd='output ' + '{}',
							get_cmd='output?',
							set_parser =self.easy_read_status,
							get_parser=self.easy_read_status_read
							)

		self.add_parameter( name = 'IQmode',  
							label = 'IQmode on/off',
							vals = vals.Enum('on','off'),
							unit   = 'NA',
							set_cmd='IQ:state ' + '{}',
							get_cmd='IQ:state?',
							set_parser =self.easy_read_IQmode,
							get_parser=self.easy_read_IQmode_read
							)

		self.add_parameter( name = 'IQmode_wideband',  
							label = 'IQmode wideband option on/off',
							vals = vals.Enum('on','off'),
							unit   = 'NA',
							set_cmd='IQ:WBSTate ' + '{}',
							get_cmd='IQ:WBSTate?',
							set_parser =self.easy_read_IQmode,
							get_parser=self.easy_read_IQmode_read
							)

		# good idea to call connect_message at the end of your constructor.
		# this calls the 'IDN' parameter that the base Instrument class creates 
		# for every instrument  which serves two purposes:
		# 1) verifies that you are connected to the instrument
		# 2) gets the ID info so it will be included with metadata snapshots later.
		self.connect_message()


	def rad_to_deg(self, theta):
		return theta*180.0/pi

	def deg_to_rad(self, theta):
		return float(theta)*pi/180.0

	def easy_read_status(self, status):
		if(status=='on'):
			ret=1
		elif(status=='off'):
			ret=0
		return ret

	def easy_read_status_read(self, status):
		if(status=='1'):
			ret='on'
		elif(status=='0'):
			ret='off'
		return ret

	def easy_read_IQmode(self, IQmode):
		if(IQmode=='on'):
			ret=1
		elif(IQmode=='off'):
			ret=0
		return ret

	def easy_read_IQmode_read(self, IQmode):
		if(IQmode=='1'):
			ret='on'
		elif(IQmode=='0'):
			ret='off'
		return ret

	def warn_over_range(self, power):
		if power*1000%10 != 0:
			log.warning('Power resolution out of limit (allowed setp size is 0.01).')
		return power

	def freqsweep_set(self,sweep_status):
		if sweep_status == 'sweep':
			ret = 'SWEep'
		else:
			ret = 'CW'
		return ret

	def freqsweep_get(self,sweep_status):
		if sweep_status == 'CW':
			ret = 'CW'
		else:
			ret = 'sweep'
		return ret

	def sweepmode_set(self,sweepmode):
		if sweepmode == 'auto':
			ret = 'AUTO'
		else:
			ret = 'SING'
		return ret

	def sweepmode_get(self,sweepmode):
		if sweepmode == 'AUTO':
			ret = 'auto'
		else:
			ret = 'single'
		return ret

	def start_sweep(self):
		self.write('*TRG')
