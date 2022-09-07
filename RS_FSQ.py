#
# *** Warning: Alpha version driver with functionalities under development.
#
# Last updated on 6 Mar 2020
#                     -- Arpit


import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter,
					validators as vals)
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter
from qcodes.utils.validators import Numbers, Arrays


from time import sleep
import numpy as np







class GeneratedSetPoints(Parameter):
    """
    A parameter that generates a setpoint array from start, stop and num points
    parameters.
    """
    def __init__(self, startparam, stopparam, numpointsparam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._startparam = startparam
        self._stopparam = stopparam
        self._numpointsparam = numpointsparam

    def get_raw(self):
        return np.linspace(self._startparam(), self._stopparam(),
                              self._numpointsparam())

class SpectrumTrace(ParameterWithSetpoints):

    def get_raw(self):
        data = self._instrument.get_trace()
        return data

class HarmonicTrace(ParameterWithSetpoints):
class HarmonicTrace(ParameterWithSetpoints):

    def get_raw(self):
        data = self._instrument.get_harmonic()
        return data

    def get_raw(self):
        data = self._instrument.get_harmonic()
        return data



class RS_FSQ(VisaInstrument):

	sense_num=1

	"""
	QCoDeS driver for the R&S FSQ Signal Analyzer
	"""

	# all instrument constructors should accept **kwargs and pass them on to
	# super().__init__

	def __init__(self, name, address, **kwargs):
		# supplying the terminator means you don't need to remove it from every response
		super().__init__(name, address, terminator='\n', timeout=5, **kwargs)

		# self.add_parameter('timeout',
		# 					get_cmd=self._get_visa_timeout,
		# 					set_cmd=self._set_visa_timeout,
		# 					unit='s',
		# 					vals=vals.MultiType(vals.Numbers(min_value=0),vals.Enum(None))
		# 					)

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
							get_cmd='SENSe'+str(self.sense_num)+':BANDwidth:VIDeo?',
							# set_parser =self.,
							# get_parser=self.
							snapshot_value = False
							)

		self.add_parameter( name = 'sweep_time',  
							label = 'Sweep time',
							vals = vals.Numbers(1e-6,16e3),
							unit   = 's',
							set_cmd='SENSe'+str(self.sense_num)+'SWEep:TIME ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+'SWEep:TIME?',
							snapshot_value = False
							# set_parser =self.,
							# get_parser=self.
							)


		self.add_parameter( name = 'sweep_time_direct',  
							label = 'Sweep time without sense',
							vals = vals.Numbers(1e-6,16e6),
							unit   = 'us',
							set_cmd='SWEep:TIME ' + '{:.12f}'+' us',
							get_cmd='SWEep:TIME?'
							# set_parser =self.,
							# get_parser=self.
							)		

		self.add_parameter( name = 'input_att',
							label = 'Input attenuation',
							vals = vals.Numbers(0,50),
							unit   = 'dB',
							set_cmd='SENSe'+str(self.sense_num)+':POWer:RF:ATTenuation ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':POWer:RF:ATTenuation?',
							snapshot_value = False,
							snapshot_value = False
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
							get_parser=self.caps_dag,
							snapshot_value = False,
							snapshot_value = False
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
							vals = vals.Numbers(0,1000),
							unit   = 'NA',
							set_cmd='SENSe'+str(self.sense_num)+':AVERage:COUNt ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':AVERage:COUNt?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'n_points',
							label = 'Number of points in trace',
							vals = vals.Numbers(155,30001),
							unit   = '',
							set_cmd='SENSe'+str(self.sense_num)+':SWEep:POINts ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':SWEep:POINts?',
							set_parser =self.sweep_point_check,
							get_parser=int
							)

		self.add_parameter( name = 'span',
							label = 'Span',
							vals = vals.Numbers(0,26.5e9),
							unit   = 'Hz',
							set_cmd='SENSe'+str(self.sense_num)+':FREQuency:SPAN ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':FREQuency:SPAN?',
							snapshot_value = False,
							snapshot_value = False
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'average_type',
							label = 'Average type',
							vals = vals.Enum('rms','log','scalar'),
							unit   = 'NA',
							set_cmd=self._set_average_type,
							get_cmd='SENSe'+str(self.sense_num)+':AVERage:TYPE?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'f_start',
							label = 'Start frequency',
							vals = vals.Numbers(20,26.5e9),
							unit   = 'Hz',
							set_cmd='SENSe'+str(self.sense_num)+':FREQuency:STARt ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':FREQuency:STARt?',
							# set_parser =self.,
							get_parser=float,
							snapshot_value = False
							)

		self.add_parameter( name = 'f_stop',
							label = 'Stop frequency',
							vals = vals.Numbers(20,26.5e9),
							unit   = 'Hz',
							set_cmd='SENSe'+str(self.sense_num)+':FREQuency:STOP ' + '{:.12f}',
							get_cmd='SENSe'+str(self.sense_num)+':FREQuency:STOP?',
							# set_parser =self.,
							get_parser=float,
							snapshot_value = False
							)

		self.add_parameter( name = 'ref_level',
							label = 'Reference level(AMPT)',
							vals = vals.Numbers(-130,30),
							unit   = 'dBm',
							set_cmd=':DISP:WIND:TRAC:Y:RLEV  ' + '{:.12f}'+'dBm',
							get_cmd=':DISP:WIND:TRAC:Y:RLEV?',
							# set_parser =self.,
							get_parser=float
							)



		self.add_parameter('freq_axis',
							unit='Hz',
							label='Freq Axis',
							parameter_class=GeneratedSetPoints,
							startparam=self.f_start,
							stopparam=self.f_stop,
							numpointsparam=self.n_points,
							vals=Arrays(shape=(self.n_points.get_latest,)),
							snapshot_value = False)


		self.add_parameter( name = 'n_harmonics',  
							label = 'No.of harmonic',
							vals = vals.Numbers(1,26),
							# unit   = 'Hz',
							set_cmd='CALC:MARK:FUNC:HARM:NHAR ' + '{:.12f}',
							# set_parser =self.,
							get_parser=float,
							snapshot_value = False
							)	

		self.add_parameter('freq_axis_harmonic',
							unit='Hz',
							label='Freq Axis_harmonic',
							parameter_class=GeneratedSetPoints,
							startparam=self.get_1,
							stopparam=self.n_harmonics,
							numpointsparam=(self.n_harmonics),
							vals=Arrays(shape=(self.n_harmonics.get_latest,)),
							snapshot_value = False)

		self.add_parameter('spectrum',
							unit='dBm',
							setpoints=(self.freq_axis,),
							label='Spectrum',
							parameter_class=SpectrumTrace,
							vals=Arrays(shape=(self.n_points.get_latest,)))



		self.add_parameter( name = 'set_harmonic',  
							label = 'Harmonic function ON',
							# vals = vals.Numbers(10,50e6),
							vals = vals.Enum('ON','OFF'),
							#unit   = 'Hz',
							set_cmd='CALC:MARK:FUNC:HARM:STAT '+ '{} '
							# get_cmd='BANDwidth:RESolution?'
							# set_parser =self.,
							# get_parser=self.
							)

		# self.add_parameter( name = 'reset_harmonic',  
		# 					label = 'Harmonic function OFF',
		# 					# vals = vals.Numbers(10,50e6),
		# 					#unit   = 'Hz',
		# 					set_cmd='CALC:MARK:FUNC:HARM:STAT OFF '
		# 					# get_cmd='BANDwidth:RESolution?'
		# 					# set_parser =self.,
		# 					# get_parser=self.
							# )

		

		# self.add_parameter( name = 'time_harmonic',  
		# 					label = 'sweep time harmonic',
		# 					vals = vals.Numbers(10,1000),
		# 					# unit   = 'Hz',
		# 					set_cmd='SWE:TIME ' + '{:.12f}'+ 'us',
		# 					# set_parser =self.,
		# 					# get_parser=float
		# 					)
		self.add_parameter( 'harmonic',
							unit='dBm/c',
							setpoints=(self.freq_axis_harmonic,),
							label='Spectrum',
							parameter_class=HarmonicTrace,
							vals=Arrays(shape=(self.n_harmonics.get_latest,))

			                # name = 'meas_harmonic',  
							# label = 'Meausure harmonics', # values in dBc
							# vals = vals.Numbers(10,50e6),
							#unit   = 'Hz',
							# get_cmd='CALC:MARK:FUNC:HARM:LIST?'
							# set_parser =self.,
							# get_parser=self.
							)

		self.add_parameter( name = 'setauto_rbw_harmonic',  
							label = 'Resolution bandwidth harmonic',
							vals = vals.Enum('ON','OFF'),
							# unit   = 'Hz',
							set_cmd='CALC:MARK:FUNC:HARM:BAND:AUTO ' +'{}'
							# set_parser =self.,
							# get_parser=float
							)

		# self.add_parameter( name = 'unsetauto_rbw_harmonic',  
		# 					label = 'Resolution bandwidth harmonic',
		# 					# unit   = 'Hz',
		# 					set_cmd='CALC:MARK:FUNC:HARM:BAND:AUTO OFF' ,
		# 					# set_parser =self.,
		# 					# get_parser=float
		# 					)




		self.connect_message()



	def get_1(self):
		return 1

	def _set_average_type(self,val : str):
		sense_num = self.sense_num
		self.write(f"SENSe{sense_num}:AVERage:TYPE {val}")

	def get_trace(self):
		self.write('*CLS')
		self.write('SYST:DISP:UPD ON')
		self.write(':INIT:CONT OFF')
		self.write(':INIT:IMMediate;*OPC')
		while self.ask('*ESR?') == '0':
		    sleep(1) # we wait until the register is 1
		datastr = self.ask(':TRAC? TRACE'+str(1))
		datalist = datastr.split(",")
		dataflt = []
		for val in datalist:
		    dataflt.append(float(val))
		dataflt=np.array(dataflt)
		return dataflt


	def get_harmonic(self):
		self.write('*CLS')
		# self.write(':INIT:CONT OFF')
		# self.write(':INIT:IMMediate;*OPC')
        #while self.ask('*ESR?') == '0': 
		    #sleep(1) # we wait until the register is 1
		datastr=self.ask('CALC:MARK:FUNC:HARM:LIST?') 
		    # sleep(1) # we wait until the register is 1
		# datastr = self.ask(':TRAC? TRACE'+str(1))

		datalist = datastr.split(",")
		dataflt = []
		for val in datalist:
		    dataflt.append(float(val))
		dataflt=np.array(dataflt)
		return dataflt

	def sweep_point_check(self, points):
		if points<701:
			valid_values=np.array([155, 201, 301, 313, 401, 501, 601, 625])
			if points in valid_values:
				points_checked=points
			else:
				points_checked=valid_values[(np.abs(valid_values-points)).argmin()]
				print('### Warning: Invalid sweep points, set to '+str(points_checked))
		else:
			if (points-1)%100==0:
				points_checked=points
			else:
				points_checked=round(points/100,0)*100+1
				print('### Warning: Invalid sweep points, set to '+str(points_checked))
		return int(points_checked)

	def caps(string):
		return string.upper()

	def caps_dag(string):
		return string.lower()

	# def _set_visa_timeout(self, timeout) -> None:

	# 	if timeout is None:
	# 		self.visa_handle.timeout = None
	# 	else:
	# 		# pyvisa uses milliseconds but we use seconds
	# 		self.visa_handle.timeout = timeout * 1000.0

	# def _get_visa_timeout(self):

	# 	timeout_ms = self.visa_handle.timeout
	# 	if timeout_ms is None:
	# 		return None
	# 	else:
	# 		# pyvisa uses milliseconds but we use seconds
	# 		return timeout_ms / 1000


	# Functions for debugging
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
