"""
Magnetism station

Deals with most of the practical aspects of susceptometry measurements.
Sends data to the data acquisition station.
Talks to the following instruments:
 * Stanford research systems SR830 Lock-in amplifier (get's the signal from the secondaries)
 * Keysight N9310A Signal Generator (Generates the oscillating field for the excitation of the primary)
 * Agilent analog discovery 2 Digital oscilloscope (Measures the current running through the primary)
 * Cryogenics Limited 16T magnet controller
 * The cryogenics station (to set the DC magnetic field and the temperature)
"""

# Import the station from q-codes
from qcodes import Station

# Import instruments
from qcodes.instrument_drivers.stanford_research.SR830 import SR830
from instrument_drivers import Keysight_N9310A, Agilent_AnalogDiscovery2

# VISA addresses for the instruments
lock_in_amplifier_address = 'GPIB0::10::INSTR'
signal_generator_address = 'USB0::0x0957::0x2018::01151879::INSTR'


# Setup all the instruments for this station
def setup_instruments():
    # Here we create actual instruments with connections to physical hardware
    # Start with the lock-in amplifier
    sr830 = SR830('lockin', lock_in_amplifier_address)

    # Next we have the signal generator
    n9310a = Keysight_N9310A.N9310A('signal_gen', signal_generator_address)

    # And finally the voltmeter (Implemented using an oscilloscope by computing the RMS)
    discovery2 = Agilent_AnalogDiscovery2.AnalogDiscovery2('dvm', visalib=visalibs["discovery2"])

    # Return the instruments as a list
    return [sr830, n9310a, discovery2]


# Setup the station
def get_station():
    # Create a station
    magnetism_station = Station()

    # Get the associated instruments
    for instrument in setup_instruments():
        magnetism_station.add_component(instrument)

    # Give the user the station
    return magnetism_station

if __name__ == '__main__':
    setup_instruments()
