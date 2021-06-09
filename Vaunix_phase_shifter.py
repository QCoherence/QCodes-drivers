import qcodes as qc
from qcodes import Instrument,validators as vals
from ctypes import *



class Vaunix_phase_shifter(Instrument): 

	def __init__(self, name, serial, **kwargs):

		super().__init__(name, **kwargs)

		self._serial = serial
		self._vnx=cdll.VNX_dps64
		self._vnx.fnLPS_SetTestMode(False)
		self._DeviceIDArray = c_int * 20
		self._Devices = self._DeviceIDArray()


		self.add_parameter( name = 'working_freq',  
							label = 'Working frequency',
							vals = vals.Numbers(0.050,18),
							unit   = 'GHz',
							set_cmd=self._set_working_freq,
							get_cmd=self._get_working_freq
							)
		self.add_parameter('phase_shift',
							label = 'Phase_shift',
							vals = vals.Numbers(0,360),
							unit   = 'degree',
							set_cmd=self._set_phase,
							get_cmd=self._get_phase 
                            )


		self.connect_message()


	def _set_phase(self, phase):
		device_id = self._find_serial()
		init_dev = self._vnx.fnLPS_InitDevice(self._Devices[device_id])
		error = self._vnx.fnLPS_SetPhaseAngle(self._Devices[device_id], (int(phase)))


	def _get_phase(self):
		device_id = self._find_serial()
		init_dev = self._vnx.fnLPS_InitDevice(self._Devices[device_id])
		phase = self._vnx.fnLPS_GetPhaseAngle(self._Devices[device_id])
		return phase

	def _set_working_freq(self, freq):
		device_id = self._find_serial()
		init_dev = self._vnx.fnLPS_InitDevice(self._Devices[device_id])
		error = self._vnx.fnLPS_SetWorkingFrequency(self._Devices[device_id], int(freq*10000))

	def _get_working_freq(self):
		device_id = self._find_serial()
		init_dev = self._vnx.fnLPS_InitDevice(self._Devices[device_id])
		freq = self._vnx.fnLPS_GetWorkingFrequency(self._Devices[device_id])
		return freq/10000.0

	def _find_serial(self):
		dev_info = self._vnx.fnLPS_GetDevInfo(self._Devices)
		ret=99
		for i in range(0,dev_info):
			ser_num = self._vnx.fnLPS_GetSerialNumber(self._Devices[i])
			if str(ser_num) == self._serial:
				ret=i
		return ret



	def get_idn(self):
		return {'vendor': 'Vaunix phase shifter', 'model': 'LPS-802',
				'serial': self._serial, 'firmware': None}

	# For debugging
	def connected_devices():
		vnx=cdll.VNX_dps64
		#vnx.fnLPS_SetTestMode(False)
		DeviceIDArray = c_int * 20
		Devices = DeviceIDArray()
		numDevices = vnx.fnLPS_GetNumDevices()
		print(str(numDevices)+'  phase shifter(s) found with serial number(s):\n')
		dev_info = vnx.fnLPS_GetDevInfo(Devices)
		# print('GetDevInfo returned', str(dev_info))
		for i in range(0,dev_info):
			ser_num = vnx.fnLPS_GetSerialNumber(Devices[i])
			print('    '+str(i+1)+'. ', str(ser_num))

	def connected_devices_class(self):
		vnx=cdll.VNX_dps64
		#vnx.fnLPS_SetTestMode(False)
		DeviceIDArray = c_int * 20
		Devices = DeviceIDArray()
		numDevices = vnx.fnLPS_GetNumDevices()
		print(str(numDevices)+'  phase shifter(s) found with serial number(s):\n')
		dev_info = vnx.fnLPS_GetDevInfo(Devices)
		# print('GetDevInfo returned', str(dev_info))
		for i in range(0,dev_info):
			ser_num = vnx.fnLPS_GetSerialNumber(Devices[i])
			print('    '+str(i+1)+'. ', str(ser_num))
