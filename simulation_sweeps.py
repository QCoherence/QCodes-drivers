# Beta version : Last updated on 19 May 2021
#                  				   -- Arpit


from qcodes import Instrument, ManualParameter
from qcodes.validators import Arrays


class simulation_sweeps(Instrument):
    """
    QCoDeS driver saving simulation data
    """

    # all instrument constructors should accept **kwargs and pass them on to
    # super().__init__

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.add_parameter(
            "x1_size", get_parser=int, initial_value=0, parameter_class=ManualParameter
        )

        self.add_parameter(
            "x2_size", get_parser=int, initial_value=0, parameter_class=ManualParameter
        )

        self.add_parameter(
            "x1_array",
            parameter_class=ManualParameter,
            snapshot_value=False,
            vals=Arrays(shape=(self.x1_size.get_latest,)),
        )

        self.add_parameter(
            "x2_array",
            vals=Arrays(shape=(self.x2_size.get_latest,)),
            parameter_class=ManualParameter,
            snapshot_value=False,
        )

        self.add_parameter(
            "y_1D_array",
            vals=Arrays(shape=(self.x1_size.get_latest,)),
            parameter_class=ManualParameter,
            snapshot_value=False,
        )

        self.add_parameter(
            "y_2D_array",
            vals=Arrays(shape=(self.x1_size, self.x2_size.get_latest)),
            parameter_class=ManualParameter,
            snapshot_value=False,
        )

        self.add_parameter(
            "freq_axis",
            parameter_class=ManualParameter,
            vals=Arrays(shape=(self.x1_size.get_latest,)),
        )
