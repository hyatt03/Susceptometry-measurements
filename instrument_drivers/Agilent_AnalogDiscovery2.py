"""
QCodes driver for Agilent Analog Discovery 2 Mixed signal oscilloscope
The parameters cannot be set (problem with underlying library)
The getters work just fine, get_trace and get_rms work too.
"""

from qcodes import Instrument
from qcodes.utils.validators import Bool, Ints
import time
import numpy as np
import dwf

default_config_values = {
    "freq": 20e4,
    "buffer": 4096,
    "enable0": True,
    "enable1": True,
    "range0": 1.0,
    "range1": 1.0,
    "triggerchannel": 0,
    "triggerlevel": 0.0
}

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
                           initial_value=default_config_values["freq"],
                           unit='Hz')

        # Parameter for buffer size
        self.add_parameter('AIBufferSize',
                           set_cmd=self.dwf_ai.bufferSizeSet,
                           get_cmd=self.dwf_ai.bufferSizeGet,
                           get_parser=int,
                           vals=Ints(),
                           initial_value=default_config_values["buffer"])

        # Parameters for channel enable
        self.add_parameter('AIChannel0Enable',
                           set_cmd=lambda x: self.dwf_ai.channelEnableSet(0, x),
                           get_cmd=lambda : self.dwf_ai.channelEnableGet(0),
                           get_parser=bool,
                           vals=Bool(),
                           initial_value=default_config_values["enable0"])

        self.add_parameter('AIChannel1Enable',
                           set_cmd=lambda x: self.dwf_ai.channelEnableSet(1, x),
                           get_cmd=lambda : self.dwf_ai.channelEnableGet(1),
                           get_parser=bool,
                           vals=Bool(),
                           initial_value=default_config_values["enable1"])

        # Parameters for channel ranges
        self.add_parameter('AIChannel0Range',
                           set_cmd=lambda x: self.dwf_ai.channelRangeSet(0, x),
                           get_cmd=lambda : self.dwf_ai.channelRangeGet(0),
                           get_parser=float,
                           initial_value=default_config_values["range0"])

        self.add_parameter('AIChannel1Range',
                           set_cmd=lambda x: self.dwf_ai.channelRangeSet(1, x),
                           get_cmd=lambda : self.dwf_ai.channelRangeGet(1),
                           get_parser=float,
                           initial_value=default_config_values["range1"])

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
                           initial_value=default_config_values["triggerchannel"])

        # Trigger Level
        self.add_parameter('AITriggerLevel',
                           set_cmd=self.dwf_ai.triggerLevelSet,
                           get_cmd=self.dwf_ai.triggerLevelGet,
                           get_parser=float,
                           initial_value=default_config_values["triggerlevel"])

        # wait at least 2 seconds with Analog Discovery for the offset to stabilize,
        # before the first reading after device open or offset/range change
        time.sleep(2)

    # Get a trace (fills the buffer and returns it)
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

    # Computes the rms value from a trace
    def get_rms(self, channel):
        # Compute rms voltage from the sample and return it
        return np.sqrt(np.mean(self.get_trace(channel)**2.))
