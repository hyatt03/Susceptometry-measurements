# Import asyncio to get event loop
import asyncio

# Import the base namespace, contains shared methods and information
from baseclient import BaseClientNamespace, main


# Create the class containing the namespace for this client
class MagnetismClientNamespace(BaseClientNamespace):
    def __init__(self, namespace):
        super().__init__(namespace)
        self.client_type = 'magnetism'


if __name__ == '__main__':
    asyncio.run(main(MagnetismClientNamespace, '/magnetism'))

