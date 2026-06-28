"""
tests/test_galaxy_generator.py
Тесты для генератора галактик.

Совет от ментора:
Тестирование генератора критично! Мы должны убедиться, что:
1. Алгоритм детерминирован (одинаковый seed = одинаковая вселенная)
2. Генерируется правильное количество планет
3. Все данные планеты корректны
"""

import unittest
from universe.galaxy_generator import GalaxyGenerator
from universe.planet import Government, Economy


class TestGalaxyGenerator(unittest.TestCase):
    """Тесты для GalaxyGenerator"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.generator = GalaxyGenerator(base_seed=0)
    
    def test_deterministic_generation(self):
        """Тест детерминированности: одинаковый seed = одинаковая вселенная"""
        gen1 = GalaxyGenerator(base_seed=12345)
        gen2 = GalaxyGenerator(base_seed=12345)
        
        # Проверяем первые планеты в первой галактике
        planet1 = gen1.get_planet(0, 0)
        planet2 = gen2.get_planet(0, 0)
        
        self.assertEqual(planet1.name, planet2.name)
        self.assertEqual(planet1.x, planet2.x)
        self.assertEqual(planet1.y, planet2.y)
        self.assertEqual(planet1.government, planet2.government)
        self.assertEqual(planet1.economy, planet2.economy)
    
    def test_different_seeds_different_planets(self):
        """Тест: разные seed дают разные планеты"""
        gen1 = GalaxyGenerator(base_seed=0)
        gen2 = GalaxyGenerator(base_seed=1)
        
        planet1 = gen1.get_planet(0, 0)
        planet2 = gen2.get_planet(0, 0)
        
        # Планеты должны отличаться (хотя бы по имени)
        self.assertNotEqual(planet1.name, planet2.name)
    
    def test_galaxy_count(self):
        """Тест: генерируется ровно 8 галактик"""
        self.assertEqual(len(self.generator.galaxies), 8)
    
    def test_planets_per_galaxy(self):
        """Тест: в каждой галактике ровно 256 планет"""
        for galaxy in self.generator.galaxies:
            self.assertEqual(len(galaxy), 256)
    
    def test_planet_attributes_valid(self):
        """Тест: все атрибуты планеты в допустимых диапазонах"""
        planet = self.generator.get_planet(0, 0)
        
        # Позиция
        self.assertTrue(0 <= planet.x <= 255)
        self.assertTrue(0 <= planet.y <= 255)
        
        # Население
        self.assertTrue(0.5 <= planet.population <= 10.5)
        
        # Радиус
        self.assertTrue(1000 <= planet.radius <= 10000)
        
        # Технологии
        self.assertTrue(1 <= planet.tech_level <= 15)
        
        # Правительство и экономика - валидные enum значения
        self.assertIsInstance(planet.government, Government)
        self.assertIsInstance(planet.economy, Economy)
    
    def test_get_galaxy_valid(self):
        """Тест: получение галактики по валидному номеру"""
        for i in range(8):
            galaxy = self.generator.get_galaxy(i)
            self.assertEqual(len(galaxy), 256)
    
    def test_get_galaxy_invalid(self):
        """Тест: получение галактики по невалидному номеру вызывает ошибку"""
        with self.assertRaises(ValueError):
            self.generator.get_galaxy(-1)
        
        with self.assertRaises(ValueError):
            self.generator.get_galaxy(8)
    
    def test_get_planet_valid(self):
        """Тест: получение планеты по валидным номерам"""
        planet = self.generator.get_planet(0, 0)
        self.assertIsNotNone(planet)
        
        planet = self.generator.get_planet(7, 255)
        self.assertIsNotNone(planet)
    
    def test_get_planet_invalid_galaxy(self):
        """Тест: получение планеты с невалидным номером галактики"""
        with self.assertRaises(ValueError):
            self.generator.get_planet(-1, 0)
        
        with self.assertRaises(ValueError):
            self.generator.get_planet(8, 0)
    
    def test_get_planet_invalid_planet_number(self):
        """Тест: получение планеты с невалидным номером планеты"""
        with self.assertRaises(ValueError):
            self.generator.get_planet(0, -1)
        
        with self.assertRaises(ValueError):
            self.generator.get_planet(0, 256)
    
    def test_planet_name_not_empty(self):
        """Тест: имя планеты не пустое"""
        for i in range(10):  # Проверяем первые 10 планет
            planet = self.generator.get_planet(0, i)
            self.assertTrue(len(planet.name) > 0)
            self.assertTrue(len(planet.name) <= 8)  # Имя не слишком длинное
    
    def test_find_planet_by_name(self):
        """Тест: поиск планеты по имени"""
        # Получаем имя первой планеты
        first_planet = self.generator.get_planet(0, 0)
        
        # Ищем её по имени
        found = self.generator.find_planet_by_name(first_planet.name, 0)
        
        self.assertIsNotNone(found)
        self.assertEqual(found.name, first_planet.name)
        self.assertEqual(found.seed, first_planet.seed)
    
    def test_find_planet_by_name_not_found(self):
        """Тест: поиск несуществующей планеты возвращает None"""
        found = self.generator.find_planet_by_name("НЕСУЩЕСТВУЮЩАЯ", 0)
        self.assertIsNone(found)
    
    def test_planet_distance_calculation(self):
        """Тест: расчет расстояния между планетами"""
        planet1 = self.generator.get_planet(0, 0)
        planet2 = self.generator.get_planet(0, 1)
        
        distance = planet1.get_distance_to(planet2)
        
        # Расстояние должно быть положительным
        self.assertTrue(distance > 0)
        
        # Расстояние до самой себя должно быть 0
        self.assertEqual(planet1.get_distance_to(planet1), 0.0)


if __name__ == '__main__':
    unittest.main()