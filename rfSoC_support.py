import sys
import numpy as np
import scipy.optimize as optimization
sys.path.append('C:/QCodes drivers and scripts/Drivers')


import qcodes as qc
from qcodes.logger.logger import start_all_logging
import datetime
from qcodes.dataset.plotting import plot_dataset
import numpy as np
import matplotlib.pyplot as plt
#qcodes.config.subscription.default_subscribers = ["Plottr"]
from time import sleep
import time

from pprint import pprint
import json

import sys
import numpy as np
import scipy.optimize as optimization

sys.path.append('C:/QCodes drivers and scripts/Scripts/Arpit/Modules')
from notify import snotify
from progress_barV2 import bar
from general_functions import find_nearest

import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt







def optimize_IQ_balance(rfsoc_device,nu,nu_det_offset,display_plots=False,amp=0.05,dc_offset_I=8,dc_offset_Q=6,active_mode='lower',acq_length = 10, adc_start = 1.0):

	mem_seq_display = rfsoc_device.display_sequence
	rfsoc_device.display_sequence = False

	phase_vec = np.arange(0,360,10)
	data_down = np.array([])
	data_up = np.array([])
	num_repetitions = 10_000

	for phase_offset in phase_vec:
			
		param_sin_I = {'amp':amp,
					 'freq':nu,
					 'dc_offset':dc_offset_I*1e-3,
					 'phase_offset':0}

		param_sin_Q = {'amp':amp,
					 'freq':nu,
					 'dc_offset':dc_offset_Q*1e-3,
					 'phase_offset':np.pi*phase_offset/180} 
		
		
		
		pulse_sin = dict(label='signal+pump', 
							  module='DAC', 
							  channel=1, 
							  mode='sin', 
							  start=0, 
							  length=acq_length+2, 
							  param=param_sin_I, 
							  parent=None)

		record_sin = dict(label='record_both', 
							  module='ADC', 
							  channel=1, 
							  mode='raw', 
							  start=adc_start, 
							  length=acq_length, 
							  param=None, 
							  parent=None)

		pulse_sin2 = dict(label='signal+pump2', 
							  module='DAC', 
							  channel=2, 
							  mode='sin', 
							  start=0, 
							  length=acq_length+2, 
							  param=param_sin_Q, 
							  parent=None)

		record_sin2 = dict(label='record_both2', 
							  module='ADC', 
							  channel=2, 
							  mode='raw', 
							  start=adc_start, 
							  length=acq_length, 
							  param=None, 
							  parent=None)

		
		
		
		
		pulses = pd.DataFrame()
		pulses = pulses.append(pulse_sin, ignore_index=True)
		pulses = pulses.append(record_sin, ignore_index=True)
		pulses = pulses.append(pulse_sin2, ignore_index=True)
		pulses = pulses.append(record_sin2, ignore_index=True)

		rfsoc_device.pulses = pulses


		rfsoc_device.acquisition_mode('IQ')
		rfsoc_device.ADC1.fmixer(nu-nu_det_offset)#MHz
		rfsoc_device.ADC2.fmixer(nu+nu_det_offset)#MHz
		rfsoc_device.freq_sync(1e6)
		rfsoc_device.ADC1.status('ON')
		rfsoc_device.ADC2.status('ON')
		rfsoc_device.output_format('BIN')
		rfsoc_device.n_rep(num_repetitions)


		rfsoc_device.process_sequencing()
		
		data_raw = rfsoc_device.ADC_power_dBm()[:2]

		data_down = np.append(data_down,data_raw[0])
		data_up = np.append(data_up,data_raw[1])

	if display_plots:

		plt.figure(figsize=(14, 10), dpi= 80) #facecolor='w', edgecolor='k'
		x_label='Phase [degree]'
		y_label='PSD [dBm]'

		plt.rc('axes', labelsize=10)    # fontsize of the x and y labels
		plt.rc('xtick', labelsize=12)    # fontsize of the tick labels
		plt.rc('ytick', labelsize=12)    # fontsize of the tick labels
		plt.rc('grid', linestyle="--")
		plt.grid(True)

		plt.plot(phase_vec,data_down,label='data_ch1')
		plt.plot(phase_vec,data_up,label='data_ch2')

		plt.xlabel(x_label, size=14)
		plt.ylabel(y_label, size=14)

		plt.legend(fontsize = 12)
		plt.show()

	optimal_phase_1 = phase_vec[find_nearest(data_up,np.min(data_up))]

	phase_vec = np.arange(optimal_phase_1-5,optimal_phase_1+5,1)
	data_down = np.array([])
	data_up = np.array([])

	for phase_offset in phase_vec:
			
		param_sin_I = {'amp':amp,
					 'freq':nu,
					 'dc_offset':dc_offset_I*1e-3,
					 'phase_offset':0}

		param_sin_Q = {'amp':amp,
					 'freq':nu,
					 'dc_offset':dc_offset_Q*1e-3,
					 'phase_offset':np.pi*phase_offset/180} 
		
		
		
		pulse_sin = dict(label='signal+pump', 
							  module='DAC', 
							  channel=1, 
							  mode='sin', 
							  start=0, 
							  length=acq_length+2, 
							  param=param_sin_I, 
							  parent=None)

		record_sin = dict(label='record_both', 
							  module='ADC', 
							  channel=1, 
							  mode='raw', 
							  start=adc_start, 
							  length=acq_length, 
							  param=None, 
							  parent=None)

		pulse_sin2 = dict(label='signal+pump2', 
							  module='DAC', 
							  channel=2, 
							  mode='sin', 
							  start=0, 
							  length=acq_length+2, 
							  param=param_sin_Q, 
							  parent=None)

		record_sin2 = dict(label='record_both2', 
							  module='ADC', 
							  channel=2, 
							  mode='raw', 
							  start=adc_start, 
							  length=acq_length, 
							  param=None, 
							  parent=None)

		
		
		
		
		pulses = pd.DataFrame()
		pulses = pulses.append(pulse_sin, ignore_index=True)
		pulses = pulses.append(record_sin, ignore_index=True)
		pulses = pulses.append(pulse_sin2, ignore_index=True)
		pulses = pulses.append(record_sin2, ignore_index=True)

		rfsoc_device.pulses = pulses


		rfsoc_device.acquisition_mode('IQ')
		rfsoc_device.ADC1.fmixer(nu-nu_det_offset)#MHz
		rfsoc_device.ADC2.fmixer(nu+nu_det_offset)#MHz
		rfsoc_device.freq_sync(1e6)
		rfsoc_device.ADC1.status('ON')
		rfsoc_device.ADC2.status('ON')
		rfsoc_device.output_format('BIN')
		rfsoc_device.n_rep(num_repetitions)


		rfsoc_device.process_sequencing()
		
		data_raw = rfsoc_device.ADC_power_dBm()[:2]

		data_down = np.append(data_down,data_raw[0])
		data_up = np.append(data_up,data_raw[1])

	if display_plots:

		plt.figure(figsize=(14, 10), dpi= 80) #facecolor='w', edgecolor='k'
		x_label='Phase [degree]'
		y_label='PSD [dBm]'

		plt.rc('axes', labelsize=10)    # fontsize of the x and y labels
		plt.rc('xtick', labelsize=12)    # fontsize of the tick labels
		plt.rc('ytick', labelsize=12)    # fontsize of the tick labels
		plt.rc('grid', linestyle="--")
		plt.grid(True)

		plt.plot(phase_vec,data_down,label='data_ch1')
		plt.plot(phase_vec,data_up,label='data_ch2')

		plt.xlabel(x_label, size=14)
		plt.ylabel(y_label, size=14)

		plt.legend(fontsize = 12)
		plt.show()

	rfsoc_device.display_sequence = mem_seq_display

	return phase_vec[find_nearest(data_up,np.min(data_up))]








