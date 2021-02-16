"""
QCodes driver for Cryogenics Limited 16T Magnet controller
Sets the DC magnetic field inside the cryostat
"""

from qcodes import VisaInstrument
import time


class MagnetController(VisaInstrument):
    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        # Sets the low frequency output amplitude
        self.add_parameter('MagneticField',
                           unit='T',
                           set_cmd=self.set_magnetic_field,
                           get_cmd=self.get_magnetic_field)

        # Connect to the instrument and get an IDN
        self.connect_message()

        # Ensure output is measured in Tesla
        self.ask('TESLA ON')

    def get_magnetic_field(self):
        # The command returns something like
        # HH:MM:SS OUTPUT: @.@ [AMPS][TESLA] AT @.# VOLTS
        #                ^^   ^
        # So we parse that out using splits at the marked locations
        field_string = self.ask('GET OUTPUT')
        return float((field_string.split(': ')[1]).split(' ')[0])

    def set_magnetic_field(self, field):
        # The ramp speed, set in amps per second, converted to tesla per second
        tesla_per_amp = 0.14619  # T/amp
        ramp = 0.25 * tesla_per_amp  # T/s

        # Start by interrupting whatever the magnet is currently doing
        self.ask('PAUSE ON')
        time.sleep(0.75)

        # Set the rate of change for the field in amps per second
        self.ask(f'SET RAMP {ramp}')
        time.sleep(0.25)

        # Set units to tesla
        self.ask('TESLA ON')
        time.sleep(0.25)
        self.ask('SET MID 0')
        time.sleep(0.25)

        # Turn on the heater
        self.ask('HEATER ON')
        time.sleep(0.25)

        # Set the magnetic field value (in tesla, 4 decimals accuracy)
        self.ask(f'SET MAX {round(float(field), 4)}')
        time.sleep(0.25)

        # Tell the magnet to go to that field value
        self.ask('RAMP MAX')
        time.sleep(0.5)

        # Enable operation
        self.ask('PAUSE OFF')
        time.sleep(0.25)

        return self.get_magnetic_field()
