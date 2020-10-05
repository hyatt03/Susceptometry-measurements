"""
Cryogenics station

Deals with most of the practical aspects of keeping things cold.
Sends data to the data acquisition station.
Talks to the following instruments:
 * Picowatt AVS-47B resistance bridge (measures various temperatures in the dilution fridge)
 * MCK50-100 Dilution fridge (controls the dilution fridge (by manipulating valves mostly)
 * Leiden cryogenics triple current source (Sets the DC magnetic field)
"""

import qcodes
from qcodes import Parameter, Station
from qcodes.tests.instrument_mocks import DummyInstrument


