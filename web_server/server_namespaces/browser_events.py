from models import db, ExperimentConfiguration, ExperimentStep, Session, DataPoint
from server_namespaces.universal_events import UniversalEvents
from default_experiment_config import get_default_experiment_configuration
import numpy as np

from peewee import DoesNotExist

from playhouse.shortcuts import model_to_dict


# All the methods related to the browser connection
class BrowserNamespace(UniversalEvents):
    # Get the temperatures
    async def on_b_get_temperatures(self, sid):
        await self.cryo_namespace.get_temperatures()

    async def on_b_get_pressures(self, sid):
        await self.cryo_namespace.get_pressures()

    async def on_b_get_cryo_status(self, sid):
        await self.cryo_namespace.get_fp_status()

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

    # Get the field strength of the large magnet
    async def on_b_get_dc_field(self, sid):
        dc_field_strength = round(float(np.abs(np.random.normal(8, 0.2))), 4)
        await self.emit('b_dc_field', dc_field_strength, room=sid)

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
                n_points_taken = ExperimentStep.select()\
                                               .where(ExperimentStep.experiment_configuration == latest_config.id)\
                                               .where(ExperimentStep.step_done==True)\
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
                n_points_total = ExperimentStep.select()\
                                               .where(ExperimentStep.experiment_configuration == latest_config.id)\
                                               .count()

                # Send it to the user
                await self.emit('b_n_points_total', n_points_total, room=sid)
            
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
        with db.connection_context():
            try:
                # Get the next step
                step = ExperimentStep.select().where(ExperimentStep.step_done==False).order_by(ExperimentStep.id).first()

                # Check if the step is none, and skip to the catch clause if it is
                if step is None:
                    raise DoesNotExist('Step does not exist')

                # Check if the step has an associated datapoint
                if DataPoint.select().where(ExperimentStep==step).count() < 1:
                    step.generate_datapoint()

                # Convert step to dict
                step_d = model_to_dict(step)
                
                # Set the experiment id (different from the step id)
                step_d['experiment_configuration_id'] = step_d['experiment_configuration']['id']

                # Remove datetime and experiment configuration from the dict
                # They are not needed in the client, and they are not directly serializable to json (due to missing datetime format)
                del(step_d['created'])
                del(step_d['experiment_configuration'])

                # Send the step dict to the clients
                await self.cryo_namespace.push_next_step(step_d)
                await self.magnetism_namespace.push_next_step(step_d)
        
            # Check if the step even exists
            except DoesNotExist:
                # It is OK if it does not exist, we should just stop measuring
                print('No more steps ready')

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
            n_steps = ec.generate_steps()

            # Alert the user
            print(f'Generated {n_steps} new steps')

            # Push new configuration to all users
            await self.emit('b_latest_experiment_config', data)
            await self.emit('b_experiment_configuration_saved', room=sid)

            # Push next step to client
            await self.push_next_step_to_clients()
