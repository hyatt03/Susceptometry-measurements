"""
QCodes driver for Leiden Cryogenics (MicroTask) GHS-2T-1T-700-CF,
which is the gas handling system for the MCK50-100 dilution fridge.
"""

from qcodes import VisaInstrument, validators as vals
from qcodes.instrument.group_parameter import GroupParameter, Group

sep = bytes.fromhex('09')  # Command separator


class LC_GHS(VisaInstrument):
    # Button addresses translated to labels on the front panel
    button_dict = {
        # Labeled buttons
        'mixture_compressor': [1],
        'bypass': [2],
        'nc-aux1': [5],
        'ledtest': [16],
        'condensing-3he': [61],
        'condensing-4he': [62],
        'normal-circulation': [63],
        'recovery': [64],
        'start': [48],
        'auto': [54],
        'reset': [10],
        'gate-valve-18': [6],

        # A-numbers
        'a0': [22],
        'a1': [52],
        'a2': [43],
        'a3': [60],
        'a4': [55],
        'a5': [49],
        'a6': [57],
        'a7': [51],
        'a8': [42],
        'a9': [40],
        'a10': [46],

        # S-numbers
        's1': [39],
        's2': [33],
        's3': [25],
        's4': [58],
        's5': [45],

        # Numbered addresses
        '0': [37],
        '1': [31],
        '2': [36],
        '3': [34],
        '4': [7],
        '5': [9],
        '6': [27],
        '7': [24],
        '8': [30],
        '9': [12],
        '10': [19],
        '11': [21],
        '12': [18],
        '13': [15],
        '14': [13],
        '15': [3],
        '16': [4],
        '17': [28],

        # Button addresses which are not connected
        'dummy': [0],
        'nc': [8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59]
    }

    acks = ['command ok', 'command error', 'parameter error', 'receive error', 'not accepted']

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        # Acknowledge type comes back when a command has been sent
        # It tells us if the machine has understood our command
        # 0 = command ok - Command accepted and executed
        # 1 = command error - Command type not excepted
        # 2 = parameter error - Wrong parameters applied
        # 3 = receive error - Received failed, send command again.
        # 4 = not accepted - Illegal data send, ignored.
        self.add_parameter('latest_ack', GroupParameter,
                           label='Acknowledge type from latest command',
                           vals=vals.Ints(0, 4))

        # Status parameter - Gets the system status
        # 1 = start
        # 2 = 3He
        # 3 = 4He
        # 4 = Normal
        # 5 = Recovery
        self.add_parameter('status', GroupParameter, label='System status', vals=vals.Ints(1, 5))
        self.status_group = Group([self.latest_ack, self.status],
                                  get_parser=lambda x: self.ack_int_parser('status', x),
                                  get_cmd='STATUS?')

        # Led status - Tells us what leds are on or off
        # 1 = off
        # 2 = on
        led_group = [self.latest_ack]
        for i in range(1, 65):
            # Create a parameter for each led
            led_label = f'led_x{i + 100}'
            self.add_parameter(led_label, GroupParameter, label=f'Led for key x{i+100}', vals=vals.Ints(1, 2))
            led_group.append(self.get(led_label))

        # Setup a group to describe the leds (and ack)
        self.led_group = Group(led_group, get_parser=self.led_status_parser, get_cmd='LEDS?')

        # Pressure status (raw ADC value)
        # P1-P7 are normal sensors
        # P8 is a flow sensor
        pressure_group = [self.latest_ack]
        for i in range(1, 9):
            # Create a parameter for each sensor
            pressure_label = f'pressure_p{i}'
            self.add_parameter(pressure_label, GroupParameter, label=f'Pressure sensor p{i}', vals=vals.Ints(0, 999999))
            pressure_group.append(self.get(pressure_label))

        # Add all the pressure sensors to a group
        self.pressure_group = Group(pressure_group, get_parser=self.pressure_status_parser, get_cmd='ADC?')

        # Pressure settings
        # P6 low - P6 value at which it stops condensing 4He
        # P6 high - P6 value at which it stops recovering 4He
        # P7 low - P7 value at which it stops condensing 3He
        # P7 high - P7 value at which it stops recovering 3He
        self.add_parameter('set_p6_low', GroupParameter, label='Low pressure limit on P6', vals=vals.Ints(0, 999999))
        self.add_parameter('set_p6_high', GroupParameter, label='High pressure limit on P6', vals=vals.Ints(0, 999999))
        self.add_parameter('set_p7_low', GroupParameter, label='Low pressure limit on P7', vals=vals.Ints(0, 999999))
        self.add_parameter('set_p7_high', GroupParameter, label='High pressure limit on P7', vals=vals.Ints(0, 999999))

        # Add all the pressure limits to a group
        self.pressure_settings_group = Group([self.latest_ack, self.set_p6_low, self.set_p6_high,
                                              self.set_p7_low, self.set_p7_high],
                                             get_parser=self.pressure_settings_parser,
                                             get_cmd="SETTINGS?",
                                             set_cmd="SETTINGS {set_p6_low},{set_p6_high},{set_p7_low},{set_p7_high}")

        # Keys on the front panel
        # 1 = off
        # 2 = on
        keys_group = [self.latest_ack]
        for i in range(1, 65):
            # Create a parameter for each key
            key_label = f'key_x{i+100}'
            self.add_parameter(key_label, GroupParameter, label=f'Status for key x{i+100}', vals=vals.Ints(1, 2))
            keys_group.append(self.get(key_label))

        # Add all the keys to a group
        self.keys_group = Group(keys_group, get_parser=self.keys_status_parser, get_cmd='KEYS?')

        # Connect to the instrument and get an IDN
        self.connect_message('ID?')

    def ack_int_parser(self, param_name, status_string):
        # Split the result into an int of an ack and an int of the result
        ack_string, res_string = status_string.split(sep)

        # Return a dict describing the contents
        return {'latest_ack': int(ack_string), param_name: int(res_string)}

    def ack_comma_sep_list(self, param_format, param_offset, status_string):
        # Create a dict to contain the results
        status_dict = {}

        # Grab the ack signal and set it to the results dict
        ack_string, res_string = status_string.split(sep)
        status_dict['latest_ack'] = int(ack_string)

        # Iterate through the led statuses and set each to the results dict
        for id, status in enumerate(res_string.split(',')):
            status_dict[param_format.format(id + param_offset)] = int(status)

        return status_dict

    def led_status_parser(self, led_status_string):
        return self.ack_comma_sep_list('led_x{}', 101, led_status_string)

    def pressure_status_parser(self, pressure_status_string):
        return self.ack_comma_sep_list('pressure_p{}', 1, pressure_status_string)

    def keys_status_parser(self, keys_status_string):
        return self.ack_comma_sep_list('key_x{}', 101, keys_status_string)

    def pressure_settings_parser(self, pressure_settings_string):
        # Create a dict to contain the results
        status_dict = {}

        # Grab the ack signal and set it to the results dict
        ack_string, res_string = pressure_settings_string.split(sep)
        status_dict['latest_ack'] = int(ack_string)

        pressure_limits = res_string.split(',')
        status_dict['set_p6_low'] = pressure_limits[0]
        status_dict['set_p6_high'] = pressure_limits[1]
        status_dict['set_p7_low'] = pressure_limits[2]
        status_dict['set_p7_high'] = pressure_limits[3]

        return status_dict

    # Helper function to manually press a button and return the acknowledgement
    def press_button(self, button):
        ack = self.ask(f'DEVMAN {self.button_dict[button][0]}')
        return self.acks[int(ack)]

