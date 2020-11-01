import socketio, asyncio
from models import db, Session


# Class containing events relevant for all different namespaces (used as a baseclass
class UniversalEvents(socketio.AsyncNamespace):
    # Init all the self variables needed
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.cryo_namespace = None
        self.magnetism_namespace = None
        self.browser_namespace = None

    # Basically an init function to allow communication between the channels
    def set_namespaces(self, cryo, magnetism, browser):
        self.cryo_namespace = cryo
        self.magnetism_namespace = magnetism
        self.browser_namespace = browser

    # Ask for idn on connect
    async def on_connect(self, sid, environ):
        await asyncio.sleep(0.5)
        await self.emit('idn', room=sid)

    # Tell the user that a client disconnected
    def on_disconnect(self, sid):
        print('disconnect ', sid)

    async def on_idn(self, sid, data):
        # Figure out what type of client we have
        client_type = data.split('_')[0]
        is_old = 'Old'

        # Connect to the database
        with db.connection_context():
            # Register sid with session
            try:
                # First check if the session exists, then we update
                Session.get(Session.idn == data).update(sid=sid).where(Session.idn == data).execute()
            except Session.DoesNotExist:
                # if it does not exist, we just create it
                Session.create(idn=data, sid=sid, type=client_type).save()
                is_old = 'New'

        print(f'{is_old} client connected with idn: {data}, and sid: {sid}')
