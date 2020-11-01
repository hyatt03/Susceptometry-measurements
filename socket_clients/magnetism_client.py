# Import asyncio to get event loop
import asyncio

# Import the base namespace, contains shared methods and information
from baseclient import BaseClientNamespace, BaseQueueClass, main


class MagnetismQueue(BaseQueueClass):
    def __init__(self, magnetism_client):
        super().__init__(magnetism_client)

        # Set the queue name
        self.queue_name = 'MagnetismQueue'

    # Defines the worker used in the queue
    async def worker(self, name, queue):
        while True:
            # Get an objective
            task = await queue.get()

            # Alert the main thread
            print('worker', name, 'got task', task)

            # Execute the task
            await asyncio.sleep(1)

            # Notify the queue that the "work item" has been processed.
            queue.task_done()


# Create the class containing the namespace for this client
class MagnetismClientNamespace(BaseClientNamespace):
    def __init__(self, namespace):
        super().__init__(MagnetismQueue, namespace)
        self.client_type = 'magnetism'

    async def on_test_queue(self):
        print('got event test queue')
        await self.append_to_queue(1234)


if __name__ == '__main__':
    asyncio.run(main(MagnetismClientNamespace, '/magnetism'))

