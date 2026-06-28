"""
ship/physics.py
Физика и навигация корабля в стиле Elite 1984 года.

Совет от ментора:
В оригинальной Elite 1984 стыковка была одной из самых сложных механик!
Игрок должен был:
1. Подлететь к вращающейся станции Coriolis
2. Совместить свой корабль с посадочным слотом
3. Снизить скорость почти до нуля
4. Правильно сориентироваться

Многие игроки покупали Docking Computer за 1500 CR, чтобы автоматизировать это.
Мы реализуем обе системы: ручную стыковку и автопилот.
"""

from typing import Optional, Tuple
from engine.math3d import Vector3, Matrix3x3
import math
import random


class DockingComputer:
    """
    Автоматическая система стыковки (Docking Computer из Elite).
    
    Совет от ментора:
    В оригинальной Elite Docking Computer стоил 1500 CR и был одним из
    самых популярных покупок. Он автоматически рассчитывал траекторию
    и управлял кораблём для безопасной стыковки.
    
    Алгоритм:
    1. Рассчитать траекторию к посадочному слоту станции
    2. Выровнять корабль по оси Z станции
    3. Медленно приблизиться, контролируя скорость
    4. Завершить стыковку при достижении слота
    """
    
    def __init__(self):
        self.is_active = False
        self.target_station = None
        self.phase = "IDLE"  # IDLE, APPROACH, ALIGN, DOCK
        self.approach_distance = 20.0
        self.docking_speed = 0.5
        self.alignment_tolerance = 0.1
    
    def activate(self, station):
        """
        Активировать компьютер стыковки.
        
        Args:
            station: целевая станция для стыковки
        """
        if not station or not station.is_docking_open:
            return False
        
        self.is_active = True
        self.target_station = station
        self.phase = "APPROACH"
        return True
    
    def deactivate(self):
        """Деактивировать компьютер стыковки."""
        self.is_active = False
        self.target_station = None
        self.phase = "IDLE"
    
    def update(self, ship, delta_time: float) -> Tuple[Vector3, Vector3]:
        """
        Рассчитать необходимые управляющие воздействия для стыковки.
        
        Args:
            ship: корабль игрока
            delta_time: время с прошлого кадра
        
        Returns:
            Кортеж (thrust_vector, angular_velocity) - тяга и угловая скорость
        
        Совет от ментора:
        Алгоритм использует PD-регулятор (Proportional-Derivative)
        для плавного и точного управления кораблём.
        Это классический подход в робототехнике и авионике.
        """
        if not self.is_active or not self.target_station:
            return Vector3(0, 0, 0), Vector3(0, 0, 0)
        
        # Получаем мировую позицию посадочного слота
        docking_slot = self.target_station.get_world_docking_slot()
        station_pos = self.target_station.position
        
        # Вычисляем вектор к цели
        to_target = docking_slot - ship.position
        distance = to_target.magnitude()
        
        # Фаза 1: APPROACH - приближение к станции
        if self.phase == "APPROACH":
            if distance < self.approach_distance:
                self.phase = "ALIGN"
            
            # Направление к цели
            direction = to_target.normalize()
            
            # Выравниваем корабль по направлению движения
            # Используем cross product для определения ошибки ориентации
            forward_error = ship.forward.cross(direction)
            
            # PD-регулятор для угловой скорости
            angular_velocity = forward_error * 3.0  # P-компонента
            
            # Тяга вперед с контролем скорости
            current_speed = ship.velocity.magnitude()
            target_speed = min(5.0, distance * 0.5)  # Медленнее ближе к цели
            
            if current_speed < target_speed:
                thrust = direction * 10.0
            else:
                thrust = direction * -5.0  # Торможение
            
            return thrust, angular_velocity
        
        # Фаза 2: ALIGN - точное выравнивание
        elif self.phase == "ALIGN":
            # Вычисляем ориентацию посадочного слота
            # В идеале корабль должен быть повёрнут "спиной" к станции
            target_forward = (station_pos - ship.position).normalize()
            
            # Ошибка ориентации
            forward_error = ship.forward.cross(target_forward)
            angular_velocity = forward_error * 5.0  # Более точное выравнивание
            
            # Очень медленное приближение
            direction = to_target.normalize()
            target_speed = self.docking_speed
            
            current_speed = ship.velocity.magnitude()
            if current_speed < target_speed:
                thrust = direction * 2.0
            else:
                thrust = direction * -2.0
            
            # Проверяем, достаточно ли выровнены
            alignment_error = forward_error.magnitude()
            if alignment_error < self.alignment_tolerance and distance < 5.0:
                self.phase = "DOCK"
            
            return thrust, angular_velocity
        
        # Фаза 3: DOCK - финальное сближение
        elif self.phase == "DOCK":
            # Почти нулевая тяга, только коррекция
            direction = to_target.normalize()
            thrust = direction * 0.5
            angular_velocity = Vector3(0, 0, 0)
            
            # Проверяем успешность стыковки
            if distance < 1.0 and ship.velocity.magnitude() < 0.2:
                self.deactivate()
                return Vector3(0, 0, 0), Vector3(0, 0, 0)
            
            return thrust, angular_velocity
        
        return Vector3(0, 0, 0), Vector3(0, 0, 0)
    
    def get_status(self) -> str:
        """Получить текущий статус компьютера стыковки."""
        if not self.is_active:
            return "НЕАКТИВЕН"
        
        status_map = {
            "APPROACH": "ПРИБЛИЖЕНИЕ",
            "ALIGN": "ВЫРАВНИВАНИЕ",
            "DOCK": "СТЫКОВКА"
        }
        return status_map.get(self.phase, "НЕИЗВЕСТНО")


