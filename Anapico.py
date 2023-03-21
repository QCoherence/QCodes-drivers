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

        for channel in self.active_channels:

            self.add_parameter(name='frequency_'+str(channel),
                               label='Frequency_'+str(channel),
                               unit='Hz',
                               get_cmd='SOUR'+str(channel)+':FREQ:CW?',
                               set_cmd='SOUR'+str(channel)+':FREQ:CW {}',
                               get_parser=float,
                               vals=vals.Numbers(1e6, 20e9))
            self.add_parameter(name='phase_'+str(channel),
                               label='Phase_'+str(channel),
                               unit='rad',
                               get_cmd='SOUR'+str(channel)+':PHAS:ADJ?',
                               set_cmd='SOUR'+str(channel)+':PHAS:ADJ {}',
                               get_parser=float,
                               vals=vals.Numbers(0, 360))
            self.add_parameter(name='power_'+str(channel),
                               label='Power_'+str(channel),
                               unit='dBm',
                               get_cmd='SOUR'+str(channel)+':POW:LEV:IMM:AMPL?',
                               set_cmd='SOUR'+str(channel)+':POW:LEV:IMM:AMPL -{}',
                               get_parser=float,
                               vals=vals.Numbers(-120, 25))
            self.add_parameter(name='status_'+str(channel),
                               label='RF Output_'+str(channel),
                               get_cmd='OUTP'+str(channel)+'?',
                               set_cmd='OUTP'+str(channel)+' {}',
                               val_mapping=create_on_off_val_mapping(on_val='1',
                                                                     off_val='0'))
            self.add_parameter(name='mode_'+str(channel),
                               label='Mode_'+str(channel),
                               get_cmd='SOUR'+str(channel)+':FREQ:MODE?',
                               set_cmd='SOUR'+str(channel)+':FREQ:MODE {}')
            self.add_parameter(name='center_frequency_'+str(channel),
                               label='Center_frequency_'+str(channel),
                               unit='Hz',
                               get_cmd='SOUR'+str(channel)+':FREQ:CENT?',
                               set_cmd='SOUR'+str(channel)+':FREQ:CENT {}',
                               vals=vals.Numbers(1e6, 20e9))
            self.add_parameter(name='span_frequency_'+str(channel),
                               label='Span_frequency_'+str(channel),
                               unit='Hz',
                               get_cmd='SOUR'+str(channel)+':FREQ:SPAN?',
                               set_cmd='SOUR'+str(channel)+':FREQ:SPAN {}',
                               vals=vals.Numbers(1e6, 20e9))
            self.add_parameter(name='start_frequency_'+str(channel),
                               label='Start_frequency_'+str(channel),
                               unit='Hz',
                               get_cmd='SOUR'+str(channel)+':FREQ:STAR?',
                               set_cmd='SOUR'+str(channel)+':FREQ:STAR {}',
                               vals=vals.Numbers(1e6, 20e9))
            self.add_parameter(name='stop_frequency_'+str(channel),
                               label='Stop_frequency_'+str(channel),
                               unit='Hz',
                               get_cmd='SOUR'+str(channel)+':FREQ:STOP?',
                               set_cmd='SOUR'+str(channel)+':FREQ:STOP {}',
                               vals=vals.Numbers(1e6, 20e9))
            self.add_parameter(name='step_frequency_'+str(channel),
                               label='Step_frequency_'+str(channel),
                               unit='Hz',
                               get_cmd='SOUR'+str(channel)+':FREQ:STEP?',
                               set_cmd='SOUR'+str(channel)+':FREQ:STEP {}',
                               vals=vals.Numbers(1e6, 20e9))

class Anapico_Single_channel(Instrument):
    """
    This class create a subinstrument from the Anapico class above. The goal is to be able to use any channel
    independently of the others as if they were independent RF sources.

    """
    def __init__(self, name: str, main_instrument, channel=int, **kwargs: Any) -> None:
        super().__init__(name, **kwargs)

        # Create all the desired Qcodes parameters
        self.add_parameter(name='frequency',
                          label='Frequency',
                          unit='Hz',
                          get_cmd='',
                          set_cmd='',
                          get_parser=float,
                          vals=vals.Numbers(1e6, 20e9))
        self.add_parameter(name='phase',
                           label='Phase',
                           unit='rad',
                           get_cmd='',
                           set_cmd='',
                           get_parser=float,
                           vals=vals.Numbers(0, 360))
        self.add_parameter(name='power',
                           label='Power',
                           unit='dBm',
                           get_cmd='',
                           set_cmd='',
                           get_parser=float,
                           vals=vals.Numbers(-120, 25))
        self.add_parameter(name='status',
                           label='RF Output',
                           get_cmd='',
                           set_cmd='',
                           val_mapping=create_on_off_val_mapping(on_val='1',
                                                                 off_val='0'))
        self.add_parameter(name='mode',
                           label='Mode',
                           get_cmd='',
                           set_cmd='')
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
                           vals=vals.Numbers(1e6, 20e9))

        # Overwrites the Qcodes parameters with the ones of the main_instrument
        for parameter_name in self.parameters.keys():
            if parameter_name=='IDN':
                self.parameters[parameter_name] = main_instrument.parameters[parameter_name]
            else:
                self.parameters[parameter_name] = main_instrument.parameters[parameter_name+'_'+str(channel)]