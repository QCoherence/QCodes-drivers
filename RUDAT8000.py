'''
Modified and QCodes-compatible version the RUDAT's QTLab driver
17/02/2022
'''

import logging
from qcodes import VisaInstrument, Instrument
from qcodes.utils import validators as vals
import urllib.request

log = logging.getLogger(__name__)


class RUDAT8000(Instrument):
    '''
    This is the QCodes driver for the RUDAT8000
    '''

    def __init__(self, name, address, **kwargs):
        '''
        Initializes the RUDAT8000

        Input:
            name (string)    : name of the instrument
            address (string) : TCPIP/GPIB address
            reset (bool)     : Reset to default values

        Output:
            None
        '''
        super().__init__(name=name, **kwargs)
        self._address = address

        ## Parameters
        self.add_parameter(name='attenuation',
            get_cmd=self.do_get_attenuation,
            set_cmd=self.do_set_attenuation,
            unit='dB',
            vals=vals.Numbers(0., 30.),
            get_parser=float)

        self.add_function('plus_att_step',
            call_cmd=self.plus_att_step)

        self.add_function('minus_att_step',
            call_cmd=self.minus_att_step)


    def do_get_attenuation(self):
        return float( urllib.request.urlopen(self._address+'/ATT?').read() )

    def do_set_attenuation(self, value):
        if (value % 0.25) != 0:
            print('value should be a multiple of 0.25')

        urllib.request.urlopen(self._address+f'/:SETATT={value}')
        if value != self.do_get_attenuation():
            print('error setting the attenuation')

    def plus_att_step(self):
        value = self.do_get_attenuation()

        if value < 30.:
            value += 0.25
            urllib.request.urlopen(self._address+f'/:SETATT={value}')

    def minus_att_step(self):
        value = self.do_get_attenuation()

        if value > 0.:
            value -= 0.25
            urllib.request.urlopen(self._address+f'/:SETATT={value}')
