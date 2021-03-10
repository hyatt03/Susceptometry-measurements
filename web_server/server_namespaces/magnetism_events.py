from server_namespaces.universal_events import UniversalEvents
from models import db, DataPoint


# All the methods related to the magnetism station from the servers perspective
class MagnetismNamespace(UniversalEvents):
    async def on_m_got_magnet_trace(self, sid, data):
        await self.browser_namespace.got_magnet_trace(data)

    async def get_magnet_trace(self):
        await self.emit('m_get_magnet_trace')

    async def get_dc_field(self):
        await self.emit('m_get_dc_field')

    async def on_m_got_magnet_rms(self, sid, rms):
        await self.browser_namespace.got_magnet_rms(rms)

    async def on_m_got_dc_field(self, sid, dc_field):
        await self.browser_namespace.got_dc_field(dc_field)

    async def on_m_got_step_results(self, sid, results):
        with db.connection_context():
            # Get the datapoint associated with the step (should be generated when step is sent)
            datapoint = DataPoint.select().where(DataPoint.step == results['step_id']).order_by(DataPoint.created).get()

            # Then we save the datapoint
            if datapoint is not None:
                datapoint.save_magnetism_data(results)

    async def on_m_set_step_ready(self, sid, step_id):
        await self.cryo_namespace.send_step_ready(step_id)

    async def push_next_step(self, step):
        print('pushing next step to magnet')
        await self.emit('m_next_step', step)
