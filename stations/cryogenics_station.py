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

# Import all the custom drivers
from instrument_drivers import LeidenCryogenics_TripleCurrentSource, \
    LeidenCryogenics_GHS_2T_1T_700_CF, Picowatt_AVS47B_direct, Keysight_2700_DMM, PfeifferVacuum_MaxiGauge

# Set the addresses for the instruments
dmm_address = 'ASRL6::INSTR'
ghs_address = 'ASRL7::INSTR'
tcs_address = 'ASRL8::INSTR'
resistance_bridge_address = 'COM9'
maxigauge_address = 'COM10'


def setup_instruments():
    # Setup the Picowatt resistance bridge
    resistance_bridge = Picowatt_AVS47B_direct.Avs_47b_direct('resistance_bridge', resistance_bridge_address)

    # Setup the Keysight 2700 DMM
    dmm = Keysight_2700_DMM.Keysight_2700_DMM('dmm', dmm_address)

    # Setup the Leiden Cryogenics Triple Current Source
    tcs = LeidenCryogenics_TripleCurrentSource.LC_TCS('tcs', tcs_address)

    # Setup the Leiden Cryogenics GHS-2T-1T-700-CF
    ghs = LeidenCryogenics_GHS_2T_1T_700_CF.LC_GHS('ghs', ghs_address)

    # Setup the Pfeiffer Vacuum MaxiGauge TPG256A
    maxigauge = PfeifferVacuum_MaxiGauge.MaxiGauge('maxigauge', maxigauge_address)

    # Return the instruments as a list
    return [resistance_bridge, tcs, ghs, dmm, maxigauge]


def get_station():
    # Create a station
    cryo_station = Station()

    # Associate the instruments with the station
    for instrument in setup_instruments():
        cryo_station.add_component(instrument)

    # Send the station to the user
    return cryo_station
