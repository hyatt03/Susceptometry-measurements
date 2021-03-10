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
from qcodes.tests.instrument_mocks import DummyInstrument
from qcodes.instrument.parameter import ArrayParameter, Parameter

import numpy as np


class SR830_fake_ChannelBuffer(ArrayParameter):
    def __init__(self, name, instrument, channel):
        """
        Args:
            name: The name of the parameter
            instrument: The parent instrument
            channel: The relevant channel (1 or 2). The name should
                should match this.
        """
        super().__init__(name,
                         shape=(1,),  # dummy initial shape
                         unit='V',  # dummy initial unit
                         setpoint_names=('Time',),
                         setpoint_labels=('Time',),
                         setpoint_units=('s',),
                         docstring='Holds an acquired (part of the) '
                                   'data buffer of one channel.')
        self.channel = channel
        self._instrument = instrument

    def prepare_buffer_readout(self):
        """
        Function to generate the setpoints for the channel buffer and
        get the right units
        """
        N = self._instrument.buffer_npts()

        # Setup the setpoints
        self.setpoint_units = ('',)
        self.setpoint_names = ('trig_events',)
        self.setpoint_labels = ('Trigger event number',)
        self.setpoints = (tuple(np.arange(0, N)),)

        # Change the shape to match buffer
        self.shape = (N,)

        # Set the unit
        self.unit = 'V'

        # Set the ready flag
        if self.channel == 1:
            self._instrument._buffer1_ready = True
        else:
            self._instrument._buffer2_ready = True

    def get_raw(self):
        """
        Get command. Returns numpy array
        """
        N = self._instrument.buffer_npts()
        if N == 0:
            raise ValueError('No points stored in SR830 data buffer.'
                             ' Can not poll anything.')

        return np.random.normal(size=self.shape)


# Setup all the instruments for this station
def setup_instruments():
    # Here we create actual instruments with connections to (fake) physical hardware
    # Start with the lock-in amplifier
    sr830 = DummyInstrument('lockin',
                            gates=['phase', 'reference_source', 'frequency', 'ext_trigger', 'harmonic', 'amplitude',
                                   'input_config', 'input_shield', 'input_coupling', 'notch_filter', 'sensitivity',
                                   'reserve', 'time_constant', 'filter_slope', 'sync_filter', 'X_offset',
                                   'Y_offset', 'R_offset', 'aux_in1', 'aux_in2', 'aux_in3', 'aux_in4', 'aux_out1',
                                   'aux_out2', 'aux_out3', 'aux_out4', 'output_interface', 'ch1_ratio', 'ch2_ratio',
                                   'ch1_display', 'ch2_display', 'X', 'Y', 'R', 'P', 'buffer_SR', 'buffer_acq_mode',
                                   'buffer_trig_mode', 'buffer_npts'])

    # Set a default npts
    sr830.buffer_npts.set(256)

    # Create fake channels
    sr830.ch1_databuffer = SR830_fake_ChannelBuffer('ch1_databuffer', sr830, 1)
    sr830.ch2_databuffer = SR830_fake_ChannelBuffer('ch2_databuffer', sr830, 2)

    # Mock methods on the lockin
    sr830.buffer_reset = lambda: 0
    sr830.buffer_start = lambda: 0
    sr830.buffer_pause = lambda: 0

    # Remove validators (they're wrong)
    sr830.ch1_ratio.vals = None
    sr830.ch2_ratio.vals = None
    sr830.buffer_SR.vals = None
    sr830.frequency.vals = None

    # Next we have the signal generator, this controls the AC field
    n9310a = DummyInstrument('signal_gen', gates=['LFOutputState', 'LFOutputFrequency', 'LFOutputAmplitude'])
    n9310a.LFOutputFrequency.vals = None

    # Next we open a connection to the magnet power supply to control the DC field
    magnet_ps = DummyInstrument('magnet_ps', gates=['MagneticField'])

    # Create mock methods
    def fake_get_magnet_ps():
        return np.random.normal(loc=magnet_ps.MagneticField.get())

    def fake_set_magnet_ps(field):
        magnet_ps.MagneticField.set(field)
        return fake_get_magnet_ps

    # And set them to the fake power supply
    magnet_ps.set_magnetic_field = lambda field: fake_set_magnet_ps(field)
    magnet_ps.get_magnetic_field = lambda: fake_get_magnet_ps()

    # And finally the voltmeter (Implemented using a Tektronix TBS1072B oscilloscope,
    # which happens to need the same driver as the TPS2012B)
    tek_scope = DummyInstrument('dvm', gates=['horizontal_scale', 'trigger_type', 'trigger_source', 'trigger_level'])
    tek_scope.trigger_type.vals = None
    tek_scope.trigger_source.vals = None

    # Mock methods
    tek_scope.force_trigger = lambda: 0
    tek_scope.clear_message_queue = lambda: 0

    class curvedata_mock():
        get_size = 1000
        noise = 0.05
        X = np.linspace(0, 8 * np.pi, get_size)

        def prepare_curvedata(self):
            pass

        def get(self):
            return np.sin(self.X) + self.noise * np.random.randn(self.get_size)

    class tek_scope_channel_mock():

        curvedata = curvedata_mock()
        scale = Parameter('scale', label='scale', set_cmd=None)
        position = Parameter('position', label='position', set_cmd=None)

        def state(self, a):
            pass

    # Mock channels
    tek_scope.channels = [tek_scope_channel_mock(), tek_scope_channel_mock()]

    tek_scope.channels[0].state = lambda a: 0

    # Set a default horizontal scale
    tek_scope.horizontal_scale.set(0.01)

    # Return the instruments as a list
    return [sr830, n9310a, tek_scope, magnet_ps]


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
