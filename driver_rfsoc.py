from time import sleep, time
import numpy as np
import ctypes  # only for DLL-based instrument

import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
                    ManualParameter, MultiParameter,
                    validators as vals)
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter

import SequenceGeneration as sqg
from qcodes.utils.delaykeyboardinterrupt import DelayedKeyboardInterrupt



class RFSoC(VisaInstrument):

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__
    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every
        # response
        super().__init__(name, address, terminator='\r\n', **kwargs)



    def write_sequence_and_DAC_memory(self):

        self.log.info(__name__+ ' sending sequence'+'  \n')
        self.write(sqg.Pulse.generate_sequence_and_DAC_memory())

        for obj in sqg.PulseGeneration.objs:

            self.log.info(__name__+ ' sending DAC {} 2D memory'.format(obj.channel)+'  \n')
            self.write(obj._DAC_2D_memory)



    def reset_DAC_2D_memory(self, channel):
        """
            Reset the 2D memory of one DAC

            Input : - channel of the DAC we wantto reset
        """

        self.log.info(__name__+ ' reset the 2D memory of DAC channel'+ channel+'  \n')

        if channel in ['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8']:

            self.write("DAC:DATA:{}:CLEAR".format(channel))

        else:
            raise ValueError('Wrong channel value')


    def reset_all_DAC_2D_memory(self):
        """
            Reset the 2D memory of all the DACs
        """
        for channel in ['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8']:

            self.write("DAC:DATA:{}:CLEAR".format(channel))




    def ask_raw(self, cmd: str) -> str:
        """
        Overwriting the ask_ray qcodes native function to query binary

        Low-level interface to ``visa_handle.ask``.

        Args:
            cmd: The command to send to the instrument.

        Returns:
            str: The instrument's response.
        """
        with DelayedKeyboardInterrupt():
            self.visa_log.debug(f"Querying: {cmd}")
            response = self.visa_handle.query_binary_values(cmd, datatype="h", is_big_endian=True)
            self.visa_log.debug(f"Response: {response}")
        return response
