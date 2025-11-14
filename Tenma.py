from typing import Any

from qcodes.instrument import VisaInstrument
from qcodes.parameters import create_on_off_val_mapping


class Tenma_72_52359(VisaInstrument):
    def __init__(self, name: str, address: str, channel=1, **kwargs: Any) -> None:
        super().__init__(name, address, terminator="\n", **kwargs)

        # Turn "on" and "off" the output.
        (
            self.add_parameter(
                name="status",
                label="Status",
                get_cmd="OUT?",
                set_cmd="OUT{}",
                val_mapping=create_on_off_val_mapping(on_val="1", off_val="0"),
            ),
        )
        # Turn "on" and "off" the beep.
        (
            self.add_parameter(
                name="beep",
                label="Beep",
                get_cmd="BEEP?",
                set_cmd="BEEP{}",
                val_mapping=create_on_off_val_mapping(on_val="1", off_val="0"),
            ),
        )
        # Give the IDN of the apparatus.
        self.add_parameter(
            name="idn",
            label="IDN",
            get_cmd="*IDN?",
            set_cmd="*IDN",
        )
        # Give you access to the save settings.
        # Parameter ranges from 1 to 5.
        self.add_parameter(
            name="use_settings",
            label="Settings",
            get_cmd="RCL?",
            set_cmd="RCL{}",
        )
        # Allows you to save settings.
        # Parameter ranges from 1 to 5.
        self.add_parameter(
            name="save_settings",
            label="Saved_settings",
            get_cmd="SAV?",
            set_cmd="SAV{}",
        )
        # OCP (Over Current Protection)
        self.add_parameter(
            name="ocp",
            label="OCP",
            get_cmd="OCP?",
            set_cmd="OCP{}",
        )
        # OVP (Over Voltage Protection)
        self.add_parameter(
            name="ovp",
            label="OVP",
            get_cmd="OVP?",
            set_cmd="OVP{}",
        )
        # <X>_ch<CH> set the value of <X> on the channel <CH>.
        # Current range : 0-3A
        # Voltage range : 0-30V
        self.add_parameter(
            name="current_ch" + str(channel),
            label="Current_ch" + str(channel),
            unit="A",
            get_cmd="ISET" + str(channel) + "?",
            set_cmd="ISET" + str(channel) + ":{}",
        )
        self.add_parameter(
            name="voltage_ch" + str(channel),
            label="Voltage_ch" + str(channel),
            unit="V",
            get_cmd="VSET" + str(channel) + "?",
            set_cmd="VSET" + str(channel) + ":{}",
        )
        # get_output_<X>_ch<CH> gives the output value of <X> on the channel <CH>.
        self.add_parameter(
            name="get_output_current_ch" + str(channel),
            label="Output_current_ch" + str(channel),
            unit="A",
            get_cmd="IOUT" + str(channel) + "?",
        )
        self.add_parameter(
            name="get_output_voltage_ch" + str(channel),
            label="Output_voltage_ch" + str(channel),
            unit="V",
            get_cmd="VOUT" + str(channel) + "?",
        )
