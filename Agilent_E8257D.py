# Last updated on 07 Jul 2025
#                     -- J-S


from qcodes import VisaInstrument, Parameter, validators as vals
from qcodes.utils.helpers import create_on_off_val_mapping
import logging

from numpy import pi
import numpy as np

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
            set_cmd="FREQ:CW " + "{:.12f}",
            get_cmd="FREQ:CW?",
        )

        self.add_parameter(
            name="power",
            label="Output power",
            vals=vals.Numbers(-135, 25),
            unit="dBm",
            set_cmd="POW:AMPL " + "{:.12f}",
            get_cmd="POW:AMPL?",
            get_parser=float,
        )

        self.add_parameter(
            name="phase",
            label="Output phase",
            vals=vals.Numbers(-2 * pi, 2 * pi),
            unit="Rad",
            set_cmd="PHASE " + "{:.12f}",
            get_cmd="PHASE?",
            set_parser=self.rad_to_deg,
            get_parser=self.deg_to_rad,
        )

        self.add_parameter(
            name="status",
            label="Output on/off",
            vals=vals.Bool(),
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
            set_cmd="OUTP " + "{}",
            get_cmd="OUTP?",
        )

        self.add_parameter(
            name="freq_start",
            label="Sweep: start frequency in Hz",
            vals=vals.Numbers(100e3, 40e9),
            unit="Hz",
            set_cmd="FREQ:START " + "{:.12f}" + "Hz",
            get_cmd="FREQ:START?",
            get_parser=float,
        )

        self.add_parameter(
            name="freq_stop",
            label="Sweep: stop frequency in Hz",
            vals=vals.Numbers(100e3, 40e9),
            unit="Hz",
            set_cmd="FREQ:STOP " + "{:.12f}" + "Hz",
            get_cmd="FREQ:STOP?",
            get_parser=float,
        )

        self.add_parameter(
            name="freq_points",
            label="Sweep: frequency points",
            vals=vals.Numbers(2, 20 * 10**9),
            unit="Hz",
            set_cmd="SWEep:POINts " + "{:.12f}",
            get_cmd="SWE:POIN?",
            get_parser=int,
        )

        self.add_parameter(
            name="dwell_time",
            label="Sweep: dwell time",
            vals=vals.Numbers(1e-3, 1000),
            unit="s",
            set_cmd="SWE:DWEL " + "{:.12f}" + "s",
            get_cmd="SWE:DWEL?",
            get_parser=float,
        )

        self.add_parameter(
            name="sourcemode",
            label="Set source mode",
            vals=vals.Enum("CW", "sweep"),
            set_cmd="SOURce:FREQuency:MODE " + "{}",
            get_cmd="SOURce:FREQuency:MODE?",
            set_parser=self.set_freqsweep,
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

    def set_freqsweep(self, freqsweep="off"):
        """
        Set the frequency sweep mode to 'on' or 'off'

        Input:
        status (string): 'on' or 'off'
        Output:
        None
        """

        if freqsweep.upper() in ("SWEEP"):
            self.write("SOURCE:FREQUENCY:MODE SWEEP")
        elif freqsweep.upper() in ("CW"):
            self.write("SOURCE:FREQUENCY:MODE CW")
        else:
            raise ValueError("set_freqsweep(): can only set on or off")

    def get_freqsweep(self):
        """
        Get the status of the frequency sweep mode from the instrument

        Input:
        None
        Output:
        status (string) : 'on' or 'off'
        """
        # Output can be '0', '1' or '0\n', '1\n' which are different strings.
        # By using int() we can only get 1 or 0 independently of the OS.
        stat = self.query("SWE:RUNN?")

        if stat == 1:
            return "on"
        elif stat == 0:
            return "off"
        else:
            raise ValueError("Output status not specified : %s" % stat)

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
