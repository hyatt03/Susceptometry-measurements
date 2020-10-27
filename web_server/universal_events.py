import socketio, asyncio
from models import db, Session


# Class containing events relevant for all different namespaces (used as a baseclass
class UniversalEvents(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        print("connect ", sid)
        await asyncio.sleep(0.5)
        await self.emit('idn', room=sid)

    def on_disconnect(self, sid):
        print('disconnect ', sid)

    async def on_idn(self, sid, data):
        # Figure out what type of client we have
        client_type = data.split('_')[0]

        # Connect to the database
        with db.connection_context():
            # Register sid with session
            try:
                # First check if the session exists, then we update
                Session.get(Session.idn == data).update(sid=sid).where(Session.idn == data).execute()
            except Session.DoesNotExist:
                # if it does not exist, we just create it
                Session.create(idn=data, sid=sid, type=client_type).save()
