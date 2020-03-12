# -*- coding: utf-8 -*-
# This is a Qcodes driver for Redpitaya card SCPI IQ server 
# written by Martina Esposito and Arpit Ranadive, 2019/2020
# This driver is a Qcodes version of the qtlab driver 'redpitaya_qtlab.py' written by Sebastian
#

from time import sleep
import time 
import numpy as np
#import qt
#import ctypes  # only for DLL-based instrument

import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
                    ManualParameter, MultiParameter,
                    validators as vals)
from qcodes.instrument.channel import InstrumentChannel
import matplotlib.pyplot as plt


class Redpitaya(VisaInstrument): 
    """
    QCoDeS driver for the Redpitaya
    """
    
    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__
    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name, address, terminator='\r\n', **kwargs)
        
        
        self.add_parameter( name = 'freq_filter',  
                            #frequency of the low pass filter
                            label = 'Low pass filter cut-off freq',
                            vals = vals.Numbers(10e3,62.5e6),      
                            unit   = 'Hz',
                            set_cmd='FILTER:FREQ ' + '{:.12f}',
                            get_cmd='FILTER:FREQ?',
                            get_parser=float
                            )

        self.add_parameter( name = 'decimation_filter',
                            # number of decimated points  
                            label = 'Decimated points',
                            # unit   = 'Hz',
                            vals = vals.Numbers(10,65535),
                            set_cmd='FILTER:DEC ' + '{:.12f}',
                            get_cmd='FILTER:DEC?',
                            get_parser=int
                            )

        self.add_parameter( name = 'start_ADC',  
                            # Starting point of the ADC aquisition in second
                            label = 'Acquisition starting time',
                            unit   = 's',
                            vals = vals.Numbers(0,8191*8e-9),  #8192 is the maximum number of samples that can be generated (65 us)
                            set_cmd='ADC:STARTPOS '  + '{}',
                            get_cmd='ADC:STARTPOS?',
                            set_parser = self.get_samples_from_sec,
                            get_parser=self.get_sec_from_samples
                            )

        self.add_parameter( name = 'stop_ADC', 
                            #stopping point of the aquisition 
                            label = 'Acquisition stopping time',
                            unit   = 's',
                            vals = vals.Numbers(0,8191*8e-9),  #8192 is the maximum number of samples that can be generated (65 us)
                            set_cmd='ADC:STOPPOS ' + '{:.12f}',
                            get_cmd='ADC:STOPPOS?',
                            set_parser = self.get_samples_from_sec,
                            get_parser=self.get_sec_from_samples
                            )

        self.add_parameter( name = 'stop_DAC', 
                            #stopping point of the LUT (Look-Up Table) 
                            label = 'Stopping time of the LUT ',
                            unit   = 's',
                            vals = vals.Numbers(0,8192*8e-9),   #8192 is the maximum number of samples that can be generated (65 us)
                            set_cmd='DAC:STOPPOS ' + '{:.12f}',
                            get_cmd='DAC:STOPPOS?',
                            set_parser = self.get_samples_from_sec,
                            get_parser=self.get_sec_from_samples
                            )

        self.add_parameter( name = 'period',  
                            #period in second
                            label = 'Period',
                            unit  = 's',
                            vals = vals.Numbers(0,1),
                            set_cmd='PERIOD '+ '{}',
                            get_cmd='PERIOD?',
                            set_parser =self.get_samples_from_sec,
                            get_parser=self.get_sec_from_samples
                            )
  
        self.add_parameter( name = 'mode_output', 
                            # Mode(string) : 
                                        #'ADC': you get the rough uptput of the ADC: the entire trace
                                        #'IQCH1', you get I and Q from channel 1
                                        #'IQCH2', you get I and Q from channel 2
                                        #'IQLP1' you get I and Q after the low pass filter
                                        #'IQINT' you get I and Q after the integration
                                        #we can use either IQLP1 or IQINT for the low pass filtering
                            label = 'Output mode',
                            vals = vals.Enum('ADC', 'IQCH1', 'IQCH2', 'IQLP1', 'IQINT'),
                            set_cmd='OUTPUT:SELECT ' + '{}',
                            get_cmd='OUTPUT:SELECT?'
                            
                            #get_parser=float
                            )
        # The get command doesn't work, not clear why
        self.add_parameter( name = 'format_output', 
                            #Format(string) : 'BIN' or 'ASCII' 
                            label='Output format',
                            vals = vals.Enum('ASCII','BIN'),
                            set_cmd='OUTPUT:FORMAT ' + '{}',
                            get_cmd='OUTPUT:FORMAT?',
                            get_parser=str
                            )

        self.add_parameter('nb_measure',
                            set_cmd='{}',
                            get_parser=int )

