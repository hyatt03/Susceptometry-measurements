from server_namespaces.universal_events import UniversalEvents
from models import db, DataPoint, TemperatureDataPoint, ConfigurationParameter
from collections import deque


# All the methods related to the cryogenics station from the servers perspective
class CryoNamespace(UniversalEvents):
    # Keep at max 20 ids ready
    steps_ready = deque([], maxlen=20)
    received_temperatures = 0

    """ #### EMITTING EVENTS #### """
    async def test_queue(self):
        await self.emit('test_queue')

    # Emitted when cooling should initiate
    async def config_start_cooling(self):
        await self.emit('c_config_start_cooling')

    # Emitted when config needs updating
    async def config_avs47b(self, config):
        await self.emit('c_config_avs47b', config)

    # Emitted when user requires current temperatures
    async def get_temperatures(self):
        await self.emit('c_get_temperatures')

    async def get_temperature_trace(self):
        await self.emit('c_get_temperature_trace')

    async def get_pressures(self):
        await self.emit('c_get_pressures')

    async def get_pressure_trace(self):
        await self.emit('c_get_pressure_trace')

    async def get_fp_status(self):
        await self.emit('c_get_frontpanel_status')

    # if the clients reset, we want to be able to tell it the step is ready
    async def on_c_is_step_ready(self, sid, step_id):
        if step_id in self.steps_ready:
            await self.send_step_ready(step_id)

    async def send_step_ready(self, step_id):
        # Keep track of the steps that have been ready
        self.steps_ready.append(step_id)

        # Send the step that is ready
        await self.emit('c_step_ready_for_measurement', step_id)

    async def push_next_step(self, step):
        await self.emit('c_next_step', step)

    async def on_c_got_step_results(self, sid, results):
        with db.connection_context():
            # Get the datapoint associated with the step (should be generated when step is sent)
            datapoint = DataPoint.select().where(DataPoint.step == results['step_id']).order_by(DataPoint.created).get()

            # Then we save the datapoint
            if datapoint is not None:
                datapoint.save_cryo_data(results)

    # Emitted when user wishes updates to the mck state
    async def get_mck_state(self):
        await self.emit('c_get_mck_state')

    """ #### RECEIVED EVENTS #### """
    # Event received when cooling starts
    async def on_c_started_cooling(self):
        print('cooling started')

    # Event received when config has be successfully applied
    async def on_c_avs47b_has_been_configured(self):
        print('avs47b config successful')

    # Event received when new temperatures are available
    async def on_c_got_temperatures(self, sid, temperatures):
        # Keep track of how many temperatures we have received
        self.received_temperatures += 1

        # Ensure a connection to the database
        with db.connection_context():
            # Check if we want to save the temperatures
            if ConfigurationParameter.read_config_value('is_saving_cryo_temperatures') and \
                self.received_temperatures % ConfigurationParameter.read_config_value('save_every_n_temperatures') == 0:
                # Save the temperatures
                TemperatureDataPoint(
                    cryo_data_point = 1,
                    t_upper_hex=temperatures['t_upper_hex'],
                    t_lower_hex=temperatures['t_lower_hex'],
                    t_he_pot=temperatures['t_he_pot'],
                    t_1st_stage=temperatures['t_1st_stage'],
                    t_2nd_stage=temperatures['t_2nd_stage'],
                    t_inner_coil=temperatures['t_inner_coil'],
                    t_outer_coil=temperatures['t_outer_coil'],
                    t_switch=temperatures['t_switch'],
                    t_he_pot_2=temperatures['t_he_pot_2']
                ).save()

                # Reset the counter so we don't get very large numbers (there is no need)
                self.received_temperatures = 0

        # Actually send the temperatures
        await self.browser_namespace.send_temperatures(temperatures)

    async def on_c_got_temperature_trace(self, sid, temperature_trace):
        await self.browser_namespace.send_temperature_trace(temperature_trace)

    async def on_c_got_pressures(self, sid, pressures):
        await self.browser_namespace.send_pressures(pressures)

    async def on_c_got_pressure_trace(self, sid, pressure_trace):
        await self.browser_namespace.send_pressure_trace(pressure_trace)

    async def on_c_got_fp_status(self, sid, status):
        await self.browser_namespace.send_cryo_status(status)

    # Event received when mck state is updated
    async def on_c_got_mck_state(self, mck_state):
        print('got mck state', mck_state)

    async def on_current_queue_size(self, size):
        print('got current queue size:', size)

    

