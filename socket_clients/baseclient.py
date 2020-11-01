# Import socket client, so we can connect to the webserver
import socketio, asyncio

# Import uuid to access a machine id
import uuid


class BaseQueueClass():
    def __init__(self, socket_client):
        super().__init__()

        # Setup the socket client
        self.socket_client = socket_client

        # Setup the queue variables
        self.queue = None
        self.worker_instance = None

        # Set the queue name
        self.queue_name = 'AbstractQueue'

    # Define the interface for the worker
    async def worker(self, name, queue):
        raise NotImplemented()

    # Create a queue, has to be
    def create_queue(self):
        # Create a queue that we will use to store our "workload".
        self.queue = asyncio.Queue()

        # Create a worker to process the items in our queue
        self.worker_instance = asyncio.create_task(self.worker(f'{self.queue_name}-worker', self.queue))

    # Kills the worker and cleans up after it
    async def destroy_queue(self):
        self.worker_instance.cancel()
        await asyncio.gather(self.worker_instance, return_exceptions=True)


# Create the base namespace we work with
# Implements any shared features such as idn
class BaseClientNamespace(socketio.AsyncClientNamespace):
    # We save the server address in the baseclient so we only have to change it one place.
    server_address = 'http://localhost:8080'

    def __init__(self, QueueClass, namespace=None):
        super().__init__(namespace)
        self.client_type = 'abstract'
        self.sid = 'no_address'

        # Initialize the queue
        self.my_queue = QueueClass(self)
        self.my_queue.create_queue()

    async def append_to_queue(self, data):
        await self.my_queue.queue.put(data)

    async def on_connect(self):
        print('connected to:', self.server_address)

    async def on_disconnect(self):
        print('Lost connection, trying to reconnect')

    # Generate and send idn, uses the mac address of the client to generate unique static idn
    async def on_idn(self):
        node = uuid.getnode()
        idn = f'{self.client_type}_{node}'
        await self.emit('idn', idn)
        print('Sent idn:', idn)


# Create an entrypoint for the client
async def main(NamespaceClass, namespace_address):
    # Define async socket client
    sio = socketio.AsyncClient()

    # Register the namespace to the client
    namespace = NamespaceClass(namespace_address)
    sio.register_namespace(namespace)

    # Connect to the server
    await sio.connect(namespace.server_address)

    # add the SID to the namespace
    namespace.sid = sio.sid

    # Run the event loop
    await sio.wait()