######################################################################
        self.add_parameter('status',
                           set_cmd='{}',
                           vals=vals.Enum('start', 'stop'),
                           set_parser = self.set_mode)

        self.add_parameter('data_size',
                           get_cmd='OUTPUT:DATASIZE?')


        self.add_parameter('data_output',
         					#get_cmd='OUTPUT:DATA?'
                            get_cmd = self.get_data)
                            #get_cmd = self.get_single_pulse)

        self.add_parameter('data_output_raw',
                             get_cmd='OUTPUT:DATA?')


        # good idea to call connect_message at the end of your constructor.
        # this calls the 'IDN' parameter that the base Instrument class creates 
        # for every instrument  which serves two purposes:
        # 1) verifies that you are connected to the instrument
        # 2) gets the ID info so it will be included with metadata snapshots later.
        self.connect_message()    

# ----------------------------------------------------- Methods -------------------------------------------------- #

#---------------------------------------------------------------------From seconds to samples and viceversa------

    def get_samples_from_sec(self, sec):
        samples=sec/8e-9
        samples=int(round(samples))
        time.sleep(0.1)
        return samples
        
    def get_sec_from_samples(self, samples):
        sec=float(samples)*8.0e-9
        time.sleep(0.1)
        return sec

#-------------------------------------------------------------Setting parameters
    def set_mode(self, mode):
        time.sleep(0.2)
        return mode


