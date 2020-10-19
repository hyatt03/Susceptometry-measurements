import unittest
from stations import cryogenics_station, magnetism_station, data_acquisition_station
from time import time
import numpy as np
import matplotlib.pyplot as plt


class MagnetismStationTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Grab the station
        self.station = magnetism_station.get_station()

    def test_initialization(self):
        # Grab the devices
        signal = self.station.components['signal_gen']
        lockin = self.station.components['lockin']
        dvm = self.station.components['dvm']

        # Check we got something
        assert(signal is not None)
        assert(lockin is not None)
        assert(dvm is not None)

        print('got signal gen, dvm, and lockin')

    def test_LF_signal(self):
        # Grab the signal gen
        signal = self.station.components['signal_gen']

        # Check the initial state (for user feedback)
        if signal.LFOutputState.get() == 1:
            print('LF is currently on')
        else:
            print('LF is currently off')

        # Set the state to off (regardless of previous state)
        print('trying to set LF to off')
        signal.LFOutputState.set(0)

        # Check if it worked
        assert(signal.LFOutputState.get() == 0)
        print('set the LF to off')

        # Set the state to on
        print('Trying to set LF on')
        signal.LFOutputState.set(1)

        # Check if it worked
        assert(signal.LFOutputState.get() == 1)
        print('set the LF to on')

        # Get the initial amplitude
        initial_amp = signal.LFOutputAmplitude.get()
        print(f'initial amplitude: {initial_amp}V')

        # Decrease the amplitude by 50 mv
        target_amp = initial_amp - 0.05
        signal.LFOutputAmplitude.set(target_amp)
        assert(signal.LFOutputAmplitude.get() == target_amp)
        print('decreased output amplitude by 50mV')

        # Increase the amplitude back to the original level
        signal.LFOutputAmplitude.set(initial_amp)
        assert(signal.LFOutputAmplitude.get() == initial_amp)
        print('Output amplitude back to normal')

        # Get the initial frequency
        initial_freq = signal.LFOutputFrequency.get()
        print(f'LF frequency is: {initial_freq} Hz')

        # Set the frequency to half the value
        signal.LFOutputFrequency.set(initial_freq / 2)
        assert(signal.LFOutputFrequency.get() == initial_freq / 2)
        print('halved the frequency')

        # Set the frequency back to 1kHz
        signal.LFOutputFrequency.set(1e3)
        assert(signal.LFOutputFrequency.get() == 1e3)
        print('set the frequency to 1kHz')

    def test_dvm(self):
        dvm = self.station.components['dvm']
        dvm.get_rms()


if __name__ == '__main__':
    unittest.main()
    