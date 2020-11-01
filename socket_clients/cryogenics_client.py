# Import asyncio to get event loop
import asyncio

# Import the base namespace, contains shared methods and information
from baseclient import BaseClientNamespace, BaseQueueClass, main


class CryoQueue(BaseQueueClass):
    def __init__(self, socket_client):
        super().__init__(socket_client)

        # Register queue processors
        self.register_queue_processor('test_queue', self.test_queue)
        self.register_queue_processor('configure_avs47b', self.configure_avs47b)
        self.register_queue_processor('get_temperatures', self.get_temperatures)
        self.register_queue_processor('start_cooling', self.start_cooling)
        self.register_queue_processor('get_mck_state', self.get_mck_state)

    @property
    def queue_name(self):
        return 'CryoQueue'

    async def configure_avs47b(self, queue, name, task):
        config = task['config']
        await asyncio.sleep(1)
        print('configuring avs47b with config:', config)

    async def get_temperatures(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting temperatures')

    async def get_mck_state(self, queue, name, task):
        await asyncio.sleep(1)
        print('getting the mck state')

    async def start_cooling(self, queue, name, task):
        await asyncio.sleep(1)
        print('going to start cooling')

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

    async def on_test_queue(self):
        await self.append_to_queue({'function_name': 'test_queue'})

    async def on_c_config_start_cooling(self):
        await self.append_to_queue({'function_name': 'start_cooling'})

    async def on_c_config_avs47b(self, config):
        await self.append_to_queue({'function_name': 'configure_avs47b', 'config': config})

    async def on_c_get_temperatures(self):
        await self.append_to_queue({'function_name': 'get_temperatures'})

    async def on_c_get_mck_state(self):
        await self.append_to_queue({'function_name': 'get_mck_state'})


if __name__ == '__main__':
    asyncio.run(main(CryoClientNamespace, '/cryo'))