#-------------------------------------------------------------------Look-Up-Table (LUT) menagement ---------

    def fill_LUT(self, function, parameters): 
        """
        Fill a LUT  
        Input:
                function(string): name of the function
                parameters(float): vector of parameters characterizing the function:
                freq (Hz), Amplitude (from 0 to 1), pulse_duration (s), delay (s)
        Output: 
                the table (int) 
        """
        if function == 'SIN': 
            freq, Amplitude, pulse_duration, delay = parameters
            if freq > 1./8e-9 or Amplitude > 1 or pulse_duration + delay >  8e-9*8192: 
                raise ValueError('One of the parameters is not correct in the sin LUT')
            else: 
                N_point = int(round(pulse_duration/8e-9))
                n_oscillation = freq*pulse_duration
                Amp_bit = Amplitude*8192                           ######### the DAC is 14 bit 8192 . The maximum aplitude will be (2^14)/2
                t = np.linspace(0, 2 * np.pi,N_point)
                return Amp_bit*np.concatenate((np.zeros(int(round(delay/8e-9))), np.sin(n_oscillation*t)))

        elif function == 'COS': 
            freq, Amplitude, pulse_duration, delay = parameters
            if freq > 1./8e-9 or Amplitude > 1 or pulse_duration + delay > 8e-9*8192: 
                raise ValueError('One of the parameters is not correct in the cos LUT')
            else: 
                N_point = int(round(pulse_duration/8e-9))
                n_oscillation = freq*pulse_duration
                
                Amp_bit = Amplitude*8192
                t = np.linspace(0,2*np.pi,N_point)
                return Amp_bit*np.concatenate((np.zeros(int(round(delay/8e-9))), np.cos(n_oscillation*t)))

        elif function == 'RAMSEY':

            freq, Amplitude, pulse_duration, t_wait, delay = parameters
            if freq > 1. / 8e-9 or Amplitude > 1 or 2*pulse_duration + delay + t_wait > 8e-9 * 8192:
                raise ValueError('One of the parameters is not correct is the Ramsey LUT')
            else :
                N_point = int(round(pulse_duration/8e-9))
                n_oscillation = freq * pulse_duration
                Amp_bit = Amplitude * 8192
                t = np.linspace(0, 2 * np.pi, N_point)
                wait_vec = np.zeros(int(round(t_wait/8e-9)))
                delay_vec = np.zeros(int(round(delay/8e-9)))
                excitation_vec = np.sin(n_oscillation*t)
                return Amp_bit*np.concatenate((delay_vec,excitation_vec,wait_vec,excitation_vec))

        elif function == 'ECHO':
            freq, Amplitude, pulse_pi_2, t_wait, delay = parameters
            if freq > 1. / 8e-9 or Amplitude > 1 or 4*pulse_pi_2 + delay + 2*t_wait > 8e-9 * 8192:
                raise ValueError('One of the parameters is not correct is the Echo LUT')
            else:
                N_point_pi_2 = int(round(pulse_pi_2/8e-9))
                N_point_pi = 2 * N_point_pi_2

                n_oscillation_pi_2 = freq * pulse_pi_2
                n_oscillation_pi = 2 * n_oscillation_pi_2

                Amp_bit = Amplitude * 8192
                t_pi_2 = np.linspace(0, 2 * np.pi, N_point_pi_2)
                t_pi = np.linspace(0, 2 * np.pi, N_point_pi)

                wait_vec = np.zeros(int(round(t_wait/8e-9)))
                delay_vec = np.zeros(int(round(delay/8e-9)))

                pi_2_vec = np.sin(n_oscillation_pi_2*t_pi_2)
                pi_vec = np.sin(n_oscillation_pi * t_pi)

                return Amp_bit*np.concatenate((delay_vec, pi_2_vec, wait_vec, pi_vec, wait_vec, pi_2_vec))
                
        elif function == 'STEP': 
            Amplitude, pulse_duration,t_slope,delay = parameters
            if Amplitude > 1 or pulse_duration + delay + 2*t_slope > 8e-9 * 8192: 
                raise ValueError('One of the parameters is not correct is the STEP LUT')
            
            Amp_bit = Amplitude*8192
            N_point = int(pulse_duration/8e-9)
            N_slope = int(t_slope/8e-9)
            N_delay = int(delay/8e-9)
            

            delay_vec = np.zeros(N_delay)
            slope_vec = np.linspace(0,1,N_slope)
            pulse_vec = np.ones(N_point)
            
            return Amp_bit*np.concatenate((delay_vec,slope_vec,pulse_vec,slope_vec[::-1]))
              
        else: 
            raise ValueError('This function is undefined')

    def send_DAC_LUT(self, table, channel, trigger = 'NONE'): 
        """
        Send a LUT to one of the DAC channels 
        Input: 
            - table (float): table to be sent 
            - channel(string): channel to which the table is sent 
            - trigger(string): send a trigger to the channels or not  
        Output: 
            None
        """
        self.log.info(__name__+ ' Send the DAC LUT \n')
        if trigger == 'NONE': 
            table_bit = table.astype(int) * 4  
        elif trigger == 'CH1': 
            table_bit = table.astype(int) * 4 + 1
        elif trigger == 'CH2': 
            table_bit = table.astype(int) * 4 + 2
        elif trigger == 'BOTH': 
            table_bit = table.astype(int) * 4 + 3
        else: 
            raise ValueError('Wrong trigger value')     

        table_bit = table_bit.astype(str)
        separator = ', '
        table_bit = separator.join(table_bit)
        if channel in ['CH1', 'CH2']: 
            time.sleep(0.1)
            #print(table_bit)
            self.write('DAC:' + channel + ' ' + table_bit)
        else: 
            raise ValueError('Wrong channel value')
                
    def send_IQ_LUT(self, table, channel, quadrature): 
        """
        Send a LUT to one of the IQ channel  (I and Q will be multiplied by the ADC input)
        Input: 
            - table (float): table to be sent 
            - channel(string): channel in which to table in sent 
            - trigger(string): send a trigger in channels or not 

        """
        self.log.info(__name__+ ' Send the IQ LUT \n')
        table_bit = table.astype(int) * 4 
        table_bit = table_bit.astype(str)
        separator = ', '
        table_bit = separator.join(table_bit)
        if quadrature in ['I', 'Q'] and channel in ['CH1', 'CH2']:
            time.sleep(0.1)
            self.write(quadrature + ':' + channel + ' ' + table_bit)
        else: 
            raise ValueError('Wrong quadrature or channel')

    def reset_LUT(self,time = 8192*8e-9): 
        """
        Reset all the LUT 
        Input: 
            time(float): duration of the table to be reset in second. 
            Default value is the all table 
        Output: 
            None
        """
        self.log.info(__name__+' Reset the DAC LUT \n')
        parameters = [0, 0, time,0]
        empty_table = self.fill_LUT('SIN',parameters)
        self.stop_DAC(time)
        self.send_DAC_LUT(empty_table,'CH1')
        self.send_DAC_LUT(empty_table,'CH2')
        self.send_IQ_LUT(empty_table,'CH1','I')
        self.send_IQ_LUT(empty_table,'CH1','Q')
        self.send_IQ_LUT(empty_table,'CH2','I')
        self.send_IQ_LUT(empty_table,'CH2','Q')

