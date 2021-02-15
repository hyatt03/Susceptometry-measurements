# Import asyncio to get event loop
import asyncio

# get numpy
import numpy as np

# import pandas to support HDF5
import pandas as pd

# Import time module for startup reference, and import deque to store temperatures and pressures
import time, sys, os
from collections import deque

# Add top level packages to path
sys.path.append(os.path.dirname(__file__) + '/..')

# Import the base namespace, contains shared methods and information
from baseclient import BaseClientNamespace, BaseQueueClass, main

# Import cryogenics station to collect data
from stations import cryogenics_station

# Experiments are naturally stateful, and we must remember some things
experiment_state = {
    'temperatures': deque(maxlen=20),  # initialize a double ended queues
    'pressures': deque(maxlen=20),
    'startup_time': time.time(),
    'current_step': {'step_done': True},
    'next_step': {},
    'experiment_file': None,
    'experiment_file_id': None,
    'step_ready_for_measurement': None
}


# We have a class that creates a queue so we can expect things to happen in a specific order
class CryoQueue(BaseQueueClass):
    def __init__(self, socket_client):
        super().__init__(socket_client)

        # Setup stations and connect to the instruments
        self.station = cryogenics_station.get_station()
        self.ghs = self.station.components['ghs']
        self.tcs = self.station.components['tcs']
        self.resistance_bridge = self.station.components['resistance_bridge']

        # Register queue processors
        self.register_queue_processor('test_queue', self.test_queue)
        self.register_queue_processor('configure_avs47b', self.configure_avs47b)
        self.register_queue_processor('get_temperatures', self.get_temperatures)
        self.register_queue_processor('get_temperature_trace', self.get_temperature_trace)
        self.register_queue_processor('update_temperatures', self.update_temperatures)
        self.register_queue_processor('get_pressures', self.get_pressures)
        self.register_queue_processor('get_pressure_trace', self.get_pressure_trace)
        self.register_queue_processor('update_pressures', self.update_pressures)
        self.register_queue_processor('start_cooling', self.start_cooling)
        self.register_queue_processor('get_mck_state', self.get_mck_state)
        self.register_queue_processor('process_next_step', self.process_next_step)

    @property
    def queue_name(self):
        return 'CryoQueue'

    # Queue task to configure the avs47b
    async def configure_avs47b(self, queue, name, task):
        config = task['config']
        await asyncio.sleep(1)
        print('configuring avs47b with config:', config)

    async def get_updated_temperatures(self, queue, name, task):
        # Get temperatures
        temperatures = {
            't_upper_hex': self.resistance_bridge.query_for_temperature(0)[1],
            't_lower_hex': self.resistance_bridge.query_for_temperature(1)[1],
            't_he_pot': self.resistance_bridge.query_for_temperature(2)[1],
            't_1st_stage': self.resistance_bridge.query_for_temperature(3)[1],
            't_2nd_stage': self.resistance_bridge.query_for_temperature(4)[1],
            't_inner_coil': self.resistance_bridge.query_for_temperature(5)[1],
            't_outer_coil': self.resistance_bridge.query_for_temperature(6)[1],
            't_switch': self.resistance_bridge.query_for_temperature(7)[1],
            't_he_pot_2': self.resistance_bridge.query_for_temperature(8)[1],
            'timestamp': time.time() - experiment_state['startup_time'],
            'started': experiment_state['startup_time']
        }

        # Append the updated temperatures to the state
        experiment_state['temperatures'].append(temperatures)

        # And return them
        return temperatures

    # Queue task to retrieve temperatures
    async def update_temperatures(self, queue, name, task):
        # Update the temperatures
        await self.get_updated_temperatures(queue, name, task)

        # Send them to the server
        await self.get_temperatures(queue, name, task)

    async def get_updated_pressures(self, queue, name, task):
        # Query the frontpanel for updated pressures
        self.ghs.get_all_params()

        # Update the pressures dict
        experiment_state['pressures'].append({
            'p_1': self.ghs.pressure_p1.get_latest(),
            'p_2': self.ghs.pressure_p2.get_latest(),
            'p_3': self.ghs.pressure_p3.get_latest(),
            'p_4': self.ghs.pressure_p4.get_latest(),
            'p_5': self.ghs.pressure_p5.get_latest(),
            'p_6': self.ghs.pressure_p6.get_latest(),
            'p_7': self.ghs.pressure_p7.get_latest(),
            'p_8': self.ghs.pressure_p8.get_latest(),
            'timestamp': time.time() - experiment_state['startup_time'],
            'started': experiment_state['startup_time']
        })

        # Return the updated state
        return experiment_state['pressures'][-1]

    # Queue task to retrieve pressures from the front panel
    async def update_pressures(self, queue, name, task):
        # Update the pressures
        await self.get_updated_pressures(queue, name, task)

        # And send them to the server
        await self.get_pressures(queue, name, task)

    # Send the temperatures to the server
    async def get_temperatures(self, queue, name, task):
        await self.socket_client.send_temperatures(experiment_state['temperatures'][-1])

    # Send a trace containing last 20 temperature measurements
    async def get_temperature_trace(self, queue, name, task):
        await self.socket_client.send_temperature_trace(experiment_state['temperatures'])

    # Send the latest pressures
    async def get_pressures(self, queue, name, task):
        await self.socket_client.send_pressures(experiment_state['pressures'][-1])

    # Send a trace containing the last 20 pressure measurements
    async def get_pressure_trace(self, queue, name, task):
        await self.socket_client.send_pressure_trace(experiment_state['pressures'])

    # Queue task to get the mck state
    async def get_mck_state(self, queue, name, task):
        # Update the status of the TCS
        self.tcs.get_all_params()

    # Queue task to cool the system down
    async def start_cooling(self, queue, name, task):
        await asyncio.sleep(1)
        print('going to start cooling')

    # Process the next step of the current experiment
    async def process_next_step(self, queue, name, task):
        # We get the step
        step = task['step']
        experiment_state['next_step'] = step

        # Wait until the current step is done
        # Sleep 1 second at a time
        while not experiment_state['current_step']['step_done']:
            await asyncio.sleep(1)

        # Set the next step to the current step
        experiment_state['current_step'] = step

        # Alert the user to what is happening
        print('processing next step')

        # Close the old datafile if necessary
        if experiment_state['experiment_file_id'] != step['experiment_configuration_id'] and experiment_state['experiment_file'] is not None:
            experiment_state['experiment_file'].close()
            experiment_state['experiment_file'] = None

        # Ensure we have an open datafile
        if experiment_state['experiment_file'] is None:
            # Start by updating the id we're working on
            experiment_state['experiment_file_id'] = step['experiment_configuration_id']

            # Open the file
            experiment_state['experiment_file'] = pd.HDFStore(f'data/cryogenics_data_experiment_{experiment_state["experiment_file_id"]}.h5')

        # Wait for the magnetism station to be ready for measurement
        # Sleep 0.1 seconds at a time
        while experiment_state['step_ready_for_measurement'] != step['id']:
            await asyncio.sleep(0.1)

        # Now the stations should be pretty syncronized
        # And we can begin measuring
        # Create dictionaries to hold the results
        pressures = {'step_id': step['id']}
        temperatures = {'step_id': step['id']}

        # Do the measurement
        for datapoint_idx in range(step['data_points_per_measurement']):            
            # Start by waiting for the system to stabalize
            await asyncio.sleep(step['data_wait_before_measuring'])

            # Get the data concurrently
            raw_data = await asyncio.gather(self.get_updated_pressures(queue, name, task), 
                                            self.get_updated_temperatures(queue, name, task))

            # Sort the data into the lists
            # Append pressures to each list
            for p_label in raw_data[0].keys():
                if p_label not in pressures.keys():
                    pressures[p_label] = []
                pressures[p_label].append(raw_data[0][p_label])

            # do the same for temperatures
            for t_label in raw_data[1].keys():
                if t_label not in temperatures.keys():
                    temperatures[t_label] = []
                temperatures[t_label].append(raw_data[1][t_label])

        # We're done measuring, so now we save the data
        # Create dataframes to prepare for saving
        pressures_frame = pd.DataFrame(pressures)
        temperatures_frame = pd.DataFrame(temperatures)

        # Save the measurement
        experiment_state['experiment_file'].append(
            'tables/pressure_data', 
            pressures_frame, 
            format='table', data_columns=True
        )
        experiment_state['experiment_file'].append(
            'tables/temperature_data', 
            temperatures_frame, 
            format='table', data_columns=True
        )

        # Next we send the results to the server
        await self.socket_client.emit('c_got_step_results', {
            'pressures': pressures, 
            'temperatures': temperatures,
            'step_id': step['id']
        })

        # Then we mark it as done
        await self.socket_client.emit('mark_step_as_done', step)
        experiment_state['current_step']['step_done'] = True

    # Queue task to test functionality
    async def test_queue(self, queue, name, task):
        # Alert that we received a test signal
        print('got test signal')
        await asyncio.sleep(1)

        # Print out task info
        print('queue:', queue)
        print('name:', name)
        print('task:', task)


