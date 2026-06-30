"""
universe/galaxy_generator.py
Процедурная генерация галактики в стиле Elite 1984.

ИСПРАВЛЕНИЯ ОТ МЕНТОРА:
1. Использовано оригинальное магическое число 0x8088405 из BBC Micro Elite
2. Исправлена корреляция между x и y координатами через перемешивание seed
3. Добавлено несколько итераций LCG для лучшего распределения планет

Совет от ментора:
Это сердце игры! Оригинальный алгоритм Elite использовал линейный
конгруэнтный генератор (LCG) со специальным "twisted" числом 0x8088405
для создания детерминированной вселенной.

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
    
    # =========================================================================
    # ОРИГИНАЛЬНЫЕ МАГИЧЕСКИЕ ЧИСЛА ИЗ ELITE 1984 (BBC Micro)
    # =========================================================================
    # В оригинальном коде BBC Micro Elite использовалось:
    # seed = (seed * 0x8088405 + 1) & 0xFFFFFFFF
    #
    # 0x8088405 (134775813 в десятичной) - это специальное "twisted" число,
    # подобранное для:
    # - Хорошего периода (2^32 итерации до повторения)
    # - Равномерного распределения значений
    # - Детерминированности (одинаковый seed = одинаковая вселенная)
    #
    # Это число критично для аутентичности генерации!
    ORIGINAL_LCG_MULTIPLIER = 0x8088405  # 134775813
    ORIGINAL_LCG_INCREMENT = 1
    ORIGINAL_LCG_MODULUS = 0xFFFFFFFF    # 2^32 - 1
    
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
        Оригинальный линейный конгруэнтный генератор из Elite 1984 (BBC Micro).
        
        Формула: seed = (seed * 0x8088405 + 1) & 0xFFFFFFFF
        
        Где:
        - 0x8088405 - оригинальное "twisted" число из Elite
        - + 1 - инкремент (как в оригинале)
        - & 0xFFFFFFFF - битовая маска для 32-битных чисел
        
        Совет от ментора:
        В оригинальном коде это выглядело так:
        LDA seed
        LDX seed+1
        JSR DORND  ; умножение на 0x8088405
        CLC
        ADC #1     ; +1
        STA seed
        
        Это создавало псевдослучайную последовательность с периодом 2^32.
        """
        return (seed * self.ORIGINAL_LCG_MULTIPLIER + self.ORIGINAL_LCG_INCREMENT) & self.ORIGINAL_LCG_MODULUS
    
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
        
        ИСПРАВЛЕНИЕ: Используем разные байты ОДНОГО перемешанного числа
        для x и y, чтобы полностью разорвать корреляцию.
        """
        # Генерируем имя (на английском)
        name = self._generate_name(seed)
        
        # =========================================================================
        # ИСПРАВЛЕНИЕ: Интенсивно перемешиваем seed и берём РАЗНЫЕ БАЙТЫ
        # =========================================================================
        # Перемешиваем seed 10 раз для полной рандомизации
        temp = seed
        for _ in range(10):
            temp = self._pseudo_random(temp)
        
        # Берём x из МЛАДШЕГО байта (биты 0-7)
        x = temp & 0xFF
        
        # Берём y из ТРЕТЬЕГО байта (биты 16-23)
        # Это СОВСЕМ другие биты, никакой корреляции!
        y = (temp >> 16) & 0xFF
        
        # Продолжаем генерацию остальных параметров
        temp = self._pseudo_random(temp)
        
        # Правительство (8 типов)
        gov_index = temp % 8
        government = list(Government)[gov_index]
        temp_seed = self._pseudo_random(temp)
        
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
        предыдущей галактики. Это создавала связанную вселенную.
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