class HyperspaceNavigator:
    """
    Навигатор гиперпространства для межзвёздных перелётов.
    
    Совет от ментора:
    В Elite 1984 гиперпрыжок состоял из нескольких фаз:
    1. CHARGING - зарядка гипердвигателя (2-3 секунды)
    2. TUNNEL - переход через туннель (звёзды растягиваются)
    3. EXIT - выход из гиперпространства
    
    Максимальная дальность прыжка зависела от топлива (70 св. лет в начале).
    Стоимость: 0.1 CR за световой год.
    """
    
    # Фазы гиперпрыжка
    PHASE_IDLE = "IDLE"
    PHASE_CHARGING = "CHARGING"
    PHASE_TUNNEL = "TUNNEL"
    PHASE_EXIT = "EXIT"
    PHASE_COMPLETE = "COMPLETE"
    
    # Временные параметры (в секундах)
    CHARGING_DURATION = 2.0
    TUNNEL_DURATION = 3.0
    EXIT_DURATION = 1.0
    
    def __init__(self):
        self.phase = self.PHASE_IDLE
        self.timer = 0.0
        self.target_planet = None
        self.source_planet = None
        self.tunnel_stars = []  # Звёзды для эффекта "туннеля"
        self._generate_tunnel_stars()
    
    def _generate_tunnel_stars(self):
        """
        Генерация звёзд для эффекта гиперпространственного туннеля.
        
        Совет от ментора:
        В оригинальной Elite эффект гиперпрыжка создавался простым
        растягиванием точек-звёзд в линии. Это было гениально просто
        и работало даже на ZX Spectrum с 48 КБ памяти!
        """
        self.tunnel_stars = []
        for _ in range(100):
            # Случайная позиция вокруг корабля
            star = Vector3(
                random.uniform(-50, 50),
                random.uniform(-50, 50),
                random.uniform(10, 100)
            )
            # Случайная скорость "растягивания"
            velocity = random.uniform(20, 50)
            self.tunnel_stars.append((star, velocity))
    
    def start_jump(self, ship, target_planet) -> bool:
        """
        Начать гиперпрыжок.
        
        Args:
            ship: корабль игрока
            target_planet: целевая планета
        
        Returns:
            True если прыжок успешно начат
        
        Совет от ментора:
        Перед прыжком всегда проверяем:
        1. Достаточно ли топлива
        2. Не пристыкован ли корабль
        3. Не находится ли уже в гиперпространстве
        """
        if self.phase != self.PHASE_IDLE:
            return False
        
        if not hasattr(ship, 'current_planet') or not ship.current_planet:
            return False
        
        # Проверяем возможность прыжка через методы корабля
        if not ship.can_hyperspace_jump(target_planet):
            return False
        
        # Начинаем прыжок через корабль (списывает топливо и деньги)
        if not ship.start_hyperspace_jump(target_planet):
            return False
        
        # Сохраняем параметры прыжка
        self.source_planet = ship.current_planet
        self.target_planet = target_planet
        self.phase = self.PHASE_CHARGING
        self.timer = 0.0
        
        return True
    
    def update(self, ship, delta_time: float) -> bool:
        """
        Обновление состояния гиперпрыжка.
        
        Args:
            ship: корабль игрока
            delta_time: время с прошлого кадра
        
        Returns:
            True если прыжок завершён (можно вернуть управление игроку)
        
        Совет от ментора:
        Возвращаем True только когда прыжок полностью завершён и
        игрок снова может управлять кораблём. Во время всех фаз
        управление заблокировано.
        """
        if self.phase == self.PHASE_IDLE:
            return False
        
        self.timer += delta_time
        
        # Фаза 1: CHARGING - зарядка двигателя
        if self.phase == self.PHASE_CHARGING:
            if self.timer >= self.CHARGING_DURATION:
                self.phase = self.PHASE_TUNNEL
                self.timer = 0.0
                self._generate_tunnel_stars()
            return False
        
        # Фаза 2: TUNNEL - переход через гиперпространство
        elif self.phase == self.PHASE_TUNNEL:
            # Обновляем звёзды туннеля (они "летят" мимо)
            for i, (star, velocity) in enumerate(self.tunnel_stars):
                star.z -= velocity * delta_time
                # Если звезда пролетела - переносим её назад
                if star.z < 10:
                    star.z = 100
                    star.x = random.uniform(-50, 50)
                    star.y = random.uniform(-50, 50)
            
            if self.timer >= self.TUNNEL_DURATION:
                self.phase = self.PHASE_EXIT
                self.timer = 0.0
            return False
        
        # Фаза 3: EXIT - выход из гиперпространства
        elif self.phase == self.PHASE_EXIT:
            if self.timer >= self.EXIT_DURATION:
                # Завершаем прыжок через корабль
                ship.complete_hyperspace_jump()
                self.phase = self.PHASE_COMPLETE
                self.timer = 0.0
            return False
        
        # Фаза 4: COMPLETE - прыжок завершён
        elif self.phase == self.PHASE_COMPLETE:
            # Сбрасываем состояние
            self.phase = self.PHASE_IDLE
            self.target_planet = None
            self.source_planet = None
            return True  # Возвращаем управление игроку
        
        return False
    
    def get_tunnel_stars(self):
        """Получить звёзды туннеля для отрисовки."""
        if self.phase == self.PHASE_TUNNEL:
            return self.tunnel_stars
        return []
    
    def get_progress(self) -> float:
        """
        Получить прогресс прыжка (0.0 - 1.0).
        
        Используется для UI - индикатор прогресса гиперпрыжка.
        """
        if self.phase == self.PHASE_CHARGING:
            return self.timer / self.CHARGING_DURATION * 0.3
        elif self.phase == self.PHASE_TUNNEL:
            return 0.3 + (self.timer / self.TUNNEL_DURATION) * 0.5
        elif self.phase == self.PHASE_EXIT:
            return 0.8 + (self.timer / self.EXIT_DURATION) * 0.2
        elif self.phase == self.PHASE_COMPLETE:
            return 1.0
        return 0.0
    
    def get_status(self) -> str:
        """Получить текущий статус гиперпрыжка."""
        status_map = {
            self.PHASE_IDLE: "ГОТОВ",
            self.PHASE_CHARGING: "ЗАРЯДКА",
            self.PHASE_TUNNEL: "ПЕРЕХОД",
            self.PHASE_EXIT: "ВЫХОД",
            self.PHASE_COMPLETE: "ЗАВЕРШЁН"
        }
        return status_map.get(self.phase, "НЕИЗВЕСТНО")
    
    def is_active(self) -> bool:
        """Проверить, активен ли гиперпрыжок."""
        return self.phase != self.PHASE_IDLE


