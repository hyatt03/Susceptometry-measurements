"""
Magnetism station

Deals with most of the practical aspects of susceptometry measurements.
Sends data to the data acquisition station.
Talks to the following instruments:
 * Stanford research systems SR830 Lock-in amplifier (get's the signal from the secondaries)
 * Keysight N9310A Signal Generator (Generates the oscillating field for the excitation of the primary)
 * Agilent analog discovery 2 Digital oscilloscope (Measures the current running through the primary)
 * The cryogenics station (to set the DC magnetic field and the temperature)
"""

# Import os to get environment variable
import os

# Import the station from q-codes
from qcodes import Station

# Import instruments
from qcodes.tests.instrument_mocks import DummyInstrument
from qcodes.instrument_drivers.stanford_research.SR830 import SR830
from instrument_drivers import Keysight_N9310A, Agilent_AnalogDiscovery2


# Setup all the instruments for this station
def setup_instruments():
    # Setup list to hold the instruments we create
    instruments = []

    # Check if we're mocking, or if we're actually setting things up
    if os.environ.get('MOCK_INSTRUMENTS', False):
        # Configure the lock-in amplifier
        sr830_gates = ['P', 'R', 'R_offset', 'X', 'X_offset', 'Y', 'Y_offset', 'amplitude']
        sr830 = DummyInstrument('lockin_mock', gates=sr830_gates)

        # Configure the signal generator
        n9310a_gates = ['LFOutputState', 'LFOutputFrequency', 'LFOutputAmplitude']
        n9310a = DummyInstrument('signal_gen_mock', gates=n9310a_gates)

        # Configure the oscilloscope as a voltmeter
        discovery2 = DummyInstrument('dvm_mock', gates=['v1', 'v2'])

        # Append the instruments to the list of instruments
        instruments.append(sr830)
        instruments.append(n9310a)
        instruments.append(discovery2)
    else:
        # Here we create actual instruments with connections to physical hardware
        # Start with the lock-in amplifier
        sr830 = SR830('lockin', 'GPIB0::10::INSTR')

        # Next we have the signal generator
        n9310a = Keysight_N9310A.N9310A('signal_gen', 'USB0::0x0957::0x2018::01151879::INSTR')

        # And finally the voltmeter
        discovery2 = Agilent_AnalogDiscovery2.AnalogDiscovery2('dvm')
        
        # Append the instruments to the list of instruments
        instruments.append(sr830)
        instruments.append(n9310a)
        instruments.append(discovery2)

    return instruments


# Setup the station
def get_station():
    # Create a station
    magnetism_station = Station()

    # Get the associated instruments
    for instrument in setup_instruments():
        magnetism_station.add_component(instrument)

    # Give the user the station
    return magnetism_station
