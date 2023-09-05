# Last updated on Jul 2021
#                  -- Dorian


import logging
from qcodes import VisaInstrument, Instrument
from qcodes import ChannelList, InstrumentChannel
from qcodes.utils import validators as vals
import numpy as np
from qcodes import MultiParameter, ArrayParameter, Parameter
import qcodes as qc

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

log = logging.getLogger(__name__)

class Mode(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_raw(self,value):

        '''
        Change mode to DCI or DCV and apply 0 Ampere/Volt (or: do nothing if the active channel is in the correct mode)

        Input:
            value: string

        Output:
            None
        '''

        oldModeName = (self._instrument.ask('APPLY?')).lower()
        modeName = value.lower()

        if oldModeName != modeName:

            if modeName == 'dci' or modeName == 'dcv':

                self._instrument.write('APPLY {} 0'.format(modeName.upper()))
            else:
                raise ValueError('The input parameter should be "dci" or "dcv"')

    def get_raw(self):

        '''
		    gets the active mode ('dci' or 'dcv')
            Input:
                None
            Output:
                String
        '''

        return self._instrument.ask('APPLY?').lower()

class Voltage(Parameter):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)


    def get_raw(self):

        '''
            Get the output voltage of the active channel.

            Input:
                - None

            Output:
                - float
        '''

        if (self._instrument.mode().upper())!='DCV':
            raise ValueError('Active channel is not in voltage mode')
        else:
            return float(self._instrument.ask('OUTPUT?'))

    def set_raw(self,value):

        '''
            Set the output voltage of the active channel.

            Input:
                - Value (float): voltage in Volt

            Output:
                - None
        '''

        self._instrument.write('APPLY DCV {}'.format(value))

