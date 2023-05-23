from typing import Union, Tuple, Any
from functools import partial
from math import ceil
from time import sleep



from qcodes.instrument import Instrument
from qcodes.instrument import InstrumentChannel, ChannelList
from qcodes.parameters import MultiChannelInstrumentParameter
from qcodes.instrument import VisaInstrument
from qcodes.utils import validators as vals
from qcodes.parameters import create_on_off_val_mapping


class iTestChannel(InstrumentChannel):

    def __init__(self, parent: Instrument, name: str, ch: int) -> None:
        super().__init__(parent, name)


        self.add_parameter(name='voltage_range',
                           label="The output voltage range in V for the desired channel",
                           unit='V',
                           get_cmd=partial(self._parent._get_channel_range, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_range, ch),
                           vals = vals.Enum(1.2, 12)
                           )

        self.add_parameter(name='ramp_mode',
                           label='Turn ON or OFF the ramp mode for the desired channel',
                           get_cmd=partial(self._parent._get_ramp_mode, ch),
                           get_parser = str,
                           set_cmd=partial(self._parent._set_ramp_mode, ch),
                           set_parser = str
                           )

        self.add_parameter(name='ramp_rate',
                           label='Ramp rate of the desired channel in V/ms',
                           unit='V/ms',
                           get_cmd=partial(self._parent._get_ramp_rate, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_ramp_rate, ch),
                           vals = vals.Numbers(0, 1)
                           )

        self.add_parameter(name='voltage',
                           label='The output voltage of the desired channel in V',
                           unit='V',
                           get_cmd=partial(self._parent._get_channel_voltage, ch),
                           get_parser=float,
                           set_cmd=partial(self._parent._set_channel_voltage, ch),
                           vals = vals.Numbers(-12, 12)
                           )

        self.add_parameter(name='current',
                           label='Returns the current in the desired channel in A',
                           unit='A',
                           get_cmd=partial(self._parent._get_channel_current, ch),
                           get_parser=float
                           )

        self.add_parameter(name='status',
                           label='Turn the output ON/OFF for the desired channel',
                           vals=vals.Enum(0, 1),
                           get_cmd=partial(self._parent._get_channel_status, ch),
                           set_cmd=partial(self._parent._set_channel_status, ch)
                           )

class iTestBilt(VisaInstrument):
    """
    This is the QCoDeS driver for the Itest voltage source BE2142. Not all the functions are implemented yet.

    This driver is derived from the Qcodes_contrib_drivers for iTest device from Bilt.
     """

    def __init__(self, name: str, address: str, num_channels: int = 4, **kwargs):
        """
                Args:
                    name: The instrument name used by qcodes
                    address: The VISA name of the resource
                    num_channels: Number of channels. Default: 4

                Returns:
                    iTestBilt object
                """
        super().__init__(name, address, terminator="\n", **kwargs)

        self.channel = num_channels
        self.module = 1  # Number of modules

        # Create the channels
        for i in range(1, num_channels + 1):
            channel = iTestChannel(parent=self, name='chan{:02}'.format(i), ch=i)
            self.add_submodule('ch{:02}'.format(i), channel)

    def _set_channel_range(self, ch: int, value: float) -> None:
        """
        Sets the output voltage range for the desired channel
        Args:
            value : Voltage range in units of V (1.2 or 12)
        """
        chan_id = self.chan_to_id(ch)
        self.write(chan_id + 'VOLT:RANGE ' + str(value))

    def _get_channel_range(self, ch: int) -> str:
        """
        Returns the output voltage range for the desired channel
        Returns:
            Output voltage range in V
        """
        chan_id = self.chan_to_id(ch)
        return self.ask(chan_id + 'VOLT:RANGE?')[:-2]

    def _set_channel_voltage(self, ch: int, value: float) -> None:
        """
        Sets the output voltage of the desired channel
        Args:
            value: The set value of voltage in V
        """
        chan_id = self.chan_to_id(ch)
        self.write(chan_id + 'VOLT {:.8f}'.format(value))
        self.write(chan_id + 'TRIG:INPUT:INIT')
        while abs(value - self._get_channel_voltage(ch)) > 1e-4 :
                    sleep(1)

    def _get_channel_voltage(self, ch: int) -> float:
        """
        Returns the output voltage of the desired channel
        Returns:
            Voltage (V)
        """
        chan_id = self.chan_to_id(ch)
        return float(self.ask('{}MEAS:VOLT?'.format(chan_id)))

    def _set_channel_status(self, ch: int, status: int) -> None:
        """
        Sets the status of the desired channel
        Args:
            status: 0 (OFF) or 1 (ON)
        """
        chan_id = self.chan_to_id(ch)
        self.write(chan_id + 'OUTP ' + str(status))

    def _get_channel_status(self, ch: int) -> str:
        """
        Returns the status of the desired channel
        Returns:
            status: 0 (OFF) or 1 (ON)
        """
        chan_id = self.chan_to_id(ch)
        status = self.ask(chan_id + 'OUTP ?')

        if status in ['1', '0']:
            return int(status)
        else:
            raise ValueError('Unknown status: {}'.format(status))

    def _set_ramp_mode(self, ch: int, mode: int) -> None:
        """
        Sets the desired channel output to ramp or step mode
        Args:
            mode: 0 (Step) or 1 (Ramp)
        """
        chan_id = self.chan_to_id(ch)
        self.write(chan_id + 'trig:input ' + str(mode))

    def _get_ramp_mode(self, ch: int) -> str:
        """
        Returns the channel output is set to ramp or step mode
        Args:
             mode: 0 (Step) or 1 (Ramp)
        """
        chan_id = self.chan_to_id(ch)
        mode = int(self.ask(chan_id + 'trig:input?'))

        if mode == 1:
            return "Ramp"
        elif mode == 0:
            return "Step"
        else:
            raise ValueError('Unknown mode')
        #Note that other modes are available need to be implemented or refer to Qcodes_contrib_drivers

    def _set_ramp_rate(self, ch: int, rate: float) -> None:
        """
        Sets the output voltage ramp rate
        Args:
            rate: rate of ramp in V/ms
        """
        chan_id = self.chan_to_id(ch)
        self.write('{}VOLT:SLOP {:.8f}'.format(chan_id, rate))

    def _get_ramp_rate(self, ch: int) -> float:
        """
        Returns the output voltage ramp rate
        """
        chan_id = self.chan_to_id(ch)
        return self.ask('{}VOLT:SLOP?'.format(chan_id))

    def _get_channel_current(self, ch: int) -> float:
        """
        Returns the output current in the desired channel
        Returns:
            Current (A)
        """
        chan_id = self.chan_to_id(ch)
        return float(self.ask('{}MEAS:CURR?'.format(chan_id)))

    def chan_to_id(self, ch: int) -> str:

        i, c = self.module, ch
        self.chan_id = 'i{};c{};'.format(i, c)
        return 'i{};c{};'.format(i, c)

