from models import db, ExperimentConfiguration, ExperimentStep, Session
from server_namespaces.universal_events import UniversalEvents
from default_experiment_config import get_default_experiment_configuration
import numpy as np


# All the methods related to the browser connection
class BrowserNamespace(UniversalEvents):
    async def on_test_cryo_queue(self, sid):
        print('got test cryo queue')
        await self.cryo_namespace.test_queue()

    async def on_test_magnetism_queue(self, sid):
        print('got test magnetism queue')
        await self.magnetism_namespace.emit('test_queue')

    # Get the temperatures
    async def on_b_get_temperatures(self, sid):
        await self.cryo_namespace.get_temperatures()

    async def send_temperatures(self, temperatures):
        with db.connection_context():
            await self.emit('b_temperatures', temperatures)

    async def send_temperature_trace(self, temperature_trace):
        with db.connection_context():
            await self.emit('b_temperature_trace', temperature_trace)

    async def got_magnet_trace(self, data):
        with db.connection_context():
            times, magnet_trace = data
            await self.emit('b_magnet_trace', {'magnet_trace': magnet_trace, 'times': times})

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
            await self.magnetism_namespace.get_magnet_trace()

    # Get a trace of the temperatures recorded
    async def on_b_get_temperature_trace(self, sid):
        with db.connection_context():
            await self.cryo_namespace.get_temperature_trace()

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

            # Push new configuration to all users
            await self.emit('b_latest_experiment_config', data)
            await self.emit('b_experiment_configuration_saved', room=sid)
