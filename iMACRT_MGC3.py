# Alpha version, only transmission -Arpit

import qcodes as qc
from qcodes import Instrument,validators as vals

import socket





class iMACRT_MGC3(Instrument): 

	def __init__(self, name, IP, **kwargs):

		super().__init__(name, **kwargs)

		# self._IP = '192.168.1.23'
		self._IP = IP
		self._port = 12000+int(self._IP.split('.')[-1])

		self._channel = 0

		self.add_parameter( name = 'channel',  
							label = 'Channel',
							vals = vals.Enum(1,2,3),
							unit   = 'NA',
							set_cmd=self._set_channel,
							get_cmd=self._get_channel
							)

		self.add_parameter( name = 'status',  
							label = 'Status',
							vals = vals.Enum('on','off'),
							unit   = 'NA',
							set_cmd=self._set_status,
							get_cmd=self._get_status
							)

		self.add_parameter( name = 'setpoint',  
							label = 'Setpoint',
							vals = vals.Numbers(0,150),
							unit   = 'uW',
							set_cmd=self._set_setpoint,
							get_cmd=self._get_setpoint
							)

		self.add_parameter( name = 'P_max',  
							label = 'Maximum power',
							vals = vals.Numbers(0,150),
							unit   = 'uW',
							set_cmd=self._set_P_max,
							get_cmd=self._get_P_max
							)

		self.add_parameter( name = 'resistance',  
							label = 'Resistance',
							vals = vals.Numbers(0,1000),
							unit   = 'ohm',
							set_cmd=self._set_resistance,
							get_cmd=self._get_resistance
							)

		self.add_parameter( name = 'range',  
							label = 'Range',
							vals = vals.Enum(0,1,2,3,4),
							unit   = 'ohm',
							set_cmd=self._set_range,
							get_cmd=self._get_range
							)

		self.add_parameter( name = 'mode',  
							label = 'Regulation mode',
							vals = vals.Enum('current','power','temp'),
							unit   = 'NA',
							set_cmd=self._set_mode,
							get_cmd=self._get_mode
							)

		self.add_parameter( name = 'reboot',  
							label = 'Reboot iMACRT',
							vals = vals.Enum(1),
							unit   = 'NA',
							set_cmd=self._set_reboot
							)

		self.connect_message()


	def _set_channel(self, channel):
		self._channel = channel


	def _get_channel(self):
		return self._channel

	def _set_P_max(self, P_max):
		self._serial_send_only(7,P_max*1e-6)

	def _get_P_max(self):
		# get not working 
		do = 'nothing'

	def _set_resistance(self, resistance):
		self._serial_send_only(8,resistance*1e-6)

	def _get_resistance(self):
		# get not working 
		do = 'nothing'

	def _set_status(self, status):
		if status=='on':
			send=1
		else:
			send=0
		self._serial_send_only(1,send)

	def _get_status(self):
		# get not working
		do = 'nothing' 

	def _set_setpoint(self, setpoint):
		self._serial_send_only(2,setpoint*1e-6)

	def _get_setpoint(self):
		# get not working
		do = 'nothing' 

	def _set_range(self, range):
		self._serial_send_only('e',range)

	def _get_range(self):
		# get not working
		do = 'nothing' 

	def _set_mode(self, mode):
		if mode=='current':
			send=0
		elif mode=='power':
			send=1
		elif mode=='temp':
			send=2
		self._serial_send_only('f',send)

	def _get_mode(self):
		# get not working
		do = 'nothing' 

	def _set_reboot(self, reboot):
		sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		server_address_out = (self._IP,self._port)
		sock_out.connect(server_address_out)
		try:
		    message = b'REBOOT 1'
		    sock_out.sendall(message)
		finally:
		    sock_out.close()


	def _serial_send_only(self,parameter,value):
		sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		server_address_out = (self._IP,self._port)
		sock_out.connect(server_address_out)

		try:
		    # print('connecting to {} port {}'.format(*server_address_out))
		    # Send data
		    message = 'MACRTSET 0x'+str(self._channel*10)+str(parameter)+' '+str(value)
		    message = message.encode()
		    # print('sending {!r}'.format(message))
		    sock_out.sendall(message)
		finally:
		    sock_out.close()



	def _get_idn(self):
		return {'vendor': 'iMACRT', 'model': 'MGD3',
				'serial': None, 'firmware': None}