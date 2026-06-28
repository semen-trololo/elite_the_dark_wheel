"""
universe/planet.py
Класс планеты для процедурно генерируемой вселенной Elite.

Совет от ментора:
В оригинальной Elite 1984 года все данные планеты (имя, экономика, правительство)
генерировались из seed-числа. Это позволяло хранить только seed, а не все данные.
Мы сохраняем этот подход - каждая планета может быть восстановлена из своего seed.

Имена планет — на английском (аутентично), а описания и вывод — на русском
(для удобства игрока).
"""

from dataclasses import dataclass
from enum import Enum


class Government(Enum):
    """Типы правительств из оригинальной Elite (на английском как термины)"""
    ANARCHY = "Анархия"
    FEUDAL = "Феодализм"
    MULTI_GOVERNMENT = "Мульти-правительство"
    DICTATORSHIP = "Диктатура"
    COMMUNIST = "Коммунизм"
    CONFEDERACY = "Конфедерация"
    DEMOCRACY = "Демократия"
    CORPORATE_STATE = "Корпоративное государство"


class Economy(Enum):
    """Типы экономик из оригинальной Elite (на английском как термины)"""
    RICH_INDUSTRIAL = "Богатая индустриальная"
    AVERAGE_INDUSTRIAL = "Средняя индустриальная"
    POOR_INDUSTRIAL = "Бедная индустриальная"
    RICH_AGRICULTURAL = "Богатая аграрная"
    AVERAGE_AGRICULTURAL = "Средняя аграрная"
    POOR_AGRICULTURAL = "Бедная аграрная"
    MAINLY_INDUSTRIAL = "В основном индустриальная"
    MAINLY_AGRICULTURAL = "В основном аграрная"


@dataclass
class Planet:
    """
    Планета в галактике Elite.
    
    Атрибуты:
        seed: уникальное число, из которого генерируются все данные планеты
        name: процедурно сгенерированное имя (на английском, как в оригинале)
        x: позиция на карте галактики (0-255)
        y: позиция на карте галактики (0-255)
        government: тип правительства
        economy: тип экономики
        population: население в миллиардах
        productivity: производительность в миллионах кредитов
        radius: радиус в километрах
        tech_level: уровень технологий (1-15)
        description: описание планеты (на русском)
    
    Совет от ментора:
    Все атрибуты (кроме seed) могут быть вычислены из seed.
    Это позволяет сохранять игру, храня только seed планеты.
    """
    seed: int
    name: str
    x: int
    y: int
    government: Government
    economy: Economy
    population: float  # в миллиардах
    productivity: float  # в миллионах кредитов
    radius: int  # в километрах
    tech_level: int  # 1-15
    description: str
    
    def __str__(self) -> str:
        """Вывод информации о планете на русском языке"""
        return (
            f"Планета: {self.name}\n"
            f"  Позиция: ({self.x}, {self.y})\n"
            f"  Правительство: {self.government.value}\n"
            f"  Экономика: {self.economy.value}\n"
            f"  Население: {self.population:.2f} млрд\n"
            f"  Производительность: {self.productivity:.0f} млн CR\n"
            f"  Радиус: {self.radius} км\n"
            f"  Технологии: уровень {self.tech_level}\n"
            f"  Описание: {self.description}"
        )
    
    def get_distance_to(self, other: 'Planet') -> float:
        """
        Вычислить расстояние до другой планеты.
        Используется для расчета стоимости гиперпрыжка.
        
        Совет от ментора:
        В оригинальной Elite расстояние вычислялось по формуле:
        sqrt((x2-x1)^2 + (y2-y1)^2) / 10 световых лет
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx**2 + dy**2)**0.5 / 10.0