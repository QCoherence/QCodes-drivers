# Last updated on 08 Apr 2026
#                     -- J-S


import logging

from qcodes import VisaInstrument
from qcodes import validators as vals
from qcodes.parameters import create_on_off_val_mapping

log = logging.getLogger(__name__)


class Yokogawa_7651(VisaInstrument):
    """
    QCoDeS driver for the Yokogawa 7651 I/V source
    """

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__

    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name, address, terminator="\n", **kwargs)

        # init: crashes the I/O, clear from visa test panel fixes the issue
        # self.write('RC')

        self.add_parameter(
            name="voltage_range",
            label="Set output voltage range in mV",
            vals=vals.Enum(10, 100, 1_000, 10_000, 30_000),
            unit="mV",
            set_cmd=self._set_V_mode,
        )

        self.add_parameter(
            name="current_range",
            label="Set output current range in mA",
            vals=vals.Enum(1, 10, 100),
            unit="mA",
            set_cmd=self._set_A_mode,
        )

        self.add_parameter(
            name="voltage_limit",
            label="Set output voltage limit in mV",
            vals=vals.Numbers(1000, 30_000),
            unit="mV",
            set_parser=self._div_1000_int,
            set_cmd="LV{}",
        )

        self.add_parameter(
            name="current_limit",
            label="Set output current limit in mA",
            vals=vals.Numbers(5, 120),
            unit="mA",
            set_parser=int,
            set_cmd="LA{}",
        )

        self.add_parameter(
            name="voltage",
            label="Set output voltage in mV",
            vals=vals.Numbers(-30_000, 30_000),
            unit="mV",
            set_cmd=self._set_value,
        )

        self.add_parameter(
            name="current",
            label="Set output current in mA",
            vals=vals.Numbers(-120, 120),
            unit="mA",
            set_cmd=self._set_value,
        )

        self.add_parameter(
            name="status",
            label="Output on/off",
            set_cmd="O{}E",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )

    def _set_V_mode(self, range):
        range_options = {10: "R2", 100: "R3", 1000: "R4", 10000: "R5", 30000: "R6"}
        self.write(f"F1{range_options[int(range)]}E")

    def _set_A_mode(self, range):
        range_options = {1: "R4", 10: "R5", 100: "R6"}
        self.write(f"F5{range_options[int(range)]}E")

    def _div_1000_int(self, val):
        return int(val / 1000)

    def _set_value(self, value):
        if value > 0:
            polarity = "+"
        else:
            polarity = "-"
        self.write(f"S{polarity}{round(abs(value) / 1000.0, 6)}E")

    def init(self):
        self.write("RC")

    # To avoid identity query error
    def get_idn(self):
        return {"vendor": "Yokogawa", "model": "7651", "serial": "0", "firmware": None}
