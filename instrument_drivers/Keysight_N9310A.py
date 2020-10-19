"""
QCodes driver for Keysight N9310A signal generator
Only implements low frequency submodule right now.
"""

from qcodes import VisaInstrument, validators as vals
import numpy as np


class N9310A(VisaInstrument):
    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='', **kwargs)

        # Turns low frequency signal on/off (expects either 1 (on) or 0 (off))
        self.add_parameter('LFOutputState',
                           set_cmd='LFO:STAT {:1.0f}',
                           get_cmd='LFO:STAT?',
                           vals=vals.Enum(*np.arange(0, 1.1, 1).tolist()),
                           get_parser=int)

        # Sets the low frequency output frequency
        self.add_parameter('LFOutputFrequency',
                           unit='Hz',
                           set_cmd='LFO:FREQ {:.1f} Hz',
                           get_cmd='LFO:FREQ?',
                           get_parser=float)

        # Sets the low frequency output amplitude
        self.add_parameter('LFOutputAmplitude',
                           unit='V',
                           set_cmd='LFO:AMPL {:.3f} V',
                           get_cmd='LFO:AMPL?',
                           get_parser=float)

        # Connect to the instrument and get an IDN
        self.connect_message()
