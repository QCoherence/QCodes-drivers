# Last updated on 07 May 2026
#                     -- J-S


import logging

import numpy as np
from numpy import pi
from qcodes import Parameter, VisaInstrument
from qcodes import validators as vals
from qcodes.parameters import create_on_off_val_mapping

log = logging.getLogger(__name__)


class FreqSweep(Parameter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_raw(self):
        return np.linspace(
            self._instrument.freq_start(),
            self._instrument.freq_stop(),
            self._instrument.freq_points(),
        )


class E8257D(VisaInstrument):
    """
    QCoDeS driver for the Agilent E8257D MW source
    """

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__

    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name, address, terminator="\n", **kwargs)

        self.add_parameter(
            name="frequency",
            label="Output frequency in Hz",
            vals=vals.Numbers(100e3, 40e9),
            unit="Hz",
            set_cmd="FREQ:CW {:.12f}",
            get_cmd="FREQ:CW?",
        )

        self.add_parameter(
            name="power",
            label="Output power",
            vals=vals.Numbers(-135, 25),
            unit="dBm",
            set_cmd="POW:AMPL {:.12f}",
            get_cmd="POW:AMPL?",
            get_parser=float,
        )

        self.add_parameter(
            name="phase",
            label="Output phase",
            vals=vals.Numbers(-2 * pi, 2 * pi),
            unit="Rad",
            set_cmd="PHASE {:.12f}",
            get_cmd="PHASE?",
            set_parser=self.rad_to_deg,
            get_parser=self.deg_to_rad,
        )

        self.add_parameter(
            name="status",
            label="Output on/off",
            vals=vals.Bool(),
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
            set_cmd="OUTP {}",
            get_cmd="OUTP?",
        )

        self.add_parameter(
            name="modulation",
            label="Modulation on/off",
            vals=vals.Bool(),
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
            set_cmd="OUTP:MOD {}",
            get_cmd="OUTP:MOD?",
        )

        self.add_parameter(
            name="pulse_modulation",
            label="Pulse modulation on/off",
            vals=vals.Bool(),
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
            set_cmd="PULM:STATe {}",
            get_cmd="PULM:STATe?",
        )

        self.add_parameter(
            name="alc",
            label="ALC on/off",
            description="This command enables or disables the automatic leveling control (ALC) circuit. "
            "The purpose of the ALC circuit is to hold output power at a desired level by adjusting the signal "
            "generator power circuits for power drift. Power will drift over time and with changes in temperature. "
            "Refer to the E8257D/67D, E8663D PSG Signal Generators User’s Guide for more information on the ALC.",
            vals=vals.Bool(),
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
            set_cmd="POWer:ALC {}",
            get_cmd="POWer:ALC?",
        )

        self.add_parameter(
            name="freq_start",
            label="Sweep: start frequency in Hz",
            vals=vals.Numbers(100e3, 40e9),
            unit="Hz",
            set_cmd="FREQ:START {:.12f}Hz",
            get_cmd="FREQ:START?",
            get_parser=float,
        )

        self.add_parameter(
            name="freq_stop",
            label="Sweep: stop frequency in Hz",
            vals=vals.Numbers(100e3, 40e9),
            unit="Hz",
            set_cmd="FREQ:STOP {:.12f}Hz",
            get_cmd="FREQ:STOP?",
            get_parser=float,
        )

        self.add_parameter(
            name="freq_points",
            label="Sweep: frequency points",
            vals=vals.Numbers(2, 20 * 10**9),
            unit="Hz",
            set_cmd="SWEep:POINts {:.12f}",
            get_cmd="SWE:POIN?",
            get_parser=int,
        )

        self.add_parameter(
            name="dwell_time",
            label="Sweep: dwell time",
            vals=vals.Numbers(1e-3, 1000),
            unit="s",
            set_cmd="SWE:DWEL {:.12f}s",
            get_cmd="SWE:DWEL?",
            get_parser=float,
        )

        self.add_parameter(
            name="sourcemode",
            label="Set source mode",
            vals=vals.Enum("CW", "sweep"),
            set_cmd="SOURce:FREQuency:MODE {}",
            get_cmd="SOURce:FREQuency:MODE?",
        )

        self.add_parameter(
            name="sweepmode",
            label="Set frequency sweep mode",
            vals=vals.Enum("AUTO", "SINGLE"),
            set_cmd=self.set_sweepmode,
            get_cmd=self.get_sweepmode,
        )

        self.add_parameter(
            name="spacing_freq",
            label="Set spacing mode of frequency sweep",
            vals=vals.Enum("LIN", "LOG"),
            set_cmd="SWE:SPAC {}",
            get_cmd="SWE:SPAC?",
        )

        self.add_parameter(
            name="freq_vec",
            label="Parameter to get the vector of frequencies used for the sweep",
            parameter_class=FreqSweep,
        )

        self.add_parameter(
            name="pulse_period",
            label="Period of the full square pulse",
            description="Total length of the pulse, high and low positions included.",
            vals=vals.Numbers(70e-9, 42),
            unit="s",
            set_cmd="PULM:INTernal:PERiod {}S",
            get_cmd="PULM:INTernal:PERiod?",
        )

        self.add_parameter(
            name="pulse_width",
            label="Width of the square pulse",
            description="Length of the high position of the pulse. Must be set after pulse period! "
            "The maximum value is pulse width - 20ns",
            vals=vals.Numbers(10e-9, 42 - 20e-9),
            unit="s",
            set_cmd="PULM:INTernal:PWIDth {}S",
            get_cmd="PULM:INTernal:PWIDth?",
            set_parser=self.set_pulse_width,
        )

        self.add_parameter(
            name="pulse_source",
            label="Type of pulse",
            description="There is 5 kind of pulses. "
            "The internal one are shapped by the device but some can be triggered externaly; "
            "the external one is outputing a signal while receiving a high state on the triggering port.",
            vals=vals.Enum(
                "Square", "Free-run", "Triggered", "Doublet", "Gated", "External"
            ),
            set_cmd=self.set_pulse_source,
            get_cmd=self.get_pulse_source,
        )

        self.add_parameter(
            name="alc_search",
            label="ALC search",
            description="Power Search is a cal routine which improves output power accuracy when ALC is off. "
            "This command enables or disables the internal power search calibration. "
            "A power search is recommended for pulse–modulated signals with pulse widths less than one microsecond. "
            "Refer to the E8257D/67D, E8663D PSG Signal Generators User’s Guide for more information on ALC and the power search function.",
            vals=vals.Enum("Manual", "Auto", "Span"),
            set_cmd=":POWer:ALC:SEARch {}",
            get_cmd=":POWer:ALC:SEARch?",
        )

        # good idea to call connect_message at the end of your constructor.
        # this calls the 'IDN' parameter that the base Instrument class creates
        # for every instrument  which serves two purposes:
        # 1) verifies that you are connected to the instrument
        # 2) gets the ID info so it will be included with metadata snapshots later.
        self.connect_message()

    def rad_to_deg(self, theta):
        return theta * 180.0 / pi

    def deg_to_rad(self, theta):
        return float(theta) * pi / 180.0

    def get_sweepmode(self):
        """
        Get if we are in sweep mode continuous or single
        """

        if self.ask("INITiate:CONTinuous?") == "0":
            return "SINGLE"
        else:
            return "AUTO"

    def set_sweepmode(self, sweepmode="single"):
        """
        Set the frequency sweep mode

        Input:
        sweepmode (string): AUTO or SINGLE
        Output:
        None
        """

        if sweepmode.upper() in ("AUTO"):
            self.write("SWE:MODE AUTO")
            self.write("SWEep:GENeration STEPped")
            self.write("TRIGger:SOURce IMMediate")
            self.write("INITiate:CONTinuous ON")

        elif sweepmode.upper() in ("SINGLE"):
            self.write("SWE:MODE AUTO")
            self.write("SWEep:GENeration STEPped")
            self.write("TRIGger:SOURce IMMediate")
            self.write("INITiate:CONTinuous OFF")
        else:
            raise ValueError("set_sweepmode(): can only set AUTO or SINGLE")

    def startsweep(self):
        """
        Start the frequency sweep. Valid in the 'SINGLE' sweep mode.

        Input:
            None
        Output:
            None
        """

        self.write(":TSWeep")

    def set_pulse_width(self, width):
        if width > self.pulse_period() - 20e-9:
            raise ValueError(
                "Pulse width can be maximally 20 ns shorter than the pulse period. "
                "Please increase the pulse period first."
            )

        return width

    def get_pulse_source(self):
        pulse_source = self.ask("PULM:SOUR?")
        pulse_source_int = self.ask("PULM:SOUR:INT?")
        match pulse_source, pulse_source_int:
            case "EXT", _:
                return "External"
            case "INT", "SQU":
                return "Square"
            case "INT", "FRUN":
                return "Free-run"
            case "INT", "TRIG":
                return "Triggered"
            case "INT", "DOUB":
                return "Doublet"
            case "INT", "GATE":
                return "Gated"
            case _, _:
                raise ValueError(
                    "Unsupported pulse mode: {pulse_source}, {pulse_source_int}."
                )

    def set_pulse_source(self, ps):
        if ps == "External":
            self.write("PULM:SOUR EXT")
        else:
            self.write("PULM:SOUR INT")
            if ps == "Free-run":
                self.write("PULM:SOUR:INT FRUN")
            else:
                self.write(f"PULM:SOUR:INT {ps}")

    def setup_pulse_mode(self):
        self.modulation("ON")
        self.pulse_modulation("ON")
        if self.alc():
            self.alc("OFF")
            print(
                "You can press the softkey `Do power search` to perform an automatic optimisation of the output power."
            )
        self.alc_search("Span")
        self.pulse_period(200e-9)
        self.pulse_width(100e-9)

    def set_gui_update(self, update="ON"):
        """
        The command switches the update of the display on/off.
        A switchover from remote control to manual control always sets
        the status of the update of the display to ON.

        Input:
            status (string): 'on' or 'off'
        Output:
            None
        """

        self.write(f"DISP:REM {update}")

    def reset(self):
        """
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        """

        self.write("*RST")
