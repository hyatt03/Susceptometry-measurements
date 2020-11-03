from server_namespaces.universal_events import UniversalEvents


# All the methods related to the cryogenics station from the servers perspective
class CryoNamespace(UniversalEvents):
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
        await self.browser_namespace.send_temperatures(temperatures)

    async def on_c_got_temperature_trace(self, sid, temperature_trace):
        print('got trace, sending')
        await self.browser_namespace.send_temperature_trace(temperature_trace)

    # Event received when mck state is updated
    async def on_c_got_mck_state(self, mck_state):
        print('got mck state', mck_state)

    async def on_current_queue_size(self, size):
        print('got current queue size:', size)
