"""
Modified and QCodes-compatible version of Remy Dassonneville's driver
17/02/2022
"""

import logging

from qcodes import Instrument, ManualParameter
from qcodes import validators as vals

log = logging.getLogger(__name__)


class Virtual_SSB0550A(Instrument):
    """
    This is the QCodes driver for the virtual instrument which records the useful
    parameters of the Single Side Band modulator SSB0550A
    """

    def __init__(self, name, **kwargs):
        """
        Initializes the Virtual_SSB0550A

        Input:
            name (string)    : name of the instrument

        Output:
            None
        """
        super().__init__(name=name, **kwargs)

        ## Parameters

        self.add_parameter(
            name="freq_start",
            unit="GHz",
            vals=vals.Numbers(1e-4, 40),
            get_parser=float,
            initial_value=0.5,
            parameter_class=ManualParameter,
        )

        self.add_parameter(
            name="freq_stop",
            unit="GHz",
            vals=vals.Numbers(1e-4, 40),
            get_parser=float,
            initial_value=5.0,
            parameter_class=ManualParameter,
        )

        self.add_parameter(
            name="conversion_loss",
            unit="dB",
            get_parser=float,
            initial_value=6.0,
            parameter_class=ManualParameter,
        )

        self.add_parameter(
            name="band_type",
            vals=vals.Enum(-1, +1),  # -1 : the SSB is a Lower Side Band
            # +1 : the SSB is a Upper Side Band
            get_parser=float,
            initial_value=-1,
            parameter_class=ManualParameter,
        )

        self.add_parameter(
            name="LO_power",
            unit="dBm",
            vals=vals.Enum(5.0, 15.0),
            get_parser=float,
            initial_value=5.0,
            parameter_class=ManualParameter,
        )

        self.add_parameter(
            name="IF_frequency",
            unit="GHz",
            get_parser=float,
            initial_value=0.05,
            parameter_class=ManualParameter,
        )

    def get_idn(self):
        return {
            "vendor": "Polyphase Microwave",
            "model": "SSB0550A ",
            "serial": None,
            "firmware": None,
        }
