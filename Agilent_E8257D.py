# Last updated on 14 Jun 2021
#                     -- Dorian


import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
ManualParameter, MultiParameter, Parameter,
validators as vals)
from qcodes.instrument.channel import InstrumentChannel
import logging

from numpy import pi
import numpy as np

log = logging.getLogger(__name__)



class FreqSweep(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_raw(self):

        start=self._instrument.freq_start.get()
        stop=self._instrument.freq_stop.get()
        step=self._instrument.freq_step.get()

        return np.arange(start,stop+step,step)


class E8257D(VisaInstrument):
    """
    QCoDeS driver for the Agilent E8257D MW source
    """

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__

    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name, address, terminator='\n', **kwargs)

        self.add_parameter( name = 'frequency',
                            label = 'Output frequency in Hz',
                            vals = vals.Numbers(100e3,40e9),
                            unit   = 'Hz',
                            set_cmd='FREQ:CW ' + '{:.12f}',
                            get_cmd='FREQ:CW?'
                            )

        self.add_parameter( name = 'power',
                            label = 'Output power in dBm',
                            vals = vals.Numbers(-135,25),
                            unit   = 'dBm',
                            set_cmd='POW:AMPL ' + '{:.12f}',
                            get_cmd='POW:AMPL?',
                            get_parser=float,
                            set_parser =self.warn_over_range
                            )

        self.add_parameter( name = 'phase',
                            label = 'Output phase in Rad',
                            vals = vals.Numbers(-2*pi,2*pi),
                            unit   = 'Rad',
                            set_cmd= 'PHASE ' + '{:.12f}',
                            get_cmd='PHASE?',
                            set_parser =self.rad_to_deg,
                            get_parser=self.deg_to_rad
                            )

        self.add_parameter( name = 'status',
                            label = 'Output on/off',
                            vals = vals.Enum('ON','OFF'),
                            unit   = 'NA',
                            set_cmd='OUTP ' + '{}',
                            get_cmd='OUTP?',
                            set_parser =self.easy_read_status,
                            get_parser=self.easy_read_status_read
                            )

        self.add_parameter( name = 'freq_start',
                            label = 'Sweep: start frequency in Hz',
                            vals = vals.Numbers(100e3,40e9),
                            unit   = 'Hz',
                            set_cmd='FREQ:START ' + '{:.12f}' + 'Hz',
                            get_cmd='FREQ:START?',
                            get_parser=float
                            )

        self.add_parameter( name = 'freq_stop',
                            label = 'Sweep: stop frequency in Hz',
                            vals = vals.Numbers(100e3,40e9),
                            unit   = 'Hz',
                            set_cmd='FREQ:STOP ' + '{:.12f}' + 'Hz',
                            get_cmd='FREQ:STOP?',
                            get_parser=float
                            )

        self.add_parameter( name = 'freq_step',
                            label = 'Sweep: frequency step',
                            vals = vals.Numbers(0.,20e9),
                            unit   = 'Hz',
                            set_cmd= 'FREQ:STEP ' + '{:.12f}' + 'Hz',
                            get_cmd='FREQ:STEP?',
                            get_parser=float
                            )

        self.add_parameter( name = 'freq_points',
                            label = 'Sweep: frequency points',
                            vals = vals.Numbers(2,20e9),
                            unit   = 'Hz',
                            set_cmd='SWEep:POINts ' + '{:.12f}',
                            get_cmd='SWE:POIN?',
                            get_parser=float
                            )

        self.add_parameter( name = 'dwell_time',
                            label = 'Sweep: dwell time',
                            vals = vals.Numbers(5e-3,1000),
                            unit   = 's',
                            set_cmd='SWE:DWEL ' + '{:.12f}' + 's',
                            get_cmd='SWE:DWEL?',
                            get_parser=float
                            )

        self.add_parameter( name = 'sourcemode',
        					label = 'Set source mode',
        					vals = vals.Enum('CW','sweep'),
        					set_cmd='SOURce:FREQuency:MODE '+ '{}',
        					get_cmd='SOURce:FREQuency:MODE?',
        					set_parser =self.set_freqsweep
        					)

        self.add_parameter( name = 'sweepmode',
        					label = 'Set frequency sweep mode',
        					vals = vals.Enum('AUTO','SINGLE'),
        					set_cmd='TRIG:FSW:SOUR '+ '{}',
        					get_cmd='TRIG:FSW:SOUR?',
        					set_parser =self.set_sweepmode
        					)
        
        self.add_parameter( name = 'spacing_freq',
                            label='Set spacing mode of frequency sweep',
                            vals=vals.Enum('LIN','LOG'),
                            set_cmd='SWE:SPAC {}',
                            get_cmd='SWE:SPAC?'
                            )

        self.add_parameter( name='freq_vec',
                            label='Parameter to get the vector of frequencies used for the sweep',
                            parameter_class=FreqSweep
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

        if(status=='ON'):
            ret=1
        elif(status=='OFF'):
            ret=0
        return ret

    def easy_read_status_read(self, status):
        if(status=='1'):
            ret='ON'
        elif(status=='0'):
            ret='OFF'
        return ret

    def warn_over_range(self, power):
        if power>25:
            log.warning('Power over range (limit to 16 dBm).')
        return power

    def set_freqsweep(self, freqsweep='off'):
        '''
        Set the frequency sweep mode to 'on' or 'off'

        Input:
        status (string): 'on' or 'off'
        Output:
        None
        '''

        if freqsweep.upper() in ('SWEEP'):
            self.write('SOURCE:FREQUENCY:MODE SWEEP')
        elif freqsweep.upper() in ('CW'):
            self.write('SOURCE:FREQUENCY:MODE CW')
        else:
            raise ValueError('set_freqsweep(): can only set on or off')

    def get_freqsweep(self):
        '''
        Get the status of the frequency sweep mode from the instrument

        Input:
        None
        Output:
        status (string) : 'on' or 'off'
        '''
        # Output can be '0', '1' or '0\n', '1\n' which are different strings.
        # By using int() we can only get 1 or 0 independently of the OS.
        stat = self.query('SWE:RUNN?')

        if stat == 1:
            return 'on'
        elif stat == 0:
            return 'off'
        else:
            raise ValueError('Output status not specified : %s' % stat)
        return


    def set_sweepmode(self, sweepmode='single'):
        '''
        Set the frequency sweep mode

        Input:
        sweepmode (string): AUTO or SINGLE
        Output:
        None
        '''

        if sweepmode.upper() in ('AUTO'):
            self.write('SWE:MODE AUTO')
            self.write('SWEep:GENeration STEPped')
            self.write('TRIGger:SOURce IMMediate')
            self.write('INITiate:CONTinuous ON')

        # difference not implemented yet
        elif sweepmode.upper() in ('SINGLE'):
            self.write('SWE:MODE AUTO')
            self.write('SWEep:GENeration STEPped')
            self.write('TRIGger:SOURce IMMediate')
            self.write('INITiate:CONTinuous ON')
        else:
            raise ValueError('set_sweepmode(): can only set AUTO or SINGLE')

    def startsweep(self):
        '''
        Start the frequency sweep. Valid in the 'SINGLE' sweep mode.

        Input:
            None
        Output:
            None
        '''

        self.write('FREQ:MODE SWE')


    def restartsweep(self):
        '''
        Restart the frequency sweep.

        Input:
            None
        Output:
            None
        '''

        self.write('SOUR:SWE:RES')

    def set_gui_update(self, update='ON'):
        '''
        The command switches the update of the display on/off.
        A switchover from remote control to manual control always sets
        the status of the update of the display to ON.

        Input:
            status (string): 'on' or 'off'
        Output:
            None
        '''

        self.write('DISP:REM %s' % update)


    def query(self, cmd):
        res= self.query(cmd + '?')
        print(res)
        return(res)

    def tell(self, cmd):
        self.write(cmd)

    def sweepmode_set(self,sweepmode):
        if sweepmode == 'auto':
            ret = 'AUTO'
        else:
            ret = 'SING'
        return ret

    def sweepmode_get(self,sweepmode):
        if sweepmode == 'AUTO':
            ret = 'auto'
        else:
            ret = 'single'
        return ret

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        self.write('*RST')
