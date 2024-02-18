##
## Simplified version of QCodes RCDAT-6000-60 driver from the QCodes Git
## Cyril Mori 18/02/2024
##


import telnetlib
import qcodes.instrument.base
from qcodes.utils.validators import Numbers

class RCDAT_8000_30(qcodes.instrument.base.Instrument):

	def __init__(self, name, address, port=23, **kwargs):
		##
		## Note that the instrument uses Telnet so its address must be
		## given in format '192.168.0.0' instead of 'TCPIP0::192.168.0.0::inst0::INSTR'
		##
		self.telnet = telnetlib.Telnet(address)
		super().__init__(name, **kwargs)
		# do a read until command here
		self.telnet.read_until(b"\n\r", timeout=1)

		# General Reference commands

		self.add_parameter(name='attenuation',
						label='attenuation',
						unit='dB',
						get_cmd='SETATT?',
						set_cmd='SETATT={}',
						get_parser=float,
						vals=Numbers(min_value=0, max_value=60))

		self.connect_message()

	@staticmethod
	def string_to_float(time_string):
		value, prefix = time_string.split(maxsplit=1)
		if prefix == 'Sec':
			value = float(value)
			return value
		elif prefix == 'mSec':
			value = float(value)*1e-3
			return value
		elif prefix == 'uSec':
			value = float(value)*1e-6
			return value

	def get_idn(self):
		return {'vendor': 'Mini-Circuits',
				'model': self.ask('*MN?'),
				'serial': self.ask('*SN?'),
				'firmware': self.ask('*FIRMWARE?')}

	def ask_raw(self, cmd):
		command = cmd + '\n\r'
		self.telnet.write(command.encode('ASCII'))
		data = self.telnet.read_until(b"\n\r", timeout=1).decode('ASCII').strip()
		return data

	def write_raw(self, cmd):
		command = cmd + '\n\r'
		self.telnet.write(command.encode('ASCII'))
		data = self.telnet.read_until(b"\n\r", timeout=1).strip()
		if data in [b'1']:
			pass
		elif data in [b'0']:
			raise ValueError('Command failed')
