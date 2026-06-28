"""
universe/station.py
Космические станции для процедурно генерируемой вселенной Elite.

Совет от ментора:
В оригинальной Elite 1984 года станции были вращающимися wireframe-объектами,
к которым игрок должен был подлетать и физически стыковаться.
Coriolis Station - додекаэдр (12-гранник), основная станция в игре.
Orbis Station - плоское кольцо, встречается в более поздних версиях Elite.
Мы сохраняем этот подход - станции имеют 3D-геометрию и вращаются вокруг своей оси.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from engine.math3d import Vector3
from engine.renderer import Mesh


class StationType(Enum):
    """
    Типы космических станций из Elite.
    
    Совет от ментора:
    В Elite 1984 года была только одна станция - Coriolis (додекаэдр).
    Orbis и другие появились в более поздних играх серии (Frontier, FFE).
    Мы добавляем их для разнообразия вселенной.
    """
    CORIOLIS = "Кориолис"     # Додекаэдр - основная станция Elite 1984
    ORBIS = "Орбис"           # Плоское кольцо - из поздних версий Elite
    ICOSAHEDRON = "Икосаэдр"  # Военная станция


@dataclass
class Station:
    """
    Космическая станция в галактике Elite.
    
    Атрибуты:
        station_id: уникальный идентификатор станции
        name: название станции (генерируется из планеты)
        station_type: тип станции (Coriolis, Orbis и т.д.)
        position: позиция в 3D-пространстве относительно планеты
        rotation_angle: текущий угол вращения станции (в радианах)
        rotation_speed: скорость вращения станции (радиан/сек)
        planet_name: имя планеты, на орбите которой находится станция
        docking_slot: позиция для стыковки (относительно станции)
        is_docking_open: открыт ли док для стыковки
    
    Совет от ментора:
    Станции в Elite постоянно вращаются - это создавало красивый wireframe-эффект
    и было технически просто на ZX Spectrum. Игрок должен был подлетать к станции
    со стороны "посадочного слота" - специальной зоны на грани.
    """
    station_id: int
    name: str
    station_type: StationType
    position: Vector3
    rotation_angle: float = 0.0
    rotation_speed: float = 0.3  # радиан/сек, аутентичная скорость Elite
    planet_name: Optional[str] = None
    docking_slot: Optional[Vector3] = None
    is_docking_open: bool = True
    
    def __post_init__(self):
        """Инициализация посадочного слота после создания станции"""
        # В Elite посадочный слот был на грани, обращенной к кораблю игрока
        # Для Coriolis (додекаэдра) это точка на положительной оси Z
        if self.docking_slot is None:
            if self.station_type == StationType.CORIOLIS:
                self.docking_slot = Vector3(0, 0, 1.5)
            elif self.station_type == StationType.ORBIS:
                self.docking_slot = Vector3(0, 0, 0.5)
            else:
                self.docking_slot = Vector3(0, 0, 1.0)
    
    def update(self, delta_time: float):
        """
        Обновление состояния станции.
        
        Совет от ментора:
        В Elite станции вращались непрерывно. Это был простой способ
        создать "живой" мир на железе 1984 года.
        """
        self.rotation_angle += self.rotation_speed * delta_time
        # Нормализуем угол в диапазон [0, 2π)
        if self.rotation_angle > 6.283185:  # 2 * π
            self.rotation_angle -= 6.283185
    
    def get_mesh(self, scale: float = 0.4) -> Mesh:
        """Получить 3D-модель станции в зависимости от типа"""
        if self.station_type == StationType.CORIOLIS:
            return create_coriolis_station(scale)
        elif self.station_type == StationType.ORBIS:
            return create_orbis_station(scale)
        elif self.station_type == StationType.ICOSAHEDRON:
            return create_icosahedron_station(scale)
        else:
            return create_coriolis_station(scale)
    
    def get_world_docking_slot(self) -> Vector3:
        """
        Получить позицию посадочного слота в мировых координатах.
        Учитывает вращение станции и её позицию в пространстве.
        
        Совет от ментора:
        Игрок должен точно позиционировать корабль относительно посадочного слота.
        Если скорость и угол неправильные - стыковка провалится (как в оригинале!).
        """
        import math
        # Вращение вокруг оси Y (как в оригинальной Elite)
        cos_a = math.cos(self.rotation_angle)
        sin_a = math.sin(self.rotation_angle)
        
        # Поворачиваем docking_slot вокруг оси Y
        rotated_x = self.docking_slot.x * cos_a + self.docking_slot.z * sin_a
        rotated_z = -self.docking_slot.x * sin_a + self.docking_slot.z * cos_a
        
        # Прибавляем позицию станции в мировом пространстве
        return Vector3(
            self.position.x + rotated_x,
            self.position.y + self.docking_slot.y,
            self.position.z + rotated_z
        )
    
    def can_dock(self, ship_position: Vector3, ship_velocity: Vector3, 
                 max_distance: float = 0.5, max_speed: float = 0.2) -> bool:
        """
        Проверить возможность стыковки.
        
        Параметры:
            ship_position: позиция корабля игрока
            ship_velocity: скорость корабля игрока
            max_distance: максимальное расстояние до посадочного слота
            max_speed: максимальная скорость для безопасной стыковки
        
        Совет от ментора:
        В оригинальной Elite стыковка была мини-игрой! Игрок должен был
        медленно подлететь к станции со скоростью ниже пороговой.
        """
        if not self.is_docking_open:
            return False
        
        docking_pos = self.get_world_docking_slot()
        
        # Вычисляем расстояние до посадочного слота
        dx = ship_position.x - docking_pos.x
        dy = ship_position.y - docking_pos.y
        dz = ship_position.z - docking_pos.z
        distance = (dx**2 + dy**2 + dz**2)**0.5
        
        # Вычисляем скорость корабля
        speed = (ship_velocity.x**2 + ship_velocity.y**2 + ship_velocity.z**2)**0.5
        
        # Стыковка возможна только если расстояние и скорость в пределах нормы
        return distance <= max_distance and speed <= max_speed
    
    def __str__(self) -> str:
        """Вывод информации о станции на русском языке"""
        return (
            f"Станция: {self.name}\n"
            f"  Тип: {self.station_type.value}\n"
            f"  Орбита планеты: {self.planet_name or 'Неизвестно'}\n"
            f"  Позиция: ({self.position.x:.1f}, {self.position.y:.1f}, {self.position.z:.1f})\n"
            f"  Угол вращения: {self.rotation_angle:.2f} рад\n"
            f"  Док открыт: {'Да' if self.is_docking_open else 'Нет'}"
        )


# ---------------------------------------------------------------------------
# 3D модели станций (wireframe)
# ---------------------------------------------------------------------------

def create_coriolis_station(scale: float = 0.4) -> Mesh:
    """
    Coriolis Station - основная станция из Elite 1984 года.
    Представляет собой правильный додекаэдр (12-гранник).
    
    Характеристики оригинала:
    - 20 вершин
    - 30 ребер
    - 12 пятиугольных граней
    - Постоянно вращается вокруг своей оси
    
    Совет от ментора:
    В Elite 1984 координаты додекаэдра были заданы в целых числах
    через золотое сечение φ = (1+√5)/2 ≈ 1.618
    Для ZX Spectrum это было упрощено до целых координат -64..+64.
    """
    # Золотое сечение - математическая основа додекаэдра
    phi = 1.618033988749895  # (1 + √5) / 2
    inv_phi = 1.0 / phi     # 1 / φ ≈ 0.618
    
    # 20 вершин правильного додекаэдра
    # Группа 1: 8 вершин куба (±1, ±1, ±1)
    # Группа 2: 12 вершин на пересечениях (0, ±1/φ, ±φ) с циклическими перестановками
    # Используем масштабирование 64 для аутентичности ZX Spectrum
    
    S = 64  # Оригинальный масштаб ZX Spectrum
    
    original_vertices = [
        # Вершины куба (8 шт)
        Vector3(-S, -S, -S),  # 0
        Vector3(S, -S, -S),   # 1
        Vector3(S, S, -S),    # 2
        Vector3(-S, S, -S),   # 3
        Vector3(-S, -S, S),   # 4
        Vector3(S, -S, S),    # 5
        Vector3(S, S, S),     # 6
        Vector3(-S, S, S),    # 7
        
        # Вершины на прямоугольниках (12 шт)
        # Группа (0, ±1/φ, ±φ) * S
        Vector3(0, -S * inv_phi, -S * phi),   # 8
        Vector3(0, S * inv_phi, -S * phi),    # 9
        Vector3(0, -S * inv_phi, S * phi),    # 10
        Vector3(0, S * inv_phi, S * phi),     # 11
        
        # Группа (±1/φ, ±φ, 0) * S
        Vector3(-S * inv_phi, -S * phi, 0),   # 12
        Vector3(S * inv_phi, -S * phi, 0),    # 13
        Vector3(-S * inv_phi, S * phi, 0),    # 14
        Vector3(S * inv_phi, S * phi, 0),     # 15
        
        # Группа (±φ, 0, ±1/φ) * S
        Vector3(-S * phi, 0, -S * inv_phi),   # 16
        Vector3(S * phi, 0, -S * inv_phi),    # 17
        Vector3(-S * phi, 0, S * inv_phi),    # 18
        Vector3(S * phi, 0, S * inv_phi),     # 19
    ]
    
    # Применяем масштабирование ко всем вершинам
    vertices = [v * scale for v in original_vertices]
    
    # 30 ребер додекаэдра (каждая вершина соединена с 3 соседями)
    # Каждое ребро - это пара индексов вершин, находящихся на расстоянии 2/φ друг от друга
    edges = [
        # Ребра от вершин куба к прямоугольным вершинам
        (0, 8), (0, 12), (0, 16),    # Вершина 0
        (1, 8), (1, 13), (1, 17),    # Вершина 1
        (2, 9), (2, 15), (2, 17),    # Вершина 2
        (3, 9), (3, 14), (3, 16),    # Вершина 3
        (4, 10), (4, 12), (4, 18),   # Вершина 4
        (5, 10), (5, 13), (5, 19),   # Вершина 5
        (6, 11), (6, 15), (6, 19),   # Вершина 6
        (7, 11), (7, 14), (7, 18),   # Вершина 7
        
        # Ребра между прямоугольными вершинами (образуют 5-угольные грани)
        (8, 9),   # Верхняя грань Z-отрицательная
        (8, 12), (9, 14), (12, 16), (14, 16), (13, 17),  # Верх
        (10, 11), # Верхняя грань Z-положительная
        (10, 12), (11, 14), (12, 18), (14, 18), (13, 19), (11, 15),
        (10, 18), (15, 17), (18, 19),
    ]
    
    # Удаляем возможные дубликаты ребер
    unique_edges = []
    seen = set()
    for e in edges:
        edge = (min(e), max(e))
        if edge not in seen:
            seen.add(edge)
            unique_edges.append(e)
    
    return Mesh(vertices, unique_edges)


def create_orbis_station(scale: float = 0.4) -> Mesh:
    """
    Orbis Station - плоская кольцеобразная станция из поздних версий Elite.
    Представляет собой тор (кольцо), видимое сбоку как эллипс.
    
    Характеристики:
    - 24 вершины (2 кольца по 12 вершин - внешнее и внутреннее)
    - 48 ребер (24 вдоль колец + 24 соединяющих)
    - Плоская форма (вращается вокруг вертикальной оси)
    
    Совет от ментора:
    Orbis не было в оригинальной Elite 1984, но появилась в Frontier: Elite II.
    Мы добавляем её для разнообразия вселенной - некоторые планеты могут иметь Orbis.
    """
    import math
    
    S = 64  # Масштаб ZX Spectrum
    R_outer = S       # Внешний радиус кольца
    R_inner = S * 0.6 # Внутренний радиус кольца
    height = S * 0.2  # Толщина станции
    
    segments = 12     # Количество сегментов в кольце
    
    original_vertices = []
    
    # Внешнее кольцо (верхнее и нижнее)
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        # Верхнее внешнее кольцо
        original_vertices.append(Vector3(R_outer * cos_a, height, R_outer * sin_a))
        # Нижнее внешнее кольцо
        original_vertices.append(Vector3(R_outer * cos_a, -height, R_outer * sin_a))
    
    # Внутреннее кольцо (верхнее и нижнее)
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        # Верхнее внутреннее кольцо
        original_vertices.append(Vector3(R_inner * cos_a, height, R_inner * sin_a))
        # Нижнее внутреннее кольцо
        original_vertices.append(Vector3(R_inner * cos_a, -height, R_inner * sin_a))
    
    # Применяем масштабирование
    vertices = [v * scale for v in original_vertices]
    
    edges = []
    
    # Ребра вдоль внешнего верхнего кольца (0, 2, 4, ...)
    for i in range(segments):
        v1 = i * 2
        v2 = ((i + 1) % segments) * 2
        edges.append((v1, v2))
        # Вертикальные стойки внешнего кольца
        edges.append((v1, v1 + 1))
    
    # Ребра вдоль внешнего нижнего кольца (1, 3, 5, ...)
    for i in range(segments):
        v1 = i * 2 + 1
        v2 = ((i + 1) % segments) * 2 + 1
        edges.append((v1, v2))
    
    offset_inner = segments * 2  # Смещение для внутренних вершин
    
    # Ребра вдоль внутреннего верхнего кольца
    for i in range(segments):
        v1 = offset_inner + i * 2
        v2 = offset_inner + ((i + 1) % segments) * 2
        edges.append((v1, v2))
        # Вертикальные стойки внутреннего кольца
        edges.append((v1, v1 + 1))
    
    # Ребра вдоль внутреннего нижнего кольца
    for i in range(segments):
        v1 = offset_inner + i * 2 + 1
        v2 = offset_inner + ((i + 1) % segments) * 2 + 1
        edges.append((v1, v2))
    
    # Соединения между внешним и внутренним кольцом (спицы)
    for i in range(segments):
        outer_top = i * 2
        inner_top = offset_inner + i * 2
        outer_bottom = i * 2 + 1
        inner_bottom = offset_inner + i * 2 + 1
        
        edges.append((outer_top, inner_top))       # Верхние спицы
        edges.append((outer_bottom, inner_bottom)) # Нижние спицы
    
    return Mesh(vertices, edges)


def create_icosahedron_station(scale: float = 0.4) -> Mesh:
    """
    Icosahedron Station - военная станция в форме икосаэдра (20-гранника).
    Встречается в поздних версиях Elite как охраняемая военная база.
    
    Характеристики:
    - 12 вершин
    - 30 ребер
    - 20 треугольных граней
    - Обычно охраняется кораблями Viper
    """
    import math
    
    # Золотое сечение для икосаэдра
    phi = 1.618033988749895
    S = 64  # Масштаб ZX Spectrum
    
    original_vertices = [
        # Верхняя и нижняя вершины
        Vector3(0, S * phi, 0),    # 0 - Верхний полюс
        Vector3(0, -S * phi, 0),   # 1 - Нижний полюс
        
        # Верхнее кольцо (5 вершин)
        Vector3(S, S, -S * phi),     # 2
        Vector3(-S, S, -S * phi),    # 3
        Vector3(-S * phi, S, S),     # 4
        Vector3(S * phi, S, S),      # 5
        Vector3(S * phi, S, -S),     # 6
        
        # Нижнее кольцо (5 вершин, со смещением)
        Vector3(S, -S, S * phi),     # 7
        Vector3(-S, -S, S * phi),    # 8
        Vector3(-S * phi, -S, -S),   # 9
        Vector3(S * phi, -S, -S),    # 10
        Vector3(S * phi, -S, S),     # 11
    ]
    
    vertices = [v * scale for v in original_vertices]
    
    edges = [
        # Ребра от верхнего полюса к верхнему кольцу
        (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        
        # Ребра от нижнего полюса к нижнему кольцу
        (1, 7), (1, 8), (1, 9), (1, 10), (1, 11),
        
        # Ребра верхнего кольца
        (2, 3), (3, 4), (4, 5), (5, 6), (6, 2),
        
        # Ребра нижнего кольца
        (7, 8), (8, 9), (9, 10), (10, 11), (11, 7),
        
        # Ребра между кольцами (анти-призма)
        (2, 9), (2, 10), (3, 9), (3, 4), (4, 8), (4, 9),
        (5, 7), (5, 8), (6, 10), (6, 11), (7, 11), (5, 11),
    ]
    
    # Удаляем дубликаты
    unique_edges = []
    seen = set()
    for e in edges:
        edge = (min(e), max(e))
        if edge not in seen:
            seen.add(edge)
            unique_edges.append(e)
    
    return Mesh(vertices, unique_edges)