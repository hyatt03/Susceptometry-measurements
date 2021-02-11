"""
QCodes driver for Leiden Cryogenics Triple current source.
"""

from qcodes import VisaInstrument, validators as vals
from qcodes.instrument.group_parameter import GroupParameter, Group


# Parser for group parameter containing status of the machine
def status_parser(status_string):
    status_array = status_string[2:].split(',')
    return {
        'range_1': status_array[0], 'current_1': status_array[1],  # Channel 1 status
        'on_1': status_array[2], 'gated_1': status_array[3],
        'range_2': status_array[4], 'current_2': status_array[5],  # Channel 2 status
        'on_2': status_array[6], 'gated_2': status_array[7],
        'range_3': status_array[8], 'current_3': status_array[9],  # Channel 3 status
        'on_3': status_array[10], 'gated_3': status_array[11]
    }


class LC_TCS(VisaInstrument):
    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        # Add range parameters
        self.add_parameter('range_1', label='Channel 1 range', vals=vals.Ints(1, 4), parameter_class=GroupParameter)
        self.add_parameter('range_2', label='Channel 2 range', vals=vals.Ints(1, 4), parameter_class=GroupParameter)
        self.add_parameter('range_3', label='Channel 3 range', vals=vals.Ints(1, 4), parameter_class=GroupParameter)

        # Add current parameters
        self.add_parameter('current_1', label='Channel 1 current', vals=vals.Ints(0, 100),
                           parameter_class=GroupParameter)
        self.add_parameter('current_2', label='Channel 2 current', vals=vals.Ints(0, 100),
                           parameter_class=GroupParameter)
        self.add_parameter('current_3', label='Channel 3 current', vals=vals.Ints(0, 100),
                           parameter_class=GroupParameter)

        # Add on/off parameters
        self.add_parameter('on_1', label='Channel 1 on', vals=vals.Bool(), parameter_class=GroupParameter,
                           val_mapping={True: 1, False: 0})
        self.add_parameter('on_2', label='Channel 2 on', vals=vals.Bool(), parameter_class=GroupParameter,
                           val_mapping={True: 1, False: 0})
        self.add_parameter('on_3', label='Channel 3 on', vals=vals.Bool(), parameter_class=GroupParameter,
                           val_mapping={True: 1, False: 0})

        # Add gated parameters
        self.add_parameter('gated_1', label='Channel 1 gated', vals=vals.Bool(), parameter_class=GroupParameter,
                           val_mapping={True: 1, False: 0})
        self.add_parameter('gated_2', label='Channel 2 gated', vals=vals.Bool(), parameter_class=GroupParameter,
                           val_mapping={True: 1, False: 0})
        self.add_parameter('gated_3', label='Channel 3 gated', vals=vals.Bool(), parameter_class=GroupParameter,
                           val_mapping={True: 1, False: 0})

        # Setup group parameter using status command to update all the parameters at once
        status_group_parameters = [
            self.range_1, self.range_2, self.range_3,
            self.current_1, self.current_2, self.current_3,
            self.on_1, self.on_2, self.on_3,
            self.gated_1, self.gated_2, self.gated_3
        ]
        self.status_group = Group(status_group_parameters,
                                  get_parser=status_parser,
                                  get_cmd='STATUS?')

        # Connect to the instrument and get an IDN
        # self.connect_message()
        print('Connect string:', self.ask('ID?'))

    def get_all_params(self):
        # Get the status of the system
        self.range_1.get()

    # Sets the current for a channel in microamps
    def set_current(self, channel, current):
        # Set the current
        self.ask(f'SETDAC {channel} 0 {current}')

        # Update the status
        self.status_group.update()

    def toggle_channel_on(self, channel):
        # Determine which channel to toggle
        toggle_ch1, toggle_ch2, toggle_ch3 = 0, 0, 0
        if channel == 1:
            toggle_ch1 = 1
        if channel == 2:
            toggle_ch2 = 1
        if channel == 3:
            toggle_ch3 = 1

        # Toggle the channel
        self.ask(f'SETUP 0,0,{toggle_ch1},0,0,0,{toggle_ch2},0,0,0,{toggle_ch3},0')

        # Update the status
        self.status_group.update()

    def toggle_channel_gated(self, channel):
        # Determine which channel to toggle
        toggle_ch1, toggle_ch2, toggle_ch3 = 0, 0, 0
        if channel == 1:
            toggle_ch1 = 1
        if channel == 2:
            toggle_ch2 = 1
        if channel == 3:
            toggle_ch3 = 1

        # Toggle the channel
        self.ask(f'SETUP 0,0,0,{toggle_ch1},0,0,0,{toggle_ch2},0,0,0,{toggle_ch3}')

        # Update the status
        self.status_group.update()
