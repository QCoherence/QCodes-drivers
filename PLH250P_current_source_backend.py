# This is backend driver without jump protection,
# use TCP wrapper to control the instrument.
#                                        -- Arpit


from qcodes import VisaInstrument
from qcodes import validators as vals

# from Arduino import serial_write
from Serial_TCP_client_functions import TCP_pi_write

oldstate = "off"


class TTi(VisaInstrument):
    """
    QCoDeS driver for the TTi PLH250-P power supply
    """

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__

    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name, address, terminator="\r\n", **kwargs)

        self.add_parameter(
            name="status",
            label="Staus of supply(keep on to avoid offset)",
            vals=vals.Enum("on", "off"),
            unit="NA",
            set_cmd="OP1 " + "{:.12f}",
            get_cmd="OP1?",
            set_parser=self.easy_read_status,
            get_parser=self.easy_read_status_read,
        )

        self.add_parameter(
            name="current_range",
            label="The output range; Low (500mA) range / High range. Note: Output needs to be switched off before changing ranges.",
            vals=vals.Enum("low", "high"),
            unit="NA",
            set_cmd="IRANGE1 " + "{:.12f}",
            get_cmd="IRANGE1?",
            set_parser=self.easy_read_Irange,
            get_parser=self.easy_read_Irange_read,
        )

        self.add_parameter(
            name="current_step",
            label="Output current step size.",
            vals=vals.Numbers(0.1, 10),
            unit="mA",
            set_cmd="DELTAI1 " + "{:.12f}",
            get_cmd="DELTAI1?",
            set_parser=self.mA_to_A,
            get_parser=self.A_to_mA,
        )

        self.add_parameter(
            name="current_change",
            label="Increase/decrease current by one step size.",
            vals=vals.Enum("up", "down"),
            unit="int",
            set_cmd="{}",
            set_parser=self.current_up_down,
        )

        self.add_parameter(
            name="current",
            label="Set output currents in mA.",
            vals=vals.Numbers(-100, 100),
            unit="mA",
            set_cmd="I1 " + "{:.12f}",
            get_cmd="I1?",
            set_parser=self.mA_to_A,
            get_parser=self.A_to_mA_with_parity,
        )

        # good idea to call connect_message at the end of your constructor.
        # this calls the 'IDN' parameter that the base Instrument class creates
        # for every instrument  which serves two purposes:
        # 1) verifies that you are connected to the instrument
        # 2) gets the ID info so it will be included with metadata snapshots later.
        self.connect_message()

    def easy_read_status(self, status):
        if status == "on":
            ret = 1
        elif status == "off":
            ret = 0
        return ret

    def easy_read_status_read(self, status):
        if status == "1":
            ret = "on"
        elif status == "0":
            ret = "off"
        return ret

    def easy_read_Irange(self, Irange):
        if Irange == "low":
            ret = 1
        elif Irange == "high":
            ret = 2
        return ret

    def easy_read_Irange_read(self, Irange):
        if Irange == "1":
            ret = "low"
        elif Irange == "2":
            ret = "high"
        return ret

    def mA_to_A(self, I):
        if I < 0:
            setstate("neg")
            I = -I
        else:
            setstate("pos")
        return I * 1e-3

    def A_to_mA(self, I):
        I = I[3:]
        return float(I) * 1e3

    def A_to_mA_with_parity(self, I):
        I = I[3:]
        I = float(I) * 1e3
        if oldstate == "neg":
            I = -1 * I
        return I

    def current_up_down(self, delta):
        if delta == "up":
            ret = "INCI1"
        elif delta == "down":
            ret = "DECI1"
        return ret


def setstate(newstate):
    global oldstate, ser
    if newstate != oldstate:
        if newstate == "neg":
            TCP_pi_write(2)
            # serial_write(2)
            oldstate = "neg"
        if newstate == "pos":
            TCP_pi_write(1)
            # serial_write(1)
            oldstate = "pos"
    if newstate == "off":
        TCP_pi_write(0)
        oldstate = "off"


def parity():
    return oldstate
