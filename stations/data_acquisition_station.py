"""
Data acquisition station

Deals with communication between cryogenics station and magnetism station,
logs all data obtained in an experiment.
May run on the same PC as the magnetism station, time will tell.
May get the following data:
 * Temperatures at various points in the cryostat (from cryo station)
 * DC magnetic field applied (from cryo station)
 * AC magnetic field function (from magnetism station)
 * AC magnetic field current (from magnetism station)
 * The excitation generated in the secondary coils (with or without sample) (from magnetism station)

It would be useful with some sort of live graphs of the incoming data.
"""

import qcodes
from qcodes import Parameter, Station
from qcodes.tests.instrument_mocks import DummyInstrument


