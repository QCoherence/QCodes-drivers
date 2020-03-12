# Alpha version -Arpit

import qcodes as qc
from qcodes import Instrument,validators as vals
from ctypes import *





class Vaunix_attn(Instrument): 

	def __init__(self, name, serial, **kwargs):

		super().__init__(name, **kwargs)

		self._serial = serial

		self._vnx=cdll.VNX_atten64
		self._vnx.fnLDA_SetTestMode(False)
		self._DeviceIDArray = c_int * 20
		self._Devices = self._DeviceIDArray()

		self.add_parameter( name = 'attn',  
							label = 'Attenuation',
							vals = vals.Numbers(0,50),
							unit   = 'dB',
							set_cmd=self._set_attn,
							get_cmd=self._get_attn
							)

		self.add_parameter( name = 'working_freq',  
							label = 'Working frequency',
							vals = vals.Numbers(0.050,18),
							unit   = 'GHz',
							set_cmd=self._set_working_freq,
							get_cmd=self._get_working_freq
							)

		self.connect_message()


	def _set_attn(self, attn):
		device_id = self._find_serial()
		init_dev = self._vnx.fnLDA_InitDevice(self._Devices[device_id])
		error = self._vnx.fnLDA_SetAttenuationHR(self._Devices[device_id], int(attn*20))


	def _get_attn(self):
		device_id = self._find_serial()
		init_dev = self._vnx.fnLDA_InitDevice(self._Devices[device_id])
		attn = self._vnx.fnLDA_GetAttenuationHR(self._Devices[device_id])
		return attn*0.05

	def _set_working_freq(self, freq):
		device_id = self._find_serial()
		init_dev = self._vnx.fnLDA_InitDevice(self._Devices[device_id])
		error = self._vnx.fnLDA_SetWorkingFrequency(self._Devices[device_id], int(freq*10000))

	def _get_working_freq(self):
		device_id = self._find_serial()
		init_dev = self._vnx.fnLDA_InitDevice(self._Devices[device_id])
		freq = self._vnx.fnLDA_GetWorkingFrequency(self._Devices[device_id])
		return freq/10000.0

	def _find_serial(self):
		dev_info = self._vnx.fnLDA_GetDevInfo(self._Devices)
		ret=99
		for i in range(0,dev_info):
			ser_num = self._vnx.fnLDA_GetSerialNumber(self._Devices[i])
			if str(ser_num) == self._serial:
				ret=i
		return ret



	def get_idn(self):
		return {'vendor': 'Vaunix digital attenuator', 'model': 'LDA-5018V',
				'serial': self._serial, 'firmware': None}

	# For debugging
	def connected_devices():
		vnx=cdll.VNX_atten64
		vnx.fnLDA_SetTestMode(False)
		DeviceIDArray = c_int * 20
		Devices = DeviceIDArray()
		numDevices = vnx.fnLDA_GetNumDevices()
		print(str(numDevices)+'  attenuator(s) found with serial number(s):\n')
		dev_info = vnx.fnLDA_GetDevInfo(Devices)
		# print('GetDevInfo returned', str(dev_info))
		for i in range(0,dev_info):
			ser_num = vnx.fnLDA_GetSerialNumber(Devices[i])
			print('    '+str(i+1)+'. ', str(ser_num))