class gain_signal_idler_cls:

	def __init__(self, rfsoc_device):

		self.rfsoc_device = rfsoc_device
		self.amp_if = 0
		self.nu_if = 160
		self.delta = 50

		self.phase_offset_if = 0    # degrees
		self.phase_offset_sig = 0    # degrees
		self.phase_offset_idl = 0   # degrees
		self.dc_offset_I = 8 # mV
		self.dc_offset_Q = 6 # mV

		self.amp_sig = 0.0005
		self.acq_length = 10.0
		self.adc_start = 1.0
		self.wait_between_pulses = 0
		self.num_rep = 10_000


	def g(self):

		nu_if = self.nu_if
		delta = self.delta
		dc_offset_I = self.dc_offset_I
		dc_offset_Q = self.dc_offset_Q
		phase_offset_if = self.phase_offset_if
		phase_offset_sig = self.phase_offset_sig
		phase_offset_idl = self.phase_offset_idl
		acq_length = self.acq_length
		adc_start = self.adc_start
		wait_between_pulses = self.wait_between_pulses
		num_rep = self.num_rep

		nu_sig = nu_if + delta
		nu_idl = nu_if - delta

		amp_sig = self.amp_sig
		amp_coeff = self.amp_if

		rfsoc_device = self.rfsoc_device

		mem_display_sequence = rfsoc_device.display_sequence
		rfsoc_device.display_sequence = False

		param_sinsin_I = {'amp1':amp_coeff,
						'phase_offset1':0,
						'freq1':nu_if,
						'amp2':amp_sig,
						'freq2':nu_idl,
						'phase_offset2':0,
						'dc_offset':dc_offset_I*1e-3}

		param_sinsin_Q = {'amp1':amp_coeff,
						'phase_offset1':np.pi*phase_offset_if/180,
						'freq1':nu_if,
						'amp2':amp_sig,
						'freq2':nu_idl,
						'phase_offset2':np.pi*phase_offset_idl/180,
						'dc_offset':dc_offset_Q*1e-3}

		param_sin_I = {'amp':amp_sig,
					 'freq':nu_idl,
					 'dc_offset':dc_offset_I*1e-3,
					 'phase_offset':0}

		param_sin_Q = {'amp':amp_sig,
					 'freq':nu_idl,
					 'dc_offset':dc_offset_Q*1e-3,
					 'phase_offset':np.pi*phase_offset_idl/180}


		pulse_sinsin = dict(label='signal+pump', 
							  module='DAC', 
							  channel=1, 
							  mode='sin+sin', 
							  start=0, 
							  length=acq_length+2, 
							  param=param_sinsin_I, 
							  parent=None)

		pulse_sin = dict(label='signal', 
							  module='DAC', 
							  channel=1, 
							  mode='sin', 
							  start=wait_between_pulses, 
							  length=acq_length+2, 
							  param=param_sin_I, 
							  parent='signal+pump')

		record_sinsin = dict(label='record_both', 
							  module='ADC', 
							  channel=1, 
							  mode='iq', 
							  start=adc_start, 
							  length=acq_length, 
							  param=None, 
							  parent=None)

		record_sin = dict(label='record_signal', 
							  module='ADC', 
							  channel=1, 
							  mode='iq', 
							  start=adc_start+wait_between_pulses, 
							  length=acq_length, 
							  param=None, 
							  parent='signal+pump')

		pulse_sinsin2 = dict(label='signal+pump2', 
							  module='DAC', 
							  channel=2, 
							  mode='sin+sin', 
							  start=0, 
							  length=acq_length+2, 
							  param=param_sinsin_Q, 
							  parent=None)

		pulse_sin2 = dict(label='signal2', 
							  module='DAC', 
							  channel=2, 
							  mode='sin', 
							  start=wait_between_pulses, 
							  length=acq_length+2, 
							  param=param_sin_Q, 
							  parent='signal+pump')

		record_sinsin2 = dict(label='record_both2', 
							  module='ADC', 
							  channel=2, 
							  mode='iq', 
							  start=adc_start, 
							  length=acq_length, 
							  param=None, 
							  parent=None)

		record_sin2 = dict(label='record_signal2', 
							  module='ADC', 
							  channel=2, 
							  mode='iq', 
							  start=adc_start+wait_between_pulses, 
							  length=acq_length, 
							  param=None, 
							  parent='signal+pump')



		pulses = pd.DataFrame()
		pulses = pulses.append(pulse_sinsin, ignore_index=True)
		pulses = pulses.append(pulse_sin, ignore_index=True)
		pulses = pulses.append(record_sinsin, ignore_index=True)
		pulses = pulses.append(record_sin, ignore_index=True)
		pulses = pulses.append(pulse_sinsin2, ignore_index=True)
		pulses = pulses.append(pulse_sin2, ignore_index=True)
		pulses = pulses.append(record_sinsin2, ignore_index=True)
		pulses = pulses.append(record_sin2, ignore_index=True)

		rfsoc_device.pulses = pulses

		rfsoc_device.acquisition_mode('IQ')
		rfsoc_device.ADC1.decfact(1)
		rfsoc_device.ADC2.decfact(1)
		rfsoc_device.freq_sync(1e6)
		rfsoc_device.ADC1.status('ON')
		rfsoc_device.ADC2.status('ON')
		rfsoc_device.output_format('BIN')
		rfsoc_device.n_rep(num_rep)
		rfsoc_device.process_sequencing()
		
		data_idl = np.array(rfsoc_device.ADC_power_dBm()[0:2])            
		
		
		####### SIGNAL Gain
		
		param_sinsin_I = {'amp1':amp_coeff,
						'phase_offset1':0,
						'freq1':nu_if,
						'amp2':amp_sig,
						'freq2':nu_sig,
						'phase_offset2':0,
						'dc_offset':dc_offset_I*1e-3}

		param_sinsin_Q = {'amp1':amp_coeff,
						'phase_offset1':np.pi*phase_offset_if/180,
						'freq1':nu_if,
						'amp2':amp_sig,
						'freq2':nu_sig,
						'phase_offset2':np.pi*phase_offset_sig/180,
						'dc_offset':dc_offset_Q*1e-3}

		param_sin_I = {'amp':amp_sig,
					 'freq':nu_sig,
					 'dc_offset':dc_offset_I*1e-3,
					 'phase_offset':0}

		param_sin_Q = {'amp':amp_sig,
					 'freq':nu_sig,
					 'dc_offset':dc_offset_Q*1e-3,
					 'phase_offset':np.pi*phase_offset_sig/180}


		pulse_sinsin = dict(label='signal+pump', 
							  module='DAC', 
							  channel=1, 
							  mode='sin+sin', 
							  start=0, 
							  length=acq_length+2, 
							  param=param_sinsin_I, 
							  parent=None)

		pulse_sin = dict(label='signal', 
							  module='DAC', 
							  channel=1, 
							  mode='sin', 
							  start=wait_between_pulses, 
							  length=acq_length+2, 
							  param=param_sin_I, 
							  parent='signal+pump')

		record_sinsin = dict(label='record_both', 
							  module='ADC', 
							  channel=1, 
							  mode='iq', 
							  start=adc_start, 
							  length=acq_length, 
							  param=None, 
							  parent=None)

		record_sin = dict(label='record_signal', 
							  module='ADC', 
							  channel=1, 
							  mode='iq', 
							  start=adc_start+wait_between_pulses, 
							  length=acq_length, 
							  param=None, 
							  parent='signal+pump')

		pulse_sinsin2 = dict(label='signal+pump2', 
							  module='DAC', 
							  channel=2, 
							  mode='sin+sin', 
							  start=0, 
							  length=acq_length+2, 
							  param=param_sinsin_Q, 
							  parent=None)

		pulse_sin2 = dict(label='signal2', 
							  module='DAC', 
							  channel=2, 
							  mode='sin', 
							  start=wait_between_pulses, 
							  length=acq_length+2, 
							  param=param_sin_Q, 
							  parent='signal+pump')

		record_sinsin2 = dict(label='record_both2', 
							  module='ADC', 
							  channel=2, 
							  mode='iq', 
							  start=adc_start, 
							  length=acq_length, 
							  param=None, 
							  parent=None)

		record_sin2 = dict(label='record_signal2', 
							  module='ADC', 
							  channel=2, 
							  mode='iq', 
							  start=adc_start+wait_between_pulses, 
							  length=acq_length, 
							  param=None, 
							  parent='signal+pump')



		pulses = pd.DataFrame()
		pulses = pulses.append(pulse_sinsin, ignore_index=True)
		pulses = pulses.append(pulse_sin, ignore_index=True)
		pulses = pulses.append(record_sinsin, ignore_index=True)
		pulses = pulses.append(record_sin, ignore_index=True)
		pulses = pulses.append(pulse_sinsin2, ignore_index=True)
		pulses = pulses.append(pulse_sin2, ignore_index=True)
		pulses = pulses.append(record_sinsin2, ignore_index=True)
		pulses = pulses.append(record_sin2, ignore_index=True)

		rfsoc_device.pulses = pulses

		rfsoc_device.acquisition_mode('IQ')
		rfsoc_device.ADC1.decfact(1)
		rfsoc_device.ADC2.decfact(1)
		rfsoc_device.freq_sync(1e6)
		rfsoc_device.ADC1.status('ON')
		rfsoc_device.ADC2.status('ON')
		rfsoc_device.output_format('BIN')
		rfsoc_device.n_rep(num_rep)
		rfsoc_device.process_sequencing()
		
		data_sig = np.array(rfsoc_device.ADC_power_dBm()[0:2])
		
#             data_tmp.append(data_sig)
		
		
		gain_sig = data_sig[0,0]-data_sig[0,1]
		gain_idl = data_idl[1,0]-data_idl[1,1]
		
		data_save = np.array([np.array([gain_sig,gain_idl]),np.array([data_sig[0,0],data_idl[1,0]]),np.array([data_sig[0,1],data_idl[1,1]])])

		rfsoc_device.display_sequence = mem_display_sequence

		return(data_save)
