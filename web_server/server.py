import uvicorn
from aiohttp import web
import asyncio
import socketio
import time
import numpy as np
from models import ExperimentStep, ExperimentConfiguration, Session, db

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
sessions = {}


async def index(request):
    """Serve the client-side application."""
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')


##### BROWSER EVENTS #####
# Get the temperatures
@sio.event
async def b_get_temperatures(sid):
    with db.connection_context():
        # Send (mocked) temperatures
        temperatures = {
            't_still': round(float(np.abs(np.random.normal(2.2212))), 4),
            't_1': round(float(np.abs(np.random.normal(3.3313))), 4),
            't_2': round(float(np.abs(np.random.normal(4.4414))), 4),
            't_3': round(float(np.abs(np.random.normal(5.5515))), 4),
            't_4': round(float(np.abs(np.random.normal(6.6616))), 4),
            't_5': round(float(np.abs(np.random.normal(7.7717))), 4),
            't_6': round(float(np.abs(np.random.normal(8.8818))), 4),
            'timestamp': time.time()
        }

        await sio.emit('b_temperatures', temperatures, room=sid)


# Get the field strength of the large magnet
@sio.event
async def b_get_dc_field(sid):
    with db.connection_context():
        dc_field_strength = round(float(np.abs(np.random.normal(8, 0.2))), 4)
        await sio.emit('b_dc_field', dc_field_strength, room=sid)


# Get the field strength of the small magnet
@sio.event
async def b_get_ac_field(sid):
    with db.connection_context():
        ac_field_strength = round(float(np.random.normal(loc=0.0, scale=0.5)), 4)
        await sio.emit('b_ac_field', ac_field_strength, room=sid)


# Number of datapoints collected
@sio.event
async def b_get_n_points_taken(sid):
    with db.connection_context():
        n_points_taken = 21
        await sio.emit('b_n_points_taken', n_points_taken, room=sid)


# Total number of datapoints to be collected during this run
@sio.event
async def b_get_n_points_total(sid):
    with db.connection_context():
        n_points_total = 210
        await sio.emit('b_n_points_total', n_points_total, room=sid)


@sio.event
async def b_get_rms(sid):
    with db.connection_context():
        rms_value = round(float(np.abs(np.random.normal(0.545535))), 5)
        await sio.emit('b_rms', rms_value, room=sid)


@sio.event
async def b_get_magnet_trace(sid):
    with db.connection_context():
        times = list(map(lambda y: float(y), np.arange(0.0, 10.5, 10.5 / 100)))
        magnet_trace = list(map(lambda y: float(y), np.random.normal(loc=8, scale=0.2, size=len(times)) + np.sin(times)))
        await sio.emit('b_magnet_trace', {'magnet_trace': magnet_trace, 'times': times}, room=sid)


@sio.event
async def b_get_temperature_trace(sid):
    with db.connection_context():
        times = list(map(lambda y: float(y), np.arange(0.0, 10.5, 10.5 / 20)))
        get_temps = lambda x: list(map(lambda y: float(y), np.abs(np.random.normal(x, size=len(times)))))
        temperatures = {
            't_still': get_temps(2.2212),
            't_1': get_temps(3.3313),
            't_2': get_temps(4.4414),
            't_3': get_temps(5.5515),
            't_4': get_temps(6.6616),
            't_5': get_temps(7.7717),
            't_6': get_temps(8.8818),
            'times': times
        }

        await sio.emit('b_temperature_trace', temperatures, room=sid)


##### UNIVERSAL EVENTS #####
@sio.event
async def connect(sid, environ):
    with db.connection_context():
        print("connect ", sid)
        await asyncio.sleep(0.5)
        await sio.emit('idn', room=sid)


@sio.event
async def idn(sid, data):
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


@sio.event
def disconnect(sid):
    with db.connection_context():
        print('disconnect ', sid)


app.router.add_static('/static', 'static')
app.router.add_get('/', index)

if __name__ == '__main__':
    # Ensure the database tables are created
    with db.connection_context():
        db.create_tables([Session, ExperimentConfiguration, ExperimentStep])

    # uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
    web.run_app(app)
