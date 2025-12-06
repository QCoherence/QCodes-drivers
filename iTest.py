from functools import partial
from time import sleep
from typing import Literal

from qcodes import validators as vals
from qcodes.instrument import Instrument, InstrumentChannel, VisaInstrument
from qcodes.parameters import create_on_off_val_mapping


class iTestChannel(InstrumentChannel):
    def __init__(self, parent: Instrument, name: str, module: int, ch: int) -> None:
        super().__init__(parent, name)

        self.add_parameter(
            name="voltage_range",
            label="voltage range",
            docstring="The output voltage range in V for the desired channel",
            unit="V",
            get_cmd=partial(self._parent._get_channel_voltage_range, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_channel_voltage_range, module, ch),
            vals=vals.Enum(
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["low_range_V_V"],
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["high_range_V_V"],
            ),
        )

        self.add_parameter(
            name="ramp_mode",
            label="ramp mode",
            docstring="Ramp mode, for BE2141/2142 only. EXP (Immediate), RAMP (according to the slope), STAIR (staircase using Width and Amplitude), STEP (staircase using Amplitude, each step is triggered), AUTO (STEP with automatic trigger everytimes)",
            get_cmd=partial(self._parent._get_ramp_mode, module, ch),
            set_cmd=partial(self._parent._set_ramp_mode, module, ch),
            val_mapping={
                0: 0,
                1: 1,
                2: 2,
                3: 3,
                4: 4,
                "EXP": 0,
                "RAMP": 1,
                "STAIR": 2,
                "STEP": 3,
                "AUTO": 4,
            },
        )

        self.add_parameter(
            name="ramp_rate",
            label="ramp rate",
            docstring="Ramp rate of the desired channel in V/ms for BE2141/2142 only",
            unit="V/ms",
            get_cmd=partial(self._parent._get_ramp_rate, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_ramp_rate, module, ch),
            vals=vals.Numbers(0, 1),
        )

        self.add_parameter(
            name="current_range",
            label="current range",
            docstring="The output current range in A for the desired channel",
            unit="A",
            get_cmd=partial(self._parent._get_channel_current_range, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_channel_current_range, module, ch),
            vals=vals.Enum(
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["low_range_I_A"],
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["high_range_I_A"],
            ),
        )

        self.add_parameter(
            name="voltage",
            docstring="The output voltage of the desired channel in V",
            unit="V",
            get_cmd=partial(self._parent._get_channel_voltage, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_channel_voltage, module, ch),
            vals=vals.Numbers(
                -self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["V_max_V"],
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["V_max_V"],
            ),
        )

        self.add_parameter(
            name="current",
            docstring="Returns the current in the desired channel in A",
            unit="A",
            get_cmd=partial(self._parent._get_channel_current, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_channel_current, module, ch),
            vals=vals.Numbers(
                -self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["I_max_A"],
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["I_max_A"],
            ),
        )

        self.add_parameter(
            name="voltage_limit_up",
            docstring="The output upper voltage limit of the desired channel in V",
            unit="V",
            get_cmd=partial(self._parent._get_channel_voltage_limit_up, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_channel_voltage_limit_up, module, ch),
            vals=vals.Numbers(
                -self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["V_max_V"],
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["V_max_V"],
            ),
        )

        self.add_parameter(
            name="voltage_limit_low",
            docstring="The output lower voltage limit of the desired channel in V",
            unit="V",
            get_cmd=partial(self._parent._get_channel_voltage_limit_low, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_channel_voltage_limit_low, module, ch),
            vals=vals.Numbers(
                -self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["V_max_V"],
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["V_max_V"],
            ),
        )

        self.add_parameter(
            name="current_limit_up",
            docstring="The output upper current limit of the desired channel in A",
            unit="A",
            get_cmd=partial(self._parent._get_channel_current_limit_up, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_channel_current_limit_up, module, ch),
            vals=vals.Numbers(
                -self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["I_max_A"],
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["I_max_A"],
            ),
        )

        self.add_parameter(
            name="current_limit_low",
            docstring="The output lower current limit of the desired channel in A",
            unit="A",
            get_cmd=partial(self._parent._get_channel_current_limit_low, module, ch),
            get_parser=float,
            set_cmd=partial(self._parent._set_channel_current_limit_low, module, ch),
            vals=vals.Numbers(
                -self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["I_max_A"],
                self._parent.inst_dictionnary[
                    "BE" + self._parent.get_instrument_model(module)
                ]["I_max_A"],
            ),
        )

        self.add_parameter(
            name="status",
            docstring="Turn the output ON/OFF for the desired channel",
            get_cmd=partial(self._parent._get_channel_status, module, ch),
            set_cmd=partial(self._parent._set_channel_status, module, ch),
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )

        self.add_parameter(
            name="current_range_auto",
            docstring="Activates or not the automatic current range selection for the BE5845 board",
            get_cmd=partial(self._parent._get_curr_range_auto, module, ch),
            set_cmd=partial(self._parent._set_curr_range_auto, module, ch),
            val_mapping=create_on_off_val_mapping(on_val="ON", off_val="OFF"),
        )

        self.add_parameter(
            name="voltage_range_auto",
            docstring="Activates or not the automatic voltage range selection for the BE2141/2142 board",
            get_cmd=partial(self._parent._get_voltage_range_auto, module, ch),
            set_cmd=partial(self._parent._set_voltage_range_auto, module, ch),
            val_mapping=create_on_off_val_mapping(on_val="ON", off_val="OFF"),
        )

        self.add_parameter(
            name="limits_monitoring",
            docstring="Activates or not the voltage or current limit monitoring for the BE5845/BE2142 board",
            vals=vals.Enum(0, 1, 2, 3),
            get_cmd=partial(self._parent._get_limits_monitoring, module, ch),
            set_cmd=partial(self._parent._set_limits_monitoring, module, ch),
        )

        self.add_parameter(
            name="output_start_delay",
            docstring="delay after the OUTPut ON command to perform the ON process",
            vals=vals.Numbers(10, 60e3),
            unit="ms",
            get_cmd=partial(self._parent._get_output_start_delay, module, ch),
            set_cmd=partial(self._parent._set_output_start_delay, module, ch),
        )

        self.add_parameter(
            name="output_stop_delay",
            docstring="delay after the OUTPut OFF command to perform the OFF process",
            vals=vals.Numbers(0, 50),
            unit="ms",
            get_cmd=partial(self._parent._get_output_stop_delay, module, ch),
            set_cmd=partial(self._parent._set_output_stop_delay, module, ch),
        )

        self.add_parameter(
            name="trigger_input_delay",
            docstring="Delay after the trigger input event",
            vals=vals.Numbers(0, 60e3),
            unit="ms",
            get_cmd=partial(self._parent._get_trigger_input_delay, module, ch),
            set_cmd=partial(self._parent._set_trigger_input_delay, module, ch),
        )

        self.add_parameter(
            name="voltage_step_amplitude",
            docstring="Step amplitude for the staircase or step modes",
            vals=vals.Numbers(1.2e-6, 12),
            unit="V",
            get_cmd=partial(self._parent._get_voltage_step_ampl, module, ch),
            set_cmd=partial(self._parent._set_voltage_step_ampl, module, ch),
        )

        self.add_parameter(
            name="voltage_step_width",
            docstring="Step width for the staircase mode",
            vals=vals.Numbers(5, 60e3),
            unit="ms",
            get_cmd=partial(self._parent._get_voltage_step_width, module, ch),
            set_cmd=partial(self._parent._set_voltage_step_width, module, ch),
        )


