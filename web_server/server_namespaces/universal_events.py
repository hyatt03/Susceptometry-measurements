import socketio, asyncio
from models import db, Session, ExperimentStep


# Class containing events relevant for all different namespaces (used as a baseclass
class UniversalEvents(socketio.AsyncNamespace):
    # Init all the self variables needed
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.cryo_namespace = None
        self.magnetism_namespace = None
        self.browser_namespace = None
        self.steps_done = []

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

    # Allow clients to identify themselves
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

    # Sends event to retrieve queue size
    # No abstract handler, should be handled in the individual classes
    async def get_queue_size(self):
        await self.emit('get_queue_size')

    # Define a method to check if a step is done
    def is_step_done(self, step_id):
        return step_id in self.steps_done

    # And an endpoint to mark a step as done
    async def on_mark_step_as_done(self, sid, step):
        # Add the id of the step to the done list
        step_id = step['id']
        self.steps_done.append(step_id)

        # Check if the step is done both places
        if self.magnetism_namespace.is_step_done(step_id) and self.cryo_namespace.is_step_done(step_id):
            # Both are done, so we should mark it as done in the database
            with db.connection_context():
                ExperimentStep.get_by_id(step_id).update(step_done=True).execute()
            
            # Next we should push the next step to the clients (if applicable)
            await self.browser_namespace.push_next_step_to_clients()

