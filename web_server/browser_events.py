from models import db, ExperimentConfiguration, ExperimentStep, Session
from universal_events import UniversalEvents
from default_experiment_config import get_default_experiment_configuration
import numpy as np
import time


# All the methods related to the browser connection
class BrowserNamespace(UniversalEvents):
    # Get the temperatures
    async def on_b_get_temperatures(self, sid):
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

            await self.emit('b_temperatures', temperatures, room=sid)

    # Get the field strength of the large magnet
    async def on_b_get_dc_field(self, sid):
        with db.connection_context():
            dc_field_strength = round(float(np.abs(np.random.normal(8, 0.2))), 4)
            await self.emit('b_dc_field', dc_field_strength, room=sid)

    # Get the field strength of the small magnet
    async def on_b_get_ac_field(self, sid):
        with db.connection_context():
            ac_field_strength = round(float(np.random.normal(loc=0.0, scale=0.5)), 4)
            await self.emit('b_ac_field', ac_field_strength, room=sid)

    # Number of datapoints collected
    async def on_b_get_n_points_taken(self, sid):
        with db.connection_context():
            n_points_taken = 21
            await self.emit('b_n_points_taken', n_points_taken, room=sid)

    # Total number of datapoints to be collected during this run
    async def on_b_get_n_points_total(self, sid):
        with db.connection_context():
            n_points_total = 210
            await self.emit('b_n_points_total', n_points_total, room=sid)

    # Get the rms value of the oscilloscope
    async def on_b_get_rms(self, sid):
        with db.connection_context():
            rms_value = round(float(np.abs(np.random.normal(0.545535))), 5)
            await self.emit('b_rms', rms_value, room=sid)

    # Get a trace of the magnet field values
    async def on_b_get_magnet_trace(self, sid):
        with db.connection_context():
            times = list(map(lambda y: float(y), np.arange(0.0, 10.5, 10.5 / 100)))
            magnet_trace = list(
                map(lambda y: float(y), np.random.normal(loc=8, scale=0.2, size=len(times)) + np.sin(times)))
            await self.emit('b_magnet_trace', {'magnet_trace': magnet_trace, 'times': times}, room=sid)

    # Get a trace of the temperatures recorded
    async def on_b_get_temperature_trace(self, sid):
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

            await self.emit('b_temperature_trace', temperatures, room=sid)

    # Gets the latest experiment configuration
    # If no experiments exist, we fall back to a default configuration
    async def on_b_get_latest_experiment_config(self, sid):
        experiment_config = get_default_experiment_configuration()

        with db.connection_context():
            if ExperimentConfiguration.select().count() > 0:
                # Use the config from the database
                latest_config = ExperimentConfiguration.select().order_by(ExperimentConfiguration.id.desc()).get()
                experiment_config['sr830_sensitivity'] = float(latest_config.sr830_sensitivity)
                experiment_config['sr830_frequency'] = float(latest_config.sr830_frequency)
                experiment_config['sr830_buffersize'] = int(latest_config.sr830_buffersize)
                experiment_config['n9310a_sweep_steps'] = int(latest_config.n9310a_sweep_steps)
                experiment_config['n9310a_min_frequency'] = float(latest_config.n9310a_min_frequency)
                experiment_config['n9310a_max_frequency'] = float(latest_config.n9310a_max_frequency)
                experiment_config['n9310a_min_amplitude'] = float(latest_config.n9310a_min_amplitude)
                experiment_config['n9310a_max_amplitude'] = float(latest_config.n9310a_max_amplitude)
                experiment_config['magnet_min_field'] = float(latest_config.magnet_min_field)
                experiment_config['magnet_max_field'] = float(latest_config.magnet_max_field)
                experiment_config['magnet_sweep_steps'] = int(latest_config.magnet_sweep_steps)
                experiment_config['oscope_resistor'] = float(latest_config.oscope_resistor)
                experiment_config['data_wait_before_measuring'] = float(latest_config.data_wait_before_measuring)
                experiment_config['data_points_per_measurement'] = int(latest_config.data_points_per_measurement)

        await self.emit('b_latest_experiment_config', experiment_config, room=sid)

    # Takes a form sent by the client and creates a new experiment
    async def on_b_set_experiment_config(self, sid, data):
        with db.connection_context():
            # First we get the session of the current user
            user = Session.get(Session.sid == sid)

            # Parse out the numbers from the client
            data['sr830_sensitivity'] = float(data['sr830_sensitivity'])
            data['sr830_frequency'] = float(data['sr830_frequency'])
            data['sr830_buffersize'] = int(data['sr830_buffersize'])
            data['n9310a_sweep_steps'] = int(data['n9310a_sweep_steps'])
            data['n9310a_min_frequency'] = float(data['n9310a_min_frequency'])
            data['n9310a_max_frequency'] = float(data['n9310a_max_frequency'])
            data['n9310a_min_amplitude'] = float(data['n9310a_min_amplitude'])
            data['n9310a_max_amplitude'] = float(data['n9310a_max_amplitude'])
            data['magnet_min_field'] = float(data['magnet_min_field'])
            data['magnet_max_field'] = float(data['magnet_max_field'])
            data['magnet_sweep_steps'] = int(data['magnet_sweep_steps'])
            data['oscope_resistor'] = float(data['oscope_resistor'])
            data['data_wait_before_measuring'] = float(data['data_wait_before_measuring'])
            data['data_points_per_measurement'] = int(data['data_points_per_measurement'])

            # Save the new configuration
            ec = ExperimentConfiguration.create(**data, created_by_id=user)
            ec.save()

            # Set all previous steps to be done
            ExperimentStep.update(step_done=True).where(ExperimentStep.step_done==False).execute()

            # Generate a new set of steps
            ec.generate_steps()

            await self.emit('b_experiment_configuration_saved')
