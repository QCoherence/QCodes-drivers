from time import sleep

import numpy as np
from qcodes import VisaInstrument
from qcodes import validators as vals
from qcodes.parameters import (
    Parameter,
    ParameterWithSetpoints,
    create_on_off_val_mapping,
)
from qcodes.validators import Arrays


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


class SpectrumTrace(ParameterWithSetpoints):
    def get_raw(self):
        data = self._instrument.get_trace()
        return data


class IQTrace(Parameter):
    def get_raw(self):
        data = self._instrument.get_iqtrace()
        return data


# class HarmonicTrace(ParameterWithSetpoints):
#
#     def get_raw(self):
#         data = self._instrument.get_harmonic()
#         return data


class RS_FSV(VisaInstrument):
    """
    QCoDes driver for the Rohde & Schwarz FSV Signal Analyzer.
    Args:
        name: instrument name
        address: VISA ressource name of instrument in format
            'TCPIP0::192.168.15.100::inst0::INSTR'
        **kwargs: passed to base class
    """

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__

    def __init__(self, name: str, address: str, **kwargs) -> None:
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name=name, address=address, terminator="\n", **kwargs)

        self.add_parameter(
            name="res_BW",
            label="Resolution bandwidth",
            vals=vals.Numbers(1, 40e6),
            unit="Hz",
            set_cmd="SENSe:BANDwidth:RESolution " + "{:.12f}",
            get_cmd="SENSe:BANDwidth:RESolution?",
        )

        self.add_parameter(
            name="video_BW",
            label="Video bandwidth",
            vals=vals.Numbers(1, 40e6),
            unit="Hz",
            set_cmd="SENSe:BANDwidth:VIDeo " + "{:.12f}",
            get_cmd="SENSe:BANDwidth:VIDeo?",
            # snapshot_value = False
        )

        self.add_parameter(
            name="sweep_time",
            label="Sweep time",
            vals=vals.Numbers(1e-6, 16e3),
            unit="s",
            set_cmd="SWEep:TIME " + "{:.12f}" + " s",
            get_cmd="SWEep:TIME?",
            get_parser=float,
        )

        self.add_parameter(
            name="auto_sweep_time_enabled",
            initial_value=True,
            get_cmd="SWE:TIME:AUTO?",
            set_cmd="SWE:TIME:AUTO " + "{}",
            vals=vals.Bool(),
            val_mapping=create_on_off_val_mapping(on_val="ON", off_val="OFF"),
        )

        self.add_parameter(
            name="input_att",
            label="Input attenuation",
            vals=vals.Numbers(0, 79),
            unit="dB",
            set_cmd="INPut:ATTenuation " + "{:.12f}",
            get_cmd="INPut:ATTenuation?",
            # snapshot_value = False
            # set_parser =self.,
            # get_parser=self.
        )

        self.add_parameter(
            name="input_att_auto",
            label="Input attenuation auto",
            vals=vals.Enum("ON", "OFF"),
            unit="NA",
            set_cmd="INPut:ATTenuation:AUTO " + "{:.12f}",
            get_cmd="INPut:ATTenuation:AUTO?",
            set_parser=self.caps,
            get_parser=self.caps_dag,
            snapshot_value=False,
        )

        self.add_parameter(
            name="center_freq",
            label="Center Frequency",
            vals=vals.Numbers(5, 30e9),
            unit="Hz",
            set_cmd="SENSe:FREQuency:CENTer " + "{:.12f}",
            get_cmd="SENSe:FREQuency:CENTer?",
            # set_parser =self.,
            # get_parser=self.
        )

        self.add_parameter(
            name="averages",
            label="Averages",
            vals=vals.Numbers(0, 200000),
            unit="NA",
            set_cmd="SENSe:AVERage:COUNt " + "{:.12f}",
            get_cmd="SENSe:AVERage:COUNt?",
            # set_parser =self.,
            # get_parser=self.
        )

        self.add_parameter(
            name="n_points",
            label="Number of points in trace",
            vals=vals.Numbers(101, 100001),
            unit="",
            set_cmd="SENSe:SWEep:POINts " + "{:.12f}",
            get_cmd="SENSe:SWEep:POINts?",
            get_parser=int,
        )

        self.add_parameter(
            name="span",
            label="Span",
            vals=vals.Numbers(0, 13.6e9),
            unit="Hz",
            set_cmd="SENSe:FREQuency:SPAN " + "{:.12f}",
            get_cmd="SENSe:FREQuency:SPAN?",
            snapshot_value=False,
            # set_parser =self.,
            # get_parser=self.
        )

        self.add_parameter(
            name="average_type",
            label="Average type",
            vals=vals.Enum("vid", "lin", "pow"),
            unit="NA",
            set_cmd=self._set_average_type,
            get_cmd="SENSe:AVERage:TYPE?",
            # set_parser =self.,
            # get_parser=self.
        )

        self.add_parameter(
            name="f_start",
            label="Start frequency",
            vals=vals.Numbers(0, 13.6e9),
            unit="Hz",
            set_cmd="SENSe:FREQuency:STARt " + "{:.12f}",
            get_cmd="SENSe:FREQuency:STARt?",
            # set_parser =self.,
            get_parser=float,
            # snapshot_value = False
        )

        self.add_parameter(
            name="f_stop",
            label="Stop frequency",
            vals=vals.Numbers(10, 13.6e9),
            unit="Hz",
            set_cmd="SENSe:FREQuency:STOP " + "{:.12f}",
            get_cmd="SENSe:FREQuency:STOP?",
            # set_parser =self.,
            get_parser=float,
            # snapshot_value = False
        )

        self.add_parameter(
            name="ref_level",
            label="Reference level(AMPT)",
            vals=vals.Numbers(-130, 10),
            unit="dBm",
            set_cmd=":DISP:TRAC:Y:RLEV  " + "{:e}",
            get_cmd=":DISP:TRAC:Y:RLEV?",
            # set_parser =self.,
            get_parser=float,
        )

        self.add_parameter(
            "freq_axis",
            unit="Hz",
            label="Freq Axis",
            parameter_class=GeneratedSetPoints,
            startparam=self.f_start,
            stopparam=self.f_stop,
            numpointsparam=self.n_points,
            vals=Arrays(shape=(self.n_points.get_latest,)),
            # snapshot_value = False
        )

        self.add_parameter(
            name="time_start",  # Time start for zero span
            label="Time start",
            vals=vals.Numbers(-1, 1),
            unit="s",
            get_cmd=(lambda: 0),
            get_parser=float,
        )

        self.add_parameter(
            "time_axis",
            unit="s",
            label="Time Axis",
            parameter_class=GeneratedSetPoints,
            startparam=self.time_start,
            stopparam=self.sweep_time,
            numpointsparam=self.n_points,
            vals=Arrays(shape=(self.n_points.get_latest,)),
            # snapshot_value = False
        )

        self.add_parameter(
            "trigger_source",
            label="Source of the trigger",
            set_cmd="TRIGger:SOURce {}",
            get_cmd="TRIGger:SOURce?",
            vals=vals.Enum(
                "IMMediate",
                "IMM",
                "EXTern",
                "EXT",
                "IFPower",
                "IFP",
                "RFPower",
                "RFP",
            ),
        )

        self.add_parameter(
            "trigger_level_ext",
            unit="V",
            label="Level of the external trigger",
            set_cmd="TRIGger:LEVel " + "{:.2f}",
            get_cmd="TRIGger:LEVel?",
            vals=vals.Numbers(0.5, 3.5),
        )

        # self.add_parameter( name = 'n_harmonics',
        #                     label = 'No.of harmonic',
        #                     vals = vals.Numbers(1,26),
        #                     # unit   = 'Hz',
        #                     set_cmd='CALC:MARK:FUNC:HARM:NHAR ' + '{:.12f}',
        #                     # set_parser =self.,
        #                     get_parser=float,
        #                     snapshot_value = False
        #                     )
        #
        # self.add_parameter('freq_axis_harmonic',
        #                     unit='Hz',
        #                     label='Freq Axis_harmonic',
        #                     parameter_class=GeneratedSetPoints,
        #                     startparam=self.get_1,
        #                     stopparam=self.n_harmonics,
        #                     numpointsparam=(self.n_harmonics),
        #                     vals=Arrays(shape=(self.n_harmonics.get_latest,)),
        #                     snapshot_value = False)

        self.add_parameter(
            "spectrum",
            unit="dBm",
            setpoints=(self.freq_axis,),
            label="Spectrum",
            parameter_class=SpectrumTrace,
            vals=Arrays(shape=(self.n_points.get_latest,)),
        )

        self.add_parameter(
            "zerospan_spectrum",
            unit="dBm",
            setpoints=(self.time_axis,),
            label="Zero Span Spectrum",
            parameter_class=SpectrumTrace,
            vals=Arrays(shape=(self.n_points.get_latest,)),
        )

        ## IQ Measurements

        self.add_parameter(
            "IQ_mode",
            label="Whether the IQ mode is on or not.",
            unit="",
            set_cmd=self.set_IQ_mode,
            vals=vals.Enum("ON", "OFF"),
        )

        self.add_parameter(
            "iq_sample_rate",
            label="Sample rate for the IQ measurements",
            unit="Hz",
            get_cmd="TRAC:IQ:SRAT?",
            set_cmd="TRAC:IQ:SRAT {:.12f}",
            vals=vals.Numbers(0, 100e6),
            get_parser=float,
        )

        self.add_parameter(
            name="iq_n_points",
            label="Number of points in the IQ trace",
            vals=vals.Numbers(101, 100001),
            unit="",
            set_cmd=self.set_iq_nb_pts,
            get_cmd=self.get_iq_nb_pts,
            get_parser=int,
        )

        self.add_parameter(
            "iq_trace",
            unit="V",
            label="IQ trace",
            parameter_class=IQTrace,
            vals=Arrays(shape=(self.iq_n_points.get_latest, 2)),
        )

        ## APD measurements

        self.add_parameter(
            "apd_mode",
            label="Whether the APD mode is on or not.",
            unit="",
            set_cmd="CALC:STAT:APD {}",
            vals=vals.Enum("ON", "OFF"),
        )

        self.add_parameter(
            "apd_x_range",
            label="Power range for the statistics of the APD",
            unit="dB",
            vals=vals.Numbers(10, 200),
            set_cmd="CALC:STAT:SCAL:X:RANG {:.6f}dB",
            get_cmd="CALC:STAT:SCAL:X:RANG?",
            get_parser=float,
        )

        self.add_parameter(
            name="apd_x_range_start",  # Token parameter
            label="APD x range start",
            vals=vals.Numbers(-200, 200),
            unit="dBm",
            get_cmd=(lambda: self.ref_level() - self.apd_x_range()),
            get_parser=float,
        )

        self.add_parameter(
            name="apd_x_range_npt",  # Token parameter
            label="APD x range number of points",
            vals=vals.Numbers(),
            unit="",
            get_cmd=(lambda: 1001),
            get_parser=int,
        )

        self.add_parameter(
            "apd_axis",
            unit="s",
            label="Amplitude power axis for the APD measurements",
            parameter_class=GeneratedSetPoints,
            startparam=self.apd_x_range_start,
            stopparam=self.ref_level,
            numpointsparam=self.apd_x_range_npt,  # APD is always 1001 pts
            vals=Arrays(shape=(1001,)),
            # snapshot_value = False
        )

        self.add_parameter(
            "apd_trace",
            unit="",
            setpoints=(self.apd_axis,),
            label="APD statistics",
            parameter_class=SpectrumTrace,
            vals=Arrays(shape=(1001,)),
        )

        self.add_parameter(
            name="apd_n_sample",
            label="Number of sample used for the APD trace",
            vals=vals.Numbers(100, 80000000),
            unit="",
            set_cmd="CALC:STAT:NSAM " + "{}",
            get_cmd="CALC:STAT:NSAM?",
            get_parser=int,
        )

        # self.add_parameter( name = 'apd_ref_level',
        #                     label = 'Reference level(AMPT)',
        #                     vals = vals.Numbers(-130,10),
        #                     unit   = 'dBm',
        #                     set_cmd='CALC:STAT:SCAL:X:RLEV  ' + '{:e}',
        #                     get_cmd='CALC:STAT:SCAL:X:RLEV?',
        #                     # set_parser =self.,
        #                     get_parser=float
        #                     )

        #
        # self.add_parameter( name = 'set_harmonic',
        #                     label = 'Harmonic function ON',
        #                     # vals = vals.Numbers(10,50e6),
        #                     vals = vals.Enum('ON','OFF'),
        #                     #unit   = 'Hz',
        #                     set_cmd='CALC:MARK:FUNC:HARM:STAT '+ '{} '
        #                     # get_cmd='BANDwidth:RESolution?'
        #                     # set_parser =self.,
        #                     # get_parser=self.
        #                     )

        # self.add_parameter( name = 'reset_harmonic',
        #                     label = 'Harmonic function OFF',
        #                     # vals = vals.Numbers(10,50e6),
        #                     #unit   = 'Hz',
        #                     set_cmd='CALC:MARK:FUNC:HARM:STAT OFF '
        #                     # get_cmd='BANDwidth:RESolution?'
        #                     # set_parser =self.,
        #                     # get_parser=self.
        #                     )

        # self.add_parameter( name = 'time_harmonic',
        #                     label = 'sweep time harmonic',
        #                     vals = vals.Numbers(10,1000),
        #                     # unit   = 'Hz',
        #                     set_cmd='SWE:TIME ' + '{:.12f}'+ 'us',
        #                     # set_parser =self.,
        #                     # get_parser=float
        #                     )
        # self.add_parameter( 'harmonic',
        #                     unit='dBm/c',
        #                     setpoints=(self.freq_axis_harmonic,),
        #                     label='Spectrum',
        #                     parameter_class=HarmonicTrace,
        #                     vals=Arrays(shape=(self.n_harmonics.get_latest,))
        #                     name = 'meas_harmonic',
        #                     label = 'Meausure harmonics', # values in dBc
        #                     vals = vals.Numbers(10,50e6),
        #                     unit   = 'Hz',
        #                     get_cmd='CALC:MARK:FUNC:HARM:LIST?'
        #                     set_parser =self.,
        #                     get_parser=self.
        #                     )
        #
        # self.add_parameter( name = 'setauto_rbw_harmonic',
        #                     label = 'Resolution bandwidth harmonic',
        #                     vals = vals.Enum('ON','OFF'),
        #                     # unit   = 'Hz',
        #                     set_cmd='CALC:MARK:FUNC:HARM:BAND:AUTO ' +'{}'
        #                     # set_parser =self.,
        #                     # get_parser=float
        #                     )

        # self.add_parameter( name = 'unsetauto_rbw_harmonic',
        #                     label = 'Resolution bandwidth harmonic',
        #                     # unit   = 'Hz',
        #                     set_cmd='CALC:MARK:FUNC:HARM:BAND:AUTO OFF' ,
        #                     # set_parser =self.,
        #                     # get_parser=float
        #                     )

        self.connect_message()

    def set_iq_nb_pts(self, nb):
        self.write(
            "TRAC:IQ:SET NORM, 1 MHz, {bw} , IMM, POS, 0, {nb_pts}".format(
                bw=self.iq_sample_rate(), nb_pts=nb
            )
        )

    def get_iq_nb_pts(self):
        r = self.ask("TRAC:IQ:SET?").split(",")[-1]
        return r

    def set_IQ_mode(self, mode):
        self.write(f"TRAC:IQ {mode}")

    def _set_average_type(self, val: str):
        self.write(f"SENSe:AVERage:TYPE {val}")

    def get_1(self):
        return 1

    #
    # def _set_average_type(self,val : str):
    #     sense_num = self.sense_num
    #     self.write(f"SENSe{sense_num}:AVERage:TYPE {val}")

    def get_trace(self):
        self.write("*CLS")
        self.write("SYST:DISP:UPD ON")
        self.write(":INIT:CONT OFF")
        self.write(":INIT:IMMediate;*OPC")
        while self.ask("*ESR?") == "0":
            sleep(1)  # we wait until the register is 1
        datastr = self.ask(":TRAC? TRACE" + str(1))
        # self.write(':INIT:CONT OFF')
        datalist = datastr.split(",")
        dataflt = []
        for val in datalist:
            dataflt.append(float(val))
        dataflt = np.array(dataflt)
        return dataflt

    def get_iqtrace(self):
        # self.write('TRAC:IQ ON')
        self.write("TRAC:IQ:EVAL ON")
        self.write("TRAC:IQ:AVER OFF")
        self.write("TRAC:IQ:AVER:COUN 1")
        self.write(
            "TRAC:IQ:SET NORM, 1 MHz, {bw} MHz, IMM, POS, 0, {nb_pts}".format(
                bw=self.iq_sample_rate() * 1e-6, nb_pts=int(self.iq_n_points())
            )
        )
        self.write("INIT;*OPC")
        while self.ask("*ESR?") == "0":
            sleep(1)  # we wait until the register is 1
        datastr = self.ask("TRAC:IQ:DATA?")
        # self.write(':INIT:CONT OFF')
        datalist = datastr.split(",")
        dataflt = np.array(datalist, dtype=float).reshape((self.iq_n_points(), 2))
        # self.write('TRAC:IQ OFF')
        return dataflt

    #
    # def get_harmonic(self):
    #     self.write('*CLS')
    #     # self.write(':INIT:CONT OFF')
    #     # self.write(':INIT:IMMediate;*OPC')
    #     datastr=self.ask('CALC:MARK:FUNC:HARM:LIST?')
    #         # sleep(1) # we wait until the register is 1
    #     # datastr = self.ask(':TRAC? TRACE'+str(1))
    #
    #     datalist = datastr.split(",")
    #     dataflt = []
    #     for val in datalist:
    #         dataflt.append(float(val))
    #     dataflt=np.array(dataflt)
    #     return dataflt
    #
    # def sweep_point_check(self, points):
    #     if points<701:
    #         valid_values=np.array([155, 201, 301, 313, 401, 501, 601, 625])
    #         if points in valid_values:
    #             points_checked=points
    #         else:
    #             points_checked=valid_values[(np.abs(valid_values-points)).argmin()]
    #             print('### Warning: Invalid sweep points, set to '+str(points_checked))
    #     else:
    #         if (points-1)%100==0:
    #             points_checked=points
    #         else:
    #             points_checked=round(points/100,0)*100+1
    #             print('### Warning: Invalid sweep points, set to '+str(points_checked))
    #     return int(points_checked)

    def caps(string):
        return string.upper()

    def caps_dag(string):
        return string.lower()

    # def _set_visa_timeout(self, timeout) -> None:

    #     if timeout is None:
    #         self.visa_handle.timeout = None
    #     else:
    #         # pyvisa uses milliseconds but we use seconds
    #         self.visa_handle.timeout = timeout * 1000.0

    # def _get_visa_timeout(self):

    #     timeout_ms = self.visa_handle.timeout
    #     if timeout_ms is None:
    #         return None
    #     else:
    #         # pyvisa uses milliseconds but we use seconds
    #         return timeout_ms / 1000

    # Functions for debugging
    def deb_ask(self, question):
        ret = self.ask(question)
        return ret

    def deb_say(self, direction):
        self.write(direction)
        return 0
