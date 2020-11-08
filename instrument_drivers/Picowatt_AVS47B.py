"""
QCodes driver for Picowatt AVS-47B AC Resistance Bridge
"""

from qcodes import VisaInstrument, validators as vals
import numpy as np


class Avs_47b(VisaInstrument):
    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\r\n', **kwargs)

        # Initial commands and queries

        # Get the version of the communication hardware
        self.add_parameter('HardwareVersion', get_cmd='HW?')

        # Get the alarm line
        # if the value is zero there is an error (check the plug)
        # if the value is one, all is OK
        self.add_parameter('AlarmLine', get_cmd='AL?', get_parser=int)

        # Set the command delimiter, default is semicolon (0), alternative is comma (1)
        self.add_parameter('CommandDelimeter', set_cmd='LIM {:1.0f}', initial_value=0, vals=vals.Ints(0, 1))

        # Set the response line terminator
        # Initial value if CRLF (3), alternatives are: 2 = CR, 1 = LF, 0 = nothing
        self.add_parameter('ResponseTerminator', set_cmd='TER {:1.0f}', initial_value=3, vals=vals.Ints(0, 3))

        # Get/Set remote mode on the device
        # Must be enabled for changes to take place
        # Values are 0 = local, and 1 = remote
        self.add_parameter('RemoteMode', get_cmd='REM?', set_cmd='REM {:1.0f}', initial_value=1, get_parser=int,
                           vals=vals.Ints(0, 1))

        # Hardware Commands

        # Get/Set input mode
        # 0 = grounded input (zero resistance)
        # 1 = Measure the selected sensor channel
        # 2 = Calibrate (bridge measures internal 100 ohm resistor)
        self.add_parameter('InputMode', get_cmd='INP?', set_cmd='INP {:1.0f}', get_parser=int, vals=vals.Ints(0, 2))

        # Get/Set multiplexer channel (7 channels available
        # Settling time is required before an accurate measurement can be conducted
        # Settling time is longer is the excitation is low
        self.add_parameter('MultiplexerChannel', get_cmd='MUX?', set_cmd='MUX {:1.0f}', get_parser=int,
                           vals=vals.Ints(0, 7))

        # Get/set the range
        range_v_map = {
            0: '0',  # No Excitation (Avoid this to avoid accidental heating)
            2: '1',  # 2 Ohm
            20: '2',  # 20 Ohm
            200: '3',  # etc..
            2000: '4',
            20000: '5',
            200000: '6',
            2000000: '7'
        }
        self.add_parameter('Range',
                           unit='Ohm',
                           get_cmd='RAN?',
                           set_cmd='RAN {:1.0f}',
                           get_parser=int,
                           val_mapping=range_v_map,
                           initial_value=2000000)

        # Get/set the excitation voltage
        # (RMS voltage across a sensor whose value is half of the selected range)
        # Excitation is symmetrical square wave current at about 13.7Hz
        excitation_v_map = {
            0: '0',  # No Excitation (Avoid this to avoid accidental heating)
            3e-6: '1',  # 3 microvolts
            1e-5: '2',  # 10 microvolts
            3e-5: '3',  # 30 microvolts
            1e-4: '4',  # etc..
            3e-4: '5',
            1e-3: '6',
            3e-3: '7'
        }
        self.add_parameter('Excitation',
                           unit='V',
                           get_cmd='EXC?',
                           set_cmd='EXC {:1.0f}',
                           get_parser=int,
                           val_mapping=excitation_v_map,
                           initial_value=3e-6)

        # Set reference for deviation (Delta R) measurements
        # 10000 sets the reference DAC to 1 volt
        # which corresponds to the middle of the selected resistance range
        self.add_parameter('ReferenceVoltage', set_cmd='REF {:1.0f}', initial_value=0, vals=vals.Ints(0, 20000))

        # Execute the null deviation macro (intended only for display set to 0)
        self.add_parameter('NullDeviation', set_cmd='NULDEV {:1.0f}', vals=vals.Ints(0, 100))

        # Get reference source (Must be set using the contact on the front panel)
        # 0 = reference DAC (aka REF MEM)
        # 1 = front panel potentiometer
        self.add_parameter('ReferenceSource', get_cmd='RFS?', get_parser=int)

        # Get the magnification (Can only be set manually, and is not very accurate)
        # 0 = 1x Delta R
        # 1 = 10x Delta R
        self.add_parameter('Magnification', get_cmd='MAG?', get_parser=int)

        # Measurement and readout commands/queries

        # Get/set display (measure using ADC command)
        # 0 = Voltage proportional to the sensor value R (Use Resistance to query for the value)
        # 1 = Deviation Delta R between R and the reference (Use Resistance to query for the value)
        # 2 = Adjust reference, this displays the voltage from the front panel potentiometer
        # 3 = Reference, this displays the reference voltage from the DAC
        # 4 = Excitation voltage, this displays the approximate excitation voltage across the sensor.
        #     Useful only on the lowest resistance ranges and high excitation.
        #     Can be used for estimating the current lead resistance
        self.add_parameter('Display', get_cmd='DIS?', set_cmd='DIS {:1.0f}', get_parser=int, vals=vals.Ints(0, 4))

        # Set the averaging on the ADC (Set the number of points to average over)
        self.add_parameter('ADCAverage', set_cmd='ADC {:1.0f}', vals=vals.Ints(1, 1000))

        # Get the ADC value
        # Returns a voltage between -2 and +2, yields exact 0 when overranged
        # Real 0 and overrange 0 can be distinguished using Overrange command.
        self.add_parameter('ADCValue', get_cmd='ADC?', get_parser=lambda x: float(x) / 10000, unit='V')

        # Set the averaging on resistance measurements (number of points to average)
        self.add_parameter('ResistanceAveraging', set_cmd='RES {:1.0f}', vals=vals.Ints(1, 1000))

        # Query for the resistance
        self.add_parameter('Resistance', get_cmd='RES?', get_parser=float)

        # Query overrange
        # 0 = no overrange
        # 1 = At least one measurement was overranged (you should probably use autoranging
        self.add_parameter('Overrange', get_cmd='OVR?', get_parser=int)

        # Query minimum resistance in ohms of averaged resistance measurement
        self.add_parameter('MinimumResistance', unit='Ohm', get_cmd='MIN?', get_parser=float)

        # Query maximum resistance in ohms of averaged resistance measurement
        self.add_parameter('MaximumResistance', unit='Ohm', get_cmd='MAX?', get_parser=float)

        # Query standard deviation of the resistance in ohms of averaged resistance measurement
        # Only reliable when noise is white
        self.add_parameter('STDResistance', unit='Ohm', get_cmd='STD?', get_parser=float)

        # Query QRatio, white noise is about 5, much higher indicated external interference
        # Affected by digitizing step if the excitation is high
        self.add_parameter('QRatio', get_cmd='QRATIO?', get_parser=float)

        # Setup autoranging
        # 0 = No autoranging
        # 1..30 = Autoranging with delay of n seconds
        # Lower excitation necessitates longer delays
        # Query range often to check if range has changed
        self.add_parameter('Autorange', unit='s', set_cmd='ARN {:1.0f}', vals=vals.Ints(0, 30))

        # Other commands and queries

        # Delay, used when changing range and excitation (delay in seconds)
        self.add_parameter('Delay', unit='s', set_cmd='DLY {:1.0f}', vals=vals.Ints(1, 30))

        # Reset
        self.add_parameter('Reset', set_cmd='RST')

        # Query for errors
        self.add_parameter('Errors', get_cmd='ERR?')

        # Connect to the instrument and get an IDN
        self.connect_message()
