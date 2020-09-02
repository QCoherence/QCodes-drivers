#
# *** Warning: Alpha version driver with functionalities under development.
#
# 
# 												                    -- Arpit




import qcodes as qc
from qcodes import (Instrument, VisaInstrument,
					ManualParameter, MultiParameter,
					validators as vals)
from qcodes.instrument.channel import InstrumentChannel
from qcodes.instrument.parameter import ParameterWithSetpoints, Parameter
from qcodes.utils.validators import Numbers, Arrays


from time import sleep
import numpy as np