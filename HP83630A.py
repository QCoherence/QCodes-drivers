##
## This driver is a modified and simplified version of the QCodes SMB100A driver
## Modified by Cyril Mori on 17/02/2024
##


import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter, Parameter,
					validators as vals)
import logging


log = logging.getLogger(__name__)





class HP83630A(VisaInstrument):
	"""
	QCoDeS driver for the HP83630A MW source
	"""

	# all instrument constructors should accept **kwargs and pass them on to
	# super().__init__

	def __init__(self, name, address, **kwargs):
		# supplying the terminator means you don't need to remove it from every response
		super().__init__(name, address, terminator='\n', **kwargs)

		self.add_parameter( name = 'frequency',
							label = 'Output frequency in Hz',
							vals = vals.Numbers(100e3,26.5e9),
							unit   = 'Hz',
							set_cmd='frequency ' + '{:.12f}',
							get_cmd='frequency?'
							)

		self.add_parameter( name = 'power',
							label = 'Output power in dBm',
							vals = vals.Numbers(-20,25),
							unit   = 'dBm',
							set_cmd='power ' + '{:.12f}',
							get_cmd='power?',
							get_parser=float,
							set_parser =self.warn_over_range
							)

		self.add_parameter( name = 'status',
							label = 'Output on/off',
							vals = vals.Enum('on','off'),
							unit   = 'NA',
							set_cmd='power:state ' + '{}',
							get_cmd='power:state?',
							set_parser =self.easy_read_status,
							get_parser=self.easy_read_status_read
							)

		# good idea to call connect_message at the end of your constructor.
		# this calls the 'IDN' parameter that the base Instrument class creates
		# for every instrument  which serves two purposes:
		# 1) verifies that you are connected to the instrument
		# 2) gets the ID info so it will be included with metadata snapshots later.
		self.connect_message()

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

	def warn_over_range(self, power):
		if power>25:
			log.warning('Power over range (limit to 16 dBm).')
		return power
