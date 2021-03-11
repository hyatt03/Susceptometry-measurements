# Import asyncio to get event loop
import asyncio

# Get OS to use environment variables
import os

# Import time and path python packages
import time, sys, os, math

# Import numpy
import numpy as np

# Import pandas for saving experiment data
import pandas as pd

# Add top level packages to path
sys.path.append(os.path.dirname(__file__) + '/..')

# Import the base namespace, contains shared methods and information
from socket_clients.baseclient import BaseClientNamespace, BaseQueueClass, main

if os.getenv('USE_FAKE_STATIONS') is None:
    # Import magnetism station to collect data
    from stations import magnetism_station
else:
    # Import the mocked magnetism station
    from stations.fake_stations import magnetism_station_fake as magnetism_station

# Setup magnetism state
magnetism_state = {
    'magnet_trace': [],
    'magnet_trace_times': [],
    'startup_time': time.time(),
    'current_step': {'step_done': True},
    'next_step': {},
    'experiment_file': None,
    'experiment_file_id': None
}


# Simple helper function to convert a list containing arrays to a list of means of each array
def get_mean_from_list_of_arrays(a):
    return list(np.array(a).mean(axis=1))


# list of parameters for the lock in amplifier
# Used when getting and setting the config
lockin_params = ['phase', 'reference_source', 'frequency', 'ext_trigger', 'harmonic', 'amplitude',
                 'input_config', 'input_shield', 'input_coupling', 'notch_filter', 'sensitivity',
                 'reserve', 'time_constant', 'filter_slope', 'sync_filter', 'X_offset', 'Y_offset',
                 'R_offset', 'aux_in1', 'aux_in2', 'aux_in3', 'aux_in4', 'aux_out1', 'aux_out2',
                 'aux_out3', 'aux_out4', 'output_interface', 'ch1_ratio', 'ch2_ratio', 'ch1_display',
                 'ch2_display', 'ch1_databuffer', 'ch2_databuffer', 'X', 'Y', 'R', 'P', 'buffer_SR',
                 'buffer_acq_mode', 'buffer_trig_mode', 'buffer_npts']

# Resistor to calculate current
resistor = 84.5  # Ohm


