"""
QCodes driver for Cryogenics Limited 16T Magnet controller
Sets the DC magnetic field inside the cryostat
"""

from qcodes import VisaInstrument
import time


class MagnetController(VisaInstrument):
    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='', **kwargs)

        # Sets the low frequency output amplitude
        self.add_parameter('MagneticField',
                           unit='T',
                           set_cmd=self.set_magnetic_field,
                           set_parser=float,
                           get_cmd='LFO:AMPL?',
                           get_parser=float)

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
        ramp = 0.1 * tesla_per_amp  # T/s

        # Start by interrupting whatever the magnet is currently doing
        self.write('PAUSE ON')
        time.sleep(0.75)

        # Set the rate of change for the field in amps per second
        self.write(f'SET RAMP {ramp}')
        time.sleep(0.25)

        # Set units to tesla
        self.write('TESLA ON')
        time.sleep(0.25)
        self.write('SET MID 0')
        time.sleep(0.25)

        # Turn on the heater
        self.write('HEATER ON')
        time.sleep(0.25)

        # Set the magnetic field value (in tesla, 4 decimals accuracy)
        self.write(f'SET MAX {round(float(field), 4)}')
        time.sleep(0.25)

        # Tell the magnet to go to that field value
        self.write('RAMP MAX')
        time.sleep(0.5)

        # Enable operation
        self.write('PAUSE OFF')
        time.sleep(0.25)
