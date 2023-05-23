from typing import Any
import qcodes.validators as vals
from qcodes.instrument import VisaInstrument, Instrument
from qcodes.parameters import create_on_off_val_mapping

class Anapico(VisaInstrument):
    """
    This is the QCoDeS driver for the Anapico four channels signal generator APUASYN20-4. Not all the functions are implemented yet.

    This driver is derived from the one of the Rohde and Schwarz SGS100A one.

    """
    def __init__(self, name: str, address: str, active_channels=[1,2,3,4], **kwargs: Any) -> None:
        super().__init__(name, address, terminator='\n', **kwargs)

        self.active_channels = active_channels

        ### Trigger settings ###

        # Continuously rearms the trigger system after completion of a triggered sweep.
        self.add_parameter(name='trigger_mode',
                           label='Trigger_mode',
                           get_cmd="INIT:CONT?",
                           set_cmd='INIT:CONT {}',
                           val_mapping=create_on_off_val_mapping(on_val='1',
                                                                 off_val='0'))

        # Choosing the trigger type which control the waveform's transmission.
        self.add_parameter(name='trigger_type',
                           label='Trigger_type',
                           get_cmd="TRIGger:SEQuence:TYPE?",
                           set_cmd='TRIGger:SEQuence:TYPE {}',
                           vals=vals.Enum('NORM', 'GATE', 'POINT'))
        # NORM  : Upon triggering, the waveform sequence plays according the settlings defined by :INITiate:CONTinuous.
        # GATE  : An external trigger signal repeadly starts and stops the waveform's playback.
        # POINT : Upon triggering, only a single point of the sweep (list) is played.

        # Set the trigger source
        self.add_parameter(name='trigger_source',
                           label='Trigger_source',
                           get_cmd="TRIGger:SEQuence:SOURce?",
                           set_cmd='TRIGger:SEQuence:SOURce {}',
                           vals=vals.Enum('IMM', 'KEY','EXT','BUS'))
        # IMM : No waiting for a trigger event occurs.
        # KEY : This choice enables manual triggering by pressing the front-panel RF on/off.
        # EXT : Enables the triggering of a sweep event by an externally applied signal.
        # BUS : Enables triggering over the remote control interface using the *TRG or GET commands.

        # Sets the amount of time to delay between the APSIN response to an external trigger.
        self.add_parameter(name='trigger_delay',
                           label='Trigger_delay',
                           get_cmd="TRIGger:SEQuence:DELay?",
                           set_cmd='TRIGger:SEQuence:DELay {}',
                           unit='s',
                           vals=vals.Numbers(0, 20))

        # Sets the polarity for an external trigger signal while using the continuous, single triggering mode.
        self.add_parameter(name='trigger_slope',
                           label='Trigger_slope',
                           get_cmd="TRIGger:SEQuence:SLOPe?",
                           set_cmd='TRIGger:SEQuence:SLOPe {}',
                           vals=vals.Enum('POS','NEG','NP','PN'))
        # POSitive|NEGative : Trigger system reacts to the rising (positive) or falling (negative) edge of the external trigger signal.
        # NP|PN : Trigger system reacts to both rising and falling edges of the trigger signal. NP selects falling first, PN rising first.

        # Sets a modulus counter on consecutive trigger events. Setting the value to N means that only every Nth trigger event will be considered.
        self.add_parameter(name='trigger_ecount',
                           label='Trigger_ecount',
                           get_cmd="TRIGger:SEQuence:ECOunt?",
                           set_cmd='TRIGger:SEQuence:ECOunt {}',
                           vals=vals.Numbers(1, 255))

        # Sets the trigger output signal polarity.
        self.add_parameter(name='trigger_output_polarity',
                           label='Trigger_output_polarity',
                           get_cmd="TRIGger:OUTPut:POLarity?",
                           set_cmd='TRIGger:OUTPut:POLarity {}',
                           vals=vals.Enum('NORM','INV'))
        # NORM : The idle state of the trigger output signal is low. A high pulse or high signal is played upon trigger events or when the RF output signal is valid.
        # INV  : The idle state of the trigger output signal is high. A low pulse or low signal is played upon trigger events or when the RF output signal is valid.

        # Sets the trigger output signal mode.
        self.add_parameter(name='trigger_output_mode',
                           label='Trigger_output_mode',
                           get_cmd="TRIGger:OUTPut:MODE?",
                           set_cmd='TRIGger:OUTPut:MODE {}',
                           vals=vals.Enum('NORM','GATE','POIN','VAL'))
        # NORM : The trigger output signal is pulsed once whenever playing a waveform sequence is triggered.
        # GATE : The trigger output signal is set when playing a waveform sequence is triggered, and reset when playing stops.
        # POIN : The trigger output signal is pulsed for each point of the sweep (list) playing.
        # VAL  : The trigger output is set while the RF output signal at one or multiple channels is valid (settled).

        # Selects the source channel for the trigger output and the RF output valid signal.
        self.add_parameter(name='trigger_output_valid_source',
                           label='Trigger_output_mode',
                           get_cmd="TRIGger:OUTPut:VALid:SOURce?",
                           set_cmd='TRIGger:OUTPut:VALid:SOURce {}',
                           vals=vals.Enum('ALL','1','2','3', '4'))
        # ALL :  The trigger output is set while RF output of all currently enabled channels is valid (settled) and reset while
        # any of the outputs has no valid RF signal (transient).

        # <integer> : The trigger output is set while RF output of the selected channel is valid (settled) or while the selected
        # channels trigger output signal is set.

        # Triggers the device if LAN ("BUS") is the selected trigger source, otherwise, *TRG is ignored.
        self.add_parameter(name='self_trigger',
                           label='Self_trigger',
                           set_cmd='*TRG',)

        for channel in self.active_channels:

            ### Frequency settings ###

            # Sets the frequency mode of the sigal generator.
            self.add_parameter(name='freq_mode_' + str(channel),
                               label='Freq_mode_' + str(channel),
                               get_cmd='SOUR' + str(channel) + ':FREQ:MODE?',
                               set_cmd='SOUR' + str(channel) + ':FREQ:MODE {}',
                               vals=vals.Enum('FIX', 'SWE', 'CHIR'))
            # FIX : Selects fixed frequency operation and stops an active frequency sweep or chirp. (equivalent to CW mode)
            # SWE : Selects the swept frequency mode.
            # CHIR : Selects the chirps mode.

            # Sets the signal generator output frequency for the CW frequency mode.
            self.add_parameter(name='frequency_'+str(channel),
                               label='Frequency_'+str(channel),
                               unit='Hz',
                               get_cmd='SOUR'+str(channel)+':FREQ:CW?',
                               set_cmd='SOUR'+str(channel)+':FREQ:CW {}',
                               get_parser=float,
                               vals=vals.Numbers(1e6, 20e9))

            # Sets the sweep center frequency.
            self.add_parameter(name='center_frequency_' + str(channel),
                               label='Center_frequency_' + str(channel),
                               unit='Hz',
                               get_cmd='SOUR' + str(channel) + ':FREQ:CENT?',
                               set_cmd='SOUR' + str(channel) + ':FREQ:CENT {}',
                               vals=vals.Numbers(1e6, 20e9))

            # Sets the frequency span.
            self.add_parameter(name='span_frequency_' + str(channel),
                               label='Span_frequency_' + str(channel),
                               unit='Hz',
                               get_cmd='SOUR' + str(channel) + ':FREQ:SPAN?',
                               set_cmd='SOUR' + str(channel) + ':FREQ:SPAN {}',
                               vals=vals.Numbers(1e6, 20e9))

            # Sets the first frequency point in a chirp or step sweep.
            self.add_parameter(name='start_frequency_' + str(channel),
                               label='Start_frequency_' + str(channel),
                               unit='Hz',
                               get_cmd='SOUR' + str(channel) + ':FREQ:STAR?',
                               set_cmd='SOUR' + str(channel) + ':FREQ:STAR {}',
                               vals=vals.Numbers(1e6, 20e9))

            # Sets the last frequency point in a chirp or step mode.
            self.add_parameter(name='stop_frequency_' + str(channel),
                               label='Stop_frequency_' + str(channel),
                               unit='Hz',
                               get_cmd='SOUR' + str(channel) + ':FREQ:STOP?',
                               set_cmd='SOUR' + str(channel) + ':FREQ:STOP {}',
                               vals=vals.Numbers(1e6, 20e9))

            # Sets the frequency step size for sweeps and chirps.
            self.add_parameter(name='step_frequency_' + str(channel),
                               label='Step_frequency_' + str(channel),
                               unit='Hz',
                               get_cmd='SOUR' + str(channel) + ':FREQ:STEP?',
                               set_cmd='SOUR' + str(channel) + ':FREQ:STEP {}',
                               vals=vals.Numbers(1e3, 20e9))

            # ON causes frequency changes in CW mode to become effective only after receiving a trigger signal
            self.add_parameter(name='freq_trigger_' + str(channel),
                               label='Freq_trigger_' + str(channel),
                               get_cmd='SOUR' + str(channel) + ':FREQ:TRIG?',
                               set_cmd='SOUR' + str(channel) + ':FREQ:TRIG {}',
                               val_mapping=create_on_off_val_mapping(on_val='1',
                                                                     off_val='0'))

            ### Phase settings ###

            # Adjusts the phase of the signal.
            self.add_parameter(name='phase_'+str(channel),
                               label='Phase_'+str(channel),
                               unit='rad',
                               get_cmd='SOUR'+str(channel)+':PHAS:ADJ?',
                               set_cmd='SOUR'+str(channel)+':PHAS:ADJ {}',
                               get_parser=float,
                               vals=vals.Numbers(0, 360))

            ### ON/OFF settings ###

            # Turns RF output power on/off
            self.add_parameter(name='status_'+str(channel),
                               label='RF Output_'+str(channel),
                               get_cmd='OUTP'+str(channel)+'?',
                               set_cmd='OUTP'+str(channel)+' {}',
                               val_mapping=create_on_off_val_mapping(on_val='1',
                                                                     off_val='0'))
            ### Power settings ###

            # Sets the signal generator power to fixed or swept.
            self.add_parameter(name='power_mode_' + str(channel),
                               label='Power_mode_' + str(channel),
                               get_cmd='SOUR' + str(channel) + ':POWer:MODE?',
                               set_cmd='SOUR' + str(channel) + ':POWer:MODE {}',
                               vals=vals.Enum('FIX', 'SWE'))
            # FIX : Selects fixed power operation and stops an active power sweep.
            # SWE : Selects the swept mode

            # Sets the RF output power.
            self.add_parameter(name='power_'+str(channel),
                               label='Power_'+str(channel),
                               unit='dBm',
                               get_cmd='SOUR'+str(channel)+':POW:LEV:IMM:AMPL?',
                               set_cmd='SOUR'+str(channel)+':POW:LEV:IMM:AMPL {}',
                               get_parser=float,
                               vals=vals.Numbers(-120, 25))

            # Sets the swep center amplitude.
            self.add_parameter(name='center_power_' + str(channel),
                               label='Center_power_' + str(channel),
                               unit='dBm',
                               get_cmd='SOUR' + str(channel) + ':POW:CENT?',
                               set_cmd='SOUR' + str(channel) + ':POW:CENT {}',
                               get_parser=float,
                               vals=vals.Numbers(-120, 25))

            # Sets the amplitude sweep span.
            self.add_parameter(name='span_power_' + str(channel),
                               label='Span_power_' + str(channel),
                               unit='dBm',
                               get_cmd='SOUR' + str(channel) + ':POWer:SPAN?',
                               set_cmd='SOUR' + str(channel) + ':POWer:SPAN {}',
                               vals=vals.Numbers(-120, 25))

            # Sets the first amplitude point in a sweep.
            self.add_parameter(name='start_power_' + str(channel),
                               label='Start_power_' + str(channel),
                               unit='dBm',
                               get_cmd='SOUR' + str(channel) + ':POWer:STAR?',
                               set_cmd='SOUR' + str(channel) + ':POWer:STAR {}',
                               vals=vals.Numbers(-120, 25))

            # Sets the last amplitude point in a sweep.
            self.add_parameter(name='stop_power_' + str(channel),
                               label='Stop_power_' + str(channel),
                               unit='dBm',
                               get_cmd='SOUR' + str(channel) + ':POWer:STOP?',
                               set_cmd='SOUR' + str(channel) + ':POWer:STOP {}',
                               vals=vals.Numbers(-120, 25))

            # Sets the amplitude size for a sweep.
            self.add_parameter(name='step_power_' + str(channel),
                               label='Step_power_' + str(channel),
                               unit='dBm',
                               get_cmd='SOUR' + str(channel) + ':POWer:STEP:LINear?',
                               set_cmd='SOUR' + str(channel) + ':POWer:STEP:LINear {}',
                               vals=vals.Numbers(-120, 25))