# A queue to process magnetism related tasks
# Such as adjusting equipment and taking measurements
class MagnetismQueue(BaseQueueClass):
    def __init__(self, socket_client):
        super().__init__(socket_client)

        # Setup stations and connect to the instruments
        self.station = magnetism_station.get_station()
        self.dvm = self.station.components['dvm']
        self.signal_gen = self.station.components['signal_gen']
        self.lockin = self.station.components['lockin']
        self.magnet_ps = self.station.components['magnet_ps']

        # Turn on the signal generator (0.5 volts peak to peak)
        self.configure_n9310a({'amplitude': 0.5, 'frequency': 1000})

        # Setup the oscilloscope
        self.configure_oscilloscope({
            'ch1': {'state': 'ON', 'scale': 0.01, 'position': 0},
            'ch2': {'state': 'OFF'},
            'trigger': {
                'trigger_type': 'EDGE',
                'trigger_source': 'CH1',
                'trigger_level': 0.0
            },
            'horizontal_scale': 100e-5
        })

        # Register queue processors
        self.register_queue_processor('get_sr830_config', self.get_sr830_config)
        self.register_queue_processor('get_n9310a_config', self.get_n9310a_config)
        self.register_queue_processor('get_oscilloscope_config', self.get_oscilloscope_config)
        self.register_queue_processor('get_magnet_trace', self.get_magnet_trace)
        self.register_queue_processor('process_next_step', self.process_next_step)
        self.register_queue_processor('set_oscilloscope_config', self.set_oscilloscope_config)
        self.register_queue_processor('set_sr830_config', self.set_sr830_config)
        self.register_queue_processor('set_magnet_config', self.set_magnet_config)
        self.register_queue_processor('set_n9310a_config', self.set_n9310a_config)
        self.register_queue_processor('get_dc_field', self.get_dc_field)

    @property
    def queue_name(self):
        return 'MagnetismQueue'

    async def get_sr830_config(self, queue, name, task):
        # Empty dict to store results
        config = {}

        # Get all the config params
        for cp in lockin_params:
            config[cp] = self.lockin[cp].get()

        self.socket_client.send_lockin_config(config)

    async def get_oscilloscope_config(self, queue, name, task):
        # Grab the config parameters
        config = {
            'ch1': {
                'state': self.dvm.channels[0].state.get(),
                'scale': self.dvm.channels[0].scale.get(),
                'position': self.dvm.channels[0].position.get()
            },
            'ch2': {
                'state': self.dvm.channels[1].state.get(),
                'scale': self.dvm.channels[1].scale.get(),
                'position': self.dvm.channels[1].position.get()
            },
            'trigger': {
                'trigger_type': self.dvm.trigger_type.get(),
                'trigger_source': self.dvm.trigger_source.get(),
                'trigger_level': self.dvm.trigger_level.get()
            },
            'horizontal_scale': self.dvm.horizontal_scale.get()
        }

        # Send it to the server
        await self.socket_client.send_oscope_config(config)

        # And return it to the requester
        return config

    async def get_n9310a_config(self, queue, name, task):
        # Collect the data from the device
        config = {
            'amplitude': self.signal_gen.LFOutputAmplitude.get(),
            'frequency': self.signal_gen.LFOutputFrequency.get()
        }

        # Send the configuration back
        await self.socket_client.send_n9310a_config(config)

        # Return it to the requester
        return config

    # Gets a trace from the oscilloscope and creates a magnetism trace
    async def get_magnet_trace(self, queue, name, task):
        # Get a trace from the oscilloscope
        # We start by forcing a trigger to prepare the scope
        self.dvm.force_trigger()

        # Then we wait for the data to arrive
        await asyncio.sleep(10 * self.dvm.horizontal_scale.get_latest())

        # Now we prepare the data
        self.dvm.channels[0].curvedata.prepare_curvedata()

        # And we get the trace
        magnetism_state['magnet_trace'] = self.dvm.channels[0].curvedata.get() / resistor

        # Compute the times
        magnetism_state['magnet_trace_times'] = np.arange(0.0, 10 * self.dvm.horizontal_scale.get_latest(),
                                                          (10 * self.dvm.horizontal_scale.get_latest()) / len(
                                                              magnetism_state['magnet_trace']))

        # Send the results to the client
        await self.get_latest_rms_of_magnet_trace(queue, name, task)
        await self.get_latest_magnet_trace(queue, name, task)

        # Return the results to the requester (used for measurements)
        return magnetism_state['magnet_trace']

    async def get_latest_magnet_trace(self, queue, name, task):
        # Send the data to the client
        # We only send every tenth datapoint here
        # It seems excessive to send 4096 datapoints
        await self.socket_client.send_magnet_trace(magnetism_state['magnet_trace_times'][::10],
                                                   magnetism_state['magnet_trace'][::10])

    async def get_latest_rms_of_magnet_trace(self, queue, name, task):
        # Compute the RMS value of the trace, and send it to the client
        await self.socket_client.send_magnet_rms(np.sqrt(np.mean(magnetism_state['magnet_trace'] ** 2.)))

    async def get_dc_field(self, queue, name, task):
        # Get the DC field
        dc_field = self.magnet_ps.MagneticField.get()

        # Send the DC field to the browser
        await self.socket_client.send_dc_field(dc_field)

        # Return it for the process next step method
        return dc_field

    async def get_sr830_trace(self, queue, name, task):
        # Clear the buffer
        self.lockin.buffer_reset()

        # Start filling the buffer at the sample rate
        self.lockin.buffer_start()

        # Compute the time to wait
        buffersize = task['step']['sr830_buffersize']
        sleep_time = buffersize / task['step']['sr830_frequency']

        # Add some extra time to ensure it has enough time to get all the datapoints
        # We want to either add 1 second or double the time, whichever is smallest
        sleep_time += np.minimum(sleep_time, 1)

        # Wait for enough points to gather
        await asyncio.sleep(sleep_time)

        # Stop filling the buffers
        self.lockin.buffer_pause()

        # Prepare the buffers
        self.lockin.ch1_databuffer.prepare_buffer_readout()
        self.lockin.ch2_databuffer.prepare_buffer_readout()

        # Return the data (cut to the buffer size)
        return [self.lockin.ch1_databuffer.get()[:buffersize],
                self.lockin.ch2_databuffer.get()[:buffersize]]

    async def process_next_step(self, queue, name, task):
        # We get the step
        step = task['step']
        magnetism_state['next_step'] = step

        # Wait until the current step is done
        # Sleep 1 second at a time
        while not magnetism_state['current_step']['step_done']:
            await asyncio.sleep(1)

        # Set the next step to the current step
        magnetism_state['current_step'] = step

        # Alert the user to what is happening
        print('processing next step')

        # Close the old datafile if necessary
        if (magnetism_state['experiment_file_id'] != step['experiment_configuration_id']
                and magnetism_state['experiment_file'] is not None):
            magnetism_state['experiment_file'].close()
            magnetism_state['experiment_file'] = None

        # Ensure we have an open datafile
        if magnetism_state['experiment_file'] is None:
            # Start by updating the id we're working on
            magnetism_state['experiment_file_id'] = step['experiment_configuration_id']

            # Ensure we have a folder to place the data in
            if not os.path.exists('data'):
                os.makedirs('data')

            # Open the file
            fp = f'data/magnetism_data_experiment_{magnetism_state["experiment_file_id"]}.h5'
            magnetism_state['experiment_file'] = pd.HDFStore(fp)

        # Set the magentic field
        await self.set_magnet_config(queue, name, {'config': {
            'magnet_field': step['magnet_field']
        }})

        # set the signal generator config
        await self.set_n9310a_config(queue, name, {'config': {
            'frequency': step['n9310a_frequency'],
            'amplitude': step['n9310a_amplitude']
        }})

        # set the lock-in amplifier config
        await self.set_sr830_config(queue, name, {'config': {
            'sensitivity': step['sr830_sensitivity'],
            'frequency': step['sr830_frequency'],
            'buffersize': step['sr830_buffersize']
        }})

        # Mark this step as ready
        await self.socket_client.emit('m_set_step_ready', step['id'])

        # Create lists to hold the results
        ac_fields = []
        dc_fields = []
        lockin_amplitudes = []
        lockin_phases = []

        # Do the measurement
        for datapoint_idx in range(step['data_points_per_measurement']):
            # Start by waiting for the system to stabalize
            await asyncio.sleep(step['data_wait_before_measuring'])

            # Get the data concurrently
            raw_data = await asyncio.gather(self.get_magnet_trace(queue, name, task),
                                            self.get_dc_field(queue, name, task),
                                            self.get_sr830_trace(queue, name, task))

            # Sort the data into the lists
            # Compute the rms value of the ac_field strength
            ac_fields.append(np.sqrt(np.mean(raw_data[0] ** 2.)))

            # Add the dc field
            dc_fields.append(raw_data[1])

            # Add the amplitude and phase of the measured signal
            lockin_amplitudes.append(raw_data[2][0])
            lockin_phases.append(raw_data[2][1])

        # Create numpy arrays from lock-in data and flatten them
        lockin_amplitudes_np = np.array(lockin_amplitudes).ravel()
        lockin_phases_np = np.array(lockin_phases).ravel()

        # Create dataframes to prepare for saving
        magnet_field_frame = pd.DataFrame({
            'ac_rms_field': ac_fields,
            'dc_field': dc_fields,
            'step_id': step['id']
        })
        lockin_frame = pd.DataFrame({
            'lockin_amplitude': lockin_amplitudes_np,
            'lockin_phase': lockin_phases_np,
            'step_id': np.ones_like(lockin_amplitudes_np, dtype=int) * step['id']
        })

        # Save the measurement
        magnetism_state['experiment_file'].append(
            'tables/magnetic_field_data',
            magnet_field_frame,
            format='table', data_columns=True
        )
        magnetism_state['experiment_file'].append(
            'tables/lockin_amplifier_data',
            lockin_frame,
            format='table', data_columns=True
        )

        print('saved data to hdf5')

        # Send the measurements to the server
        # await self.socket_client.emit('m_got_step_results', {
        #     'ac_rms_field': ac_fields,
        #     'dc_field': dc_fields,
        #     'lockin_amplitude': get_mean_from_list_of_arrays(lockin_amplitudes),
        #     'lockin_phase': get_mean_from_list_of_arrays(lockin_phases),
        #     'step_id': step['id']
        # })

        # Test not sending data for stability
        await self.socket_client.emit('m_got_step_results', {
            'ac_rms_field': [],
            'dc_field': [],
            'lockin_amplitude': [],
            'lockin_phase': [],
            'step_id': step['id']
        })

        # Then we mark it as done
        await self.socket_client.emit('mark_step_as_done', step)
        magnetism_state['current_step']['step_done'] = True

    def configure_oscilloscope(self, config):
        # Setup the oscilloscope
        # Start by clearing the message queue
        self.dvm.clear_message_queue()

        # set the horizontal scale
        if 'horizontal_scale' in config:
            self.dvm.horizontal_scale.set(config['horizontal_scale'])

        # Configure channels
        for ch_i in range(1, 3):
            if 'ch' + str(ch_i) in config:
                # First we grab the config
                ch = config['ch' + str(ch_i)]

                # We set the on/off state (by typing 'ON' or 'OFF' into the parameter)
                if 'state' in ch:
                    self.dvm.channels[ch_i - 1].state(ch['state'])

                # We set the scale in volts per division
                if 'scale' in ch:
                    self.dvm.channels[ch_i - 1].scale.set(ch['scale'])  # V/div

                # We set the position by a fraction of the divisions
                if 'position' in ch:
                    self.dvm.channels[ch_i - 1].position.set(ch['position'])  # divisions

        # Configure the trigger
        if 'trigger' in config:
            # Configure trigger type
            if 'trigger_type' in config['trigger']:
                self.dvm.trigger_type.set(config['trigger']['trigger_type'])

            # Configure trigger source
            if 'trigger_source' in config['trigger']:
                self.dvm.trigger_source.set(config['trigger']['trigger_source'])

            # Configure trigger level
            if 'trigger_level' in config['trigger']:
                self.dvm.trigger_level.set(config['trigger']['trigger_level'])

    async def set_oscilloscope_config(self, queue, name, task):
        # Call the configure function with the configuration
        self.configure_oscilloscope(task['config'])

    async def set_sr830_config(self, queue, name, task):
        # Grab the config
        config = task['config']

        # Reset any ratios
        self.lockin.ch1_ratio('none')
        self.lockin.ch2_ratio('none')

        # Set the sensitivity
        self.lockin.sensitivity.set(config['sensitivity'])

        # Set the buffer frequency
        self.lockin.buffer_SR(config['frequency'])

        # Set the remaining config parameters
        for cp in lockin_params:
            if cp in config:
                self.lockin[cp].set(config[cp])

    async def set_magnet_config(self, queue, name, task):
        # We can only set the magnetic field, so we set that
        if 'magnet_field' in task['config']:
            old_field = self.magnet_ps.MagneticField.get()
            new_field = task['config']['magnet_field']

            # If there is not at least a 1% difference in the fields, we don't do anything
            if not math.isclose(old_field, new_field, abs_tol=1e-4, rel_tol=0.01):
                self.magnet_ps.MagneticField.set(new_field)

    def configure_n9310a(self, config):
        # Turn on the signal generator
        self.signal_gen.LFOutputState.set(1)

        # Set the output amplitude
        if 'amplitude' in config:
            self.signal_gen.LFOutputAmplitude.set(config['amplitude'])

        # Set the output frequency
        if 'frequency' in config:
            self.signal_gen.LFOutputFrequency.set(config['frequency'])

    async def set_n9310a_config(self, queue, name, task):
        # Call the configuration method with the config
        self.configure_n9310a(task['config'])


