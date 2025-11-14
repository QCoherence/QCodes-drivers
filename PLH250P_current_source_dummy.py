# This is dummy driver to register current as
# measurement parameter.
#                                        -- Arpit


from qcodes import Instrument
from qcodes import validators as vals


class TTi(Instrument):
    """
    Dummy QCoDeS driver for the TTi PLH250-P power supply to register as parameter.
    """

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__

    def __init__(self, name, **kwargs):
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name, **kwargs)

        self.add_parameter(
            name="status",
            label="Staus of supply(keep on to avoid offset)",
            vals=vals.Enum("on", "off"),
            unit="NA",
        )

        self.add_parameter(
            name="current_range",
            label="The output range; Low (500mA) range / High range. Note: Output needs to be switched off before changing ranges.",
            vals=vals.Enum("low", "high"),
            unit="NA",
        )

        self.add_parameter(
            name="current_step",
            label="Output current step size.",
            vals=vals.Numbers(0.1, 10),
            unit="mA",
        )

        self.add_parameter(
            name="current_change",
            label="Increase/decrease current by one step size.",
            vals=vals.Enum("up", "down"),
        )

        self.add_parameter(
            name="current",
            label="Set output currents in mA.",
            vals=vals.Numbers(-100, 100),
            unit="mA",
        )

        # good idea to call connect_message at the end of your constructor.
        # this calls the 'IDN' parameter that the base Instrument class creates
        # for every instrument  which serves two purposes:
        # 1) verifies that you are connected to the instrument
        # 2) gets the ID info so it will be included with metadata snapshots later.
        self.connect_message()

    def get_idn(self):
        return {
            "vendor": "Dummy corp",
            "model": "current source 001",
            "serial": "dummy 100",
            "firmware": None,
        }
