from typing import Union, Tuple, Any
from functools import partial
from math import ceil
from time import sleep

from typing import Any
from functools import partial

from qcodes.instrument import Instrument
from qcodes.instrument import InstrumentChannel, ChannelList
from qcodes.parameters import MultiChannelInstrumentParameter
from qcodes.instrument import VisaInstrument
from qcodes.utils import validators as vals
from qcodes.parameters import create_on_off_val_mapping


class iTestChannel(InstrumentChannel):

    def __init__(self, parent: Instrument, name: str, module: int, ch: int) -> None:
        super().__init__(parent, name)

        self.add_parameter(name='voltage_range',
                           label="The output voltage range in V for the desired channel",
                           unit='V',
                           get_cmd=partial(self._parent._get_channel_voltage_range, module, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_voltage_range, module, ch),
                           vals = vals.Enum(self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['low_range_V_V'], self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['high_range_V_V'])
                           )

        self.add_parameter(name='ramp_mode',
                           label='Turn ON or OFF the ramp mode for the desired channel for BE2141/2142 only',
                           get_cmd=partial(self._parent._get_ramp_mode, module, ch),
                           get_parser = str,
                           set_cmd=partial(self._parent._set_ramp_mode, module, ch),
                           set_parser = str
                           )

        self.add_parameter(name='ramp_rate',
                           label='Ramp rate of the desired channel in V/ms for BE2141/2142 only',
                           unit='V/ms',
                           get_cmd=partial(self._parent._get_ramp_rate, module, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_ramp_rate, module, ch),
                           vals = vals.Numbers(0, 1)
                           )

        self.add_parameter(name='current_range',
                           label="The output current range in A for the desired channel",
                           unit='A',
                           get_cmd=partial(self._parent._get_channel_current_range, module, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_current_range, module, ch),
                           vals = vals.Enum(self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['low_range_I_A'], self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['high_range_I_A'])
                           )

        self.add_parameter(name='voltage',
                           label='The output voltage of the desired channel in V',
                           unit='V',
                           get_cmd=partial(self._parent._get_channel_voltage, module, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_voltage, module, ch),
                           vals = vals.Numbers(-self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['V_max_V'], self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['V_max_V'])
                           )

        self.add_parameter(name='current',
                           label='Returns the current in the desired channel in A',
                           unit='A',
                           get_cmd=partial(self._parent._get_channel_current, module, ch),
                           get_parser=float
                           )

        self.add_parameter(name='voltage_limit_up',
                           label='The output upper voltage limit of the desired channel in V',
                           unit='V',
                           get_cmd=partial(self._parent._get_channel_voltage_limit_up, module, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_voltage_limit_up, module, ch),
                           vals = vals.Numbers(-self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['V_max_V'], self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['V_max_V'])
                           )

        self.add_parameter(name='voltage_limit_low',
                           label='The output lower voltage limit of the desired channel in V',
                           unit='V',
                           get_cmd=partial(self._parent._get_channel_voltage_limit_low, module, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_voltage_limit_low, module, ch),
                           vals = vals.Numbers(-self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['V_max_V'], self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['V_max_V'])
                           )

        self.add_parameter(name='current_limit_up',
                           label='The output upper current limit of the desired channel in A',
                           unit='A',
                           get_cmd=partial(self._parent._get_channel_voltage_limit_up, module, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_voltage_limit_up, module, ch),
                           vals = vals.Numbers(-self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['I_max_A'], self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['I_max_A'])
                           )

        self.add_parameter(name='current_limit_low',
                           label='The output lower current limit of the desired channel in A',
                           unit='A',
                           get_cmd=partial(self._parent._get_channel_current_limit_low, module, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_current_limit_low, module, ch),
                           vals = vals.Numbers(-self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['I_max_A'], self._parent.inst_dictionnary['BE'+self._parent.get_instrument_model(module)]['I_max_A'])
                           )


        self.add_parameter(name='status',
                           label='Turn the output ON/OFF for the desired channel',
                           vals=vals.Enum(0, 1),
                           get_cmd=partial(self._parent._get_channel_status, module, ch),
                           set_cmd=partial(self._parent._set_channel_status, module, ch)
                           )

        self.add_parameter(name='curr_range_auto',
                           label='Activates or not the automatic current range selection for the BE5845 board',
                           vals=vals.Enum(0, 1),
                           get_cmd=partial(self._parent._get_curr_range_auto, module, ch),
                           set_cmd=partial(self._parent._set_curr_range_auto, module, ch)
                           )

        self.add_parameter(name='voltage_range_auto',
                           label='Activates or not the automatic voltage range selection for the BE2141/2142 board',
                           vals=vals.Enum(0, 1),
                           get_cmd=partial(self._parent._get_voltage_range_auto, module, ch),
                           set_cmd=partial(self._parent._set_voltage_range_auto, module, ch)
                           )

        self.add_parameter(name='limits_monitoring',
                           label='Activates or not the voltage or current limit monitoring for the BE5845/BE2142 board',
                           vals=vals.Enum(0, 1, 2, 3),
                           get_cmd=partial(self._parent._get_limits_monitoring, module, ch),
                           set_cmd=partial(self._parent._set_limits_monitoring, module, ch)
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
                channel = iTestChannel(parent=self, name='mod{}_chan{:02}'.format(j,i), module = j, ch=i)
                self.add_submodule('mod{}_ch{:02}'.format(j,i), channel)

    def _set_channel_voltage_range(self, module: int, ch: int, value: float) -> None:
        """
        Sets the output voltage range for the desired channel of the desired module
        Args:
            value : Voltage range in units of V (1.2 or 12) for BE2141/BE2142
            value : Voltage range in units of V 15V for BE5845
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == '5845':
            self.write(chan_id +'OUTP 0')
            self.write(chan_id + 'VOLT:RANGE ' + str(15))
            print('Be careful: output has been turned off to change range')

        elif board_model == '2141' or board_model == '2142':
            self.write(chan_id +'OUTP 0')
            self.write(chan_id + 'VOLT:RANGE ' + str(value))
            print('Be careful: output has been turned off to change range')

    def _get_channel_voltage_range(self, module: int, ch: int) -> str:
        """
        Returns the output voltage range for the desired channel
        Returns:
            Output voltage range in V
        """
        chan_id = self.chan_to_id(module, ch)
        return self.ask(chan_id + 'VOLT:RANGE?')[:-2]

    def _set_channel_voltage(self, module: int, ch: int, value: float) -> None:
        """
        Sets the output voltage of the desired channel of the desired module
        Args:
            value: The set value of voltage in V
        """
        chan_id = self.chan_to_id(module, ch)

        range_val = float(self._get_channel_voltage_range(module, ch))

        if value > range_val:
            raise ValueError('The asked voltage is too much for the selected voltage range')

        self.write(chan_id + 'VOLT {:.8f}'.format(value))
        

        self.write(chan_id + 'TRIG:INPUT:INIT')
        while abs(value - self._get_channel_voltage(module, ch)) > 1e-4 :
                    sleep(1)

    def _get_channel_voltage(self, module: int, ch: int) -> float:
        """
        Returns the output voltage of the desired channel
        Returns:
            Voltage (V)
        """
        chan_id = self.chan_to_id(module, ch)
        return float(self.ask('{}MEAS:VOLT?'.format(chan_id)))

    def _set_channel_status(self, module: int, ch: int, status: int) -> None:
        """
        Sets the status of the desired channel
        Args:
            status: 0 (OFF) or 1 (ON)
        """
        chan_id = self.chan_to_id(module, ch)
        self.write(chan_id + 'OUTP ' + str(status))

    def _get_channel_status(self, module:int , ch: int) -> str:
        """
        Returns the status of the desired channel
        Returns:
            status: 0 (OFF) or 1 (ON)
        """
        chan_id = self.chan_to_id(module, ch)
        status = self.ask(chan_id + 'OUTP ?')

        if status in ['1', '0']:
            return int(status)
        else:
            raise ValueError('Unknown status: {}'.format(status))

    def _set_ramp_mode(self, module: int, ch: int, mode: int) -> None:
        """
        Sets the desired channel output to ramp or step mode
        Args:
            mode: 0 (Step) or 1 (Ramp)
        """
        chan_id = self.chan_to_id(module, ch)
        self.write(chan_id + 'trig:input ' + str(mode))

    def _get_ramp_mode(self, module: int, ch: int) -> str:
        """
        Returns the channel output is set to ramp or step mode
        Args:
             mode: 0 (Step) or 1 (Ramp)
        """
        chan_id = self.chan_to_id(module, ch)
        mode = int(self.ask(chan_id + 'trig:input?'))

        if mode == 1:
            return "Ramp"
        elif mode == 0:
            return "Step"
        else:
            raise ValueError('Unknown mode')
        #Note that other modes are available need to be implemented or refer to Qcodes_contrib_drivers

    def _set_ramp_rate(self, module: int, ch: int, rate: float) -> None:
        """
        Sets the output voltage ramp rate
        Args:
            rate: rate of ramp in V/ms
        """
        chan_id = self.chan_to_id(module, ch)
        self.write('{}VOLT:SLOP {:.8f}'.format(chan_id, rate))

    def _get_ramp_rate(self, ch: int) -> float:
        """
        Returns the output voltage ramp rate
        """
        chan_id = self.chan_to_id(module, ch)
        return self.ask('{}VOLT:SLOP?'.format(chan_id))

    def _get_channel_current(self, ch: int) -> float:
        """
        Returns the output current in the desired channel
        Returns:
            Current (A)
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == '2142' or board_model == '5845':

            val = float(self.ask('{}MEAS:CURR?'.format(chan_id)))
        else:
            raise ValueError('Not asking a BE2142 or BE5845 board')

        return val

    def _set_channel_voltage_limit_up(self, module: int, ch: int, value_up: float) -> None:
        """
        Sets the output voltage upper limit for the desired channel
        Args:
            value_up : Voltage upper limit in units of V

        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == '5845':

            self.write(chan_id + 'LIM:VOLT:UPP ' + str(value_up))
            self.write(chan_id + 'LIM:STAT 1')

        elif board_model == '2142':
            self.write(chan_id + 'limit:upp ' + str(value_up))
            self.write(chan_id + 'LIM:STAT 1')
            

        elif board_model == '2141':
            self.write(chan_id + 'limit:upp ' + str(value_up))
            print('Be careful : Not possible to activate voltage or current limits on BE2141')
        
    def _set_channel_voltage_limit_low(self, module: int, ch: int, value_down: float) -> None:
        """
        Sets the output voltage lower limit for the desired channel
        Args:
            
            value_down : Voltage lower limit in units of V
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == '5845':

            self.write(chan_id + 'LIM:VOLT:LOW ' + str(value_up))
            self.write(chan_id + 'LIM:STAT 1')

        elif board_model == '2142':
            self.write(chan_id + 'limit:low ' + str(value_up))
            self.write(chan_id + 'LIM:STAT 1')

        if board_model == '2141':
            self.write(chan_id + 'limit:low ' + str(value_up))
            print('Be careful : Not possible to activate voltage or current limits on BE2141')

    def _set_channel_current_limit_up(self, module: int, ch: int, value_up: float) -> None:
        """
        Sets the output current upper limit for the desired channel. Only works for BE2142 or BE5845
        Args:
            value_up : Current lower limit in units of A

        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)
        if board_model == '5845'or board_model == '2142':

            self.write(chan_id + 'LIM:CURR:UPP ' + str(value_up))
            self.write(chan_id + 'LIM:STAT 1')

        else:
            raise ValueError('Not asking a BE5845 or BE2142 board')

    def _set_channel_current_limit_low(self, module: int, ch: int, value_down: float) -> None:
        """
        Sets the output current lower limit for the desired channel. Only works for BE2142 or BE5845 
        Args:
            
            value_down : Current lower limit in units of A
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)
        if board_model == '5845'or board_model == '2142':

            self.write(chan_id + 'LIM:CURR:LOW ' + str(value_up))
            self.write(chan_id + 'LIM:STAT 1')
        else:
            raise ValueError('Not asking a BE5845 or BE2142 board')

    def _get_channel_voltage_limit_up(self, module: int, ch: int) -> str:
        """
        Returns the output voltage upper  limit for the desired channel
        Returns:
            Limit up (V)
             
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == '5845':

            out = self.ask('{}LIM:VOLT:UPP?'.format(chan_id))

        elif board_model == '2141' or board_model == '2142':
            out = self.ask('{}limit:upp?'.format(chan_id))

        return str(out)

    def _get_channel_voltage_limit_low(self, module: int, ch: int) -> str:
        """
        Returns the output voltage upper and lower limit for the desired channel
        Returns:
            Limit down (V)
             
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == '5845':

            out = self.ask('{}LIM:VOLT:LOW?'.format(chan_id))

        elif board_model == '2141' or board_model == '2142':
            out = self.ask('{}limit:low?'.format(chan_id))

        return str(out)

    def _get_channel_current_limit_up(self, module: int, ch: int) -> str:
        """
        Returns the output current upper  limit for the desired channel
        Returns:
            Limit up (A)
             
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == '5845' or board_model == '2142':

            out = self.ask('{}LIM:CURR:UPP?'.format(chan_id))
        else:
            raise ValueError('Not asking a BE5845 or BE2142 board')

        return str(out)

    def _get_channel_current_limit_low(self, module: int, ch: int) -> str:
        """
        Returns the output current upper and lower limit for the desired channel
        Returns:
            Limit down (A)
             
        """
        chan_id = self.chan_to_id(module, ch)

        board_model = self.get_instrument_model(module)

        if board_model == '5845' or board_model == '2142':

            out = self.ask('{}LIM:CURR:LOW?'.format(chan_id))
        else:
            raise ValueError('Not asking a BE5845 or BE2142 board')

        return str(out)

    def _set_curr_range_auto(self, module:int, ch:int, value:int) -> None:

        """
        Sets automatic selction of the current range for the BE5845 depending on current setting.
        The range will only be changed when the module is off, so not during a measurement.

        Args:
            value : 1 (ON), 0 (OFF)
        
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)
        

        if board_model == '5845':
            self.write(chan_id + 'CURR:RANG:AUTO ' + str(value))
        else:
            raise ValueError('Not aksing BE5845 module or Unknown status: {}'.format(value))

    def _get_curr_range_auto(self, module:int, ch:int) -> str:

        """
        Queries whether the automatic selection of current range for BE5845 is activated.

        Returns:
                status of automatic current range selection as 'ON' or 'OFF' (string)

        """

        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == '5845':

            val = str(self.ask(chan_id + 'CURR:RANGE:AUTO?'))

            if val == '1':
                val_str = 'ON'
            elif val == '0':
                val_str = 'OFF'
        else:
            raise ValueError('Not asking a BE5845 module')

        return val_str

    def _set_voltage_range_auto(self, module:int, ch:int, value:int) -> None:

        """
        Sets automatic selection of the voltage range for the BE2141/2142 depending on voltage setting.
        The range will only be changed when the module is off, so not during a measurement.

        Args:
            value : 1 (ON), 0 (OFF)
        
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)
        

        if board_model == '2141' or board_model == '2142':
            self.write(chan_id + 'VOLT:RANG:AUTO ' + str(value))
        else:
            raise ValueError('Not aksing BE2141 or BE2142 module or Unknown status: {}'.format(value))

    def _get_voltage_range_auto(self, module:int, ch:int) -> str:

        """
        Queries whether the automatic selection of voltage range for BE2141/2142 is activated.

        Returns:
                status of automatic voltage range selection as 'ON' or 'OFF' (string)

        """

        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == '2141' or board_model == '2142':

            val = str(self.ask(chan_id + 'VOLT:RANGE:AUTO?'))

            if val == '1':
                val_str = 'ON'
            elif val == '0':
                val_str = 'OFF'
        else:
            raise ValueError('Not asking a BE2141 or BE2142 module')

        return val_str

    def _set_limits_monitoring(self, module:int, ch:int, value:int) -> None:
        """
        Sets on or off the limit in current or voltage monitoring

        Args:
            0 : Turns off current and voltage limit monitoring
            1 : current monitoring only for BE5845; Voltage and current monitoring for BE2142
            2 : voltage monitoring only
            3 : voltage and current monitoring (equivalent to value 1 for the LIM:STAT instruction)

        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == '5845':

            if value == 1 or value == 2: 

                self.write(chan_id + 'LIM:FUNC ' + str(value))

            elif value == 3: 

                self.write(chan_id + 'LIM:STAT ' + str(value-2))
                self.write(chan_id + 'LIM:FUNC ' + str(value))

            elif value == 0:

                self.write(chan_id + 'LIM:STAT ' + str(value))

        elif board_model == '2142':

                self.write(chan_id + 'LIM:STAT ' + str(value))


        else:
            raise ValueError('Not asking a BE5845 or BE2142 board')

    def _get_limits_monitoring(self, module:int, ch:int) -> str:
        """
        Returns the state the limit in current or voltage monitoring

        Returns:
            The state of the limits monitoring (no monitoring, current only, voltage only, voltage & current)

        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == '5845':

            val = str(self.ask(chan_id + 'LIM:STAT?'))

            val_2 = str(self.ask(chan_id + 'LIM:FUNC?'))

            if val == '1':

                val_str = 'Voltage & current monitoring'
            
            elif val_2 == '1':

                val_str = 'Current monitoring only'
                    
            elif val_2 == '2':

                val_str = 'Voltage monitoring only'

            elif val_2 == '3':

                val_str = 'Voltage & current monitoring'

            elif val == '0':

                if val_2 != '1' and val_2 != '2' and val_2 != '3':

                    val_str = 'No limit monitoring'

        elif board_model == '2142':

                val_str = str(self.ask(chan_id + 'LIM:STAT?'))


        else:
            raise ValueError('Not asking a BE5845 or BE2142 board')

            
        return val_str

    def _set_channel_current_range(self, module: int, ch: int, value: float) -> None:
        """
        Sets the output curent range for the desired channel of the desired module
        Args:
            value : Current range in units of A (15 mA) for BE2141/BE2142
            value : Current range in units of A (2 or 200 mA) for BE5845
        """
        chan_id = self.chan_to_id(module, ch)
        board_model = self.get_instrument_model(module)

        if board_model == '5845':
            self.write(chan_id +'OUTP 0')

            self.write(chan_id + 'CURR:RANGE ' + str(value))
            print('Be careful: output has been turned off to change range')

        elif board_model == '2141' or board_model == '2142':
            self.write(chan_id +'OUTP 0')
            print('Be careful: output has been turned off to change range')
            self.write(chan_id + 'CURR:RANGE ' + str(0.015))

    def _get_channel_current_range(self, module: int, ch: int) -> str:
        """
        Returns the output current range for the desired channel
        Returns:
            Output current range in A
        """
        chan_id = self.chan_to_id(module, ch)
        return self.ask(chan_id + 'CURR:RANGE?')[:-2]

    def get_instrument_model(self,inst: int) -> str:
        """
        Returns the model of the board at position 'inst' in the chassis.
        The returned string is of the form 'inst1,1111;inst2,2222;inst3,3333;inst4,4444;inst5,5555'
        The function only returns the asked inst model.

        Returns:
            Model in string format XXXX

        """

        string_chassis = str(self.ask('inst:list?'))

        if inst == 1:

            index_start_inst = 2

        else:
            
            index_start_inst = int((int(inst)-1)*7) + 2

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

        string_chassis = str(self.ask('inst:list?'))

        

        for i in range(len(string_chassis)):

            if string_chassis[i] == ',': # We use the comma separator to detect the number of borads in the chassis from the returned string of inst:list? instruction

                self.n_inst += 1 
        
        inst_array = ['','','']

        total_channel_number = 0

        for i in range(self.n_inst):

            inst_array[i] = self.get_instrument_model(int(i+1))


            if inst_array[i] == '2141' or inst_array[i] == '2142':

                self.inst_dictionnary['BE'+self.get_instrument_model(int(i+1))] = {'V_max_V':12,
                                                                            'I_max_A':0.015,
                                                                            'nb_range_V':2,
                                                                            'nb_range_I':1,
                                                                            'nb_channels':4,
                                                                            'low_range_V_V':1.2,
                                                                            'high_range_V_V':12,
                                                                            'low_range_I_A':0.015,
                                                                            'high_range_I_A':0.015,
                                                                            'position_in_chassis':int(i+1)}
            elif inst_array[i] == '5845':

                self.inst_dictionnary['BE'+self.get_instrument_model(int(i+1))] = {'V_max_V':15,
                                                                            'I_max_A':0.2,
                                                                            'nb_range_V':1,
                                                                            'nb_range_I':2,
                                                                            'nb_channels':6,
                                                                            'low_range_V_V':15,
                                                                            'high_range_V_V':15,
                                                                            'low_range_I_A':0.002,
                                                                            'high_range_I_A':0.2,
                                                                            'position_in_chassis':int(i+1)}

            total_channel_number += self.inst_dictionnary['BE' + inst_array[i]]['nb_channels']

        return self.inst_dictionnary, total_channel_number


        


    def chan_to_id(self, module:int, ch: int) -> str:

        # Returns the string to be put at the beginning of each VISA instruction to adress specifically a board (module) and a channel

        i, c = module, ch
        
        
        if module > self.n_inst:
            raise ValueError('Error: The adressed module number is larger than the number of modules in the chassis')

        board_chan_number = self.inst_dictionnary['BE'+self.get_instrument_model(module)]['nb_channels']

        if ch > board_chan_number:

            raise ValueError('Error: The adressed channel number is larger than the number of channels of the adressed module')
        
        self.chan_id = 'i{};c{};'.format(i, c)

        return 'i{};c{};'.format(i, c)

