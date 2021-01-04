# Import asyncio to get event loop
import asyncio

# get numpy
import numpy as np
import time
from collections import deque

# Import the base namespace, contains shared methods and information
from baseclient import BaseClientNamespace, BaseQueueClass, main

experiment_state = {
    'temperatures': deque(maxlen=20),  # initialize a double ended queues
    'pressures': deque(maxlen=20),
    'startup_time': time.time()
}


class CryoQueue(BaseQueueClass):
    def __init__(self, socket_client):
        super().__init__(socket_client)

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

    @property
    def queue_name(self):
        return 'CryoQueue'

    # Queue task to configure the avs47b
    async def configure_avs47b(self, queue, name, task):
        config = task['config']
        await asyncio.sleep(1)
        print('configuring avs47b with config:', config)

    # Queue task to retrieve temperatures
    async def update_temperatures(self, queue, name, task):
        experiment_state['temperatures'].append({
            't_still': round(float(np.abs(np.random.normal(2.2212))), 4),
            't_1': round(float(np.abs(np.random.normal(2.2212))), 4),
            't_2': round(float(np.abs(np.random.normal(2.2212))), 4),
            't_3': round(float(np.abs(np.random.normal(2.2212))), 4),
            't_4': round(float(np.abs(np.random.normal(2.2212))), 4),
            't_5': round(float(np.abs(np.random.normal(2.2212))), 4),
            't_6': round(float(np.abs(np.random.normal(2.2212))), 4),
            'timestamp': time.time() - experiment_state['startup_time']
        })

        await self.get_temperatures(queue, name, task)

    async def update_pressures(self, queue, name, task):
        experiment_state['pressures'].append({
            'p_1': round(float(np.abs(np.random.normal(2.2212))), 4),
            'p_2': round(float(np.abs(np.random.normal(2.2212))), 4),
            'p_3': round(float(np.abs(np.random.normal(2.2212))), 4),
            'p_4': round(float(np.abs(np.random.normal(2.2212))), 4),
            'p_5': round(float(np.abs(np.random.normal(2.2212))), 4),
            'p_6': round(float(np.abs(np.random.normal(2.2212))), 4),
            'p_7': round(float(np.abs(np.random.normal(2.2212))), 4),
            'p_8': round(float(np.abs(np.random.normal(2.2212))), 4),
            'timestamp': time.time() - experiment_state['startup_time']
        })

        await self.get_pressures(queue, name, task)

    async def get_temperatures(self, queue, name, task):
        await self.socket_client.send_temperatures(experiment_state['temperatures'][-1])

    async def get_temperature_trace(self, queue, name, task):
        await self.socket_client.send_temperature_trace(experiment_state['temperatures'])

    async def get_pressures(self, queue, name, task):
        await self.socket_client.send_pressures(experiment_state['pressures'][-1])

    async def get_pressure_trace(self, queue, name, task):
        await self.socket_client.send_pressure_trace(experiment_state['pressures'])

    # Queue task to get the mck state
    async def get_mck_state(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting the mck state')

    # Queue task to cool the system down
    async def start_cooling(self, queue, name, task):
        await asyncio.sleep(1)
        print('going to start cooling')

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


if __name__ == '__main__':
    asyncio.run(main(CryoClientNamespace, '/cryo'))
