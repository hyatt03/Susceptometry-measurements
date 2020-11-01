# Import socket client, so we can connect to the webserver
import socketio

# Import uuid to access a machine id
import uuid


# Create the base namespace we work with
# Implements any shared features such as idn
class BaseClientNamespace(socketio.AsyncClientNamespace):
    # We save the server address in the baseclient so we only have to change it one place.
    server_address = 'http://localhost:8080'

    def __init__(self, namespace=None):
        super().__init__(namespace)
        if not hasattr(self, 'client_type'):
            self.client_type = 'abstract'

        self.sid = 'no_address'

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

