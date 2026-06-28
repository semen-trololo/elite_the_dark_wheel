import unittest
from ship.models import create_sidewinder, create_fighter_ship


class TestShipModels(unittest.TestCase):
    
    def test_sidewinder_creation(self):
        ship = create_sidewinder()
        # 12 вершин
        self.assertEqual(len(ship.vertices), 12)
        # 28 рёбер
        self.assertEqual(len(ship.edges), 28)
    
    def test_fighter_ship_creation(self):
        ship = create_fighter_ship()
        self.assertEqual(len(ship.vertices), 10)
        self.assertEqual(len(ship.edges), 20)


if __name__ == '__main__':
    unittest.main()