class CollisionSystem:
    """
    Система обнаружения столкновений.
    
    Совет от ментора:
    В Elite 1984 столкновения были простыми - использовались
    bounding spheres (ограничивающие сферы) для быстрой проверки.
    Это работало даже на процессоре Z80 с тактовой частотой 3.5 МГц!
    
    Мы используем тот же подход:
    1. Проверяем расстояние между объектами
    2. Если расстояние < суммы радиусов - столкновение
    3. Рассчитываем урон на основе скорости столкновения
    """
    
    def __init__(self):
        # Радиусы столкновений для разных объектов
        self.collision_radius = {
            "ship": 2.0,
            "station": 15.0,
            "asteroid": 3.0,
            "projectile": 0.5
        }
    
    def check_collision(self, pos1: Vector3, radius1: float,
                       pos2: Vector3, radius2: float) -> bool:
        """
        Проверить столкновение двух сфер.
        
        Args:
            pos1, radius1: позиция и радиус первого объекта
            pos2, radius2: позиция и радиус второго объекта
        
        Returns:
            True если сферы пересекаются
        
        Совет от ментора:
        Оптимизация: сравниваем квадраты расстояний, чтобы избежать
        дорогой операции извлечения квадратного корня.
        dist^2 < (r1 + r2)^2 эквивалентно dist < r1 + r2
        """
        delta = pos1 - pos2
        distance_sq = delta.x**2 + delta.y**2 + delta.z**2
        radius_sum = radius1 + radius2
        return distance_sq < radius_sum**2
    
    def check_ship_station_collision(self, ship, station) -> Tuple[bool, float]:
        """
        Проверить столкновение корабля со станцией.
        
        Args:
            ship: корабль игрока
            station: космическая станция
        
        Returns:
            Кортеж (столкновение, сила_удара)
        
        Совет от ментора:
        В Elite столкновение со станцией на высокой скорости
        означало мгновенную смерть (Game Over). Мы делаем то же самое,
        но с более щадящей системой урона для лучшей играбельности.
        """
        ship_radius = self.collision_radius["ship"]
        station_radius = self.collision_radius["station"]
        
        collision = self.check_collision(
            ship.position, ship_radius,
            station.position, station_radius
        )
        
        if not collision:
            return False, 0.0
        
        # Рассчитываем силу удара на основе скорости
        speed = ship.velocity.magnitude()
        impact_force = speed * 2.0  # Урон пропорционален скорости
        
        return True, impact_force
    
    def get_collision_radius(self, object_type: str) -> float:
        """Получить радиус столкновения для типа объекта."""
        return self.collision_radius.get(object_type, 1.0)


