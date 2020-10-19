"""
QCodes driver for Agilent Analog Discovery 2 Mixed signal oscilloscope
"""

from qcodes import Instrument
import time
import numpy as np
import dwf

import matplotlib.pyplot as plt

class AnalogDiscovery2(Instrument):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        # Open first device
        self.dwf_ai = dwf.DwfAnalogIn()

        # Prepare to read sample
        self.dwf_ai.frequencySet(20e4)
        self.dwf_ai.bufferSizeSet(4096)
        self.dwf_ai.channelEnableSet(0, True)
        self.dwf_ai.channelRangeSet(0, 1.0)

        # Setup trigger
        self.dwf_ai.triggerAutoTimeoutSet()
        self.dwf_ai.triggerSourceSet(self.dwf_ai.TRIGSRC.DETECTOR_ANALOG_IN)
        self.dwf_ai.triggerTypeSet(self.dwf_ai.TRIGTYPE.EDGE)
        self.dwf_ai.triggerChannelSet(0)
        self.dwf_ai.triggerLevelSet(0.)
        self.dwf_ai.triggerConditionSet(self.dwf_ai.TRIGCOND.RISING_POSITIVE)

        # wait at least 2 seconds with Analog Discovery for the offset to stabilize,
        # before the first reading after device open or offset/range change
        time.sleep(2)

    def get_rms(self):
        # Begin acquisition
        self.dwf_ai.configure(False, True)

        # Wait for acquisition to finish
        while True:
            if self.dwf_ai.status(True) == self.dwf_ai.STATE.DONE:
                break
            time.sleep(0.001)

        # Grab the data
        rgdSamples = np.array(self.dwf_ai.statusData(0, 4096))

        # Compute rms voltage from the sample and return it
        return np.sqrt(np.mean(rgdSamples**2.))

