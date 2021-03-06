# Import asyncio to get event loop
import asyncio

# get numpy
import numpy as np

# Get OS to use environment variables
import os

# import pandas to support HDF5
import pandas as pd

# Import time module for startup reference, and import deque to store temperatures and pressures
import time, sys, os
from collections import deque

# Add top level packages to path
sys.path.append(os.path.dirname(__file__) + '/..')

# Import the base namespace, contains shared methods and information
from baseclient import BaseClientNamespace, BaseQueueClass, main

if os.getenv('USE_FAKE_STATIONS') is None:
    # Import cryogenics station to collect data
    from stations import cryogenics_station
else:
    # Import the mocked magnetism station
    from stations.fake_stations import cryogenics_station_fake as cryogenics_station

# Experiments are naturally stateful, and we must remember some things
experiment_state = {
    'temperatures': deque(maxlen=50),  # initialize a double ended queues
    'pressures': deque(maxlen=50),
    'startup_time': time.time(),
    'current_step': {'step_done': True},
    'next_step': {},
    'experiment_file': None,
    'experiment_file_id': None,
    'step_ready_for_measurement': None
}


# We have a class that creates a queue so we can expect things to happen in a specific order
class CryoQueue(BaseQueueClass):
    # Add a lock to wait for query on resistance to finish
    running_query_on_resistance = False

    # Add adjustable delay parameter for the resistance bridge (seconds)
    picowatt_delay = 3

    def __init__(self, socket_client):
        super().__init__(socket_client)

        # Setup stations and connect to the instruments
        self.station = cryogenics_station.get_station()
        self.ghs = self.station.components['ghs']
        self.tcs = self.station.components['tcs']
        self.resistance_bridge = self.station.components['resistance_bridge']
        self.dmm = self.station.components['dmm']
        self.maxigauge = self.station.components['maxigauge']

        # Register queue processors
        self.register_queue_processor('configure_avs47b', self.configure_avs47b)
        self.register_queue_processor('get_temperatures', self.get_temperatures)
        self.register_queue_processor('get_temperature_trace', self.get_temperature_trace)
        self.register_queue_processor('update_temperatures', self.update_temperatures)
        self.register_queue_processor('get_pressures', self.get_pressures)
        self.register_queue_processor('get_pressure_trace', self.get_pressure_trace)
        self.register_queue_processor('get_fp_status', self.get_fp_status)
        self.register_queue_processor('update_pressures', self.update_pressures)
        self.register_queue_processor('start_cooling', self.start_cooling)
        self.register_queue_processor('get_mck_state', self.get_mck_state)
        self.register_queue_processor('process_next_step', self.process_next_step)
        self.register_queue_processor('get_avs47b_config', self.get_avs47b_config)
        self.register_queue_processor('run_background_jobs', self.run_background_jobs)
        self.register_queue_processor('start_circulation', self.start_circulation)

    @property
    def queue_name(self):
        return 'CryoQueue'

    # Queue task to configure the avs47b
    async def configure_avs47b(self, queue, name, task):
        # Grab the config
        config = task['config']

        # Create a list of accepted parameters
        params = ['InputMode', 'MultiplexerChannel', 'Range', 'Excitation', 'ReferenceVoltage', 'ReferenceSource', 'Magnification', 'Display']

        # Check if the parameters are in the config dict and change the ones that are
        for p in params:
            if p in config:
                self.resistance_bridge[p].set(config[p])

        # First we update the bridge to reflect the setting we just set
        # The bools are remote, save config, and return decoded
        self.resistance_bridge.send_config(True, False, False)

        # Next we update our local config to reflect what the state of the device actually is
        self.resistance_bridge.send_config(True, True, False)

    async def get_avs47b_config(self, queue, name, task):
        self.resistance_bridge.send_config(True, True, False)

        # Create a list of accepted parameters
        params = ['InputMode', 'MultiplexerChannel', 'Range', 'Excitation', 'ReferenceVoltage', 'ReferenceSource',
                  'Magnification', 'Display']

        # Check if the parameters are in the config dict and change the ones that are
        config = {}
        for p in params:
            config[p] = self.resistance_bridge[p].get_latest()

        await self.socket_client.emit('c_avs47b_got_config', config)

    async def get_updated_temperatures(self, queue, name, task):
        # Get temperatures
        scan_data = self.dmm.scan_channels()
        t_still = await self.query_resistance_bridge_for_temperature(1)
        t_mixing_chamber_1 = await self.query_resistance_bridge_for_temperature(2)
        t_mixing_chamber_2 = await self.query_resistance_bridge_for_temperature(3)

        # Setup the dict containing the temperatures
        temperatures = {
            't_upper_hex': scan_data['Upper HEx'],
            't_lower_hex': scan_data['Lower HEx'],
            't_he_pot': scan_data['He Pot CCS'],
            't_1st_stage': scan_data['1st stage'],
            't_2nd_stage': scan_data['2nd stage'],
            't_inner_coil': scan_data['Inner Coil'],
            't_outer_coil': scan_data['Outer Coil'],
            't_switch': scan_data['Switch'],
            't_he_pot_2': scan_data['He Pot'],
            't_still': t_still,
            't_mixing_chamber_1': t_mixing_chamber_1,
            't_mixing_chamber_2': t_mixing_chamber_2,
            'timestamp': time.time() - experiment_state['startup_time'],
            'started': experiment_state['startup_time']
        }

        # Append the updated temperatures to the state
        experiment_state['temperatures'].append(temperatures)

        # And return them
        return temperatures

    async def query_resistance_bridge_for_temperature(self, channel):
        # Wait until lock is released
        while self.running_query_on_resistance:
            await asyncio.sleep(0.2)

        # Lock the bridge to this query
        self.running_query_on_resistance = True

        # First we setup the query
        self.resistance_bridge.setup_query_for_resistance(channel)

        # Next we wait for the signal to become available
        resistance = 0
        for i in range(20):
            # Sleep while the measurement populates
            await asyncio.sleep(self.picowatt_delay)

            # Get the resistance
            m_complete, resistance, ch_out = self.resistance_bridge.query_for_resistance()

            print('got results from ch', ch_out, 'when querying ch',
                  channel, 'the resistance is', resistance, 'm', m_complete)

            # Return the resistance when the measurement is complete
            if m_complete:
                break

        # Unlock the bridge
        self.running_query_on_resistance = False

        # Convert the resistance to temperature
        return self.resistance_bridge.convert_to_temperature(channel, resistance)

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
            'p_9': self.maxigauge.get_pressure(5)[1],
            'p_10': self.maxigauge.get_pressure(6)[1],
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
        print('Cooling by script is currently disabled')

    # Queue task to send the frontpanel status and ack to the frontend
    async def get_fp_status(self, queue, name, task):
        await self.socket_client.send_fp_status({
            'ack': self.ghs.latest_ack.get_latest(),
            'status': self.ghs.status.get_latest()
        })

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
        print('processing next step for experiment:', step['experiment_configuration_id'])

        # Close the old datafile if necessary
        if experiment_state['experiment_file_id'] != step['experiment_configuration_id'] and \
                experiment_state['experiment_file'] is not None:
            experiment_state['experiment_file'].close()
            experiment_state['experiment_file'] = None

        # Ensure we have an open datafile
        if experiment_state['experiment_file'] is None:
            # Start by updating the id we're working on
            experiment_state['experiment_file_id'] = step['experiment_configuration_id']

            # Ensure we have a folder to place the data in
            if not os.path.exists('data'):
                os.makedirs('data')

            # Open the file
            experiment_state['experiment_file'] = pd.HDFStore(
                f'data/cryogenics_data_experiment_{experiment_state["experiment_file_id"]}.h5'
            )

        # Be sure to ask the server if the step is ready
        await self.socket_client.is_step_ready(step['id'])

        print('Requested is step ready, waiting for response')

        # Wait for the magnetism station to be ready for measurement
        # Sleep 0.5 seconds at a time
        while experiment_state['step_ready_for_measurement'] != step['id']:
            await asyncio.sleep(0.5)

        print('Got step is ready signal, doing measurement.')

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

            # Send it to the client, so the updates feel like they're incoming
            await asyncio.gather(self.get_pressures(queue, name, task), 
                                 self.get_temperatures(queue, name, task))

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

        # Wait a second to let other background tasks run
        await asyncio.sleep(1)

        # Then we mark it as done
        await self.socket_client.emit('mark_step_as_done', step)
        experiment_state['current_step']['step_done'] = True

    async def start_circulation(self, queue, name, task):
        # We start by resetting so we know the state of the system
        # This closes all valves and turns off all pumps
        self.ghs.press_button('reset')

        # Wait between
        await asyncio.sleep(1)

        # Next we start s3 as the backing pump for s1
        self.ghs.press_button('s3')

        # And we let it spin up
        await asyncio.sleep(1)

        # Next we open all the way to the still
        self.ghs.press_button('3')
        self.ghs.press_button('2')
        self.ghs.press_button('0')

        # And we open the gate valve
        self.ghs.press_button('gate-valve-18')

        # Now we wait until the pressure is low on P4
        while self.ghs.pressure_p4.get() > 3:
            await asyncio.sleep(0.1)

        # And we turn on the turbopump
        self.ghs.press_button('s1')

        # We now open the first dump
        self.ghs.press_button('10')
        self.ghs.press_button('9')

        # And we wait a little for the pressure to stabalize
        await asyncio.sleep(1)

        # Next we open the trap
        self.ghs.press_button('4')
        self.ghs.press_button('5')

        # And we bypass the compressor and open the final valve
        self.ghs.press_button('bypass')
        self.ghs.press_button('6')

    async def pump_still(self):
        # We start by resetting so we know the state of the system
        # This closes all valves and turns off all pumps
        self.ghs.press_button('reset')

        # Wait for everything to shut down
        await asyncio.sleep(1)

        # We now open the first dump so the pressure has somewhere to go
        self.ghs.press_button('10')
        self.ghs.press_button('9')

        # Next we start s3 as the backing pump for s1
        self.ghs.press_button('s3')

        # And we let it spin up
        await asyncio.sleep(1)

        # Next we open all the way to the still
        self.ghs.press_button('3')
        self.ghs.press_button('2')
        self.ghs.press_button('0')

        # Now we wait until the pressure is low on P4
        while self.ghs.pressure_p4.get() > 3:
            await asyncio.sleep(1)

        # And we turn on the turbopump
        self.ghs.press_button('s1')

        # We wait for the turbopump to spin up
        await asyncio.sleep(10)

        # And we open the gate valve
        self.ghs.press_button('gate-valve-18')

    async def pump_ivc_and_still(self):
        # We start by pumping the still
        await self.pump_still()

        # We wait for that a bit
        await asyncio.sleep(5)

        # Then we open to the IVC
        self.ghs.press_button('a10')

    async def run_background_jobs(self, queue, name, task):
        # Get the temperatures
        await self.update_temperatures(queue, name, task)

        # Wait and rerun the job
        await asyncio.sleep(5)
        await self.queue.put({'function_name': 'run_background_jobs'})


