from aiohttp import web
import socketio
from models import ExperimentStep, ExperimentConfiguration, Session, db
from browser_events import BrowserNamespace

# Create app
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

# Register browser namespace
sio.register_namespace(BrowserNamespace('/browser'))

# Create web-server for the initial request
async def index(request):
    """Serve the client-side application."""
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

# Setup the routes
app.router.add_static('/static', 'static')
app.router.add_get('/', index)

if __name__ == '__main__':
    # Ensure the database tables are created
    with db.connection_context():
        db.create_tables([Session, ExperimentConfiguration, ExperimentStep])

    # Run the app
    web.run_app(app)
