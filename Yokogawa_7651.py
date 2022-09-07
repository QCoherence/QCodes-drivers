# Last updated on 30 Oct 2020
#                     -- Arpit


import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter,
					validators as vals)
from qcodes.instrument.channel import InstrumentChannel
import logging

from numpy import pi

log = logging.getLogger(__name__)





class Yokogawa_7651(VisaInstrument): 
	"""
	QCoDeS driver for the Yokogawa 7651 I/V source
	"""
	
	# all instrument constructors should accept **kwargs and pass them on to
	# super().__init__

	def __init__(self, name, address, **kwargs):
		# supplying the terminator means you don't need to remove it from every response
		super().__init__(name, address, terminator='\n', **kwargs)

		# init: crashes the I/O, clear from visa test panel fixes the issue
		# self.write('RC')

		self.add_parameter( name = 'voltage_range',  
							label = 'Set output voltage range in mV',
							vals = vals.Enum(10,100,1_000,10_000,30_000),
							unit   = 'mV',
							set_cmd = self._set_V_mode)

		self.add_parameter( name = 'current_range',  
							label = 'Set output current range in mA',
							vals = vals.Enum(1,10,100),
							unit   = 'mA',
							set_cmd = self._set_A_mode)

		self.add_parameter( name = 'voltage_limit',  
							label = 'Set output voltage limit in mV',
							vals = vals.Numbers(1000,30_000),
							unit   = 'mV',
							set_parser = self._div_1000_int,
							set_cmd = 'LV'+'{}')

		self.add_parameter( name = 'current_limit',  
							label = 'Set output current limit in mA',
							vals = vals.Numbers(5,120),
							unit   = 'mA',
							set_parser = int,
							set_cmd = 'LA'+'{}')

		self.add_parameter( name = 'voltage',  
							label = 'Set output voltage in mV',
							vals = vals.Numbers(-30_000,30_000),
							unit   = 'mV',
							set_cmd = self._set_V)

		self.add_parameter( name = 'current',  
							label = 'Set output current in mA',
							vals = vals.Numbers(-120,120),
							unit   = 'mA',
							set_cmd = self._set_A)

		self.add_parameter( name = 'status',  
							label = 'Output on/off',
							vals = vals.Enum('on','off'),
							set_cmd='O' + '{}' + 'E',
							set_parser =self._easy_read_status
							)



	def _set_V_mode(self,range):

		range_options = {10:"R2", 100:"R3", 1000:"R4", 10000:"R5", 30000:"R6" }
		self.write('F1'+range_options[int(range)]+'E')

	def _set_A_mode(self,range):

		range_options = {1:"R4", 10:"R5", 100:"R6"}
		self.write('F5'+range_options[int(range)]+'E')

	def _div_1000_int(self,val):

		return int(val/1000)

	def _set_V(self,voltage):

		if voltage>0:
			polarity = '+'
		else:
			polarity = '-'
		self.write('S'+polarity+str(round(abs(voltage)/1000.,6))+'E')

	def _set_A(self,current):

		if current>0:
			polarity = '+'
		else:
			polarity = '-'
		self.write('S'+polarity+str(round(abs(current)/1000.,6))+'E')

	def _easy_read_status(self,state):

		if state == 'on':
			ret = '1'
		else:
			ret = '0'
		return ret

	def init(self):

		self.write('RC')