class Current(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_raw(self):

        '''
            Get the output current of the active channel.

            Input:
                - None
        '''

        if (self._instrument.mode().upper())!='DCI':
            # raise ValueError('Active channel is not in current mode')
            return 0
        else:
            return float(self._instrument.ask('OUTPUT?'))

    def set_raw(self,value):

        '''
            Set the output current of the active channel.

            Input:
                - currentValue (float): Current in amps

            Output:
                - None
        '''

        self._instrument.write('APPLY DCI {}'.format(value))

class Range(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_raw(self,value):

        '''
            Set the current/voltage range. The range is selected accordingly out of the following lists:
                In current mode:
                    "low resolution":   Imax = 0.1 mA, dI = 50 nA
                                        Imax = 1 mA,   dI = 500 nA
                                        Imax = 10 mA,  dI = 5 uA
                                        Imax = 100 mA, dI = 50 uA
                    "high resolution":  Imax = 0.1 mA, dI = 0.1 nA
                                        Imax = 1 mA,   dI = 1 nA
                                        Imax = 10 mA,  dI = 10 nA
                                        Imax = 100 mA,  dI = 100 nA
                In voltage mode:
                    "low resolution":   Vmax = 0.15625 V, dV = 79 uV
                                        Vmax = 0.3125 V, dV = 157 uV
                                        Vmax = 0.625 V, dV = 313 uV
                                        Vmax = 1.25 V, dV = 625 uV
                                        Vmax = 2.5 V, dV = 1.25 mV
                                        Vmax = 5 V, dV = 2.5 mV
                                        Vmax = 10 V, dV = 5.0 mV
                    "high resolution":  Vmax = 1 V, dV = 1 uV
                                        Vmax = 10 V, dV = 10 uV

            Input:
                - value (float or string): Maximum expected current or voltage in Ampere or Volt, or alternatively "AUTO" for autorange.
            Output:
                - None
        '''
        if self._instrument.mode.get()=='dci':

            if value not in [0.0001,0.001,0.01,0.1]:

                raise ValueError('Provided range not valid in DCI mode')

        else :
            if self._instrument.resolution.get().lower()=='LOW':

                if value not in [0.15625,0.3125,0.625,1.25,2.5,5,10]:

                    raise ValueError('Provided range not valid in low resolution DCV mode')
            else :

                if value not in [1,10]:

                    raise ValueError('Provided range not valid in high resolution DCV mode')


        self._instrument.write('RANGE {}'.format(value))

    def get_raw(self):

        '''
            Get the range of the device

            Input:
                - None
            Output:
                - String
        '''

        return self._instrument.ask('RANGE?')

class ChannelStatus(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



    def set_raw(self,value):

        '''
            Sets the active channel (A or B). All subsequent set and get commands are applied to this channel until it is changed again.

            Input:
                channelName: String

            Output:
                None
        '''

        if value.lower() == 'a':
            self._instrument.write('USE CHANA ')
            self._instrument.write('MON STATE CHANA ')
        elif value.lower() == 'b':

            self._instrument.write('USE CHANB ')
            self._instrument.write('MON STATE CHANB ')
        else:
            raise ValueError('The input parameter should be "A" or "B"')

    def get_raw(self):

        '''
            gets active channel

            Input:
                None

            Output:
                String
        '''

        channelInt = int(self._instrument.ask('USE?'))
        if channelInt == 0:
            return 'A'
        elif channelInt == 100:
            return 'B'



class HP3245A(VisaInstrument):
    """
    QCoDeS driver for the current source.

    Args:
        name: instrument name
        address: Address of instrument probably in format
            'GPIB0::16::INSTR'

    """

    def __init__(self, name: str, address: str,**kwargs) -> None:

        super().__init__(name=name, address=address,terminator='\r\n',**kwargs)


        self.add_parameter(name='voltage',
                           label='Voltage',
                           parameter_class=Voltage,
                           get_parser=float,
                           unit='V',
                           snapshot_get=False)

        self.add_parameter(name='current',
                           label='Current',
                           parameter_class=Current,
                           get_parser=float,
                           unit='A',
                           snapshot_get=False)

        self.add_parameter(name='resolution',
                           label='Resolution',
                           get_cmd='DCRES?',
                           set_cmd='DCRES {}',
                           vals=qc.utils.validators.Enum('HIGH','LOW'),
                           snapshot_get=False)

        self.add_parameter(name='range',
                           label='Range',
                           unit='V/A',
                           parameter_class=Range,
                           snapshot_get=False)


        self.add_parameter(name='mode',
                           label='Mode',
                           parameter_class=Mode,
                           vals=qc.utils.validators.Enum('DCI','DCV','dci','dcv'),
                           snapshot_get=False)


        self.add_parameter(name='autorange',
                           label='Autorange',
                           get_cmd='ARANGE?',
                           set_cmd='ARANGE {}',
                           vals=qc.utils.validators.Enum('ON','OFF'),
                           snapshot_get=False)


        self.add_parameter(name='output_terminal',
                           label='Output terminal',
                           set_cmd='TERM {}',
                           vals=qc.utils.validators.Enum('FRONT','REAR'),
                           snapshot_get=False)

        self.add_parameter(name='channel',
        				   label = 'Channel',
                           parameter_class=ChannelStatus,
                           vals=qc.utils.validators.Enum('A','B','a','b'),
                           snapshot_get=False)

        self.connect_message()
        #self.reset()

    def get_idn(self) -> Dict[str, Optional[str]]:
        """
        Overwrite native function to implement IDN? instead of *IDN?

        Parse a standard VISA ``*IDN?`` response into an ID dict.

        Even though this is the VISA standard, it applies to various other
        types as well, such as IPInstruments, so it is included here in the
        Instrument base class.

        Override this if your instrument does not support ``*IDN?`` or
        returns a nonstandard IDN string. This string is supposed to be a
        comma-separated list of vendor, model, serial, and firmware, but
        semicolon and colon are also common separators so we accept them here
        as well.

        Returns:
            A dict containing vendor, model, serial, and firmware.
        """
        idstr = ''  # in case self.ask fails
        try:
            idstr = self.ask('IDN?')
            # form is supposed to be comma-separated, but we've seen
            # other separators occasionally
            idparts: List[Optional[str]]
            for separator in ',;:':
                # split into no more than 4 parts, so we don't lose info
                idparts = [p.strip() for p in idstr.split(separator, 3)]
                if len(idparts) > 1:
                    break
            # in case parts at the end are missing, fill in None
            if len(idparts) < 4:
                idparts += [None] * (4 - len(idparts))
        except:
            self.log.debug('Error getting or interpreting IDN?: '
                           + repr(idstr))
            idparts = [None, self.name, None, None]

        # some strings include the word 'model' at the front of model
        if str(idparts[1]).lower().startswith('model'):
            idparts[1] = str(idparts[1])[5:].strip()

        return dict(zip(('vendor', 'model', 'serial', 'firmware'), idparts))



    def reset(self):
        '''
        Reset the instrument

        Input:
            None

        Output:
            None
        '''
        self.write('RST')

    def clear_mem(self):
        '''
        Clear HP3245A memory

        Input:
            None
        Output:
            None
        '''
        self.write('SCRATCH')

    def get_all(self):
        '''
        Get all parameters of the instrument

        Input:
            None

        Output:
            None
        '''
        self.mode.get()
        self.channel.get()
        self.resolution.get()
        self.range.get()
        self.autorange.get()

        if   self.mode.get() == 'dci':

            self.current.get()
        else:
            self.voltage.get()
