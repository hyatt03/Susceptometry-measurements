"""
QCodes driver for Keysight 2700 digital multimeter
Only implements scanning of resistances for now
"""

from qcodes import VisaInstrument, validators as vals
import numpy as np


class Keysight_2700_DMM(VisaInstrument):
    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        self.n_channels = 9
        self.line_cycles = 5
        self.buffer_size = 1000
        self.sample_count = 1

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
        self.write('ROUT:SCAN (@101:10{self.n_channels})')

        # Enable scanner
        self.write('ROUT:SCAN:LSEL INT')

        # Set the sample count
        self.write(f'SAMP:COUN {self.sample_count}')

        # Enable continous initiation
        self.write('INIT:CONT ON')

        # Set output format
        self.write('FORM:ELEM READ,CHAN,TST')

    def scan_channels(self):
        # Get data from buffer
        data = self.ask('TRAC:DATA?')
        
        print('got data', data)
