"""
demo_galaxy.py
Демонстрация работы генератора галактик.

Запусти этот файл, чтобы увидеть процедурную генерацию в действии!
Названия планет — на английском (аутентично), вывод — на русском.
"""

from universe.galaxy_generator import GalaxyGenerator


def main():
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ ПРОЦЕДУРНОЙ ГЕНЕРАЦИИ ГАЛАКТИКИ")
    print("Клон Elite 1984 - Фаза 2")
    print("=" * 70)
    print()
    
    # Создаем генератор с seed=0 (как в оригинале)
    generator = GalaxyGenerator(base_seed=0)
    
    print(f"✓ Сгенерировано {len(generator.galaxies)} галактик")
    print(f"✓ Каждая галактика содержит {len(generator.galaxies[0])} планет")
    print(f"✓ Всего планет: {len(generator.galaxies) * len(generator.galaxies[0])}")
    print()
    
    # Показываем информацию о первой галактике
    print("=" * 70)
    print("ГАЛАКТИКА 1 (первые 10 планет)")
    print("=" * 70)
    print()
    
    galaxy_1 = generator.get_galaxy(0)
    for i in range(10):
        planet = galaxy_1[i]
        print(f"Планета {i+1}: {planet.name}")
        print(f"  Позиция: ({planet.x}, {planet.y})")
        print(f"  Правительство: {planet.government.value}")
        print(f"  Экономика: {planet.economy.value}")
        print(f"  Население: {planet.population:.2f} млрд")
        print(f"  Технологии: уровень {planet.tech_level}")
        print()
    
    # Показываем информацию о конкретной планете
    print("=" * 70)
    print("ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ПЛАНЕТЕ")
    print("=" * 70)
    print()
    
    planet = generator.get_planet(0, 0)
    print(planet)
    print()
    
    # Демонстрируем расчет расстояния
    print("=" * 70)
    print("РАСЧЕТ РАССТОЯНИЙ")
    print("=" * 70)
    print()
    
    planet1 = generator.get_planet(0, 0)
    planet2 = generator.get_planet(0, 1)
    distance = planet1.get_distance_to(planet2)
    
    print(f"Расстояние от {planet1.name} до {planet2.name}: {distance:.2f} световых лет")
    print()
    
    # Демонстрируем детерминированность
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ ДЕТЕРМИНИРОВАННОСТИ")
    print("=" * 70)
    print()
    
    gen1 = GalaxyGenerator(base_seed=42)
    gen2 = GalaxyGenerator(base_seed=42)
    
    p1 = gen1.get_planet(0, 0)
    p2 = gen2.get_planet(0, 0)
    
    print(f"Генератор 1 (seed=42) - первая планета: {p1.name}")
    print(f"Генератор 2 (seed=42) - первая планета: {p2.name}")
    print()
    
    if p1.name == p2.name:
        print("✓ Одинаковый seed дает одинаковую вселенную!")
        print("✓ Это позволяет сохранять игру, храня только seed.")
    else:
        print("✗ Ошибка: планеты должны быть одинаковыми!")
    
    print()
    print("=" * 70)
    print("ГОТОВО!")
    print("=" * 70)
    print()
    print("Следующий шаг:")
    print("  - Создать космические станции (universe/station.py)")
    print("  - Создать карту галактики (gui/galaxy_screen.py)")
    print("  - Добавить механику гиперпрыжков (ship/physics.py)")
    print()


if __name__ == '__main__':
    main()