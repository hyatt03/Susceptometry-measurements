"""
File containing tests of the stations, mostly to verify the driver.
It assumes physical access to the insturments (They could potentially be simulated)
At the time of writing the current setup in the lab is the following:
 * The signal generator (n9310a) has it's LF output connected to the oscilloscope ch 0
 * The oscilloscope (analog discovery 2) ch 1 is connected to its own signal gen ch 0
 * The lock in amplifier (sr830) is connected to a susceptometer with an allen wrench in
   using the internal signal generator for measurements (this will not be the production env)
"""

import unittest
from stations import cryogenics_station, magnetism_station, data_acquisition_station
import time
import numpy as np
import matplotlib.pyplot as plt


# Helper function to test frequencies
def count_rising(trace):
    n = 0
    for v_idx in range(1, len(trace)):
        if trace[v_idx] >= 0. and trace[v_idx - 1] < 0.:
            n += 1

    return n


# Class containing tests for the magnetism station
class MagnetismStationTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Grab the station
        self.station = magnetism_station.get_station()

    # Test to check that we can initialize the instruments
    # This checks they are plugged in
    def step1_test_initialization(self):
        # Grab the devices
        signal = self.station.components['signal_gen']
        lockin = self.station.components['lockin']
        dvm = self.station.components['dvm']

        # Check we got something
        assert(signal is not None)
        assert(lockin is not None)
        assert(dvm is not None)

        print('got signal gen, dvm, and lockin')

    # Test to check we can set and retrieve the parameters of the signal gen
    def step2_test_LF_signal(self):
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

    # Test to check if we set/get the parameters of the oscilloscope
    def step3_test_dvm(self):
        # The config does not work (problem with underlying library)
        print('could not configure dvm')
        
    # Test to check values from oscilloscope correspond to changes in signal gen
    def step4_test_dvm_shows_changes_from_signal_gen(self):
        dvm = self.station.components['dvm']
        signal = self.station.components['signal_gen']

        # Enable the LF output and check a few amplitudes
        signal.LFOutputState.set(1)
        for target_v in [0.2, 0.4, 0.6, 0.8]:
            signal.LFOutputAmplitude.set(target_v)
            time.sleep(0.1)
            assert(round(np.sqrt(2) * dvm.get_rms(0), 1) == target_v)

        print('Setting output amplitudes works (to one digit at least)')

        # Set the output to 0.5v for the rest of tests
        signal.LFOutputAmplitude.set(0.5)

        # Check the frequency
        for freq, counts in [(0.5e3, 10), (1e3, 20), (1.5e3, 30), (2e3, 40)]:
            signal.LFOutputFrequency.set(freq)
            time.sleep(0.1)
            n = count_rising(dvm.get_trace(0))
            assert(np.abs(n - counts) <= 2)

        print('Setting output frequency works')

    # Workaround to force order of tests
    def test_runner(self):
        print('\nRunnning test 1 (Initialization')
        self.step1_test_initialization()

        print('\nRunning test 2 (LF signal internal)')
        self.step2_test_LF_signal()

        print('\nRunning test 3 (dvm internal)')
        self.step3_test_dvm()

        print('\nRunning test 4 (dvm and LF cross test)')
        self.step4_test_dvm_shows_changes_from_signal_gen()


if __name__ == '__main__':
    unittest.main()
    