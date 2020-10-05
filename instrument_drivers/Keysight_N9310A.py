"""
QCodes driver for Keysight N9310A signal generator
Only implements low frequency submodule right now.
"""

from qcodes import VisaInstrument, validators as vals
import numpy as np


# Takes a string with a unit (Hz or kHz) and converts it to a number in Hz
def hz_float_parser(val):
    num, unit = val.split(' ')
    if unit.lower() == 'khz':
        return float(num) * 1e3

    return float(num)


# Takes a string with a unit (V or mV) and converts it to a number in V
def v_float_parser(val):
    num, unit = val.split(' ')
    if unit.lower() == 'mv':
        return float(num) * 1e3

    return float(num)


class N9310A(VisaInstrument):
    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\r', **kwargs)

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
                           get_parser=hz_float_parser)

        # Sets the low frequency output amplitude
        self.add_parameter('LFOutputAmplitude',
                           unit='V',
                           set_cmd='LFO:AMPL {:.3f} V',
                           get_cmd='LFO:AMPL?',
                           get_parser=v_float_parser)

        # Connect to the instrument and get an IDN
        self.connect_message()
