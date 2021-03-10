"""
Cryogenics station

Deals with most of the practical aspects of keeping things cold.
Sends data to the data acquisition station.
Talks to the following instruments:
 * Picowatt AVS-47B resistance bridge (measures various temperatures in the dilution fridge)
 * MCK50-100 Dilution fridge (controls the dilution fridge (by manipulating valves mostly))
 * Leiden Cryogenics GHS-2T-1T-700-CF Gas Handling system (Actually controls the flow of gas)
 * Leiden cryogenics triple current source
   (Heats inside the MCK50-100 both to control the temperature of the sample and to control the dilution process)
"""

# Import the station from QCodes
from qcodes import Station
from qcodes.tests.instrument_mocks import DummyInstrument
from qcodes.instrument.parameter import ArrayParameter, Parameter

import numpy as np

def setup_instruments():
    # Mock the Picowatt resistance bridge
    resistance_bridge = DummyInstrument('resistance_bridge', gates=['AlarmLine', 'InputMode', 'MultiplexerChannel',
                                                                    'Range', 'Excitation', 'ReferenceVoltage',
                                                                    'ReferenceSource', 'Magnification', 'Display',
                                                                    'ADCValue', 'Resistance', 'Overrange'])

    resistance_bridge.query_for_temperature = lambda a: (0, np.round(np.random.normal(), 3) + 5, a)

    # Setup the Leiden Cryogenics Triple Current Source
    tcs = DummyInstrument('tcs', gates=['range_1', 'range_2', 'range_3', 'current_1', 'current_2', 'current_3',
                                        'on_1', 'on_2', 'on_3', 'gated_1', 'gated_2', 'gated_3'])

    def tcs_get_all_params_mock():
        tcs.range_1.set(np.random.normal())
        tcs.range_2.set(np.random.normal())
        tcs.range_3.set(np.random.normal())

    tcs.get_all_params = tcs_get_all_params_mock

    # Setup the Leiden Cryogenics GHS-2T-1T-700-CF
    ghs_gates = ['set_p6_low', 'set_p6_high', 'set_p7_low', 'set_p7_high', 'status', 'latest_ack']

    for i in range(1, 65):
        # Create a parameter for each key
        ghs_gates.append(f'key_x{i + 100}')

    for i in range(1, 9):
        # Create a parameter for each sensor
        ghs_gates.append(f'pressure_p{i}')

    for i in range(1, 65):
        # Create a parameter for each led
        ghs_gates.append(f'led_x{i + 100}')

    class ghs_mock(DummyInstrument):
        # Mock GHS methods
        def get_all_params(self):
            # Get system status
            self.status.set(4)

            # Get pressure settings
            self.set_p6_low.set(1)
            self.set_p6_high.set(100)
            self.set_p7_low.set(1)
            self.set_p7_high.set(100)

            # Get LED statuses
            for i in range(1, 65):
                # Create a parameter for each led
                self[f'led_x{i + 100}'].set(0)

            # Get KEY statuses
            for i in range(1, 65):
                # Create a parameter for each key
                self[f'key_x{i + 100}'].set(0)

            # Get pressures
            for i in range(1, 9):
                # Create a parameter for each sensor
                self[f'pressure_p{i}'].set(np.random.normal() + 3)

    ghs = ghs_mock('ghs', gates=ghs_gates)

    # Return the instruments as a list
    return [resistance_bridge, tcs, ghs]


def get_station():
    # Create a station
    cryo_station = Station()

    # Associate the instruments with the station
    for instrument in setup_instruments():
        cryo_station.add_component(instrument)

    # Send the station to the user
    return cryo_station
