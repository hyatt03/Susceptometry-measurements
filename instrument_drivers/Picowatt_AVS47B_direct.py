"""
QCodes driver for Picowatt AVS-47B AC Resistance Bridge
This version expects a direct connection to the bridge, and not a converter box
Only driver that requires pyserial
"""

from qcodes import Instrument, validators as vals
import serial
import numpy as np
from scipy.interpolate import CubicSpline
import time, os, sys


class Avs_47b_direct(Instrument):
    # Paths of calibration files to convert between resistance [in ohms] and temperature [in kelvin]
    calib_file = os.path.dirname(__file__) + '/avs_calibration_files/calib.txt'

    # Map the channels to the type of sensor mounted
    sensors = {
        1: 'ruo2',
        2: 'dale',
        3: 'dale'
    }

    def __init__(self, name, address, **kwargs):
        """
        Class to keep track of parameters associated with direct connection to AVS-47B.
        """
        
        # Config the superclass
        super().__init__(name, **kwargs)

        # Load up the calibration
        calib_data = np.loadtxt(self.calib_file)
        self.dale_calib = CubicSpline(calib_data[:, 0], calib_data[:, 1])
        self.ruo2_10k_calib = CubicSpline(calib_data[:, 2], calib_data[:, 3])

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
        self.add_parameter('AlarmLine', get_cmd=None, set_cmd=None, initial_value=0)

        # Hardware Commands

        # Get/Set input mode
        # 0 = grounded input (zero resistance)
        # 1 = Measure the selected sensor channel
        # 2 = Calibrate (bridge measures internal 100 ohm resistor)
        self.add_parameter('InputMode', vals=vals.Ints(0, 2), get_cmd=None, set_cmd=None, initial_value=0)

        # Get/Set multiplexer channel (7 channels available
        # Settling time is required before an accurate measurement can be conducted
        # Settling time is longer is the excitation is low
        self.add_parameter('MultiplexerChannel', vals=vals.Ints(0, 7), get_cmd=None, set_cmd=None, initial_value=1)

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
        self.add_parameter('Excitation', unit='V', val_mapping=self.excitation_v_map, get_cmd=None, set_cmd=None, initial_value=1e-4)

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

        # Parameter where we save the raw ADC value
        self.add_parameter('ADCValue', get_cmd=None, set_cmd=None, initial_value=0)

        # Query for the resistance
        # self.add_parameter('Resistance', unit='Ohm', get_cmd=self.get_resistance, set_cmd=None, initial_value=0)
        self.add_parameter('Resistance', unit='Ohm', get_cmd=None, set_cmd=None, initial_value=0)

        # Query overrange
        # 0 = no overrange
        # 1 = At least one measurement was overranged (you should probably use autoranging
        self.add_parameter('Overrange', get_cmd=None, set_cmd=None)

        # Now we open the serial connection
        self.ser.open()

        # And then we send a config in local mode
        self.send_config(False, True)
        print('Opened serial connection to AVS-47B')

    def construct_txstring(self, remote):
        """
        Constructs a txstring from the device configuration
        Settings are only written if remote is enabled
        """
        # Allocate 48 bits
        txstring = [0]*48

        # Set disable AL
        txstring[-5] = self.AlarmLine.get()

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
        input_int = f'{int(0):0=2b}'
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

    def decode_rxstring(self, rxstring):
        """
        Method to decode the results from the AVS-47B
        """
        # Convert the array to a string
        a = ''
        for b in rxstring:
            a += str(b)

        # Extract the variables we need to determine the output
        ovr = int(a[5], base=2)
        pol = int(a[6], base=2)
        msd = int(a[7], base=2)
        d3 = int(a[8:12], base=2)
        d2 = int(a[12:16], base=2)
        d1 = int(a[16:20], base=2)
        lsd = int(a[20:24], base=2)

        # Extract variables that determine the state of the machine at time of measurement
        input_out = int(a[26:28], base=2)
        ch_out = int(a[28:31], base=2)
        disp_out = int(a[31:34], base=2)
        excitation = int(a[34:37], base=2)
        range_out = int(a[37:40], base=2)
        
        # Compute the 4.5 digit number
        adc = 10000*msd + 1000*d3 + 100*d2 + 10*d1 + lsd

        # Set the sign and convert to float
        if pol == 0:
            adc *= -1.

        # Convert the ADC value to a resistance
        resistance = adc * 10**(range_out - 5)
        
        return ovr, resistance, adc, input_out, ch_out, disp_out, excitation, range_out

    def send_config(self, remote=False, save_device_config=False, return_decoded=False):
        """
        Sends the current config to the bridge, used with remote=False when opening a connection
        Set remote to true to change settings on the device
        Set "save_device_config" to true to overwrite local variables with settings from device
        Returns the rxstring, which can be decoded by "decode_rxstring" method
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

        # Check if we should save the devices config to the configuration of the module
        if save_device_config:
            ovr, resistance, adc, input_out, ch_out, disp_out, excitation, range_out = self.decode_rxstring(rxstring)
            
            # Save the overrange
            self.Overrange.set(ovr)

            # Save the measured resistance
            self.Resistance.set(resistance)

            # Save the measured ADC value
            self.ADCValue.set(adc)

            # Save the input type
            self.InputMode.set(input_out)

            # Save the channel
            self.MultiplexerChannel.set(ch_out)

            # Save the display
            self.Display.set(disp_out)

            # Convert the excitation to an actual value and save it
            for key, val in self.excitation_v_map.items():
                if int(val) == excitation:
                    self.Excitation.set(key)
                    break

            # Convert the range to an actual value and save it
            for key, val in self.range_v_map.items():
                if int(val) == range_out:
                    self.Range.set(key)
                    break
            
            # Check if we want to return the decoded content (applies both if we save or if we don't)
            if return_decoded:
                return ovr, resistance, adc, input_out, ch_out, disp_out, excitation, range_out
        elif return_decoded:
            return self.decode_rxstring(rxstring)

        # Return the rxstring
        return rxstring

    def get_alarm_signal(self):
        """
        Queries the device to check if data is ready
        """
        # Queries the alarmline and sets the result to the property
        al = self.ser.dsr
        self.AlarmLine.set(al)

        # We also return it so we can use it immediately
        return al

    def query_for_resistance(self, channel):
        """
        Queries the device for resistance, may take a while before a measurement is returned
        """
        print('in query for resistance')

        # First we change to the channel we want to measure
        self.MultiplexerChannel.set(channel)

        # And we set the alarmline, so we get a signal when data is ready
        self.AlarmLine.set(0)

        print('set alarmline')

        # Now we send the updated configuration
        # We set it to remote mode for it all to function
        # And we don't want to overwrite our users configuration
        self.send_config(True, False)

        print('sent config')

        # Now we query the alarmline, waiting for it to turn true
        # We sleep meanwhile
        while not self.get_alarm_signal():
            time.sleep(0.005)

        print('done waiting for alarm line')

        for i in range(20):
            # Now we sleep 10 msecs waiting for the shift register to be populated with data
            time.sleep(1)

            # Now we retreive the data, we save the results to the config
            ovr, resistance, _, _, ch_out, _, _, _ = self.send_config(True, True, True)

    	    # Keep repeating measurement until ovr reports false
            if ovr == 0:
                break
            else:
                print('got overrange, repeating')

        # Return wether we are overrange, the resistance, and the channel we actually measured.
        return ovr, resistance, ch_out

    def get_resistance(self):
        return self.query_for_resistance(self.MultiplexerChannel.get())[1]

    def query_for_temperature(self, channel):
        """
        Queries the AVS-47B for the resistance on a single channel and converts it to a temperature
        """ 
        # We have a two calibrations for one channel, take heigh for that
        q_chan = channel
        if channel == 8:
            q_chan = 2

        # First we get the resistance
        ovr, resistance, ch_out = self.query_for_resistance(q_chan)

        # Now we grab the calibration
        if channel not in self.sensors:
            raise ValueError('This sensor is not calibrated')

        if self.sensors[channel] == 'dale':
            temp = self.dale_calib(resistance)
        else:
            temp = self.ruo2_10k_calib(resistance)

        # return whether we are overranged, the temperature, and the channel measured
        return ovr, temp, ch_out

    def read_write_data(self, rx, tx):
        """
        Writes a single bit to the shift register, and receives the corresponding bit from the AVS
        """
        # Iterate through the bits in the tx
        for i in range(len(tx)):
            # Set the clock pulse to 0
            self.ser.rts = False

            # Read the DI state
            rx[i] = int(self.ser.cts)

            # Set the DC state from the input signal
            self.ser.dtr = bool(tx[i])

            # sleep for a short while
            # python is pretty slow, so we don't need it

            # Set the clock pulse to 1
            self.ser.rts = True

            # sleep for a short while
            # python is pretty slow, so we don't need it

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
            # python is pretty slow, so we don't need it

            # Set the dataline to 1
            self.ser.dtr = True

            # sleep for a short while
            # python is pretty slow, so we don't need it

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
