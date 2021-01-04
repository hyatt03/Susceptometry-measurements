# Import webserver related packages
from aiohttp import web
import socketio

# Import our own models (and a database connection
from models import ExperimentStep, ExperimentConfiguration, Session, StationStatus, db

# Import namespaces for the socket connections
from server_namespaces.browser_events import BrowserNamespace
from server_namespaces.cryo_events import CryoNamespace
from server_namespaces.magnetism_events import MagnetismNamespace

# Create app and setup websockets
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

# Initialize namespaces
cryo_space = CryoNamespace('/cryo')
magnetism_space = MagnetismNamespace('/magnetism')
browser_space = BrowserNamespace('/browser')

# Setup cross references between namespaces
for space in [cryo_space, magnetism_space, browser_space]:
    space.set_namespaces(cryo_space, magnetism_space, browser_space)

# Register namespaces for websockets
sio.register_namespace(cryo_space)
sio.register_namespace(magnetism_space)
sio.register_namespace(browser_space)

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
    web.run_app(app, port=3000)