#--------------------------------------------------------------------------Output Data----

    def get_data(self):
        time.sleep(0.2)
        t = 0 
        nb_measure = self.nb_measure()
        mode = self.mode_output()
        print(nb_measure, 'pulses.', 'Mode:',mode)
        self.format_output('ASCII')
        self.status('start')
        time.sleep(2) # Timer to change if no time to start
        signal = np.array([], dtype ='int32')
        t0 = time.time()

        while t < nb_measure:
            try:
                time.sleep(0.2)
                rep = self.ask('OUTPUT:DATA?')
                #print(rep)
                #rep = self.data_output_raw()
                if rep[1] != '0' or len(rep)<=2:
                    print ('Memory problem %s' %rep[1])
                    #print(2,t)
                    self.status('stop')
                    #print(3,t)
                    self.status('start')
                else: 
                    # signal.append( rep[3:-1] + ',')
                    rep = eval( '[' + rep[3:-1] + ']' )
                    signal = np.concatenate((signal,rep))
                    tick = np.bitwise_and(rep,3) # extraction du debut de l'aquisition: LSB = 3
                    t += len(np.where(tick[1:] - tick[:-1])[0])+1 # idex of the tick   
                    #print(t)
                    t1 = time.time()
                    #print (t1 - t0, t)
                    t0 = t1
            except: 
                t=t
        self.status('stop')
        time.sleep(2)
        trash = self.ask('OUTPUT:DATA?')
        #print(mode)
        if t > nb_measure: 
            jump_tick = np.where(tick[1:] - tick[:-1])[0]
            len_data_block = jump_tick[1] - jump_tick[0]
            signal = signal[:nb_measure*len_data_block]
            
        if (mode == 'ADC' or mode == 'IQCH1' or mode == 'IQCH2'):
            #print(12)
            data_1 = signal[::2]/(4*8192.)
            data_2 = signal[1::2]/(4*8192.)
            return data_1, data_2
        else: 
            ICH1 = signal[::4]/(4*8192.)
            QCH1 = signal[1::4]/(4*8192.)
            ICH2 = signal[2::4]/(4*8192.)
            QCH2 = signal[3::4]/(4*8192.)
            return ICH1, QCH1, ICH2, QCH2
            
    def get_single_pulse(self):
        #self.mode_output(mode)
        self.format_output('ASCII')
        self.status('start')
        signal = np.array([], dtype ='int32')

        #Some sleep needed otherwise the data acquisition is too fast.
        time.sleep(0.8)
        rep = self.ask('OUTPUT:DATA?')
        if rep[1] != '0' or len(rep)<=2:
            print ('Memory problem %s' %rep[1])
            #print(2,t)
            self.status('stop')
            #print(3,t)
            self.status('start')
        else: 
            # signal.append( rep[3:-1] + ',')
            rep = eval( '[' + rep[3:-1] + ']' )
            signal = np.concatenate((signal,rep))
            tick = np.bitwise_and(rep,3) # extraction du debut de l'aquisition: LSB = 3
        self.status('stop')
        jump_tick = np.where(tick[1:] - tick[:-1])[0]
        len_data_block = jump_tick[1] - jump_tick[0]
        signal = signal[:len_data_block]

        print(self.mode_output())

        if self.mode_output() == ('ADC' or 'IQCH1' or 'IQCH2'):
            #print(self.mode_output())
            data_1 = signal[::2]/(4*8192.)
            data_2 = signal[1::2]/(4*8192.)
            return data_1, data_2
        else: 
            ICH1 = signal[::4]/(4*8192.)
            QCH1 = signal[1::4]/(4*8192.)
            ICH2 = signal[2::4]/(4*8192.)
            QCH2 = signal[3::4]/(4*8192.)
            return ICH1, QCH1, ICH2, QCH2

    def get_data_binary(self, mode, nb_measure):

        t = 0 
        self.set_mode_output(mode)
        self.set_format_output('BIN')
        self.start()
        signal = np.array([], dtype='int32')
        t0 = time.time()
        while t < nb_measure:
            try:
                rep = self.data_output_bin()
                if rep[0] != 0:
                    print ('Memory problem %s' %rep[0])
                    self.stop()
                    self.start()
                else: 
                    signal = np.concatenate((signal,rep[1:]))
                    if mode == ('ADC' or 'IQCH1' or 'IQCH2'): 
                        t = len(signal)/2
                    else: 
                        t = len(signal)/4
                t1 = time.time()
                print (t1 - t0, t)
                t0 = t1
            except: 
                t=t


        self.stop()
        trash = self.data_output()
            
        if mode == ('ADC' or 'IQCH1' or 'IQCH2'):
            data_1 = signal[::2][:nb_measure]/(4*8192.)
            data_2 = signal[1::2][:nb_measure]/(4*8192.)
            return data_1, data_2

        else:
            ICH1 = signal[::4][:nb_measure]/(4*8192.)
            QCH1 = signal[1::4][:nb_measure]/(4*8192.)
            ICH2 = signal[2::4][:nb_measure]/(4*8192.)
            QCH2 = signal[3::4][:nb_measure]/(4*8192.)
            return ICH1, QCH1, ICH2, QCH2     
    



    # def data_size(self):
    #     """
    #         Ask for the data size
    #     """ 
    #     #sleep(0.1)
    #     self.log.info(__name__ + ' Ask for the data size \n')
    #     #self.query('OUTPUT:DATASIZE?')
    #     self.write('OUTPUT:DATASIZE?')

        
    # def data_output(self):
    #     """
    #         Ask for the output data 
    #         Input:
    #             None
    #         Output: 
    #             - data: table of ASCII 
    #     """
    #     #sleep(0.2)
    #     self.log.info(__name__ + ' Ask for the output data \n')
    #     #data = self.query('OUTPUT:DATA?')
    #     data = self.write('OUTPUT:DATA?')
    #     return data


    # def get_data(self, mode, nb_measure):
    #     t = 0 
    #     self.mode_output(mode)
    #     self.format_output('ASCII')
    #     #self.start()
    #     self.status('start')
    #     signal = np.array([], dtype ='int32')
    #     t0 = time.time()

    #     while t < nb_measure:
    #         try:
    #             #time.sleep(0.1)
    #             rep = self.data_output()
    #             if rep[1] != '0' or len(rep)<=2:
    #                 print ('Memory problem %s' %rep[1])
    #                 self.status('stop')
    #                 self.status('start')
    #             else: 
    #                 # signal.append( rep[3:-1] + ',')
    #                 rep = eval( '[' + rep[3:-1] + ']' )
    #                 signal = np.concatenate((signal,rep))
    #                 tick = np.bitwise_and(rep,3) # extraction du debut de l'aquisition: LSB = 3
    #                 t += len(np.where(tick[1:] - tick[:-1])[0])+1 # idex of the tick   
    #                 # print t 
    #                 t1 = time.time()
    #                 print (t1 - t0, t)
    #                 t0 = t1
    #         except: 
    #             t=t
    #     #self.stop()
    #     self.status('stop')
            
    #     trash = self.data_output()
    #     # except: 
    #         # 'no trash'
    #     # i = 0 
    #     # while i==0: 
    #         # try: 
    #             # qt.msleep(0.25)
    #             # trash = self.data_output()
    #             # i = i +len(trash)
    #         # except: 
    #             # i = 0


    #     if t > nb_measure: 
    #         jump_tick = np.where(tick[1:] - tick[:-1])[0]
    #         len_data_block = jump_tick[1] - jump_tick[0]
    #         signal = signal[:nb_measure*len_data_block]
            
    #     if mode == ('ADC' or 'IQCH1' or 'IQCH2'):
    #         data_1 = signal[::2]/(4*8192.)
    #         data_2 = signal[1::2]/(4*8192.)
    #         print('OK')
    #         return data_1, data_2
    #     else: 
    #         ICH1 = signal[::4]/(4*8192.)
    #         QCH1 = signal[1::4]/(4*8192.)
    #         ICH2 = signal[2::4]/(4*8192.)
    #         QCH2 = signal[3::4]/(4*8192.)
    #         return ICH1, QCH1, ICH2, QCH2

    
    
        
        
        
        
