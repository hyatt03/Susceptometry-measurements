from universal_events import UniversalEvents


# All the methods related to the cryogenics station
class CryoNamespace(UniversalEvents):
    async def on_done_with_task(self, sid, data):
        print('client done with task', sid, data)
