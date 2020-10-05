import unittest
from stations import cryogenics_station, magnetism_station, data_acquisition_station


class MagnetismStationTest(unittest.TestCase):
    def test_initialization(self):
        station = magnetism_station.get_station()
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
