# Import asyncio to get event loop
import asyncio

# Import time and path python packages
import time, sys, os

# Import numpy
import numpy as np

# Import pandas for saving experiment data
import pandas as pd

# Import plotting libraries
import matplotlib.pyplot as plt

# Import qcodes for measurering 
import qcodes as qc
from qcodes.measure import Measure
from qcodes.dataset.plotting import plot_dataset

# Add top level packages to path
sys.path.append(os.path.dirname(__file__) + '/..')

# Import the base namespace, contains shared methods and information
from socket_clients.baseclient import BaseClientNamespace, BaseQueueClass, main

# Import magnetism station to collect data
from stations import magnetism_station

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

        # Turn on the signal generator (0.4 volts peak to peak)
        self.signal_gen.LFOutputState.set(1)
        self.signal_gen.LFOutputAmplitude.set(0.2)
        self.signal_gen.LFOutputFrequency.set(1000)

        # Register queue processors
        self.register_queue_processor('test_queue', self.test_queue)

        self.register_queue_processor('get_sr830_config', self.get_sr830_config)
        self.register_queue_processor('get_n9310a_config', self.get_n9310a_config)
        self.register_queue_processor('get_oscilloscope_config', self.get_oscilloscope_config)
        self.register_queue_processor('get_magnet_config', self.get_magnet_config)
        self.register_queue_processor('get_magnet_state', self.get_magnet_state)
        self.register_queue_processor('get_magnet_trace', self.get_magnet_trace)
        self.register_queue_processor('get_latest_datapoint', self.get_latest_datapoint)

        self.register_queue_processor('process_next_step', self.process_next_step)

        self.register_queue_processor('set_oscilloscope_config', self.set_oscilloscope_config)
        self.register_queue_processor('set_sr830_config', self.set_sr830_config)
        self.register_queue_processor('set_magnet_config', self.set_magnet_config)
        self.register_queue_processor('set_n9310a_config', self.set_n9310a_config)

    @property
    def queue_name(self):
        return 'MagnetismQueue'

    async def test_queue(self, queue, name, task):
        # Alert that we received a test signal
        print('got test signal')
        await asyncio.sleep(1)

        # Print out task info
        print('queue:', queue)
        print('name:', name)
        print('task:', task)

    async def get_sr830_config(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting sr830 config')

    async def get_oscilloscope_config(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting the oscilloscope config')

    async def get_n9310a_config(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting n9310a config')

    async def get_magnet_config(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting magnet config')

    async def get_magnet_state(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting magnet state')

    async def get_latest_datapoint(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting the latest datapoint')

    # Gets a trace from the oscilloscope and creates a magnetism trace
    async def get_magnet_trace(self, queue, name, task):
        # Get a trace from the oscilloscope
        magnetism_state['magnet_trace'] = self.dvm.get_trace(0)

        # Compute the times
        magnetism_state['magnet_trace_times'] = np.arange(0.0, 1, 1/len(magnetism_state['magnet_trace'])) / 100

        # Send the results to the client
        await self.get_latest_rms_of_magnet_trace(queue, name, task)
        await self.get_latest_magnet_trace(queue, name, task)

        # Return the results to the requester (used for measurements)
        return magnetism_state['magnet_trace']

    async def get_latest_magnet_trace(self, queue, name, task):
        # Send the data to the client
        # We only send every tenth datapoint here
        # It seems excessive to send 4096 datapoints
        await self.socket_client.send_magnet_trace(magnetism_state['magnet_trace_times'][::10], magnetism_state['magnet_trace'][::10])

    async def get_latest_rms_of_magnet_trace(self, queue, name, task):
        # Compute the RMS value of the trace, and send it to the client
        await self.socket_client.send_magnet_rms(np.sqrt(np.mean(magnetism_state['magnet_trace']**2.)))

    async def get_dc_field(self, queue, name, task):
        await asyncio.sleep(1)
        return 1.0

    async def get_sr830_trace(self, queue, name, task):
        # Clear the buffer
        self.lockin.buffer_reset()

        # Start filling the buffer at the sample rate
        self.lockin.buffer_start()        

        # Compute the time to wait
        buffersize = task['step']['sr830_buffersize']
        sleep_time = buffersize / task['step']['sr830_frequency']
        sleep_time += np.minimum(sleep_time, 1)  # Add some extra time to ensure it has enough time to get all the datapoints
                                                 # We want to either add 1 second or double the time, whichever is smallest

        # Wait for enough points to gather
        await asyncio.sleep(sleep_time)

        # Stop filling the buffers
        self.lockin.buffer_pause()

        # Dump the buffer of channel 1
        self.lockin.ch1_databuffer.prepare_buffer_readout()
        ch1_meas = Measure(self.lockin.ch1_databuffer)
        ch1_raw_data = ch1_meas.run()

        # Dump the buffer of channel 2
        self.lockin.ch2_databuffer.prepare_buffer_readout()
        ch2_meas = Measure(self.lockin.ch2_databuffer)
        ch2_raw_data = ch2_meas.run()
        
        # Return the data (cut to the buffer size)
        return [ch1_raw_data.lockin_ch1_databuffer[:buffersize], ch2_raw_data.lockin_ch2_databuffer[:buffersize]]

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
        if magnetism_state['experiment_file_id'] != step['experiment_configuration_id'] and magnetism_state['experiment_file'] is not None:
            magnetism_state['experiment_file'].close()
            magnetism_state['experiment_file'] = None

        # Ensure we have an open datafile
        if magnetism_state['experiment_file_id'] is None:
            # Start by updating the id we're working on
            magnetism_state['experiment_file_id'] = step['experiment_configuration_id']

            # Open the file
            magnetism_state['experiment_file'] = pd.HDFStore(f'data/magnetism_data_experiment_{magnetism_state["experiment_file_id"]}.h5')

        # Set the magentic field
        await self.set_magnet_config(queue, name, {'config': {
            'magnet_field': step['magnet_field']
        }})

        # set the signal generator config
        await self.set_n9310a_config(queue, name, {'config': {
            'frequency': step['n9310a_frequency'], 
            'amplitude': step['n9310a_amplitude']
        }})

        # set the oscilloscope config
        await self.set_oscilloscope_config(queue, name, {'config': {
            'resistor': step['oscope_resistor']
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
            ac_fields.append(np.sqrt(np.mean(raw_data[0]**2.)))

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

        # Send the measurements to the server
        await self.socket_client.emit('m_got_step_results', {
            'ac_rms_field': ac_fields, 
            'dc_field': dc_fields,
            'lockin_amplitude': get_mean_from_list_of_arrays(lockin_amplitudes), 
            'lockin_phase': get_mean_from_list_of_arrays(lockin_phases), 
            'step_id': step['id']
        })

        # Then we mark it as done
        await self.socket_client.emit('mark_step_as_done', step)
        magnetism_state['current_step']['step_done'] = True

    async def set_oscilloscope_config(self, queue, name, task):
        config = task['config']
        await asyncio.sleep(1)
        print('setting oscilloscope config')

    async def set_sr830_config(self, queue, name, task):
        config = task['config']

        # Set the displays to show phase and amplitude of the signal
        self.lockin.ch1_display('R')
        self.lockin.ch2_display('Phase')

        # Reset any ratios
        self.lockin.ch1_ratio('none')
        self.lockin.ch2_ratio('none')

        # Set the sensitivity
        self.lockin.sensitivity.set(config['sensitivity'])

        # Set the buffer frequency
        self.lockin.buffer_SR(config['frequency'])

    async def set_magnet_config(self, queue, name, task):
        config = task['config']
        await asyncio.sleep(1)
        print('setting magnet config')

    async def set_n9310a_config(self, queue, name, task):
        config = task['config']
        await asyncio.sleep(1)
        print('setting n9310a config')


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

    async def on_test_queue(self):
        await self.append_to_queue({'function_name': 'test_queue'})

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


if __name__ == '__main__':
    asyncio.run(main(MagnetismClientNamespace, '/magnetism'))

