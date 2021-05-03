"""
QCodes driver for Keysight 2700 digital multimeter
Only implements scanning of resistances for now
"""

from qcodes import VisaInstrument, validators as vals
import numpy as np

from time import sleep

import os

class Keysight_2700_DMM(VisaInstrument):
    # Paths of calibration files to convert between resistance [in ohms] and temperature [in kelvin]
    calib_files = [
        os.path.dirname(__file__) + '/avs_calibration_files/1)Upper HEx.txt',  # Sensor 101
        os.path.dirname(__file__) + '/avs_calibration_files/2)Lower HEx.txt',  # Sensor 102
        os.path.dirname(__file__) + '/avs_calibration_files/3)He Pot CCS.txt',  # Sensor 103
        os.path.dirname(__file__) + '/avs_calibration_files/4)1st stage.txt',  # Sensor 104
        os.path.dirname(__file__) + '/avs_calibration_files/5)2nd stage.txt',  # Sensor 105
        os.path.dirname(__file__) + '/avs_calibration_files/6)Inner Coil.txt',  # Sensor 106
        os.path.dirname(__file__) + '/avs_calibration_files/7)Outer Coil.txt',  # Sensor 107
        os.path.dirname(__file__) + '/avs_calibration_files/8)Switch.txt',   # Sensor 108
        os.path.dirname(__file__) + '/avs_calibration_files/9)He Pot.txt' # Sensor 109
    ]

    sensor_names = {
        '101': 'Upper HEx',
        '102': 'Lower HEx',
        '103': 'He Pot CCS',
        '104': '1st stage',
        '105': '2nd stage',
        '106': 'Inner Coil',
        '107': 'Outer Coil',
        '108': 'Switch',
        '109': 'He Pot'
    }

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\r', timeout=10, **kwargs)

        # Set a few parameters
        self.n_channels = 9
        self.line_cycles = 5
        self.buffer_size = 9
        self.sample_count = 1

        # Load up the calibration
        self.calibrations = []
        for fn in self.calib_files:
            calib = np.loadtxt(fn, delimiter=',')
            sort = np.argsort(calib[:, 1])
            calib[:, 0] = (calib[:, 0])[sort]
            calib[:, 1] = (calib[:, 1])[sort]
            self.calibrations.append(calib)

        # Connect to the instrument and get an IDN
        self.connect_message()

        # Initialize the device
        self.write('*RST')        
        self.write('*CLS')
        self.write('TRAC:CLE')

        # Reset scanner and clear errors
        self.write('ROUT:SCAN:LSEL NONE')
        self.write(':SYST:CLE')
        
        # Set the device to run resistance measurement
        self.write(f'FUNC "FRES" , (@101:10{self.n_channels})')

        # Set the device to autorange
        self.write(f':FRES:RANG:AUTO ON , (@101:10{self.n_channels})')

        # Set number of line cycles per integration
        self.write(f':FRES:NPLC {self.line_cycles}')

        # Set trigger source
        self.write('TRIG:SOUR IMM')

        # Set auto clearing of results
        self.write('TRIG:DEL:AUTO ON')
        self.write('TRAC:CLE:AUTO ON')

        # Set buffer size
        self.write(f'TRAC:POIN {self.buffer_size}')

        # Select source of readings
        self.write('TRAC:FEED SENS')

        # Set buffer to always on
        self.write('TRAC:FEED:CONT ALW')
        
        # Set timestamp to absolute
        self.write('TRAC:TST:FORM ABS')

        # Set list of channels to scan
        self.write(f'ROUT:SCAN (@101:10{self.n_channels})')

        # Enable scanner
        self.write('ROUT:SCAN:LSEL INT')

        # Set the sample count
        self.write(f'SAMP:COUN {self.sample_count}')

        # Enable continous initiation
        self.write('INIT:CONT ON')

        # Set output format
        self.write('FORM:ELEM READ,CHAN')

    def convert_to_kelvin(self, channel_string, resistance):
        channel = int(channel_string[-1]) - 1

        # Now we grab the calibration
        calib = self.calibrations[channel]

        # And we interpolate the result
        return np.interp(resistance, calib[:, 1], calib[:, 0])

    def scan_channels(self):
        # Create dict to save resistances
        results = {}

        # Get data from buffer
        data = self.ask('TRAC:DATA?')

        # Split it into the channels and resistances
        data_array = data.split(',')

        # Iterate through the data (the resistance and channel alternate, so stepsize is 2)
        for i in range(0, len(data_array), 2):
            # Grab the current resistance and channel
            res, chan = data_array[i], data_array[i+1]

            # And save the data
            results[self.sensor_names[chan]] = self.convert_to_kelvin(chan, float(res))

        # Return the saved data
        return results