class Anapico_Single_channel(Instrument):
    """
    This class create a subinstrument from the Anapico class above. The goal is to be able to use any channel
    independently of the others as if they were independent RF sources.

    """
    def __init__(self, name: str, main_instrument, channel=int, **kwargs: Any) -> None:
        super().__init__(name, **kwargs)

        ### ON/OFF settings ###

        self.add_parameter(name='status',
                           label='RF Output',
                           get_cmd='',
                           set_cmd='',
                           val_mapping=create_on_off_val_mapping(on_val='1',
                                                                 off_val='0'))
        # self.add_parameter(name='mode',
        #                    label='Mode',
        #                    get_cmd='',
        #                    set_cmd='')

        ### Frequency settings ###

        self.add_parameter(name='freq_mode',
                          label='Freq_mode',
                          get_cmd='',
                          set_cmd='',
                          vals=vals.Enum('FIX','SWE','CHIR'))
        self.add_parameter(name='frequency',
                          label='Frequency',
                          unit='Hz',
                          get_cmd='',
                          set_cmd='',
                          get_parser=float,
                          vals=vals.Numbers(1e6, 20e9))
        self.add_parameter(name='center_frequency',
                           label='Center_frequency',
                           unit='Hz',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(1e6, 20e9))
        self.add_parameter(name='span_frequency',
                           label='Span_frequency',
                           unit='Hz',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(1e6, 20e9))
        self.add_parameter(name='start_frequency',
                           label='Start_frequency',
                           unit='Hz',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(1e6, 20e9))
        self.add_parameter(name='stop_frequency',
                           label='Stop_frequency',
                           unit='Hz',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(1e6, 20e9))
        self.add_parameter(name='step_frequency',
                           label='Step_frequency',
                           unit='Hz',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(1e3, 20e9))
        self.add_parameter(name='freq_trigger',
                           label='Freq_trigger',
                           get_cmd='',
                           set_cmd='',
                           val_mapping=create_on_off_val_mapping(on_val='1',
                                                                 off_val='0'))

        ### Phase settings ###

        self.add_parameter(name='phase',
                           label='Phase',
                           unit='rad',
                           get_cmd='',
                           set_cmd='',
                           get_parser=float,
                           vals=vals.Numbers(0, 360))

        ### Power settings ###

        self.add_parameter(name='power_mode',
                           label='Power_mode',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Enum('FIX','SWE'))
        self.add_parameter(name='power',
                           label='Power',
                           unit='dBm',
                           get_cmd='',
                           set_cmd='',
                           get_parser=float,
                           vals=vals.Numbers(-120, 25))
        self.add_parameter(name='center_power',
                           label='Center_power',
                           unit='dBm',
                           get_cmd='',
                           set_cmd='',
                           get_parser=float,
                           vals=vals.Numbers(-120,25))
        self.add_parameter(name='span_power',
                           label='Span_power',
                           unit='dBm',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(-120,25))
        self.add_parameter(name='start_power',
                           label='Start_power',
                           unit='dBm',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(-120,25))
        self.add_parameter(name='stop_power',
                           label='Stop_power',
                           unit='dBm',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(-120,25))
        self.add_parameter(name='step_power',
                           label='Step_power',
                           unit='dBm',
                           get_cmd='',
                           set_cmd='',
                           vals=vals.Numbers(-120,25))


        # Overwrites the Qcodes parameters with the ones of the main_instrument
        for parameter_name in self.parameters.keys():
            if parameter_name=='IDN':
                self.parameters[parameter_name] = main_instrument.parameters[parameter_name]
            else:
                self.parameters[parameter_name] = main_instrument.parameters[parameter_name+'_'+str(channel)]