from server_namespaces.universal_events import UniversalEvents


# All the methods related to the magnetism station from the servers perspective
class MagnetismNamespace(UniversalEvents):
    async def on_m_got_magnet_trace(self, sid, data):
        await self.browser_namespace.got_magnet_trace(data)

    async def get_magnet_trace(self):
        await self.emit('m_get_magnet_trace')

    async def on_m_got_magnet_rms(self, sid, rms):
        await self.browser_namespace.got_magnet_rms(rms)

    async def push_next_step(self, step):
        print('pushing next step to magnet')
        await self.emit('m_next_step', step)
