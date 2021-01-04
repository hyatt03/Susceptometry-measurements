# Import asyncio to get event loop
import asyncio

# Import numpy
import numpy as np
import time

# Import the base namespace, contains shared methods and information
from baseclient import BaseClientNamespace, BaseQueueClass, main

#from stations import magnetism_station

magnetism_state = {
    'magnet_trace': [],
    'magnet_trace_times': [],
    'startup_time': time.time()
}


# A queue to process magnetism related tasks
# Such as adjusting equipment and taking measurements
class MagnetismQueue(BaseQueueClass):
    def __init__(self, socket_client):
        super().__init__(socket_client)

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
        magnetism_state['magnet_trace_times'] = np.arange(0.0, 1, 0.01) / 100
        magnetism_state['magnet_trace'] = np.random.normal(loc=0, scale=0.2, size=100) + \
                                          np.sin(2 * np.pi * 1000 * magnetism_state['magnet_trace_times'])

        await self.get_latest_rms_of_magnet_trace(queue, name, task)
        await self.get_latest_magnet_trace(queue, name, task)

    async def get_latest_magnet_trace(self, queue, name, task):
        await self.socket_client.send_magnet_trace(magnetism_state['magnet_trace_times'], magnetism_state['magnet_trace'])

    async def get_latest_rms_of_magnet_trace(self, queue, name, task):
        await self.socket_client.send_magnet_rms(np.sqrt(np.mean(magnetism_state['magnet_trace']**2.)))

    async def process_next_step(self, queue, name, task):
        # We execute the step
        step = task['step']
        await asyncio.sleep(1)
        print('processing next step')

        # Then we mark it as done
        await self.socket_client.emit('mark_step_as_done', step)

        # Then we ask for the next step
        await self.socket_client.emit('get_next_step')

    async def set_oscilloscope_config(self, queue, name, task):
        config = task['config']
        await asyncio.sleep(1)
        print('setting oscilloscope config')

    async def set_sr830_config(self, queue, name, task):
        config = task['config']
        await asyncio.sleep(1)
        print('setting sr830 config')

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

    def background_job(self):
        pass
        # while True:
        #     self.on_m_get_magnet_trace()
        #     asyncio.sleep(5)

    def on_test_queue(self):
        self.append_to_queue({'function_name': 'test_queue'})

    """#### GET methods ####"""
    def on_m_get_sr830_config(self):
        self.append_to_queue({'function_name': 'get_sr830_config'})

    def on_m_get_oscilloscope_config(self):
        self.append_to_queue({'function_name': 'get_get_oscilloscope_config'})

    def on_m_get_n9310a_config(self):
        self.append_to_queue({'function_name': 'get_n9310a_config'})

    def on_m_get_magnet_config(self):
        self.append_to_queue({'function_name': 'get_magnet_config'})

    def on_m_get_magnet_state(self):
        self.append_to_queue({'function_name': 'get_magnet_state'})

    def on_m_get_latest_datapoint(self):
        self.append_to_queue({'function_name': 'get_latest_datapoint'})

    def on_m_get_magnet_trace(self):
        self.append_to_queue({'function_name': 'get_magnet_trace'})

    """#### SET methods ####"""
    def on_m_set_next_step(self, step):
        self.append_to_queue({'function_name': 'process_next_step', 'step': step})

    """#### CONFIG methods ####"""
    def on_m_config_set_oscilloscope_config(self, config):
        self.append_to_queue({'function_name': 'set_oscilloscope_config', 'config': config})

    def on_m_config_set_sr830_config(self, config):
        self.append_to_queue({'function_name': 'set_sr830_config', 'config': config})

    def on_m_config_set_magnet_config(self, config):
        self.append_to_queue({'function_name': 'set_magnet_config', 'config': config})

    def on_m_config_set_n9310a_config(self, config):
        self.append_to_queue({'function_name': 'set_n9310a_config', 'config': config})

    """ #### SEND METHODS ###"""
    def send_magnet_trace(self, times, trace):
        self.emit('m_got_magnet_trace', [list(times), list(trace)])

    def send_magnet_rms(self, rms):
        self.emit('m_got_magnet_rms', float(rms))


if __name__ == '__main__':
    asyncio.run(main(MagnetismClientNamespace, '/magnetism'))

