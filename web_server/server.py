import uvicorn
from aiohttp import web
import asyncio
import socketio
import time
import numpy as np

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
    dc_field_strength = round(float(np.abs(np.random.normal(8, 0.2))), 4)
    await sio.emit('b_dc_field', dc_field_strength, room=sid)


# Get the field strength of the small magnet
@sio.event
async def b_get_ac_field(sid):
    ac_field_strength = round(float(np.random.normal(loc=0.0, scale=0.5)), 4)
    await sio.emit('b_ac_field', ac_field_strength, room=sid)


# Number of datapoints collected
@sio.event
async def b_get_n_points_taken(sid):
    n_points_taken = 21
    await sio.emit('b_n_points_taken', n_points_taken, room=sid)


# Total number of datapoints to be collected during this run
@sio.event
async def b_get_n_points_total(sid):
    n_points_total = 210
    await sio.emit('b_n_points_total', n_points_total, room=sid)


@sio.event
async def b_get_rms(sid):
    rms_value = round(float(np.abs(np.random.normal(0.545535))), 5)
    await sio.emit('b_rms', rms_value, room=sid)


##### UNIVERSAL EVENTS #####
@sio.event
async def connect(sid, environ):
    print("connect ", sid)
    await asyncio.sleep(0.5)
    await sio.emit('idn', room=sid)


@sio.event
async def idn(sid, data):
    print("idn ", data)
    sessions[sid] = data


@sio.event
def disconnect(sid):
    print('disconnect ', sid)


app.router.add_static('/static', 'static')
app.router.add_get('/', index)

if __name__ == '__main__':
    # uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
    web.run_app(app)
