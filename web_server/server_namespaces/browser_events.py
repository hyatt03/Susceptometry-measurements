from models import db, ExperimentConfiguration, ExperimentStep, Session, ConfigurationParameter
from server_namespaces.universal_events import UniversalEvents
from default_experiment_config import get_default_experiment_configuration

import numpy as np

# All the methods related to the browser connection
class BrowserNamespace(UniversalEvents):
    # Get the temperatures
    async def on_b_get_temperatures(self, sid):
        await self.cryo_namespace.get_temperatures()

    async def on_b_get_pressures(self, sid):
        await self.cryo_namespace.get_pressures()

    async def on_b_get_cryo_status(self, sid):
        await self.cryo_namespace.get_fp_status()

    async def on_b_get_is_saving_temperatures(self, sid):
        with db.connection_context():
            saving = ConfigurationParameter.read_config_value('is_saving_cryo_temperatures')
            await self.emit('b_got_is_saving_temperatures', saving)

    async def on_b_begin_save_temperatures(self, sid):
        with db.connection_context():
            ConfigurationParameter.overwrite_config_value('is_saving_cryo_temperatures', True)
            await self.emit('b_got_is_saving_temperatures', True)

    async def on_b_end_save_temperatures(self, sid):
        with db.connection_context():
            ConfigurationParameter.overwrite_config_value('is_saving_cryo_temperatures', False)
            await self.emit('b_got_is_saving_temperatures', False)

    async def send_cryo_status(self, status):
        await self.emit('b_got_cryo_status', status)

    async def send_temperatures(self, temperatures):
        await self.emit('b_temperatures', temperatures)

    async def send_temperature_trace(self, temperature_trace):
        await self.emit('b_temperature_trace', temperature_trace)

    async def send_pressures(self, pressures):
        await self.emit('b_pressures', pressures)

    async def send_pressure_trace(self, pressure_trace):
        await self.emit('b_pressure_trace', pressure_trace)

    async def got_magnet_trace(self, data):
        times, magnet_trace = data
        await self.emit('b_magnet_trace', {'magnet_trace': magnet_trace, 'times': times})

    async def got_magnet_rms(self, rms):
        await self.emit('b_ac_field', round(rms, 4))

    async def got_picowatt_config(self, config):
        with db.connection_context():
            config['Delay'] = ConfigurationParameter.read_config_value('picowatt_delay')
            await self.emit('b_got_picowatt_config', config)

    # Get the field strength of the large magnet
    async def on_b_get_dc_field(self, sid):
        dc_field_strength = round(float(np.abs(np.random.normal(8, 0.2))), 4)
        # await self.emit('b_dc_field', dc_field_strength, room=sid)

    async def got_dc_field(self, dc_field_strength):
        await self.emit('b_dc_field', dc_field_strength)

    # Get the field strength of the small magnet
    async def on_b_get_ac_field(self, sid):
        ac_field_strength = round(float(np.random.normal(loc=0.0, scale=0.5)), 4)
        await self.emit('b_ac_field', ac_field_strength, room=sid)

    # Number of datapoints collected
    async def on_b_get_n_points_taken(self, sid):
        with db.connection_context():
            if ExperimentConfiguration.select().count() > 0:
                # get the latest config from the database
                latest_config = ExperimentConfiguration.select().order_by(ExperimentConfiguration.id.desc()).get()

                # Compute the number of points taken
                n_points_taken = ExperimentStep.select() \
                    .where(ExperimentStep.experiment_configuration == latest_config.id) \
                    .where(ExperimentStep.step_done == True) \
                    .count()

                # Send it to the user
                await self.emit('b_n_points_taken', n_points_taken, room=sid)

    # Total number of datapoints to be collected during this run
    async def on_b_get_n_points_total(self, sid):
        with db.connection_context():
            if ExperimentConfiguration.select().count() > 0:
                # get the latest config from the database
                latest_config = ExperimentConfiguration.select().order_by(ExperimentConfiguration.id.desc()).get()

                # Compute the number of points taken
                n_points_total = ExperimentStep.select() \
                    .where(ExperimentStep.experiment_configuration == latest_config.id) \
                    .count()

                # Send it to the user
                await self.emit('b_n_points_total', n_points_total, room=sid)

    async def on_b_get_experiment_list(self, sid, data):
        # Grab the page we want
        page = data['page']

        # Open connection to database
        with db.connection_context():
            # Count number of experiments
            experiment_count = ExperimentConfiguration.select().count()

            # If no experiments exist, we send that to the client, otherwise we paginate
            experiments = []
            if experiment_count > 0:
                # Paginate the experiments
                experiments = list(ExperimentConfiguration \
                                   .select() \
                                   .order_by(ExperimentConfiguration.id.desc()) \
                                   .paginate(page, 10) \
                                   .dicts())

            # Parse the dates out
            # Add number of datapoints collected
            # Add the total number of datapoints in the run
            for e in experiments:
                e['created'] = e['created'].isoformat()

                # Compute the number of points taken
                e['n_points_taken'] = ExperimentStep.select() \
                    .where(ExperimentStep.experiment_configuration == e['id']) \
                    .where(ExperimentStep.step_done == True) \
                    .count()

                # Compute the number of points taken
                e['n_points_total'] = ExperimentStep.select() \
                    .where(ExperimentStep.experiment_configuration == e['id']) \
                    .count()

            await self.emit('b_got_experiment_list', {'list': experiments, 'count': experiment_count, 'page': page})

    # Get the rms value of the oscilloscope
    async def on_b_get_rms(self, sid):
        rms_value = round(float(np.abs(np.random.normal(0.545535))), 5)
        await self.emit('b_rms', rms_value, room=sid)

    # Get a trace of the magnet field values
    async def on_b_get_magnet_trace(self, sid):
        await self.magnetism_namespace.get_magnet_trace()

    # Get a trace of the temperatures recorded
    async def on_b_get_temperature_trace(self, sid):
        await self.cryo_namespace.get_temperature_trace()

    async def on_b_get_pressure_trace(self, sid):
        await self.cryo_namespace.get_pressure_trace()

    async def push_next_step_to_clients(self):
        # Grab the latest step
        step = await self.get_next_step()

        if step is not None:
            # Send the step dict to the clients
            await self.cryo_namespace.push_next_step(step)
            await self.magnetism_namespace.push_next_step(step)

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

    async def on_b_get_picowatt_config(self, sid):
        await self.cryo_namespace.get_avs47b_config()

    async def on_b_set_picowatt_config(self, sid, config):
        with db.connection_context():
            ConfigurationParameter.overwrite_config_value('picowatt_delay', config['Delay'])

        await self.cryo_namespace.on_c_get_picowatt_delay(1)
        await self.cryo_namespace.config_avs47b(config)

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
            data['oscope_resistor'] = 84.5  # Not configurable any more
            data['data_wait_before_measuring'] = float(data['data_wait_before_measuring'])
            data['data_points_per_measurement'] = int(data['data_points_per_measurement'])

            # Save the new configuration
            ec = ExperimentConfiguration.create(**data, created_by_id=user)
            ec.save()

            # Set all previous steps to be done
            ExperimentStep.update(step_done=True).where(ExperimentStep.step_done == False).execute()

            # Generate a new set of steps
            n_steps = ec.generate_steps()

            # Alert the user
            print(f'Generated {n_steps} new steps')

            # Push new configuration to all users
            await self.emit('b_latest_experiment_config', data)
            await self.emit('b_experiment_configuration_saved', room=sid)

            # Push next step to client
            await self.push_next_step_to_clients()

    async def on_b_start_circulation(self, sid):
        print('got start circulation from browser')
        await self.cryo_namespace.start_circulation()
