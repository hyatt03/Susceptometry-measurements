"""
QCodes driver for Picowatt AVS-47B AC Resistance Bridge
This version expects a direct connection to the bridge, and not a converter box
Only driver that requires pyserial
"""

from qcodes import Instrument, validators as vals
import serial
import numpy as np
import time


class Avs_47b_direct(Instrument):
    def __init__(self, name, address, **kwargs):
        """
        Class to keep track of parameters associated with direct connection to AVS-47B.
        """
        
        # Config the superclass
        super().__init__(name, **kwargs)
        
        # Initialize the serial connection (not open yet)
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = address

        # The parameters can be set by the user using the standard QCodes API.
        # The parameters are sent to the device whenever a query or config is issued.
        # The parameters are then updated to reflect what the state of the device is (where applicable).

        # Get the alarm line
        # if the value is zero there can be an error (wait a bit, then check the plug or address)
        # if the value is one, all is OK (it means a measurement is ready)
        self.add_parameter('AlarmLine', get_cmd=None, set_cmd=None)

        # Hardware Commands

        # Get/Set input mode
        # 0 = grounded input (zero resistance)
        # 1 = Measure the selected sensor channel
        # 2 = Calibrate (bridge measures internal 100 ohm resistor)
        self.add_parameter('InputMode', vals=vals.Ints(0, 2), get_cmd=None, set_cmd=None, initial_value=1)

        # Get/Set multiplexer channel (7 channels available
        # Settling time is required before an accurate measurement can be conducted
        # Settling time is longer is the excitation is low
        self.add_parameter('MultiplexerChannel', vals=vals.Ints(0, 7), get_cmd=None, set_cmd=None, initial_value=0)

        # Get/set the range
        self.range_v_map = {
            0: '0',  # No Excitation (Avoid this to avoid accidental heating)
            2: '1',  # 2 Ohm
            20: '2',  # 20 Ohm
            200: '3',  # etc..
            2000: '4',
            20000: '5',
            200000: '6',
            2000000: '7'
        }
        self.add_parameter('Range', unit='Ohm', val_mapping=self.range_v_map, get_cmd=None, set_cmd=None, initial_value=2000000)

        # Get/set the excitation voltage
        # (RMS voltage across a sensor whose value is half of the selected range)
        # Excitation is symmetrical square wave current at about 13.7Hz
        self.excitation_v_map = {
            0: '0',  # No Excitation (Use this to avoid accidental heating)
            3e-6: '1',  # 3 microvolts
            1e-5: '2',  # 10 microvolts
            3e-5: '3',  # 30 microvolts
            1e-4: '4',  # etc..
            3e-4: '5',
            1e-3: '6',
            3e-3: '7'
        }
        self.add_parameter('Excitation', unit='V', val_mapping=self.excitation_v_map, get_cmd=None, set_cmd=None, initial_value=0)

        # Set reference for deviation (Delta R) measurements
        # 10000 sets the reference DAC to 1 volt
        # which corresponds to the middle of the selected resistance range
        self.add_parameter('ReferenceVoltage', vals=vals.Ints(0, 20000), get_cmd=None, set_cmd=None, initial_value=0)

        # Get reference source (Must be set using the contact on the front panel)
        # 0 = reference DAC (aka REF MEM)
        # 1 = front panel potentiometer
        self.add_parameter('ReferenceSource', vals=vals.Ints(0, 1), get_cmd=None, set_cmd=None)

        # Get the magnification (Can only be set manually, and is not very accurate)
        # 0 = 1x Delta R
        # 1 = 10x Delta R
        self.add_parameter('Magnification', vals=vals.Ints(0, 1), get_cmd=None, set_cmd=None)

        # Measurement and readout commands/queries

        # Get/set display (measure using ADC command)
        # 0 = Voltage proportional to the sensor value R (Use Resistance to query for the value)
        # 1 = Deviation Delta R between R and the reference (Use Resistance to query for the value)
        # 2 = Adjust reference, this displays the voltage from the front panel potentiometer
        # 3 = Reference, this displays the reference voltage from the DAC
        # 4 = Excitation voltage, this displays the approximate excitation voltage across the sensor.
        #     Useful only on the lowest resistance ranges and high excitation.
        #     Can be used for estimating the current lead resistance
        self.add_parameter('Display', vals=vals.Ints(0, 4), get_cmd=None, set_cmd=None, initial_value=0)

        # Set the averaging on the ADC (Set the number of points to average over)
        self.add_parameter('ADCAverage', vals=vals.Ints(1, 1000), get_cmd=None, set_cmd=None)

        # Get the ADC value
        # Returns a voltage between -2 and +2, yields exact 0 when overranged
        # Real 0 and overrange 0 can be distinguished using Overrange command.
        self.add_parameter('ADCValue', unit='V', get_cmd=None, set_cmd=None)

        # Set the averaging on resistance measurements (number of points to average)
        self.add_parameter('ResistanceAveraging', vals=vals.Ints(1, 1000), get_cmd=None, set_cmd=None)

        # Query for the resistance
        self.add_parameter('Resistance', unit='Ohm', get_cmd=None, set_cmd=None)

        # Query overrange
        # 0 = no overrange
        # 1 = At least one measurement was overranged (you should probably use autoranging
        self.add_parameter('Overrange', get_cmd=None, set_cmd=None)

        # Query minimum resistance in ohms of averaged resistance measurement
        self.add_parameter('MinimumResistance', unit='Ohm', get_cmd=None, set_cmd=None)

        # Query maximum resistance in ohms of averaged resistance measurement
        self.add_parameter('MaximumResistance', unit='Ohm', get_cmd=None, set_cmd=None)

        # Query standard deviation of the resistance in ohms of averaged resistance measurement
        # Only reliable when noise is white
        self.add_parameter('STDResistance', unit='Ohm', get_cmd=None, set_cmd=None)

        # Query QRatio, white noise is about 5, much higher indicated external interference
        # Affected by digitizing step if the excitation is high
        self.add_parameter('QRatio', get_cmd=None, set_cmd=None)

        # Setup autoranging
        # 0 = No autoranging
        # 1..30 = Autoranging with delay of n seconds
        # Lower excitation necessitates longer delays
        # Query range often to check if range has changed
        self.add_parameter('Autorange', unit='s', vals=vals.Ints(0, 30), get_cmd=None, set_cmd=None)

        # Other commands and queries

        # Query for errors
        self.add_parameter('Errors', get_cmd=None, set_cmd=None)

        # Now we open the serial connection
        self.ser.open()

        # And then we send a config in local mode
        self.send_config(False)
        print('Opened serial connection to AVS-47B')

    def construct_txstring(self, remote):
        # Allocate 48 bits
        txstring = [0]*48

        # Set disable AL
        txstring[-5] = 1

        # Set remote mode
        txstring[-7] = int(remote)

        # Set range
        range_int =  f'{int(self.range_v_map[self.Range.get()]):0=3b}'
        txstring[-9] = int(range_int[-1])
        txstring[-10] = int(range_int[-2])
        txstring[-11] = int(range_int[-3])

        # Set the excitation
        excitation_int = f'{int(self.excitation_v_map[self.Excitation.get()]):0=3b}'
        txstring[-12] = int(excitation_int[-1])
        txstring[-13] = int(excitation_int[-2])
        txstring[-14] = int(excitation_int[-3])

        # Set the display
        display_int = f'{int(self.Display.get()):0=3b}'
        txstring[-15] = int(display_int[-1])
        txstring[-16] = int(display_int[-2])
        txstring[-17] = int(display_int[-3])

        # Set the channel
        channel_int = f'{int(self.MultiplexerChannel.get()):0=3b}'
        txstring[-18] = int(channel_int[-1])
        txstring[-19] = int(channel_int[-2])
        txstring[-20] = int(channel_int[-3])
        
        # Set the input
        input_int = f'{int(self.InputMode.get()):0=2b}'
        txstring[-21] = int(input_int[-1])
        txstring[-22] = int(input_int[-2])
        
        # Set the ref voltage address to 3
        txstring[-25] = 1
        txstring[-26] = 1

        # Program the reference voltage
        ref_voltage_int = f'{int(self.ReferenceVoltage.get()):0=16b}'
        for i in range(len(ref_voltage_int)):
            txstring[i] = int(ref_voltage_int[i])

        # Return the 48bit txstring
        return txstring

    def send_config(self, remote=True):
        """
        Sends the current config to the bridge, used with remote=False when opening a connection
        """
        # First we send the address
        # Construct an address (we just use the default (1) as recommended)
        hw_address = [0, 0, 0, 0, 0, 0, 0, 1]
        hw_address_old = [0, 0, 0, 0, 0, 0, 0, 1]

        # Construct the TXString and allocate the rxstring
        txstring = self.construct_txstring(remote)
        rxstring = [0]*48

        # Read the old address and write the new address
        self.read_write_data(hw_address_old, hw_address)

        # Strobe the address
        self.strobe()

        # Read and write the config
        self.read_write_data(rxstring, txstring)

        # Strobe the txstring
        self.strobe()

        print(hw_address_old, rxstring)

        return rxstring


    def query_for_resistance(self):
        """
        Queries the device for resistance, may take a while before a measurement is returned
        """
        pass

    def read_write_data(self, rx, tx):
        # Iterate through the bits in the tx
        for i in range(len(tx)):
            # Set the clock pulse to 0
            self.ser.rts = False

            # Read the DI state
            rx[i] = int(self.ser.cts)

            # Set the DC state from the input signal
            self.ser.dtr = bool(tx[i])

            # sleep for a short while
            time.sleep(1e-5)

            # Set the clock pulse to 1
            self.ser.rts = True

            # sleep for a short while
            time.sleep(1e-5)

            # Set the clock pulse to 0
            self.ser.rts = False

            # Set the dataline to 0
            self.ser.dtr = False

    def strobe(self):
        """
        Strobes the device, must be run after sending address and after sending config
        """
        # Loop 3 times
        for _ in range(3):
            # Set the clock pulse to 0
            self.ser.rts = False
            
            # Set the dataline to 0
            self.ser.dtr = False

            # sleep for a short while
            time.sleep(1e-5)

            # Set the dataline to 1
            self.ser.dtr = True

            # sleep for a short while
            time.sleep(1e-5)

            # Set the dataline to 0
            self.ser.dtr = False

    def close(self):
        """
        Closes the serial connection
        """
        if self.ser.is_open:
            # First we set the device to local mode
            self.send_config(False)

            # Then we close the connection
            self.ser.close()