class PhysicsEngine:
    """
    Центральный физический движок, объединяющий все системы.
    
    Совет от ментора:
    Использование паттерна Component (Компонент) из нашего архитектурного
    плана позволяет легко добавлять новые системы физики без изменения
    существующего кода. Это принцип Open/Closed из SOLID.
    """
    
    def __init__(self):
        self.docking_computer = DockingComputer()
        self.hyperspace_navigator = HyperspaceNavigator()
        self.collision_system = CollisionSystem()
    
    def update(self, ship, stations: list, delta_time: float):
        """
        Обновление всех физических систем.
        
        Args:
            ship: корабль игрока
            stations: список станций в текущей системе
            delta_time: время с прошлого кадра
        
        Совет от ментора:
        Порядок обновления важен:
        1. Сначала автопилот (если активен)
        2. Затем гиперпрыжок (если активен)
        3. Затем столкновения
        4. В конце - обычная физика корабля
        """
        # 1. Автопилот стыковки
        if self.docking_computer.is_active:
            thrust, angular_vel = self.docking_computer.update(ship, delta_time)
            # Применяем управляющие воздействия
            ship.velocity = ship.velocity + thrust * delta_time
            ship.angular_velocity = angular_vel
        
        # 2. Гиперпрыжок
        hyperspace_complete = self.hyperspace_navigator.update(ship, delta_time)
        if hyperspace_complete:
            # Прыжок завершён, можно вернуть управление
            pass
        
        # 3. Проверка столкновений
        for station in stations:
            collision, impact = self.collision_system.check_ship_station_collision(
                ship, station
            )
            if collision and not ship.is_docked:
                # Проверяем возможность стыковки
                if ship.can_dock_with_station(station):
                    ship.dock_with_station(station)
                    self.docking_computer.deactivate()
                else:
                    # Столкновение на высокой скорости - урон!
                    ship.take_damage(impact)
    
    def get_status(self) -> dict:
        """Получить статус всех физических систем."""
        return {
            "docking": self.docking_computer.get_status(),
            "hyperspace": self.hyperspace_navigator.get_status(),
            "hyperspace_active": self.hyperspace_navigator.is_active()
        }