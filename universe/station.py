"""
universe/station.py
Космические станции для процедурно генерируемой вселенной Elite.

ИСПРАВЛЕНИЯ:
1. ✅ Док-порт размещён В ЦЕНТРЕ передней грани (Z ≈ 77, а не 64)
2. ✅ Порт находится НА ПОВЕРХНОСТИ станции
3. ✅ Порт прямоугольный (ширина > высота)
4. ✅ Визуальные ориентиры для пилота
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from engine.math3d import Vector3
from engine.renderer import Mesh
import math


class StationType(Enum):
    CORIOLIS = "Кориолис"
    ORBIS = "Орбис"
    ICOSAHEDRON = "Икосаэдр"


@dataclass
class Station:
    station_id: int
    name: str
    station_type: StationType
    position: Vector3
    rotation_angle: float = 0.0
    rotation_speed: float = 0.3
    planet_name: Optional[str] = None
    docking_slot: Optional[Vector3] = None
    is_docking_open: bool = True
    scale: float = 0.4
    
    # =========================================================================
    # ГЕОМЕТРИЧЕСКИЕ КОНСТАНТЫ
    # =========================================================================
    # Передняя грань додекаэдра: центр находится на Z ≈ 77
    # (среднее между вершинами куба Z=64 и вершинами Z=103.5)
    DOCK_Z_POSITION = 77.0  # Позиция порта на оси Z
    DOCK_APPROACH_OFFSET = 5.0  # Запас перед портом
    
    def __post_init__(self):
        """Док-порт размещён на оси Z — в центре передней грани."""
        if self.docking_slot is None:
            if self.station_type == StationType.ORBIS:
                r_local = 64.0
                z_pos = (r_local + self.DOCK_APPROACH_OFFSET) * self.scale
                self.docking_slot = Vector3(0, 0, z_pos)
            else:
                # ✅ ИСПРАВЛЕНО: Используем правильную Z-координату центра грани
                z_pos = (self.DOCK_Z_POSITION + self.DOCK_APPROACH_OFFSET) * self.scale
                self.docking_slot = Vector3(0, 0, z_pos)
    
    def update(self, delta_time: float):
        """Вращение станции вокруг оси Y."""
        self.rotation_angle += self.rotation_speed * delta_time
        self.rotation_angle %= (2 * math.pi)
    
    def get_mesh(self, scale: Optional[float] = None) -> Mesh:
        s = scale if scale is not None else self.scale
        if s != self.scale:
            self.scale = s
            if self.station_type == StationType.CORIOLIS:
                z_pos = (self.DOCK_Z_POSITION + self.DOCK_APPROACH_OFFSET) * self.scale
                self.docking_slot = Vector3(0, 0, z_pos)
            else:
                r_local = 64 * 1.618033988749895 if self.station_type != StationType.ORBIS else 64.0
                z_pos = (r_local + self.DOCK_APPROACH_OFFSET) * self.scale
                self.docking_slot = Vector3(0, 0, z_pos)
        
        if self.station_type == StationType.CORIOLIS:
            return create_coriolis_station(self.scale)
        elif self.station_type == StationType.ORBIS:
            return create_orbis_station(self.scale)
        elif self.station_type == StationType.ICOSAHEDRON:
            return create_icosahedron_station(self.scale)
        return create_coriolis_station(self.scale)
    
    def get_world_docking_slot(self) -> Vector3:
        """Позиция слота в мировых координатах."""
        cos_a = math.cos(self.rotation_angle)
        sin_a = math.sin(self.rotation_angle)
        
        local_x = self.docking_slot.x
        local_z = self.docking_slot.z
        
        rotated_x = local_x * cos_a + local_z * sin_a
        rotated_z = -local_x * sin_a + local_z * cos_a
        
        return Vector3(
            self.position.x + rotated_x,
            self.position.y + self.docking_slot.y,
            self.position.z + rotated_z
        )
    
    def get_docking_normal(self) -> Vector3:
        """Вектор нормали порта в мировых координатах."""
        cos_a = math.cos(self.rotation_angle)
        sin_a = math.sin(self.rotation_angle)
        
        normal_x = sin_a
        normal_z = cos_a
        
        return Vector3(normal_x, 0.0, normal_z).normalize()
    
    def get_docking_approach_axis(self) -> Vector3:
        """Ось подхода к станции."""
        return self.get_docking_normal()
    
    def get_lateral_offset(self, ship_position: Vector3) -> float:
        """Боковое отклонение корабля от оси подхода."""
        to_ship = ship_position - self.position
        axis = self.get_docking_approach_axis()
        along = to_ship.dot(axis)
        along_vec = axis * along
        lateral = to_ship - along_vec
        return lateral.magnitude()
    
    def can_dock(self, ship_position: Vector3, ship_velocity: Vector3,
                 max_distance: float = 5.0, max_speed: float = 3.0,
                 max_lateral: float = 2.0) -> bool:
        """Жёсткая проверка стыковки."""
        if not self.is_docking_open:
            return False
        
        docking_pos = self.get_world_docking_slot()
        
        dx = ship_position.x - docking_pos.x
        dy = ship_position.y - docking_pos.y
        dz = ship_position.z - docking_pos.z
        dist_sq = dx*dx + dy*dy + dz*dz
        
        speed_sq = ship_velocity.magnitude() ** 2
        lateral = self.get_lateral_offset(ship_position)
        
        return (dist_sq <= max_distance**2 and
                speed_sq <= max_speed**2 and
                lateral <= max_lateral)
    
    def __str__(self) -> str:
        return (
            f"Станция: {self.name}\n"
            f"  Тип: {self.station_type.value}\n"
            f"  Орбита: {self.planet_name or 'Неизвестно'}\n"
            f"  Позиция: ({self.position.x:.1f}, {self.position.y:.1f}, {self.position.z:.1f})\n"
            f"  Угол: {self.rotation_angle:.2f} рад\n"
            f"  Док: {'Открыт' if self.is_docking_open else 'Закрыт'}"
        )


# ---------------------------------------------------------------------------
# 3D модели станций (wireframe)
# ---------------------------------------------------------------------------

def create_coriolis_station(scale: float = 0.4) -> Mesh:
    """
    Coriolis Station - реконструкция Elite 1984 (BBC Micro).
    
    ИСПРАВЛЕНО: Док-порт в центре передней грани на правильной Z-координате.
    """
    phi = 1.618033988749895
    inv_phi = 1.0 / phi
    S = 64
    
    vertices = []
    edges = []
    
    # =========================================================================
    # ЧАСТЬ 1: ДОДЕКАЭДР (20 вершин, 30 рёбер)
    # =========================================================================
    vertices.extend([
        Vector3(-S, -S, -S), Vector3(S, -S, -S), Vector3(S, S, -S), Vector3(-S, S, -S),
        Vector3(-S, -S, S), Vector3(S, -S, S), Vector3(S, S, S), Vector3(-S, S, S),
        Vector3(0, -S * inv_phi, -S * phi), Vector3(0, S * inv_phi, -S * phi),
        Vector3(0, -S * inv_phi, S * phi), Vector3(0, S * inv_phi, S * phi),
        Vector3(-S * inv_phi, -S * phi, 0), Vector3(S * inv_phi, -S * phi, 0),
        Vector3(-S * inv_phi, S * phi, 0), Vector3(S * inv_phi, S * phi, 0),
        Vector3(-S * phi, 0, -S * inv_phi), Vector3(S * phi, 0, -S * inv_phi),
        Vector3(-S * phi, 0, S * inv_phi), Vector3(S * phi, 0, S * inv_phi),
    ])
    edges.extend([
        (0, 8), (0, 12), (0, 16), (1, 8), (1, 13), (1, 17),
        (2, 9), (2, 15), (2, 17), (3, 9), (3, 14), (3, 16),
        (4, 10), (4, 12), (4, 18), (5, 10), (5, 13), (5, 19),
        (6, 11), (6, 15), (6, 19), (7, 11), (7, 14), (7, 18),
        (8, 9), (10, 11), (12, 13), (14, 15), (16, 17), (18, 19),
    ])
    
    # =========================================================================
    # ЧАСТЬ 2: ДОК-ПОРТ (прямоугольник В ЦЕНТРЕ передней грани)
    # =========================================================================
    # Передняя грань додекаэдра: пятиугольник
    # Вершины: (±64, ±64, 64) и (0, ±39.6, 103.5)
    # Центр грани: Z ≈ 77 (среднее арифметическое)
    
    dock_start_idx = len(vertices)
    
    # ✅ ИСПРАВЛЕНО: Порт на поверхности грани (Z=77)
    dock_width = S * 0.35    # ширина (по X) — ШИРОКИЙ
    dock_height = S * 0.20   # высота (по Y) — прямоугольный
    dock_z = 77.0            # ✅ ЦЕНТР передней грани
    
    # 4 угла прямоугольника
    corners = [
        (-dock_width, -dock_height),
        (dock_width, -dock_height),
        (dock_width, dock_height),
        (-dock_width, dock_height),
    ]
    
    for x, y in corners:
        vertices.append(Vector3(x, y, dock_z))
    
    # Рёбра прямоугольника
    edges.extend([
        (dock_start_idx + 0, dock_start_idx + 1),
        (dock_start_idx + 1, dock_start_idx + 2),
        (dock_start_idx + 2, dock_start_idx + 3),
        (dock_start_idx + 3, dock_start_idx + 0),
    ])
    
    # =========================================================================
    # ЧАСТЬ 3: ВНУТРЕННИЕ ОРИЕНТИРЫ (крест для точного захода)
    # =========================================================================
    cross_start_idx = len(vertices)
    # Горизонтальная линия
    vertices.append(Vector3(-dock_width * 0.9, 0, dock_z))
    vertices.append(Vector3(dock_width * 0.9, 0, dock_z))
    edges.append((cross_start_idx, cross_start_idx + 1))
    
    # Вертикальная линия
    vertices.append(Vector3(0, -dock_height * 0.9, dock_z))
    vertices.append(Vector3(0, dock_height * 0.9, dock_z))
    edges.append((cross_start_idx + 2, cross_start_idx + 3))
    
    # =========================================================================
    # Применяем масштабирование
    # =========================================================================
    vertices = [v * scale for v in vertices]
    
    return Mesh(vertices, edges)


def create_orbis_station(scale: float = 0.4) -> Mesh:
    """Orbis Station - плоское кольцо."""
    S = 64
    R_outer = S
    R_inner = S * 0.6
    height = S * 0.2
    segments = 12
    original_vertices = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        original_vertices.append(Vector3(R_outer * cos_a, height, R_outer * sin_a))
        original_vertices.append(Vector3(R_outer * cos_a, -height, R_outer * sin_a))
        original_vertices.append(Vector3(R_inner * cos_a, height, R_inner * sin_a))
        original_vertices.append(Vector3(R_inner * cos_a, -height, R_inner * sin_a))
    vertices = [v * scale for v in original_vertices]
    edges = []
    for i in range(segments):
        o_top, o_bot = i * 4, i * 4 + 1
        i_top, i_bot = i * 4 + 2, i * 4 + 3
        n_o_top, n_o_bot = ((i + 1) % segments) * 4, ((i + 1) % segments) * 4 + 1
        n_i_top, n_i_bot = ((i + 1) % segments) * 4 + 2, ((i + 1) % segments) * 4 + 3
        edges.extend([
            (o_top, n_o_top), (o_bot, n_o_bot), (i_top, n_i_top), (i_bot, n_i_bot),
            (o_top, o_bot), (i_top, i_bot), (o_top, i_top), (o_bot, i_bot)
        ])
    return Mesh(vertices, edges)


def create_icosahedron_station(scale: float = 0.4) -> Mesh:
    """Icosahedron Station."""
    phi = 1.618033988749895
    S = 64
    vertices = [
        Vector3(0, S * phi, 0), Vector3(0, -S * phi, 0),
        Vector3(S, S, -S * phi), Vector3(-S, S, -S * phi),
        Vector3(-S * phi, S, S), Vector3(S * phi, S, S),
        Vector3(S * phi, S, -S), Vector3(S, -S, S * phi),
        Vector3(-S, -S, S * phi), Vector3(-S * phi, -S, -S),
        Vector3(S * phi, -S, -S), Vector3(S * phi, -S, S),
    ]
    edges = [
        (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 7), (1, 8), (1, 9), (1, 10), (1, 11),
        (2, 3), (3, 4), (4, 5), (5, 6), (6, 2),
        (7, 8), (8, 9), (9, 10), (10, 11), (11, 7),
        (2, 9), (2, 10), (3, 9), (4, 8), (5, 7), (6, 10), (6, 11), (5, 11), (3, 8), (4, 7)
    ]
    vertices = [v * scale for v in vertices]
    return Mesh(vertices, edges)