# Create the class containing the namespace for this client
class CryoClientNamespace(BaseClientNamespace):
    def __init__(self, namespace):
        # Setup the baseclient
        super().__init__(CryoQueue, namespace)

        # Set the client type
        self.client_type = 'cryo'

    async def background_job(self):
        # Get the picowatt delay from the server
        await self.get_picowatt_delay()

        # Start running the background jobs
        await self.append_to_queue({'function_name': 'run_background_jobs'})

        while True:
            # Get the pressures
            await self.append_to_queue({'function_name': 'update_pressures'})
            await self.append_to_queue({'function_name': 'get_mck_state'})
            
            # Wait
            await asyncio.sleep(5)

    # Received when cooling should start
    async def on_c_config_start_cooling(self):
        await self.append_to_queue({'function_name': 'start_cooling'})

    # Received when front panel status is wanted
    async def on_c_get_frontpanel_status(self):
        await self.append_to_queue({'function_name': 'get_fp_status'})

    async def on_c_get_config_avs47b(self):
        await self.append_to_queue({'function_name': 'get_avs47b_config'})

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

    async def on_c_got_picowatt_delay(self, delay):
        self.my_queue.picowatt_delay = delay

    async def on_c_start_circulation(self):
        print('got start circulation')
        await self.append_to_queue({'function_name': 'start_circulation'})

    async def get_picowatt_delay(self):
        await self.emit('c_get_picowatt_delay')

    # Event sent when temperatures should be updated
    async def send_temperatures(self, temperatures):
        await self.emit('c_got_temperatures', temperatures)

    async def send_temperature_trace(self, temperature_trace):
        await self.emit('c_got_temperature_trace', list(temperature_trace))

    async def send_pressures(self, pressures):
        await self.emit('c_got_pressures', pressures)

    async def send_pressure_trace(self, pressure_trace):
        await self.emit('c_got_pressure_trace', list(pressure_trace))

    async def send_fp_status(self, status):
        await self.emit('c_got_fp_status', status)

    async def is_step_ready(self, step_id):
        await self.emit('c_is_step_ready', step_id)

    # Event received when server has a new step for us
    async def on_c_next_step(self, step):
        await self.append_to_queue({'function_name': 'process_next_step', 'step': step})

    # Event we receive when the magnetism station is ready for measurements
    # Process next step polls for this to be ready
    async def on_c_step_ready_for_measurement(self, step_id):
        experiment_state['step_ready_for_measurement'] = step_id


if __name__ == '__main__':
    asyncio.run(main(CryoClientNamespace, '/cryo'))
