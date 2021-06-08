"""
QCodes driver for Pfeiffer Vacuum MaxiGauge vacuum gauge controller
"""

from qcodes import Instrument
import serial

### ------- Control Symbols as defined on p. 81 of the english
###        manual for the Pfeiffer Vacuum TPG256A  -----------
C = { 
  'ETX': "\x03", # End of Text (Ctrl-C)   Reset the interface
  'CR':  "\x0D", # Carriage Return        Go to the beginning of line
  'LF':  "\x0A", # Line Feed              Advance by one line
  'ENQ': "\x05", # Enquiry                Request for data transmission
  'ACQ': "\x06", # Acknowledge            Positive report signal
  'NAK': "\x15", # Negative Acknowledge   Negative report signal
  'ESC': "\x1b", # Escape
}

LINE_TERMINATION=C['CR']+C['LF'] # CR, LF and CRLF are all possible (p.82)


class MaxiGauge(Instrument):
    def __init__(self, name, address, **kwargs):
        """
        Class to keep track of parameters associated with Pfeiffer Vacuum MaxiGauge.
        """

        # Config the superclass
        super().__init__(name, **kwargs)

        # Initialize the serial connection (not open yet)
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = address

        # Add a parameter for each sensor
        for i in range(1, 7):
            self.add_parameter(f'Pressure{i}', get_cmd=lambda: self.get_pressure(i)[1], set_cmd=None)

        # Now we open the serial connection
        self.ser.open()

        # Tell the user what happened
        print('Opened serial connection to MaxiGauge')

    def close(self):
        """
        Closes the serial connection
        """
        if self.ser.is_open:
            # We close the connection
            self.ser.close()

    def send(self, m):
        """
        Sends a message to the vacuum gauge (it includes the enquire and control signals) and returns a response
        """

        # First we clear the input buffer
        self.ser.reset_input_buffer()

        # Then we send the message
        self.ser.write(bytes(m + LINE_TERMINATION, 'ascii'))

        # Then we wait for an ack
        self.ser.read_until()

        # Then we send an enquire signal
        self.ser.write(bytes(C['ENQ'], 'ascii'))

        # And we read the response
        return self.ser.read_until()

    def get_pressure(self, channel):
        """
        Gets a pressure from a channel, decodes it, and returns the status and pressure as numbers
        """
        # Request the pressure, convert it from a bytes array, remove control symbols, and split into the two results
        s, p = self.send(f'PR{channel}').decode('ascii').strip().split(',')

        # Decode the numbers and return them
        return int(s), float(p)