class iTestBilt(VisaInstrument):
    """
    This is the QCoDeS driver for the Itest voltage sources BE2141, BE2142 and BE5845. Not all the functions are implemented yet.

    If nothing is specified in the header of a function, it is usable for the three mentionned boards. Otherwise mentionned.

    This driver is derived from the Qcodes_contrib_drivers for iTest device from Bilt.
    """

    def __init__(self, name: str, address: str, **kwargs):
        """
        Args:
            name: The instrument name used by qcodes
            address: The VISA name of the resource
        Returns:
            iTestBilt object
        """
        super().__init__(name, address, terminator="\n", **kwargs)

        self.inst_dictionnary = {}

        self.n_inst = 0

        # Obtain the instrument dictionnary to identify the boards in your chassis
        self.inst_dictionnary, self.channel = self.get_parameters_instruments()

        # Create the channels
        for j in range(1, self.n_inst + 1):
            for i in range(1, self.channel + 1):
                channel = iTestChannel(
                    parent=self, name=f"mod{j}_chan{i:02}", module=j, ch=i
                )
                self.add_submodule(f"mod{j}_ch{i:02}", channel)

        print(f"Connected to {self.IDN()['model']}")

    def _get_channel_voltage_range(self, module: int, ch: int) -> str:
        """
        Returns the output voltage range for the desired channel
        Returns:
            Output voltage range in V
        """
        chan_id = self.chan_to_id(module, ch)
        return self.ask(f"{chan_id}VOLT:RANGE?")[:-2]

    def _set_channel_voltage_range(self, module: int, ch: int, value: float) -> None:
        """
        Sets the output voltage range for the desired channel of the desired module
        Args:
            value: Voltage range in units of V (1.2 or 12) for BE2141/BE2142
            value: Voltage range in units of V 15V for BE5845
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            self.write(f"{chan_id}OUTP 0")
            self.write(f"{chan_id}VOLT:RANGE 15")
            print("Be careful: output has been turned off to change range")

        elif board_model == "2141" or board_model == "2142":
            self.write(f"{chan_id}OUTP 0")
            self.write(f"{chan_id}VOLT:RANGE {value}")
            print("Be careful: output has been turned off to change range")

    def _get_channel_voltage(self, module: int, ch: int) -> float:
        """
        Returns the output voltage of the desired channel
        Returns:
            Voltage (V)
        """
        chan_id = self.chan_to_id(module, ch)
        return float(self.ask(f"{chan_id}MEAS:VOLT?"))

    def _set_channel_voltage(self, module: int, ch: int, value: float) -> None:
        """
        Sets the output voltage of the desired channel of the desired module
        Args:
            value: The set value of voltage in V
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            self.write(f"{chan_id}VOLT {value:.8f}")

        elif board_model == "2141" or board_model == "2142":
            range_val = float(self._get_channel_voltage_range(module, ch))

            if value > range_val:
                raise ValueError(
                    "The asked voltage is too much for the selected voltage range"
                )

            board_model = self.get_instrument_model(module)

            self._set_ramp_mode(module, ch, mode="RAMP")
            # self._set_ramp_rate(module, ch, rate = 0.001) # V/ms
            self.write(f"{chan_id}VOLT {value:.8f}")

            self.write(f"{chan_id}TRIG:INput:INIT")

            while self.ask(f"{chan_id}VOLT:STAT?") != "1":
                sleep(1)

    def _get_channel_status(self, module: int, ch: int) -> int:
        """
        Returns the status of the desired channel
        Returns:
            status: 0 (OFF) or 1 (ON)
        """
        chan_id = self.chan_to_id(module, ch)
        status = self.ask(f"{chan_id}OUTP ?")

        if status in ["1", "0"]:
            return int(status)
        else:
            raise Exception(f"Unknown status: {status}")

    def _set_channel_status(self, module: int, ch: int, status: int) -> None:
        """
        Sets the status of the desired channel
        Args:
            status: 0 (OFF) or 1 (ON)
        """
        chan_id = self.chan_to_id(module, ch)
        self.write(f"{chan_id}OUTP {status}")

    def _get_ramp_mode(self, module: int, ch: int) -> int:
        """
        Returns the channel output is set to EXP (immediate), RAMP,
        STAIR, STEP or AUTO mode
        Returns:
             mode: 0 (EXP), 1 (RAMP), 2 (STAIR), 3 (STEP), 4 (AUTO)
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            raise ValueError("Not asking a BE2141 or BE2142 board")

        return int(self.ask(f"{chan_id}trig:input?"))

    def _set_ramp_mode(
        self,
        module: int,
        ch: int,
        mode: Literal["EXP", "RAMP", "STAIR", "STEP", "AUTO", 0, 1, 2, 3, 4],
    ) -> None:
        """
        Sets the desired channel output to EXP (immediate), RAMP,
        STAIR, STEP or AUTO mode
        Args:
            mode: EXP, RAMP, STAIR, STEP or AUTO
        """

        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            raise ValueError("Not asking a BE2141 or BE2142 board")

        self.write(f"{chan_id}TRIG:INput {mode}")

    def _get_ramp_rate(self, module: int, ch: int) -> float:
        """
        Returns the output voltage ramp rate
        """
        chan_id = self.chan_to_id(module, ch)
        return float(self.ask(f"{chan_id}VOLT:SLOP?"))

    def _set_ramp_rate(self, module: int, ch: int, rate: float) -> None:
        """
        Sets the output voltage ramp rate
        Args:
            rate: rate of ramp in V/ms
        """
        chan_id = self.chan_to_id(module, ch)
        self.write(f"{chan_id}VOLT:SLOP {rate:.8f}")

    def _get_channel_current(self, module: int, ch: int) -> float:
        """
        Returns the output current in the desired channel
        Returns:
            Current (A)
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "2142" or board_model == "5845":
            val = float(self.ask(f"{chan_id}MEAS:CURR?"))
        else:
            raise ValueError("Not asking a BE2142 or BE5845 board")

        return val

    def _set_channel_current(self, module: int, ch: int, value: float) -> None:
        """
        Sets the output current of the desired channel of the desired module
        Args:
            value: The set value of current in A
        """
        chan_id = self.chan_to_id(module, ch)

        range_val = float(self._get_channel_current_range(module, ch))

        if value > range_val:
            raise ValueError(
                "The asked current is too much for the selected current range"
            )

        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            self.write(f"{chan_id}CURR {value}")

        else:
            raise ValueError("Not asking a BE5845 board")

    def _get_channel_voltage_limit_up(self, module: int, ch: int) -> str:
        """
        Returns the output voltage upper limit for the desired channel
        Returns:
            Limit up (V)
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            out = self.ask(f"{chan_id}LIM:VOLT:UPP?")

        elif board_model == "2141" or board_model == "2142":
            out = self.ask(f"{chan_id}limit:upp?")

        else:
            raise ValueError(f"Unsupported board model {board_model}")

        return str(out)

    def _set_channel_voltage_limit_up(
        self, module: int, ch: int, value_up: float
    ) -> None:
        """
        Sets the output voltage upper limit for the desired channel
        Args:
            value_up: Voltage upper limit in units of V
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            self.write(f"{chan_id}LIM:VOLT:UPP {value_up}")
            self.write(f"{chan_id}LIM:STAT 1")

        elif board_model == "2142":
            self.write(f"{chan_id}limit:upp {value_up}")
            self.write(f"{chan_id}LIM:STAT 1")

        elif board_model == "2141":
            self.write(f"{chan_id}limit:upp {value_up}")
            print(
                "Be careful : Not possible to activate voltage or current limits on BE2141"
            )

    def _get_channel_voltage_limit_low(self, module: int, ch: int) -> str:
        """
        Returns the output voltage upper and lower limit for the desired channel
        Returns:
            Limit down (V)
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            out = self.ask(f"{chan_id}LIM:VOLT:LOW?")

        elif board_model == "2141" or board_model == "2142":
            out = self.ask(f"{chan_id}limit:low?")

        else:
            raise ValueError(f"Unsupported board model {board_model}")

        return str(out)

    def _set_channel_voltage_limit_low(
        self, module: int, ch: int, value_down: float
    ) -> None:
        """
        Sets the output voltage lower limit for the desired channel
        Args:
            value_down: Voltage lower limit in units of V
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            self.write(f"{chan_id}LIM:VOLT:LOW {value_down}")
            self.write(f"{chan_id}LIM:STAT 1")

        elif board_model == "2142":
            self.write(f"{chan_id}limit:low {value_down}")
            self.write(f"{chan_id}LIM:STAT 1")

        if board_model == "2141":
            self.write(f"{chan_id}limit:low {value_down}")
            print(
                "Be careful : Not possible to activate voltage or current limits on BE2141"
            )

    def _get_channel_current_limit_up(self, module: int, ch: int) -> str:
        """
        Returns the output current upper  limit for the desired channel
        Returns:
            Limit up (A)
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == "5845" or board_model == "2142":
            out = self.ask(f"{chan_id}LIM:CURR:UPP?")
        else:
            raise ValueError("Not asking a BE5845 or BE2142 board")

        return str(out)

    def _set_channel_current_limit_up(
        self, module: int, ch: int, value_up: float
    ) -> None:
        """
        Sets the output current upper limit for the desired channel. Only works for BE2142 or BE5845
        Args:
            value_up: Current lower limit in units of A
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)
        if board_model == "5845" or board_model == "2142":
            self.write(f"{chan_id}LIM:CURR:UPP {value_up}")
            self.write(f"{chan_id}LIM:STAT 1")

        else:
            raise ValueError("Not asking a BE5845 or BE2142 board")

    def _get_channel_current_limit_low(self, module: int, ch: int) -> str:
        """
        Returns the output current upper and lower limit for the desired channel
        Returns:
            Limit down (A)
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == "5845" or board_model == "2142":
            out = self.ask(f"{chan_id}LIM:CURR:LOW?")
        else:
            raise ValueError("Not asking a BE5845 or BE2142 board")

        return str(out)

    def _set_channel_current_limit_low(
        self, module: int, ch: int, value_down: float
    ) -> None:
        """
        Sets the output current lower limit for the desired channel. Only works for BE2142 or BE5845
        Args:
            value_down: Current lower limit in units of A
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)
        if board_model == "5845" or board_model == "2142":
            self.write(f"{chan_id}LIM:CURR:LOW {value_down}")
            self.write(f"{chan_id}LIM:STAT 1")
        else:
            raise ValueError("Not asking a BE5845 or BE2142 board")

    def _get_curr_range_auto(self, module: int, ch: int) -> str:
        """
        Queries whether the automatic selection of current range for BE5845 is activated.
        Returns:
                status of automatic current range selection as 'ON' or 'OFF' (string)
        """

        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            val = str(self.ask(f"{chan_id}CURR:RANGE:AUTO?"))

            if val == "1":
                val_str = "ON"
            elif val == "0":
                val_str = "OFF"
        else:
            raise ValueError("Not asking a BE5845 module")

        return val_str

    def _set_curr_range_auto(self, module: int, ch: int, value: int) -> None:
        """
        Sets automatic selction of the current range for the BE5845 depending on current setting.
        The range will only be changed when the module is off, so not during a measurement.
        Args:
            value: 1 (ON), 0 (OFF)
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            self.write(f"{chan_id}CURR:RANG:AUTO {value}")
        else:
            raise ValueError(f"Not aksing BE5845 module or Unknown status: {value}")

    def _get_voltage_range_auto(self, module: int, ch: int) -> str:
        """
        Queries whether the automatic selection of voltage range for BE2141/2142 is activated.
        Returns:
                status of automatic voltage range selection as 'ON' or 'OFF' (string)
        """

        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "2141" or board_model == "2142":
            val = str(self.ask(f"{chan_id}VOLT:RANGE:AUTO?"))

            if val == "1":
                val_str = "ON"
            elif val == "0":
                val_str = "OFF"
        else:
            raise ValueError("Not asking a BE2141 or BE2142 module")

        return val_str

    def _set_voltage_range_auto(self, module: int, ch: int, value: int) -> None:
        """
        Sets automatic selection of the voltage range for the BE2141/2142 depending on voltage setting.
        The range will only be changed when the module is off, so not during a measurement.
        Args:
            value : 1 (ON), 0 (OFF)
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "2141" or board_model == "2142":
            self.write(f"{chan_id}VOLT:RANG:AUTO {value}")
        else:
            raise ValueError(
                f"Not aksing BE2141 or BE2142 module or Unknown status: {value}"
            )

    def _get_limits_monitoring(self, module: int, ch: int) -> str:
        """
        Returns the state the limit in current or voltage monitoring
        Returns:
            The state of the limits monitoring (no monitoring, current only, voltage only, voltage & current)
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            val = str(self.ask(f"{chan_id}LIM:STAT?"))

            val_2 = str(self.ask(f"{chan_id}LIM:FUNC?"))

            if val == "1":
                val_str = "Voltage & current monitoring"

            elif val_2 == "1":
                val_str = "Current monitoring only"

            elif val_2 == "2":
                val_str = "Voltage monitoring only"

            elif val_2 == "3":
                val_str = "Voltage & current monitoring"

            elif val == "0":
                if val_2 != "1" and val_2 != "2" and val_2 != "3":
                    val_str = "No limit monitoring"

        elif board_model == "2142":
            val_str = str(self.ask(chan_id + "LIM:STAT?"))

        else:
            raise ValueError("Not asking a BE5845 or BE2142 board")

        return val_str

    def _set_limits_monitoring(self, module: int, ch: int, value: int) -> None:
        """
        Sets on or off the limit in current or voltage monitoring
        Args:
            0: Turns off current and voltage limit monitoring
            1: current monitoring only for BE5845; Voltage and current monitoring for BE2142
            2: voltage monitoring only
            3: voltage and current monitoring (equivalent to value 1 for the LIM:STAT instruction)
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            if value == 1 or value == 2:
                self.write(f"{chan_id}LIM:FUNC {value}")

            elif value == 3:
                self.write(f"{chan_id}LIM:STAT {value - 2}")
                self.write(f"{chan_id}LIM:FUNC {value}")

            elif value == 0:
                self.write(f"{chan_id}LIM:STAT {value}")

        elif board_model == "2142":
            self.write(f"{chan_id}LIM:STAT {value}")

        else:
            raise ValueError("Not asking a BE5845 or BE2142 board")

    def _get_channel_current_range(self, module: int, ch: int) -> str:
        """
        Returns the output current range for the desired channel
        Returns:
            Output current range in A
        """
        chan_id = self.chan_to_id(module, ch)
        return self.ask(f"{chan_id}CURR:RANGE?")[:-2]

    def _set_channel_current_range(self, module: int, ch: int, value: float) -> None:
        """
        Sets the output curent range for the desired channel of the desired module
        Args:
            value: Current range in units of A (15 mA) for BE2141/BE2142
            value: Current range in units of A (2 or 200 mA) for BE5845
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == "5845":
            self.write(f"{chan_id}OUTP 0")

            self.write(f"{chan_id}CURR:RANGE {value}")
            print("Be careful: output has been turned off to change range")

        elif board_model == "2141" or board_model == "2142":
            self.write(f"{chan_id}OUTP 0")
            print("Be careful: output has been turned off to change range")
            self.write(f"{chan_id}CURR:RANGE {0.015}")

    def _get_output_start_delay(self, module: int, ch: int) -> float:
        """
        Returns the output delay to perform the ON process
        for the desired channel
        Returns:
            Delay in ms
        """
        chan_id = self.chan_to_id(module, ch)
        return float(self.ask(f"{chan_id}STAR:DEL?"))

    def _set_output_start_delay(self, module: int, ch: int, value: float) -> None:
        """
        Set the output delay to perform the ON process
        for the desired channel
        Args:
            value: delay time in ms (10 ms to 60 s)
        """
        chan_id = self.chan_to_id(module, ch)
        return self.write(f"{chan_id}STAR:DEL {value}")

    def _get_output_stop_delay(self, module: int, ch: int) -> float:
        """
        Returns the output delay to perform the OFF process
        for the desired channel
        Returns:
            Delay in ms
        """
        chan_id = self.chan_to_id(module, ch)
        return float(self.ask(f"{chan_id}STOP:DEL?"))

    def _set_output_stop_delay(self, module: int, ch: int, value: float) -> None:
        """
        Set the output delay to perform the OFF process
        for the desired channel
        Args:
            value: delay time in ms (0 to 50 ms)
        """
        chan_id = self.chan_to_id(module, ch)
        return self.write(f"{chan_id}STOP:DEL {value}")

    def _get_trigger_input_delay(self, module: int, ch: int) -> float:
        """
        Returns delay after the trigger input event
        Returns:
            Delay in ms
        """
        chan_id = self.chan_to_id(module, ch)
        return float(self.ask(f"{chan_id}TRIG:INput:DEL?"))

    def _set_trigger_input_delay(self, module: int, ch: int, value: float) -> None:
        """
        Set delay after the trigger input event
        Args:
            value: delay time in ms (0 ms to 60 s)
        """
        chan_id = self.chan_to_id(module, ch)
        return self.write(f"{chan_id}TRIG:INput:DEL {value}")

    def _get_voltage_step_ampl(self, module: int, ch: int) -> float:
        """
        Returns the step amplitude for the staircase or step modes
        Returns:
            Step amplitude in V
        """
        chan_id = self.chan_to_id(module, ch)
        return float(self.ask(f"{chan_id}VOLT:STep:AMPL?"))

    def _set_voltage_step_ampl(self, module: int, ch: int, value: float) -> None:
        """
        Sets the step amplitude for the staircase or step modes
        Args:
            value: step amplitude in V
        """
        chan_id = self.chan_to_id(module, ch)
        return self.write(f"{chan_id}VOLT:STep:AMPL {value}")

    def _get_voltage_step_width(self, module: int, ch: int) -> float:
        """
        Returns the step width for the staircase mode
        Returns:
            Step width in ms
        """
        chan_id = self.chan_to_id(module, ch)
        return float(self.ask(f"{chan_id}VOLT:STep:WID?"))

    def _set_voltage_step_width(self, module: int, ch: int, value: float) -> None:
        """
        Sets the step width for the staircase mode
        Args:
            value: step width in ms
        """
        chan_id = self.chan_to_id(module, ch)
        return self.write(f"{chan_id}VOLT:STep:WID {value}")

    def get_instrument_model(self, inst: int) -> str:
        """
        Returns the model of the board at position 'inst' in the chassis.
        The returned string is of the form 'inst1,1111;inst2,2222;inst3,3333;inst4,4444;inst5,5555'
        The function only returns the asked inst model.
        Returns:
            Model in string format XXXX
        """

        string_chassis = str(self.ask("inst:list?"))

        if inst == 1:
            index_start_inst = 2

        else:
            index_start_inst = int((int(inst) - 1) * 7) + 2

        index_end_inst = int(index_start_inst + 4)

        return str(string_chassis[index_start_inst:index_end_inst])

    def get_parameters_instruments(self):
        """
        Returns some useful parameters of the different boards in the chassis.
        The parameters are hardcoded here because not available from any foundable VISA instruction

        Feel free to update for new boards model than the one we use now or new parameters to extract

        Returns:
                inst_dictionnary, total_channel_number
                inst_dictionnary : Dictionnary which contains some basic properties of all the borads in your chassis.
                total_channel_number: int, the total number of channels in the chassis
        """

        string_chassis = str(self.ask("inst:list?"))

        for i in range(len(string_chassis)):
            if (
                string_chassis[i] == ","
            ):  # We use the comma separator to detect the number of borads in the chassis from the returned string of inst:list? instruction
                self.n_inst += 1

        inst_array = ["", "", ""]

        total_channel_number = 0

        for i in range(self.n_inst):
            inst_array[i] = self.get_instrument_model(int(i + 1))

            if inst_array[i] == "2141" or inst_array[i] == "2142":
                self.inst_dictionnary["BE" + self.get_instrument_model(int(i + 1))] = {
                    "V_max_V": 12,
                    "I_max_A": 0.015,
                    "nb_range_V": 2,
                    "nb_range_I": 1,
                    "nb_channels": 4,
                    "low_range_V_V": 1.2,
                    "high_range_V_V": 12,
                    "low_range_I_A": 0.015,
                    "high_range_I_A": 0.015,
                    "position_in_chassis": int(i + 1),
                }
            elif inst_array[i] == "5845":
                self.inst_dictionnary["BE" + self.get_instrument_model(int(i + 1))] = {
                    "V_max_V": 15,
                    "I_max_A": 0.2,
                    "nb_range_V": 1,
                    "nb_range_I": 2,
                    "nb_channels": 6,
                    "low_range_V_V": 15,
                    "high_range_V_V": 15,
                    "low_range_I_A": 0.002,
                    "high_range_I_A": 0.2,
                    "position_in_chassis": int(i + 1),
                }

            total_channel_number += self.inst_dictionnary[f"BE{inst_array[i]}"][
                "nb_channels"
            ]

        return self.inst_dictionnary, total_channel_number

    def chan_to_id(self, module: int, ch: int) -> str:
        # Returns the string to be put at the beginning of each VISA instruction to adress specifically a board (module) and a channel

        i, c = module, ch

        if module > self.n_inst:
            raise ValueError(
                "Error: The adressed module number is larger than the number of modules in the chassis"
            )

        board_chan_number = self.inst_dictionnary[
            f"BE{self.get_instrument_model(module)}"
        ]["nb_channels"]

        if ch > board_chan_number:
            raise ValueError(
                "Error: The adressed channel number is larger than the number of channels of the adressed module"
            )

        self.chan_id = f"i{i};c{c};"

        return f"i{i};c{c};"
