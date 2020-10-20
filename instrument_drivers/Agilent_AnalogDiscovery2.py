"""
QCodes driver for Agilent Analog Discovery 2 Mixed signal oscilloscope
"""

from qcodes import Instrument
from qcodes.utils.validators import Bool, Ints
import time
import numpy as np
import dwf

import matplotlib.pyplot as plt

class AnalogDiscovery2(Instrument):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        # Open first device
        self.dwf_ai = dwf.DwfAnalogIn()

        # Setup parameters
        # Parameter for acquisition frequency
        self.add_parameter('AIFrequency',
                           set_cmd=self.dwf_ai.frequencySet,
                           get_cmd=self.dwf_ai.frequencyGet,
                           get_parser=float,
                           initial_value=20e4,
                           unit='Hz')

        # Parameter for buffer size
        self.add_parameter('AIBufferSize',
                           set_cmd=self.dwf_ai.bufferSizeSet,
                           get_cmd=self.dwf_ai.bufferSizeGet,
                           get_parser=int,
                           vals=Ints(),
                           initial_value=4096)

        # Parameters for channel enable
        self.add_parameter('AIChannel0Enable',
                           set_cmd=lambda x: self.dwf_ai.channelEnableSet(0, x),
                           get_cmd=lambda : self.dwf_ai.channelEnableGet(0),
                           get_parser=bool,
                           vals=Bool(),
                           initial_value=True)

        self.add_parameter('AIChannel1Enable',
                           set_cmd=lambda x: self.dwf_ai.channelEnableSet(1, x),
                           get_cmd=lambda : self.dwf_ai.channelEnableGet(1),
                           get_parser=bool,
                           vals=Bool(),
                           initial_value=False)

        # Parameters for channel ranges
        self.add_parameter('AIChannel0Range',
                           set_cmd=lambda x: self.dwf_ai.channelRangeSet(0, x),
                           get_cmd=lambda : self.dwf_ai.channelRangeGet(0),
                           get_parser=float,
                           initial_value=1.0)

        self.add_parameter('AIChannel1Range',
                           set_cmd=lambda x: self.dwf_ai.channelRangeSet(1, x),
                           get_cmd=lambda : self.dwf_ai.channelRangeGet(1),
                           get_parser=float,
                           initial_value=1.0)

        # Trigger Parameters
        # Non config parameters (could be configurable)
        self.dwf_ai.triggerAutoTimeoutSet()
        self.dwf_ai.triggerSourceSet(self.dwf_ai.TRIGSRC.DETECTOR_ANALOG_IN)
        self.dwf_ai.triggerTypeSet(self.dwf_ai.TRIGTYPE.EDGE)
        self.dwf_ai.triggerConditionSet(self.dwf_ai.TRIGCOND.RISING_POSITIVE)

        # Trigger channel
        self.add_parameter('AITriggerChannel',
                           set_cmd=self.dwf_ai.triggerChannelSet,
                           get_cmd=self.dwf_ai.triggerChannelGet,
                           get_parser=int, # We can either select channel 0 or 1
                           vals=Ints(0, 1),
                           initial_value=0)

        # Trigger Level
        self.add_parameter('AITriggerLevel',
                           set_cmd=self.dwf_ai.triggerLevelSet,
                           get_cmd=self.dwf_ai.triggerLevelGet,
                           get_parser=float,
                           initial_value=0.)

        # wait at least 2 seconds with Analog Discovery for the offset to stabilize,
        # before the first reading after device open or offset/range change
        time.sleep(2)

    def get_trace(self, channel):
        # Begin acquisition
        self.dwf_ai.configure(False, True)

        # Wait for acquisition to finish
        while True:
            if self.dwf_ai.status(True) == self.dwf_ai.STATE.DONE:
                break
            time.sleep(0.001)

        # Return the data
        return np.array(self.dwf_ai.statusData(channel, self.AIBufferSize.get()))

    def get_rms(self, channel):
        # Compute rms voltage from the sample and return it
        return np.sqrt(np.mean(self.get_trace(channel)**2.))

