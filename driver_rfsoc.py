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

# VisaInstrument is a class used for most instruments that communicate over a
#  text channel (ethernet for ex). In QCoDeS it is best to use this class

#  A QCoDeS instrument driver is nothing but an object and has some sub-objects
# (or parameters) that represent the state of the physical instrument

# A parameter represents a single value of a single feature of an instrument
# In most cases you will probably be adding parameters via the add_parameter
# method on the instrument class

#
# class GeneratedSetPoints(Parameter):
#       """
#     A parameter that generates a setpoint array from start, stop and num points
#     parameters.
#     """
#     def __init__(self, startparam, stopparam, numpointsparam, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._startparam = startparam
#         self._stopparam = stopparam
#         self._numpointsparam = numpointsparam
#
#     def get_raw(self):
#         return np.linspace(self._startparam(), self._stopparam() -1,
#                               self._numpointsparam())



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
