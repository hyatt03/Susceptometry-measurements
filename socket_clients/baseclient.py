# Import socket client, so we can connect to the webserver
import socketio, asyncio

# Import os to get environment variables
import os

# Import uuid to access a machine id
import uuid


class BaseQueueClass():
    n_workers = 2

    def __init__(self, socket_client):
        super().__init__()

        # Setup the socket client
        self.socket_client = socket_client

        # Setup the queue variables
        self.queue = None
        self.worker_instances = []

        # Initialize queue processors
        self.queue_functions = {}

    @property
    def queue_name(self):
        return 'AbstractQueue'

    # Define the interface for the worker
    async def worker(self, name, queue):
        while True:
            # Get an objective
            task = await queue.get()

            # Execute the task
            try:
                await self.queue_functions[task['function_name']](queue, name, task)
            except Exception as e:
                # Exceptions happen here when the namespace is not ready for example
                # So we put it on the queue again
                print('got exception on queue task:', task['function_name'])
                print(e)

                await self.queue.put(task)

                # Disconnect and reconnect here to prevent namespace errors
                await self.socket_client.disconnect()
                await self.socket_client.connect_to_server()

            # Notify the queue that the "work item" has been processed.
            queue.task_done()

    # Register functions that can process things from the queue
    def register_queue_processor(self, name, function):
        self.queue_functions[name] = function

    # Create a queue, has to be
    def create_queue(self):
        # Create a queue that we will use to store our "workload".
        self.queue = asyncio.Queue()

        # Create a worker to process the items in our queue
        for i in range(0, self.n_workers):
            self.worker_instances.append(asyncio.create_task(self.worker(f'{self.queue_name}-worker-{i}', self.queue)))

    # Kills the worker and cleans up after it
    async def destroy_queue(self):
        self.worker_instance.cancel()
        await asyncio.gather(self.worker_instance, return_exceptions=True)


# Create the base namespace we work with
# Implements any shared features such as idn
class BaseClientNamespace(socketio.AsyncClientNamespace):
    # We save the server address in the baseclient so we only have to change it one place.
    server_address = os.environ.get('SERVER_ADDRESS', 'http://172.20.2.237:3000')

    def __init__(self, QueueClass, namespace=None):
        super().__init__(namespace)
        self.client_type = 'abstract'
        self.sid = 'no_address'

        # Initialize the queue
        self.my_queue = QueueClass(self)
        self.my_queue.create_queue()

    def background_job(self):
        pass

    # Helper function to append to the queue
    async def append_to_queue(self, data):
        await self.my_queue.queue.put(data)

    # Event received when size of queue is required
    # Returns the size immediately
    async def on_get_queue_size(self):
        await self.emit('current_queue_size', self.my_queue.queue.qsize())

    # Event received when this client connects to the server
    async def on_connect(self):
        print('connected to:', self.server_address)

        # Run the IDN
        await self.on_idn()

    # Event received when the connection to the server is lost
    def on_disconnect(self):
        print('Lost connection, trying to reconnect')

    # Generate and send idn, uses the mac address of the client to generate unique static idn
    async def on_idn(self):
        # Generate IDN
        node = uuid.getnode()
        idn = f'{self.client_type}_{node}'

        # Send the IDN
        await self.emit('idn', idn)
        print('Sent idn:', idn)

        # Ask for the latest non-completed step
        await self.emit('get_latest_step')


# Create an entrypoint for the client
async def main(NamespaceClass, namespace_address):
    # Define async socket client
    sio = socketio.AsyncClient()

    # Register the namespace to the client
    namespace = NamespaceClass(namespace_address)
    sio.register_namespace(namespace)

    async def connect_to_server():
        # Connect to the server
        await sio.connect(namespace.server_address)

        # add the SID to the namespace
        namespace.sid = sio.sid

        # Wait a short while just in case
        await asyncio.sleep(1.0)

    # Add the connection method to the namespace (for reconnects)
    namespace.connect_to_server = connect_to_server

    # Wait for the connection to be established
    await connect_to_server()

    # Run the background job
    asyncio.create_task(namespace.background_job())

    # Run the event loop
    await sio.wait()

