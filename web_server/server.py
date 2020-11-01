# Import webserver related packages
from aiohttp import web
import socketio

# Import our own models (and a database connection
from models import ExperimentStep, ExperimentConfiguration, Session, StationStatus, db

# Import namespaces for the socket connections
from browser_events import BrowserNamespace
from cryo_events import CryoNamespace
from magnetism_events import MagnetismNamespace

# Create app and setup websockets
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

# Register namespaces for websockets
sio.register_namespace(BrowserNamespace('/browser'))
sio.register_namespace(CryoNamespace('/cryo'))
sio.register_namespace(MagnetismNamespace('/magnetism'))

# Open the index template to cache it
with open('index.html') as f:
    index_page_html = f.read()


# Create an index page for the initial browser request
async def index(request):
    return web.Response(text=index_page_html, content_type='text/html')

# Setup the http routes
app.router.add_static('/static', 'static')
app.router.add_get('/', index)

if __name__ == '__main__':
    # Ensure the database tables are created
    with db.connection_context():
        db.create_tables([Session, ExperimentConfiguration, ExperimentStep, StationStatus])

    # Run the app
    web.run_app(app)
