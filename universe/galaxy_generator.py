"""
universe/galaxy_generator.py
Процедурная генерация галактики в стиле Elite 1984.

Совет от ментора:
Это сердце игры! Оригинальный алгоритм Elite использовал линейный
конгруэнтный генератор (LCG) для создания детерминированной вселенной.
Из одного seed-числа генерируются 8 галактик по 256 планет каждая.

Важно: алгоритм детерминированный - одинаковый seed всегда дает
одинаковую вселенную. Это критично для сохранения игры!

Названия планет генерируются на английском (как в оригинале Elite 1984),
а описания — на русском языке для удобства игрока.
"""

from typing import List
from universe.planet import Planet, Government, Economy


class GalaxyGenerator:
    """
    Генератор галактик в стиле Elite 1984.
    
    Атрибуты:
        base_seed: базовое seed-число для генерации
        galaxies: список из 8 галактик, каждая содержит 256 планет
    
    Совет от ментора:
    Оригинальный алгоритм использовал "twisted" слова - специальный набор
    слогов для генерации названий планет. Мы используем оригинальные
    английские слоги из Elite 1984 для аутентичности.
    """
    
    # Оригинальные слоги из Elite 1984 для генерации названий планет
    # Эти слоги использовались в оригинальном коде игры на ZX Spectrum
    # Примеры имён: "ZAON", "REIN", "QUOR", "TION", "GEAR"
    SYLLABLES = [
        "AB", "ED", "RE", "IN", "IS", "ON", "TI", "LA", "QU", "OU",
        "GE", "ER", "AL", "EN", "AR", "AT", "OR", "IT", "VE", "US"
    ]
    
    # Описания планет на русском языке (для удобства игрока)
    DESCRIPTIONS_ADJECTIVES = [
        "удивительная", "необычная", "странная", "экзотическая",
        "древняя", "молодая", "бурная", "спокойная", "загадочная"
    ]
    
    DESCRIPTIONS_FEATURES = [
        "обширными океанами", "высокими горами", "густыми лесами",
        "бескрайними пустынями", "активными вулканами", "ледяными полярными шапками",
        "гигантскими каньонами", "радиоактивными пустошами", "биосветящимися равнинами"
    ]
    
    def __init__(self, base_seed: int = 0):
        """
        Инициализация генератора галактик.
        
        Args:
            base_seed: базовое seed-число (по умолчанию 0, как в оригинале)
        
        Совет от ментора:
        В оригинальной Elite base_seed был фиксированным. Мы позволяем
        менять его для создания разных вселенных (как в Elite: Dangerous).
        """
        self.base_seed = base_seed
        self.galaxies: List[List[Planet]] = []
        self._generate_all_galaxies()
    
    def _pseudo_random(self, seed: int) -> int:
        """
        Линейный конгруэнтный генератор псевдослучайных чисел.
        
        Формула: (a * seed + c) mod m
        Где a, c, m - специально подобранные константы
        
        Совет от ментора:
        В оригинале использовалась формула: seed = (seed * 0x8088405 + 1) & 0xFFFFFFFF
        Мы используем похожую, но адаптированную для Python.
        """
        # LCG с константами, дающими хороший период
        a = 214013
        c = 2531011
        m = 2**32
        return (a * seed + c) % m
    
    def _generate_name(self, seed: int) -> str:
        """
        Генерация названия планеты из seed (на английском, как в оригинале).
        
        Алгоритм из оригинальной Elite:
        1. Извлекаем 4 слога из seed
        2. Составляем слово
        3. Убираем последнюю букву (для благозвучия)
        
        Совет от ментора:
        В оригинале имена были типа "ZAON", "REIN", "QUOR", "TION"
        Алгоритм гарантировал, что имена будут звучать "по-научному"
        """
        temp_seed = seed
        syllables = []
        
        # Генерируем 4 слога (как в оригинале)
        for _ in range(4):
            index = temp_seed % len(self.SYLLABLES)
            syllables.append(self.SYLLABLES[index])
            temp_seed = self._pseudo_random(temp_seed)
        
        # Составляем имя из всех 4 слогов
        name = "".join(syllables)
        
        # Убираем последний символ для благозвучия (как в оригинале)
        if len(name) > 1:
            name = name[:-1]
        
        return name.capitalize()
    
    def _generate_planet(self, seed: int) -> Planet:
        """
        Генерация одной планеты из seed.
        
        Алгоритм:
        1. Генерируем имя (на английском)
        2. Определяем позицию (x, y)
        3. Определяем правительство и экономику
        4. Вычисляем население, производительность, радиус
        5. Определяем уровень технологий
        6. Генерируем описание (на русском)
        
        Совет от ментора:
        Все вычисления детерминированы - одинаковый seed всегда даст
        одинаковую планету. Это позволяет восстанавливать вселенную
        из сохранений без хранения всех данных.
        """
        temp_seed = seed
        
        # Генерируем имя (на английском)
        name = self._generate_name(seed)
        
        # Позиция на карте (0-255)
        x = temp_seed % 256
        temp_seed = self._pseudo_random(temp_seed)
        y = temp_seed % 256
        temp_seed = self._pseudo_random(temp_seed)
        
        # Правительство (8 типов)
        gov_index = temp_seed % 8
        government = list(Government)[gov_index]
        temp_seed = self._pseudo_random(temp_seed)
        
        # Экономика (8 типов)
        eco_index = temp_seed % 8
        economy = list(Economy)[eco_index]
        temp_seed = self._pseudo_random(temp_seed)
        
        # Население (0.5 - 10.0 миллиардов)
        population = (temp_seed % 1000) / 100.0 + 0.5
        temp_seed = self._pseudo_random(temp_seed)
        
        # Производительность (зависит от экономики и населения)
        base_productivity = (temp_seed % 500) + 100
        # Индустриальные экономики более продуктивны
        if "Industrial" in economy.value:
            base_productivity *= 2
        productivity = base_productivity * population
        temp_seed = self._pseudo_random(temp_seed)
        
        # Радиус (1000 - 10000 км)
        radius = (temp_seed % 9000) + 1000
        temp_seed = self._pseudo_random(temp_seed)
        
        # Уровень технологий (1-15)
        tech_level = (temp_seed % 15) + 1
        temp_seed = self._pseudo_random(temp_seed)
        
        # Описание планеты (на русском языке)
        adj_index = temp_seed % len(self.DESCRIPTIONS_ADJECTIVES)
        feature_index = (temp_seed // len(self.DESCRIPTIONS_ADJECTIVES)) % len(self.DESCRIPTIONS_FEATURES)
        temp_seed = self._pseudo_random(temp_seed)
        
        description = (
            f"Это {self.DESCRIPTIONS_ADJECTIVES[adj_index]} планета с "
            f"{self.DESCRIPTIONS_FEATURES[feature_index]}."
        )
        
        return Planet(
            seed=seed,
            name=name,
            x=x,
            y=y,
            government=government,
            economy=economy,
            population=population,
            productivity=productivity,
            radius=radius,
            tech_level=tech_level,
            description=description
        )
    
    def _generate_galaxy(self, galaxy_seed: int) -> List[Planet]:
        """
        Генерация одной галактики (256 планет).
        
        Args:
            galaxy_seed: seed для этой галактики
        
        Returns:
            Список из 256 планет
        
        Совет от ментора:
        В оригинальной Elite каждая галактика генерировалась из seed
        предыдущей галактики. Это создавало связанную вселенную.
        """
        planets = []
        current_seed = galaxy_seed
        
        for _ in range(256):
            planet = self._generate_planet(current_seed)
            planets.append(planet)
            # Обновляем seed для следующей планеты
            current_seed = self._pseudo_random(current_seed)
        
        return planets
    
    def _generate_all_galaxies(self):
        """
        Генерация всех 8 галактик.
        
        Совет от ментора:
        Каждая следующая галактика использует seed от последней планеты
        предыдущей галактики. Это создает детерминированную цепочку.
        """
        current_seed = self.base_seed
        
        for galaxy_num in range(8):
            galaxy = self._generate_galaxy(current_seed)
            self.galaxies.append(galaxy)
            # Seed для следующей галактики = seed последней планеты текущей
            current_seed = galaxy[-1].seed
    
    def get_galaxy(self, galaxy_number: int) -> List[Planet]:
        """
        Получить галактику по номеру (0-7).
        
        Args:
            galaxy_number: номер галактики (0-7)
        
        Returns:
            Список из 256 планет
        
        Raises:
            ValueError: если номер галактики вне диапазона 0-7
        """
        if not 0 <= galaxy_number <= 7:
            raise ValueError(f"Номер галактики должен быть 0-7, получено: {galaxy_number}")
        return self.galaxies[galaxy_number]
    
    def get_planet(self, galaxy_number: int, planet_number: int) -> Planet:
        """
        Получить конкретную планету.
        
        Args:
            galaxy_number: номер галактики (0-7)
            planet_number: номер планеты (0-255)
        
        Returns:
            Объект Planet
        
        Raises:
            ValueError: если номера вне допустимых диапазонов
        """
        if not 0 <= galaxy_number <= 7:
            raise ValueError(f"Номер галактики должен быть 0-7, получено: {galaxy_number}")
        if not 0 <= planet_number <= 255:
            raise ValueError(f"Номер планеты должен быть 0-255, получено: {planet_number}")
        
        return self.galaxies[galaxy_number][planet_number]
    
    def find_planet_by_name(self, name: str, galaxy_number: int) -> Planet:
        """
        Найти планету по имени в указанной галактике.
        
        Args:
            name: имя планеты (на английском)
            galaxy_number: номер галактики (0-7)
        
        Returns:
            Объект Planet или None, если не найдена
        """
        galaxy = self.get_galaxy(galaxy_number)
        name_upper = name.upper()
        
        for planet in galaxy:
            if planet.name.upper() == name_upper:
                return planet
        
        return None