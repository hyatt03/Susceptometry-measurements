"""
QCodes driver for Agilent Analog Discovery 2 Mixed signal oscilloscope
"""

from qcodes import Instrument
import numpy as np
from ctypes import *
import sys, time


class AnalogDiscovery2(Instrument):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        # Connect to the library (dwf)
        if sys.platform.startswith("win"):
            dwf = cdll.dwf
        elif sys.platform.startswith("darwin"):
            dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
        else:
            dwf = cdll.LoadLibrary("libdwf.so")

        self.dwf = dwf

        # Device reference
        self.hdwf = c_int()

        # Status signal
        self.status = c_byte()

        # Sample space
        self.voltage = c_double()

        # Input amplitude peak to peak (value of 5 will set range to -2.5V to 2.5V)
        self.ampAcq = c_double(5)

        # offset voltage
        self.offset_voltage = c_int(0)

        # Open the device
        self.dwf.FDwfDeviceOpen(c_int(-1), byref(self.hdwf))

        # Handle errors
        if self.hdwf.value == 0:
            szerr = create_string_buffer(512)
            dwf.FDwfGetLastErrorMsg(szerr)
            raise IOError(f'Failed to open device: {str(szerr.value)}')

        # Setup parameters for acquisition
        # Enable channel 0
        self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(0), c_bool(True))

        # Set 0V offset
        self.dwf.FDwfAnalogInChannelOffsetSet(self.hdwf, c_int(0), self.offset_voltage)

        # Set the range
        self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(0), self.ampAcq)

        # Open channel
        self.dwf.FDwfAnalogInConfigure(self.hdwf, c_int(0), c_bool(False))

        # wait at least 2 seconds for the offset to stabilize
        time.sleep(2)

    def get_data(self):
        # Get analog input info from the device
        self.dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(self.status))

        # Read voltage on the first channel
        self.dwf.FDwfAnalogInStatusSample(self.hdwf, c_int(0), byref(self.voltage))