# Create the class containing the namespace for this client
class CryoClientNamespace(BaseClientNamespace):
    def __init__(self, namespace):
        # Setup the baseclient
        super().__init__(CryoQueue, namespace)

        # Set the client type
        self.client_type = 'cryo'

    async def background_job(self):
        while True:
            await self.append_to_queue({'function_name': 'update_temperatures'})
            await self.append_to_queue({'function_name': 'update_pressures'})
            await self.append_to_queue({'function_name': 'get_mck_state'})
            await asyncio.sleep(5)

    # Received when testing should start
    async def on_test_queue(self):
        await self.append_to_queue({'function_name': 'test_queue'})

    # Received when cooling should start
    async def on_c_config_start_cooling(self):
        await self.append_to_queue({'function_name': 'start_cooling'})

    # Received when config for avs47b should be updated
    async def on_c_config_avs47b(self, config):
        await self.append_to_queue({'function_name': 'configure_avs47b', 'config': config})

    # Received when new temperatures are wanted
    async def on_c_get_temperatures(self):
        await self.append_to_queue({'function_name': 'get_temperatures'})

    async def on_c_get_temperature_trace(self):
        await self.append_to_queue({'function_name': 'get_temperature_trace'})

    async def on_c_get_pressures(self):
        await self.append_to_queue({'function_name': 'get_pressures'})

    async def on_c_get_pressure_trace(self):
        await self.append_to_queue({'function_name': 'get_pressure_trace'})

    # Received when the mck state is desired
    async def on_c_get_mck_state(self):
        await self.append_to_queue({'function_name': 'get_mck_state'})

    # Event sent when temperatures should be updated
    async def send_temperatures(self, temperatures):
        await self.emit('c_got_temperatures', temperatures)

    async def send_temperature_trace(self, temperature_trace):
        await self.emit('c_got_temperature_trace', list(temperature_trace))

    async def send_pressures(self, pressures):
        await self.emit('c_got_pressures', pressures)

    async def send_pressure_trace(self, pressure_trace):
        await self.emit('c_got_pressure_trace', list(pressure_trace))

    # Event received when server has a new step for us
    async def on_c_next_step(self, step):
        await self.append_to_queue({'function_name': 'process_next_step', 'step': step})

    # Event we receive when the magnetism station is ready for measurements
    # Process next step polls for this to be ready
    async def on_c_step_ready_for_measurement(self, step_id):
        experiment_state['step_ready_for_measurement'] = step_id


if __name__ == '__main__':
    asyncio.run(main(CryoClientNamespace, '/cryo'))
