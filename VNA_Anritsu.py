import logging
import time
from functools import partial
from typing import Any, Optional

import numpy as np
from qcodes import (
    ArrayParameter,
    ChannelList,
    InstrumentChannel,
    ManualParameter,
    MultiParameter,
    VisaInstrument,
)
from qcodes import validators as vals
from qcodes.parameters import Parameter, ParameterWithSetpoints
from qcodes.validators import Arrays

log = logging.getLogger(__name__)


class GeneratedSetPoints(Parameter):
    """
    A parameter that generates a setpoint array from start, stop and num points
    parameters.
    """

    def __init__(self, startparam, stopparam, numpointsparam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._startparam = startparam
        self._stopparam = stopparam
        self._numpointsparam = numpointsparam

    def get_raw(self):
        return np.linspace(
            self._startparam(), self._stopparam(), self._numpointsparam()
        )


class FrequencySweepMagPhase(MultiParameter):
    """
    Sweep that return magnitude and phase.
    """

    def __init__(self, name, instrument, start, stop, npts, channel, **kwargs):
        super().__init__(name, names=("", ""), shapes=((), ()), instrument=instrument)
        self._instrument = instrument
        self.set_sweep(start, stop, npts)
        self._channel = channel
        self.names = ("magnitude", "phase")
        self.labels = (
            "{} magnitude".format(instrument.short_name),
            "{} phase".format(instrument.short_name),
        )
        self.units = ("dB", "rad")
        # self.units = ('dB', 'deg')
        self.setpoint_units = (("Hz",), ("Hz",))
        self.setpoint_labels = (
            ("{} frequency".format(instrument.short_name),),
            ("{} frequency".format(instrument.short_name),),
        )
        self.setpoint_names = (
            ("{}_frequency".format(instrument.short_name),),
            ("{}_frequency".format(instrument.short_name),),
        )

    def set_sweep(self, start, stop, npts):
        #  needed to update config of the software parameter on sweep change
        # freq setpoints tuple as needs to be hashable for look up
        f = tuple(np.linspace(int(start), int(stop), num=npts))
        self.setpoints = ((f,), (f,))
        self.shapes = ((npts,), (npts,))

    def get_raw(self):
        old_format = self._instrument.format()
        self._instrument.format("Complex")
        data = self._instrument._get_sweep_data(force_polar=True)
        self._instrument.format(old_format)
        real, imag = np.transpose(np.reshape(data, (-1, 2)))
        # return abs(real + 1j*imag), np.angle(real + 1j*imag)
        return 20.0 * np.log10(abs(real + 1j * imag)), np.angle(real + 1j * imag)
        # return abs(data), np.angle(data)


class CWPhase(ParameterWithSetpoints):
    """
    Sweep that returns phase(for CW mode, with set delay).
    """

    def get_raw(self):
        old_format = self._instrument.format()
        self._instrument.format("Phase")
        data = self._instrument._get_sweep_data_CW(force_polar=False)
        self._instrument.format(old_format)
        return data


class CWMagPhase(MultiParameter):
    """
    Sweep that returns magnitude and phase (for CW mode, with set delay).
    """

    def __init__(self, name, instrument, npts_cw, channel, **kwargs):
        super().__init__(name, names=("", ""), shapes=((), ()), instrument=instrument)
        self._instrument = instrument
        self.set_sweep_cw(npts_cw)
        self._channel = channel
        self.names = ("magnitude", "phase")
        self.labels = (
            "{} magnitude".format(instrument.short_name),
            "{} phase".format(instrument.short_name),
        )
        self.units = ("dB", "rad")
        # self.units = ('dB', 'deg')
        self.setpoint_units = (("# points",), ("# points",))
        self.setpoint_labels = (
            ("{} nbpoints".format(instrument.short_name),),
            ("{} nbpoints".format(instrument.short_name),),
        )
        self.setpoint_names = (
            ("{}_nbpoints".format(instrument.short_name),),
            ("{}_nbpoints".format(instrument.short_name),),
        )

    def set_sweep_cw(self, npts_cw):
        #  needed to update config of the software parameter on sweep change
        # freq setpoints tuple as needs to be hashable for look up
        n_points = tuple(np.linspace(int(1), int(npts_cw), num=npts_cw))
        self.setpoints = ((n_points,), (n_points,))
        self.shapes = ((npts_cw,), (npts_cw,))

    def get_raw(self):
        old_format = self._instrument.format()
        self._instrument.format("Complex")
        data = self._instrument._get_sweep_data_CW(force_polar=True)
        self._instrument.format(old_format)
        real, imag = np.transpose(np.reshape(data, (-1, 2)))
        # return abs(real + 1j*imag), np.angle(real + 1j*imag)
        return 20.0 * np.log10(abs(real + 1j * imag)), np.angle(real + 1j * imag)


class FrequencySweep(ArrayParameter):
    """
    Hardware controlled parameter class for Rohde Schwarz ZNB trace.

    Instrument returns an array of transmission or reflection data depending
    on the active measurement.

    Args:
            name: parameter name
            instrument: instrument the parameter belongs to
            start: starting frequency of sweep
            stop: ending frequency of sweep
            npts: number of points in frequency sweep

    Methods:
              set_sweep(start, stop, npts): sets the shapes and
                      setpoint arrays of the parameter to correspond with the sweep
              get(): executes a sweep and returns magnitude and phase arrays

    """

    def __init__(self, name, instrument, start, stop, npts, channel, **kwargs):
        super().__init__(
            name,
            shape=(npts,),
            instrument=instrument,
            unit="dB",
            label="{} magnitude".format(instrument.short_name),
            setpoint_units=("Hz",),
            setpoint_labels=("{} frequency".format(instrument.short_name),),
            setpoint_names=("{}_frequency".format(instrument.short_name),),
        )
        self.set_sweep(start, stop, npts)
        self._channel = channel

    def set_sweep(self, start, stop, npts):
        #  needed to update config of the software parameter on sweep change
        # freq setpoints tuple as needs to be hashable for look up
        f = tuple(np.linspace(int(start), int(stop), num=npts))
        self.setpoints = (f,)
        self.shape = (npts,)

    def get_raw(self):
        data = self._instrument._get_sweep_data()
        if self._instrument.format() in ["Polar", "Complex", "Smith", "Inverse Smith"]:
            log.warning(
                "QCoDeS Dataset does not currently support Complex "
                "values. Will discard the imaginary part. In order to "
                "acquire phase and amplitude use the "
                "FrequencySweepMagPhase parameter."
            )
        return data


class AnritsuChannel(InstrumentChannel):
    def __init__(
        self,
        parent: "MS46522B",
        name: str,
        channel: int,
        vna_parameter: str = None,
        existing_trace_to_bind_to: Optional[str] = None,
    ) -> None:
        """
        Args:
                parent: Instrument that this channel is bound to.
                name: Name to use for this channel.
                channel: channel on the VNA to use
                : Name of parameter on the vna that this should
                        measure such as S12. If left empty this will fall back to
                        `name`.
                existing_trace_to_bind_to: Name of an existing trace on the VNA.
                        If supplied try to bind to an existing trace with this name
                        rather than creating a new trace.

        """
        n = channel
        n_fixed = n
        self._instrument_channel = channel

        if vna_parameter is None:
            vna_parameter = name
        self._vna_parameter = vna_parameter
        super().__init__(parent, name)

        if existing_trace_to_bind_to is None:
            self._tracename = "Tr{}".format(channel)
        else:
            print("what to do?")

        # self._min_source_power: float
        # do not modify unless you know what you are doing!
        self._min_source_power = -30
        self.max_source_power = 16

        self._VNA_mode = None

        # ----------------------------------------------------- start updating

        self.add_parameter(
            name="VNA_mode",
            label="Mode of VNA measurement (S21/S11)",
            vals=vals.Enum("S21", "S11"),
            unit="NA",
            set_cmd=self._set_mode,
            get_cmd=self._get_mode,
        )

        self.add_parameter(
            name="vna_parameter",  # depreciated in newer mode of operation, kept for backward compatibility -Arpit
            label="VNA parameter",
            get_cmd="CALC{}:PAR:DEF? '{}'".format(
                self._instrument_channel, self._tracename
            ),
            get_parser=self._strip,
            snapshot_value=False,
        )

        self.add_parameter(
            name="power",
            label="Power",
            unit="dBm",
            get_cmd="SOUR{}:POW:PORT1?".format(n_fixed),
            set_cmd="SOUR{}:POW:PORT1 {{:.4f}}".format(n_fixed),
            get_parser=float,
            vals=vals.Numbers(self._min_source_power, self.max_source_power),
        )

        # there is an 'increased bandwidth option' (p. 4 of manual) that does not get taken into account here
        self.add_parameter(
            name="bandwidth",
            label="Bandwidth",
            unit="Hz",
            get_cmd="SENS{}:BWID?".format(n_fixed),
            set_cmd="SENS{}:BWID {{:.4f}}".format(n_fixed),
            get_parser=int,
            vals=vals.Enum(
                10,
                20,
                30,
                50,
                70,
                100,
                200,
                300,
                500,
                700,
                1e3,
                3e3,
                5e3,
                7e3,
                10e3,
                30e3,
                50e3,
                70e3,
                100e3,
                300e3,
                500e3,
            ),
            snapshot_value=False,
        )

        self.add_parameter(
            name="avg",
            label="Averages",
            unit="",
            get_cmd="SENS{}:AVER:COUN?".format(n_fixed),
            set_cmd="SENS{}:AVER:COUN {{:.4f}}".format(n_fixed),
            get_parser=int,
            vals=vals.Ints(1, 5000),
        )

        self.add_parameter(
            name="avg_status",
            label="Averaging status",
            unit="",
            get_cmd="SENS:AVER?",
            set_cmd="SENS:AVER {}",
            get_parser=int,
            vals=vals.Enum("on", "off"),
        )

        self.add_parameter(
            name="start",
            get_cmd="SENS{}:FREQ:START?".format(n_fixed),
            set_cmd=self._set_start,
            get_parser=float,
            vals=vals.Numbers(self._parent._min_freq, self._parent._max_freq - 10),
        )

        self.add_parameter(
            name="stop",
            get_cmd="SENS{}:FREQ:STOP?".format(n_fixed),
            set_cmd=self._set_stop,
            get_parser=float,
            vals=vals.Numbers(self._parent._min_freq + 1, self._parent._max_freq),
        )

        self.add_parameter(
            name="center",
            get_cmd="SENS{}:FREQ:CENT?".format(n_fixed),
            set_cmd=self._set_center,
            get_parser=float,
            vals=vals.Numbers(
                self._parent._min_freq + 0.5, self._parent._max_freq - 10
            ),
        )

        self.add_parameter(
            name="span",
            get_cmd="SENS{}:FREQ:SPAN?".format(n_fixed),
            set_cmd=self._set_span,
            get_parser=float,
            vals=vals.Numbers(1, self._parent._max_freq - self._parent._min_freq),
        )

        self.add_parameter(
            name="npts",
            get_cmd="SENS{}:SWE:POIN?".format(n_fixed),
            set_cmd=self._set_npts,
            get_parser=int,
            vals=vals.Ints(2, 20_001),
        )

        # self.add_parameter(name='status',
        #                    get_cmd='CONF:CHAN{}:MEAS?'.format(n_fixed),
        #                    set_cmd='CONF:CHAN{}:MEAS {{}}'.format(n_fixed),
        #                    get_parser=int)

        self.add_parameter(
            name="format",
            get_cmd=partial(self._get_format, tracename=self._tracename),
            set_cmd=self._set_format,
            val_mapping={
                "dB": "MLOG",
                "Linear Magnitude": "MLIN",
                "Phase": "PHAS",
                "Unwr Phase": "UPH",
                "Polar": "POL",
                "Smith": "SMIT",
                "Inverse Smith": "ISM",
                "SWR": "SWR",
                "Real": "REAL",
                "Imaginary": "IMAG",
                "Delay": "GDEL",
                "Complex": "COMP",
            },
            snapshot_value=False,
        )

        self.add_parameter(
            name="trace_mag_phase",
            start=self.start(),
            stop=self.stop(),
            npts=self.npts(),
            channel=n,
            parameter_class=FrequencySweepMagPhase,
        )

        self.add_parameter(
            name="trace",
            start=self.start(),
            stop=self.stop(),
            npts=self.npts(),
            channel=n,
            parameter_class=FrequencySweep,
        )

        self.add_parameter(
            name="avgcount",
            label="Average counter",
            get_cmd=":SENS{}:AVER:SWE?".format(n_fixed),
            get_parser=int,
        )

        self.add_parameter(
            name="marker1_value",
            label="Marker 1 value",
            unit="dB",
            get_cmd=":CALC:MARK1:Y?",
            get_parser=float,
        )

        self.add_parameter(
            name="marker1_frequency",
            label="Marker 1 Frequency ",
            unit="Hz",
            get_cmd=":CALC:MARK1:X?",
            set_cmd=":CALC:MARK1:X {:.4f}",
            get_parser=float,
            set_parser=float,
            vals=vals.Numbers(100e3, 20e9),
        )

        self.add_function("autoscale_all", call_cmd=":DISP:WIND:Y:AUTO")

        self.add_parameter(
            name="cw_mode",
            label="on/off status of the CW sweep mode",
            get_cmd=":SENSe{}:SWEep:CW?".format(n_fixed),
            set_cmd=":SENSe{}:SWEep:CW ".format(n_fixed) + "{}",
            val_mapping={"on": "1", "off": "0"},
        )

        self.add_parameter(
            name="cw_frequency",
            label="CW frequency",
            unit="Hz",
            get_cmd=":SENSe{}:FREQuency:CW?".format(n_fixed),
            set_cmd=self._set_cw_freq,
            get_parser=float,
            vals=vals.Numbers(self._parent._min_freq, self._parent._max_freq),
        )

        self.add_parameter(
            name="npts_cw",
            label="CW sweep mode number of points",
            get_cmd=":SENSe{}:SWEep:CW:POINt?".format(n_fixed),
            set_cmd=":SENSe{}:SWEep:CW:POINt ".format(n_fixed) + "{}",
            get_parser=int,
        )
        # set_perser = int,
        # vals = vals.Numbers(1, 20001) )

        self.add_parameter(
            name="f_start_CW",
            label="Start frequency for CW mode spectroscopy",
            parameter_class=ManualParameter,
        )

        self.add_parameter(
            name="f_stop_CW",
            label="Stop frequency for CW mode spectroscopy",
            parameter_class=ManualParameter,
        )

        self.add_parameter(
            "freq_axis_CW",
            unit="Hz",
            label="Freq Axis for CW mode spectroscopy",
            parameter_class=GeneratedSetPoints,
            startparam=self.f_start_CW,
            stopparam=self.f_stop_CW,
            numpointsparam=self.npts_cw,
            vals=Arrays(shape=(self.npts_cw.get_latest,)),
            snapshot_value=False,
        )

        self.add_parameter(
            name="trace_CWphase",
            setpoints=(self.freq_axis_CW,),
            parameter_class=CWPhase,
            vals=Arrays(shape=(self.npts_cw.get_latest,)),
        )

        self.add_parameter(
            name="trace_CWMagPhase",  # See if needed Gwen 'setpoints=(self.freq_axis_CW,),'
            npts_cw=self.npts_cw(),
            channel=n,
            parameter_class=CWMagPhase,
        )  # To check if needed to set a vals parameter Gwen 'vals=Arrays(shape=(2,self.npts_cw.get_latest,))'

    def _get_format(self, tracename):
        n = self._instrument_channel
        self.write(f"CALC{n}:PAR:SEL '{tracename}'")
        return self.ask(f"CALC{n}:PAR:FORM?")

    def _set_format(self, val):
        unit_mapping = {
            "MLOG": "dB",
            "MLIN": "",
            "PHAS": "rad",
            "UPH": "rad",
            "POL": "",
            "SMIT": "",
            "ISM": "",
            "SWR": "U",
            "REAL": "U",
            "IMAG": "U",
            "GDEL": "S",
            "COMP": "",
        }
        label_mapping = {
            "MLOG": "Magnitude",
            "MLIN": "Magnitude",
            "PHAS": "Phase",
            "UPH": "Unwrapped phase",
            "POL": "Complex Magnitude",
            "SMIT": "Complex Magnitude",
            "ISM": "Complex Magnitude",
            "SWR": "Standing Wave Ratio",
            "REAL": "Real Magnitude",
            "IMAG": "Imaginary Magnitude",
            "GDEL": "Delay",
            "COMP": "Complex Magnitude",
        }
        channel = self._instrument_channel
        self.write(f"CALC{channel}:PAR:SEL '{self._tracename}'")
        self.write(f"CALC{channel}:PAR:FORM {val}")
        self.trace.unit = unit_mapping[val]
        self.trace.label = "{} {}".format(self.short_name, label_mapping[val])

    def _strip(self, var):
        "Strip newline and quotes from instrument reply"
        return var.rstrip("\n")  # [1:-1]

    def _set_start(self, val):
        channel = self._instrument_channel
        self.write("SENS{}:FREQ:START {:.7f}".format(channel, val))
        stop = self.stop()
        if val >= stop and self.cw_mode() == "off":
            raise ValueError("Stop frequency must be larger than start frequency.")
        # we get start as the vna may not be able to set it to the exact value provided
        start = self.start()
        if val != start:
            log.warning("Could not set start to {} setting it to {}".format(val, start))
        self.update_traces()

    def _set_stop(self, val):
        channel = self._instrument_channel
        start = self.start()
        if val <= start and self.cw_mode() == "off":
            raise ValueError("Stop frequency must be larger than start frequency.")
        self.write("SENS{}:FREQ:STOP {:.7f}".format(channel, val))
        # we get stop as the vna may not be able to set it to the exact value provided
        stop = self.stop()
        if val != stop:
            log.warning("Could not set stop to {} setting it to {}".format(val, stop))
        self.update_traces()

    def _set_npts(self, val):
        channel = self._instrument_channel
        self.write("SENS{}:SWE:POIN {:.7f}".format(channel, val))
        self.update_traces()

    def _set_span(self, val):
        channel = self._instrument_channel
        self.write("SENS{}:FREQ:SPAN {:.7f}".format(channel, val))
        self.update_traces()

    def _set_center(self, val):
        channel = self._instrument_channel
        self.write("SENS{}:FREQ:CENT {:.7f}".format(channel, val))
        self.update_traces()

    def _set_cw_freq(self, val):
        channel = self._instrument_channel
        self.write("SENS{}:FREQ:CW {:.7f}".format(channel, val))

        cwfreq = self.cw_frequency()
        if val != cwfreq:
            log.warning(
                "Could not set cw frequency to {} setting it to {}".format(val, cwfreq)
            )

    def _set_mode(self, mode):
        self._VNA_mode = mode

        self.write(":CALCulate1:PARameter1:DEFine " + mode)

    def _get_mode(self):
        return self._VNA_mode

    def update_traces(self):
        """updates start, stop and npts of all trace parameters"""
        start = self.start()
        stop = self.stop()
        npts = self.npts()
        for _, parameter in self.parameters.items():
            if isinstance(parameter, (ArrayParameter, MultiParameter)):
                try:
                    parameter.set_sweep(start, stop, npts)
                except AttributeError:
                    pass

    def _get_sweep_data(self, force_polar=False):
        instrument_parameter = self.vna_parameter()
        root_instr = self.root_instrument
        # if instrument_parameter != self._vna_parameter:
        # 	raise RuntimeError("Invalid parameter. Tried to measure "
        # 					   "{} got {}".format(self._vna_parameter,
        # 										  instrument_parameter))
        self.write("SENS{}:AVER:STAT ON".format(self._instrument_channel))
        self.write("SENS{}:AVER:CLEAR".format(self._instrument_channel))
        # print('Success status 1')
        #
        #     # preserve original state of the znb
        # initial_state = self.status()
        # self.status(1)
        # self._parent.cont_meas_off()
        self._parent.cont_meas_on()
        # print('Success status 2')
        try:
            # if force polar is set, the SDAT data format will be used. Here
            # the data will be transferred as a complex number independent of
            # the set format in the instrument.
            if force_polar:
                data_format_command = "SDAT"
            else:
                data_format_command = "FDAT"
            # instrument averages over its last 'avg' number of sweeps
            # need to ensure averaged result is returned
            # print('Success status 3')
            # for avgcount in range(self.avg()):
            #     print('What am I doing?')
            #     print('self.avg()', avgcount, self.avg())
            #     self.write('INIT{}:IMM; *WAI'.format(self._instrument_channel))

            # while self.avgcount()<self.avg():
            #     time.sleep(0.1)
            #     print(self.avgcount())

            # print('Do I reach here?')
            self._parent.write(
                f"CALC{self._instrument_channel}:PAR:SEL '{self._tracename}'"
            )
            # print('Any error here? No')

            # Fix for array shape mismatch issue fixed by QTLab run - Arpit
            self._parent.write("form:Data real")

            # time.sleep(1)

            # print('Creating sweeps. Waiting till the averaging are done!')
            while self.avgcount() < self.avg():
                time.sleep(0.1)
                # print(self.avgcount())

            # data = root_instr.visa_handle.query_binary_values('CALC:DATA:FDAT?',
            #                                                   datatype='f',#f=float
            #                                                   is_big_endian=False)#output of active trace
            # self.write('form:Data real')
            # data = root_instr.visa_handle.query_binary_values('calculate:Data:Fdata?',
            #             datatype='d', is_big_endian=False, container=np.array)

            data = root_instr.visa_handle.query_binary_values(
                "CALC{}:DATA:{}?".format(self._instrument_channel, data_format_command),
                datatype="d",
                is_big_endian=False,
                container=np.array,
            )

            # data_str = self.ask(
            #     'CALC{}:DATA:{}?'.format(self._instrument_channel,
            #                              data_format_command))
            # print(data)
            # data = np.array(data_str.rstrip().split(',')).astype('float64')
            # data = np.array(data_str).astype('float64')
            # data = np.array(data_str.rstrip().split('\\n')).astype('float64')

            # print('Any error here?2 ')
            if self.format() in ["Polar", "Complex", "Smith", "Inverse Smith"]:
                print("Finally I am here")
                # real, imag = np.transpose(np.reshape(data, (-1, 2)))
                # print ('angle',np.angle(real + 1j*imag))
                # data = data[0::2] + 1j * data[1::2]
                # data = real + 1j * imag
                # print('magphase',data)
        finally:
            self._parent.cont_meas_on()
            # self.status(initial_state)
        return data

    def _get_sweep_data_CW(
        self, force_polar=False
    ):  # Modified by Gwen to fit channel choice in the Qcodes script and being able to record complex S param in CW mode (as for a usual frequency sweep)
        instrument_parameter = self.vna_parameter()
        root_instr = self.root_instrument
        # if instrument_parameter != self._vna_parameter:
        # 	raise RuntimeError("Invalid parameter. Tried to measure "
        # 					   "{} got {}".format(self._vna_parameter,
        # 										  instrument_parameter))
        self.write("SENS{}:AVER:STAT ON".format(self._instrument_channel))
        self.write("SENS{}:AVER:CLEAR".format(self._instrument_channel))

        try:
            # if force polar is set, the SDAT data format will be used. Here
            # the data will be transferred as a complex number independent of
            # the set format in the instrument.
            if force_polar:
                data_format_command = "SDAT"
            else:
                data_format_command = "FDAT"
            # instrument averages over its last 'avg' number of sweeps
            # need to ensure averaged result is returned
            # print('Success status 3')
            # for avgcount in range(self.avg()):
            #     print('What am I doing?')
            #     print('self.avg()', avgcount, self.avg())
            #     self.write('INIT{}:IMM; *WAI'.format(self._instrument_channel))

            # while self.avgcount()<self.avg():
            #     time.sleep(0.1)
            #     print(self.avgcount())

            # print('Do I reach here?')
            self._parent.write(
                f"CALC{self._instrument_channel}:PAR:SEL '{self._tracename}'"
            )
            # print('Any error here? No')

            # Fix for array shape mismatch issue fixed by QTLab run - Arpit
            self._parent.write("form:Data real")

            data = root_instr.visa_handle.query_binary_values(
                "CALC{}:DATA:{}?".format(self._instrument_channel, data_format_command),
                datatype="d",
                is_big_endian=False,
                container=np.array,
            )

        finally:
            pass

        return data


class MS46522B(VisaInstrument):
    """
    qcodes driver for the Rohde & Schwarz ZNB8 and ZNB20
    virtual network analyser. It can probably be extended to ZNB4 and 40
    without too much work.

    Requires FrequencySweep parameter for taking a trace

    Args:
            name: instrument name
            address: Address of instrument probably in format
                    'TCPIP0::192.168.15.100::inst0::INSTR'
            init_s_params: Automatically setup channels for all S parameters on the
                    VNA.
            reset_channels: If True any channels defined on the VNA at the time
                    of initialization are reset and removed.
            **kwargs: passed to base class

    TODO:
    - check initialisation settings and test functions
    """

    CHANNEL_CLASS = AnritsuChannel

    def __init__(
        self,
        name: str,
        address: str,
        init_s_params: bool = True,
        reset_channels: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, address=address, terminator="\n", **kwargs)

        # TODO(JHN) I could not find a way to get max and min freq from
        # the API, if that is possible replace below with that
        # See page 1025 in the manual. 7.3.15.10 for details of max/min freq
        # no attempt to support ZNB40, not clear without one how the format
        # is due to variants
        # fullmodel = self.get_idn()['model']
        # if fullmodel is not None:
        #     model = fullmodel.split('-')[0]
        # else:
        #     raise RuntimeError("Could not determine ZNB model")
        # # format seems to be ZNB8-4Port
        # mFrequency = {'MS46522B-010':(50e3, 8.5e9), 'MS46522B-020':(50e3, 20e9), 'MS46522B-040':(50e3, 43.5e9), 'MS46522B-082':(55e9, 92e9)}
        # if model not in mFrequency.keys():
        #     raise RuntimeError("Unsupported Anritsu model {}".format(model))
        self._min_freq: float
        self._max_freq: float
        # self._min_freq, self._max_freq = mFrequency[model]
        self._min_freq, self._max_freq = 50e3, 20e9

        self.add_parameter(name="num_ports", get_cmd=":SYST:PORT:COUN?", get_parser=int)
        num_ports = self.num_ports()

        self.add_parameter(
            name="rf_power",
            get_cmd=":SYST:HOLD:RF?",
            set_cmd=":SYST:HOLD:RF {}",
            val_mapping={True: "1", False: "0"},
        )

        self.add_parameter(
            name="trigger_source",
            label="Source for triggering",
            get_cmd=":TRIG:SOUR?",
            set_cmd=":TRIG:SOUR {}",
            val_mapping={"internal": "INT", "external": "EXT"},
        )

        self.add_parameter(
            name="external_trigger_type",
            label="Type of external trigger",
            get_cmd=":TRIGger:EXTernal:TYPe?",
            set_cmd=":TRIGger:EXTernal:TYPe {}",
            val_mapping={"all": "ALL", "point": "POIN"},
        )

        self.add_function("reset", call_cmd="*RST")
        # self.add_function('tooltip_on', call_cmd='SYST:ERR:DISP ON')
        # self.add_function('tooltip_off', call_cmd='SYST:ERR:DISP OFF')
        self.add_function("cont_meas_on", call_cmd="SENS:HOLD:FUNC CONT")
        self.add_function("cont_meas_off", call_cmd="SENS:HOLD:FUNC HOLD")
        self.add_function("single_sweep", call_cmd="SENS:HOLD:FUNC SING")
        # self.add_function('update_display_once', call_cmd='SYST:DISP:UPD ONCE')
        # self.add_function('update_display_on', call_cmd='SYST:DISP:UPD ON')
        # self.add_function('update_display_off', call_cmd='SYST:DISP:UPD OFF')
        # self.add_function('display_sij_split', call_cmd='DISP:LAY GRID;:DISP:LAY:GRID {},{}'.format(
        #     num_ports, num_ports))
        self.add_function("display_single_window", call_cmd="DISP:WIND:SPLIT R2C1")
        self.add_function("display_dual_window", call_cmd="DISPlay:COUNt 2")
        self.add_function("rf_off", call_cmd=":SYST:HOLD:RF OFF")
        self.add_function("rf_on", call_cmd=":SYST:HOLD:RF ON")
        if reset_channels:
            self.reset()
            # self.clear_channels()
        channels = ChannelList(
            self, "VNAChannels", self.CHANNEL_CLASS, snapshotable=True
        )
        self.add_submodule("channels", channels)
        if init_s_params:
            for i in range(1, num_ports + 1):
                for j in range(1, num_ports + 1):
                    ch_name = "S" + str(i) + str(j)
                    self.add_channel(ch_name)
            self.channels.lock()
            # self.display_sij_split()
            self.channels.autoscale_all()

        # self.update_display_on()
        if reset_channels:
            self.rf_off()
        self.connect_message()

    def add_channel(self, channel_name: str, **kwargs: Any) -> None:
        i_channel = len(self.channels) + 1
        self.write("DISPlay:COUNt {}".format(i_channel))
        channel = self.CHANNEL_CLASS(self, channel_name, i_channel, **kwargs)
        self.channels.append(channel)

        # shortcut
        setattr(self, channel_name, channel)
        # initialising channel
        self.write("SENS{}:SWE:TYP LIN".format(i_channel))  # done
        self.write("TRIG: IMM")
        self.write("SENS{}:AVER:TYPe SWEepbysweep".format(i_channel))
        self.write("SENS{}:AVER:STAT ON".format(i_channel))

    def clear_channels(self):
        """
        Remove all channels from the instrument and channel list and
        unlock the channel list.
        """
        # self.write('CALCulate:PARameter:DELete:ALL')
        print("work on how to clear these")
        for submodule in self.submodules.values():
            if isinstance(submodule, ChannelList):
                submodule._channels = []
                submodule._channel_mapping = {}
                submodule._locked = False

    def manual_mode(self):
        self.write(":DISPlay:COUNt 1")
        self.channels.S21.write(":DISPlay:WINDow1:SPLit R1C1")
