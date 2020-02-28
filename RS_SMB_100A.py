# Last updated on 2 Jan 2020
#                     -- Arpit


import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter,
					validators as vals)
from qcodes.instrument.channel import InstrumentChannel

from numpy import pi



class SMB100A(VisaInstrument): 
	"""
	QCoDeS driver for the Rohde and Schwarz SMB 100A MW source
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
							vals = vals.Numbers(-120,16),
							unit   = 'dBm',
							set_cmd='power ' + '{:.12f}',
							get_cmd='power?'
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