# Create the class containing the namespace for this client
# Pretty much just appends to a queue
class MagnetismClientNamespace(BaseClientNamespace):
    def __init__(self, namespace):
        # Setup the baseclient
        super().__init__(MagnetismQueue, namespace)

        # Set the client type
        self.client_type = 'magnetism'

    async def background_job(self):
        while True:
            await asyncio.sleep(5)
            await self.on_m_get_magnet_trace()

    """#### GET methods ####"""
    async def on_m_get_sr830_config(self):
        await self.append_to_queue({'function_name': 'get_sr830_config'})

    async def on_m_get_oscilloscope_config(self):
        await self.append_to_queue({'function_name': 'get_get_oscilloscope_config'})

    async def on_m_get_n9310a_config(self):
        await self.append_to_queue({'function_name': 'get_n9310a_config'})

    async def on_m_get_magnet_config(self):
        await self.append_to_queue({'function_name': 'get_magnet_config'})

    async def on_m_get_magnet_state(self):
        await self.append_to_queue({'function_name': 'get_magnet_state'})

    async def on_m_get_latest_datapoint(self):
        await self.append_to_queue({'function_name': 'get_latest_datapoint'})

    async def on_m_get_magnet_trace(self):
        await self.append_to_queue({'function_name': 'get_magnet_trace'})

    async def on_m_get_dc_field(self):
        await self.append_to_queue({'function_name': 'get_dc_field'})

    """#### SET methods ####"""
    async def on_m_next_step(self, step):
        await self.append_to_queue({'function_name': 'process_next_step', 'step': step})

    """#### CONFIG methods ####"""
    async def on_m_config_set_oscilloscope_config(self, config):
        await self.append_to_queue({'function_name': 'set_oscilloscope_config', 'config': config})

    async def on_m_config_set_sr830_config(self, config):
        await self.append_to_queue({'function_name': 'set_sr830_config', 'config': config})

    async def on_m_config_set_magnet_config(self, config):
        await self.append_to_queue({'function_name': 'set_magnet_config', 'config': config})

    async def on_m_config_set_n9310a_config(self, config):
        print('got signal config')
        await self.append_to_queue({'function_name': 'set_n9310a_config', 'config': config})

    """ #### SEND METHODS ###"""
    async def send_magnet_trace(self, times, trace):
        await self.emit('m_got_magnet_trace', [list(times), list(trace)])

    async def send_magnet_rms(self, rms):
        await self.emit('m_got_magnet_rms', float(rms))

    async def send_lockin_config(self, config):
        await self.emit('m_got_lockin_config', config)

    async def send_dc_field(self, dc_field):
        await self.emit('m_got_dc_field', dc_field)

    async def send_n9310a_config(self, config):
        await self.emit('m_got_n9310a_config', config)

    async def send_oscope_config(self, config):
        await self.emit('m_got_oscope_config', config)


if __name__ == '__main__':
    asyncio.run(main(MagnetismClientNamespace, '/magnetism'))
