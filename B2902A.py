'''
Modified version of the QCodes B2962A driver: qcodes.instrument_drivers.Keysight.Keysight_B2962A
17/02/2022
'''

import logging
from typing import Any, Dict, Optional
from qcodes import VisaInstrument
from qcodes import Instrument
from qcodes.instrument.channel import InstrumentChannel
from qcodes.utils import validators as vals

log = logging.getLogger(__name__)


class B2902AChannel(InstrumentChannel):
    """

    """
    def __init__(self, parent: Instrument, name: str, chan: int) -> None:
        """
        Args:
            parent: The instrument to which the channel is attached.
            name: The name of the channel
            chan: The number of the channel in question (1-2)
        """
        # Sanity Check inputs
        if name not in ['ch1', 'ch2']:
            raise ValueError("Invalid Channel: {}, expected 'ch1' or 'ch2'"
                             .format(name))
        if chan not in [1, 2]:
            raise ValueError("Invalid Channel: {}, expected '1' or '2'"
                             .format(chan))

        super().__init__(parent, name)

        self.add_parameter('source_voltage',
                           label=f"Channel {chan} Voltage",
                           get_cmd=f'SOURCE{chan:d}:VOLT?',
                           get_parser=float,
                           set_cmd=f'SOURCE{chan:d}:VOLT {{:.5G}}',     # 5 digits of resolution
                           unit='V',
                           vals=vals.Numbers(-210, 210))

        self.add_parameter('source_current',
                           label=f"Channel {chan} Current",
                           get_cmd=f'SOURCE{chan:d}:CURR?',
                           get_parser=float,
                           set_cmd=f'SOURCE{chan:d}:CURR {{:.5G}}',     # 5 digits of resolution
                           unit='A',
                           vals=vals.Numbers(-3.03, 3.03))

        self.add_parameter('voltage',
                           get_cmd=f'MEAS:VOLT? (@{chan:d})',
                           get_parser=float,
                           label=f'Channel {chan} Voltage',
                           unit='V')

        self.add_parameter('current',
                           get_cmd=f'MEAS:CURR? (@{chan:d})',
                           get_parser=float,
                           label=f'Channel {chan} Current',
                           unit='A')

        self.add_parameter('resistance',
                           get_cmd=f'MEAS:RES? (@{chan:d})',
                           get_parser=float,
                           label=f'Channel {chan} Resistance',
                           unit='ohm')

        self.add_parameter('voltage_limit',
                           get_cmd=f'SENS{chan:d}:VOLT:PROT?',
                           get_parser=float,
                           set_cmd=f'SENS{chan:d}:VOLT:PROT {{:.5G}}',     # 5 digits of resolution
                           label=f'Channel {chan} Voltage Limit',
                           unit='V')

        self.add_parameter('current_limit',
                           get_cmd=f'SENS{chan:d}:CURR:PROT?',
                           get_parser=float,
                           set_cmd=f'SENS{chan:d}:CURR:PROT {{:.5G}}',     # 5 digits of resolution
                           label='Channel {} Current Limit',
                           unit='A')

        self.add_parameter('enable',
                           get_cmd=f'OUTP{chan:d}?',
                           set_cmd=f'OUTP{chan:d} {{:d}}',
                           val_mapping={'on':  1, 'off': 0})

        self.add_parameter('source_mode',
                           get_cmd=f':SOUR{chan:d}:FUNC:MODE?',
                           set_cmd=f':SOUR{chan:d}:FUNC:MODE {{:s}}',
                           val_mapping={'current': 'CURR', 'voltage': 'VOLT'})

        self.channel = chan



class B2902A(VisaInstrument):
    """
    This is the qcodes driver for the Keysight B2902A Precision Source
    """
    def __init__(self, name: str, address: str, **kwargs: Any):
        super().__init__(name, address, terminator='\n', **kwargs)

        # The B2902A supports two channels
        for ch_num in [1, 2]:
            ch_name = f"ch{ch_num:d}"
            channel = B2902AChannel(self, ch_name, ch_num)
            self.add_submodule(ch_name, channel)

        self.connect_message()

        self.add_parameter('format',
                           label='Output format',
                           get_cmd=f':FORM?',
                           set_cmd=f':FORM {{:s}}',
                           val_mapping={'ascii':'ASC', 'float32':'REAL,32', 'float64':'REAL,64'})

        self.add_parameter('remote_display',
                           label='Remote display mode',
                           get_cmd=f':DISP:ENAB?',
                           set_cmd=f':DISP:ENAB {{:d}}',
                           val_mapping={'on':  1, 'off': 0})


    def get_idn(self) -> Dict[str, Optional[str]]:
        IDN_str = self.ask_raw('*IDN?')
        vendor, model, serial, firmware = map(str.strip, IDN_str.split(','))
        IDN: Dict[str, Optional[str]] = {
            'vendor': vendor, 'model': model,
            'serial': serial, 'firmware': firmware}
        return IDN
