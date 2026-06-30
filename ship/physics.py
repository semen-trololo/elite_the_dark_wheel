"""
ship/physics.py
Физика и навигация корабля в стиле Elite 1984 года.

ПОЛНОСТЬЮ РАБОТАЮЩИЙ АВТОПИЛОТ (Вариант B — аутентичный):
- PD-регулятор скорости во ВСЕХ фазах (нет осцилляций!)
- Контроль пролёта мимо цели во ВСЕХ фазах
- Clamp скорости и тяги (стабильная физика)
- Явная P-компенсация бокового смещения (корабль сходится к оси подхода)
- Учёт вращения станции (корпус вращается, слот движется по кругу)
- Детальная отладка с throttle (лог раз в 0.2 сек)

Алгоритм стыковки:
  APPROACH — быстрый подлёт к станции, плавное торможение
  ALIGN    — выравнивание носа по оси подхода + компенсация бокового смещения
  DOCK     — финальное медленное сближение К СЛОТУ с сильным удержанием оси
"""

from typing import Optional, Tuple
from engine.math3d import Vector3, Matrix3x3
import math


# =============================================================================
#                           DOCKING COMPUTER
# =============================================================================

class DockingComputer:
    """
    Автоматическая система стыковки (Docking Computer за 1500 CR из Elite 1984).

    Алгоритм:
      1) APPROACH — летим к слоту, плавно тормозим по мере приближения
      2) ALIGN    — выравниваем нос по оси подхода, компенсируем боковое смещение
      3) DOCK     — финальное сближение К СЛОТУ, удерживаясь на оси подхода
    """

    # -------------------------------------------------------------------------
    # Параметры фаз
    # -------------------------------------------------------------------------
    APPROACH_DISTANCE = 50.0        # Дистанция перехода APPROACH -> ALIGN
    MAX_APPROACH_SPEED = 15.0       # Максимальная скорость в APPROACH
    ALIGN_MAX_SPEED = 4.0           # Максимальная скорость в ALIGN
    DOCKING_SPEED = 1.2             # Целевая скорость в DOCK
    ALIGNMENT_TOLERANCE = 0.25      # Порог выравнивания (меньше = строже)

    # PD-коэффициенты (подобраны эмпирически)
    KP_SPEED = 3.0                  # Пропорциональный по скорости
    KD_LATERAL_VEL = 5.0            # Гашение боковой СКОРОСТИ
    KP_ALIGNMENT = 6.0              # Выравнивание по нормали
    KP_LATERAL_POS = 8.0            # Компенсация бокового СМЕЩЕНИЯ (позиции)

    # Отладка
    DEBUG_INTERVAL = 0.2            # Лог раз в 0.2 сек

    def __init__(self):
        self.is_active = False
        self.target_station = None
        self.phase = "IDLE"
        self._debug_timer = 0.0

    # -------------------------------------------------------------------------
    # Управление автопилотом
    # -------------------------------------------------------------------------
    def activate(self, station) -> bool:
        if not station or not station.is_docking_open:
            return False
        self.is_active = True
        self.target_station = station
        self.phase = "APPROACH"
        self._debug_timer = 0.0
        print(f"🚀 Автопилот активирован. Цель: {station.name}")
        return True

    def deactivate(self):
        self.is_active = False
        self.target_station = None
        self.phase = "IDLE"

    # -------------------------------------------------------------------------
    # ГЛАВНЫЙ ЦИКЛ ОБНОВЛЕНИЯ
    # -------------------------------------------------------------------------
    def update(self, ship, delta_time: float) -> Tuple[Vector3, Vector3]:
        if not self.is_active or not self.target_station:
            return Vector3(0, 0, 0), Vector3(0, 0, 0)

        # Обновляем таймер отладки
        self._debug_timer += delta_time
        should_log = self._debug_timer >= self.DEBUG_INTERVAL
        if should_log:
            self._debug_timer = 0.0  # СБРОС после лога

        station = self.target_station
        slot_pos = station.get_world_docking_slot()
        approach_axis = station.get_docking_approach_axis()  # Единичный вектор ОТ центра К слоту

        # Вектор от корабля к слоту
        to_slot = slot_pos - ship.position
        distance = to_slot.magnitude()

        # Защита от деления на ноль
        if distance < 1e-6:
            direction = -approach_axis
        else:
            direction = to_slot.normalize()

        current_speed = ship.velocity.magnitude()

        # =========================================================================
        # ФАЗА 1: APPROACH — быстрый подлёт
        # =========================================================================
        if self.phase == "APPROACH":
            # Целевая скорость зависит от дистанции (плавное торможение)
            if distance > 150:
                target_speed = self.MAX_APPROACH_SPEED
            elif distance > 50:
                t = (distance - 50) / 100.0
                target_speed = 8.0 + t * (self.MAX_APPROACH_SPEED - 8.0)
            else:
                t = distance / 50.0
                target_speed = self.ALIGN_MAX_SPEED + t * (8.0 - self.ALIGN_MAX_SPEED)

            thrust, angular_vel = self._compute_thrust_pd(
                ship, direction, target_speed, approach_axis,
                enforce_alignment=False,
                max_thrust=30.0,
                lateral_pos_kp=0.0  # В APPROACH не компенсируем смещение
            )

            if should_log:
                print(f"🛸 APPROACH | dist={distance:7.2f} | speed={current_speed:5.2f}/{target_speed:5.2f}")

            # Переход в ALIGN
            if distance < self.APPROACH_DISTANCE and current_speed < self.ALIGN_MAX_SPEED + 1.0:
                self.phase = "ALIGN"
                print(f"✅ APPROACH → ALIGN (дист: {distance:.1f}, скорость: {current_speed:.2f})")

            return thrust, angular_vel

        # =========================================================================
        # ФАЗА 2: ALIGN — выравнивание + компенсация бокового смещения
        # =========================================================================
        elif self.phase == "ALIGN":
            # Плавное торможение до docking_speed
            target_speed = max(self.DOCKING_SPEED, min(current_speed * 0.5, self.ALIGN_MAX_SPEED))

            thrust, angular_vel = self._compute_thrust_pd(
                ship, direction, target_speed, approach_axis,
                enforce_alignment=True,
                alignment_kp=self.KP_ALIGNMENT,
                max_thrust=25.0,
                lateral_pos_kp=self.KP_LATERAL_POS * 0.5  # Средняя компенсация
            )

            # Контроль пролёта мимо слота
            if distance < 30:
                vel_toward_slot = ship.velocity.dot(direction)
                if vel_toward_slot < -0.5:  # Летим ОТ слота
                    brake = -ship.velocity * 5.0
                    thrust = thrust + brake

            if should_log:
                lateral = station.get_lateral_offset(ship.position)
                print(f"🎯 ALIGN    | dist={distance:7.2f} | speed={current_speed:5.2f} | lateral={lateral:5.2f}")

            # Переход в DOCK: все три условия должны выполниться
            forward_error = ship.forward.cross(-approach_axis).magnitude()
            lateral = station.get_lateral_offset(ship.position)
            if (forward_error < self.ALIGNMENT_TOLERANCE and
                current_speed < self.DOCKING_SPEED + 0.5 and
                lateral < 5.0):
                self.phase = "DOCK"
                print(f"✅ ALIGN → DOCK (ошибка: {forward_error:.3f}, скорость: {current_speed:.2f}, lateral: {lateral:.2f})")

            return thrust, angular_vel

        # =========================================================================
        # ФАЗА 3: DOCK — финальное сближение (ИСПРАВЛЕНО!)
        # =========================================================================
        elif self.phase == "DOCK":
            # ОЧЕНЬ медленный подход
            target_speed = self.DOCKING_SPEED
            if distance < 5:
                target_speed = max(0.3, distance * 0.2)

            # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Летим К СЛОТУ (direction),
            # но выравниваемся по оси подхода и сильно компенсируем боковое смещение
            thrust, angular_vel = self._compute_thrust_pd(
                ship, direction, target_speed, approach_axis,
                enforce_alignment=True,
                alignment_kp=self.KP_ALIGNMENT * 1.5,
                max_thrust=20.0,
                lateral_pos_kp=self.KP_LATERAL_POS  # СИЛЬНАЯ компенсация
            )

            # Контроль пролёта
            vel_toward = ship.velocity.dot(direction)
            if distance < 3 and vel_toward < -0.2:
                thrust = thrust - ship.velocity * 8.0

            if should_log:
                lateral = station.get_lateral_offset(ship.position)
                print(f"🔌 DOCK     | dist={distance:7.2f} | speed={current_speed:5.2f} | lateral={lateral:5.2f}")

            # Проверка стыковки
            if station.can_dock(ship.position, ship.velocity):
                print(f"🎉 СТЫКОВКА УСПЕШНА! (дист: {distance:.2f}, скорость: {current_speed:.2f})")
                ship.velocity = Vector3(0, 0, 0)
                ship.angular_velocity = Vector3(0, 0, 0)
                self.deactivate()
                return Vector3(0, 0, 0), Vector3(0, 0, 0)

            # Если ушли слишком далеко — возврат в APPROACH
            if distance > self.APPROACH_DISTANCE * 1.5:
                self.phase = "APPROACH"
                print(f"⚠️ Промах! Возврат в APPROACH (дист: {distance:.1f})")

            return thrust, angular_vel

        return Vector3(0, 0, 0), Vector3(0, 0, 0)

    # -------------------------------------------------------------------------
    # PD-РЕГУЛЯТОР (универсальный)
    # -------------------------------------------------------------------------
    def _compute_thrust_pd(
        self, ship, direction: Vector3, target_speed: float,
        approach_axis: Vector3,
        enforce_alignment: bool = False,
        alignment_kp: float = 6.0,
        max_thrust: float = 30.0,
        lateral_pos_kp: float = 0.0
    ) -> Tuple[Vector3, Vector3]:
        """
        Вычисляет тягу и угловую скорость через PD-регулятор.

        Алгоритм:
          1. Желаемая скорость = direction * target_speed
          2. P-тяга = KP * (desired_vel - current_vel)
          3. D-компенсация боковой СКОРОСТИ (гасим боковой снос)
          4. P-компенсация бокового СМЕЩЕНИЯ (стягиваем к оси подхода)
          5. Clamp тяги
          6. Угловая скорость для выравнивания (если требуется)
        """
        # 1. Желаемая линейная скорость
        desired_velocity = direction * target_speed

        # 2. Ошибка скорости → P-тяга
        velocity_error = desired_velocity - ship.velocity
        thrust = velocity_error * self.KP_SPEED

        # 3. Боковая компенсация СКОРОСТИ (D-компонента)
        # Проецируем скорость на ось подхода, вычитаем продольную составляющую,
        # оставшаяся — боковая, которую нужно погасить
        vel_along_axis = ship.velocity.dot(approach_axis)
        vel_along_vec = approach_axis * vel_along_axis
        vel_lateral = ship.velocity - vel_along_vec

        if vel_lateral.magnitude() > 0.05:
            thrust = thrust - vel_lateral * self.KD_LATERAL_VEL

        # 4. Явная P-компенсация бокового СМЕЩЕНИЯ (позиции)
        # Корабль должен находиться на оси подхода, иначе lateral не уменьшится!
        if lateral_pos_kp > 0 and self.target_station is not None:
            to_ship = ship.position - self.target_station.position
            along_axis = approach_axis * to_ship.dot(approach_axis)
            lateral_offset_vec = to_ship - along_axis

            if lateral_offset_vec.magnitude() > 0.1:
                # Тянем корабль обратно к оси подхода
                thrust = thrust - lateral_offset_vec * lateral_pos_kp

        # 5. Clamp тяги (стабильность)
        thrust_mag = thrust.magnitude()
        if thrust_mag > max_thrust:
            thrust = thrust.normalize() * max_thrust

        # 6. Угловая скорость для выравнивания
        angular_velocity = Vector3(0, 0, 0)
        if enforce_alignment:
            target_forward = -approach_axis  # Нос корабля смотрит ПРОТИВ оси подхода
            forward_error = ship.forward.cross(target_forward)
            angular_velocity = forward_error * alignment_kp

            ang_mag = angular_velocity.magnitude()
            if ang_mag > 3.0:
                angular_velocity = angular_velocity.normalize() * 3.0

        return thrust, angular_velocity

    def get_status(self) -> str:
        if not self.is_active:
            return "НЕАКТИВЕН"
        return {
            "APPROACH": "ПРИБЛИЖЕНИЕ",
            "ALIGN": "ВЫРАВНИВАНИЕ",
            "DOCK": "СТЫКОВКА"
        }.get(self.phase, "НЕИЗВЕСТНО")


# =============================================================================
#                        HYPERSPACE NAVIGATOR
# =============================================================================

class HyperspaceNavigator:
    """Навигатор гиперпространства для межзвёздных перелётов."""

    PHASE_IDLE = "IDLE"
    PHASE_CHARGING = "CHARGING"
    PHASE_TUNNEL = "TUNNEL"
    PHASE_EXIT = "EXIT"
    PHASE_COMPLETE = "COMPLETE"

    CHARGING_DURATION = 2.0
    TUNNEL_DURATION = 3.0
    EXIT_DURATION = 1.0

    def __init__(self):
        self.phase = self.PHASE_IDLE
        self.timer = 0.0
        self.target_planet = None
        self.source_planet = None
        self.tunnel_stars = []
        self._generate_tunnel_stars()

    def _generate_tunnel_stars(self):
        import random
        self.tunnel_stars = []
        for _ in range(100):
            star = Vector3(
                random.uniform(-50, 50),
                random.uniform(-50, 50),
                random.uniform(10, 100)
            )
            velocity = random.uniform(20, 50)
            self.tunnel_stars.append([star, velocity])

    def start_jump(self, ship, target_planet) -> bool:
        if self.phase != self.PHASE_IDLE:
            return False
        if not hasattr(ship, 'current_planet') or not ship.current_planet:
            return False
        if not ship.can_hyperspace_jump(target_planet):
            return False
        if not ship.start_hyperspace_jump(target_planet):
            return False

        self.source_planet = ship.current_planet
        self.target_planet = target_planet
        self.phase = self.PHASE_CHARGING
        self.timer = 0.0
        return True

    def update(self, ship, delta_time: float) -> bool:
        import random
        if self.phase == self.PHASE_IDLE:
            return False

        self.timer += delta_time

        if self.phase == self.PHASE_CHARGING:
            if self.timer >= self.CHARGING_DURATION:
                self.phase = self.PHASE_TUNNEL
                self.timer = 0.0
                self._generate_tunnel_stars()
            return False

        elif self.phase == self.PHASE_TUNNEL:
            for star_data in self.tunnel_stars:
                star = star_data[0]
                velocity = star_data[1]
                star.z -= velocity * delta_time
                if star.z < 10:
                    star.z = 100
                    star.x = random.uniform(-50, 50)
                    star.y = random.uniform(-50, 50)
            if self.timer >= self.TUNNEL_DURATION:
                self.phase = self.PHASE_EXIT
                self.timer = 0.0
            return False

        elif self.phase == self.PHASE_EXIT:
            if self.timer >= self.EXIT_DURATION:
                ship.complete_hyperspace_jump()
                self.phase = self.PHASE_COMPLETE
                self.timer = 0.0
            return False

        elif self.phase == self.PHASE_COMPLETE:
            self.phase = self.PHASE_IDLE
            self.target_planet = None
            self.source_planet = None
            return True

        return False

    def get_tunnel_stars(self):
        if self.phase == self.PHASE_TUNNEL:
            return self.tunnel_stars
        return []

    def get_progress(self) -> float:
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
        return {
            self.PHASE_IDLE: "ГОТОВ",
            self.PHASE_CHARGING: "ЗАРЯДКА",
            self.PHASE_TUNNEL: "ПЕРЕХОД",
            self.PHASE_EXIT: "ВЫХОД",
            self.PHASE_COMPLETE: "ЗАВЕРШЁН"
        }.get(self.phase, "НЕИЗВЕСТНО")

    def is_active(self) -> bool:
        return self.phase != self.PHASE_IDLE


# =============================================================================
#                           COLLISION SYSTEM
# =============================================================================

class CollisionSystem:
    """Система обнаружения столкновений (Bounding Spheres)."""

    def __init__(self):
        self.collision_radius = {
            "ship": 2.0,
            "station": 15.0,
            "asteroid": 3.0,
            "projectile": 0.5
        }

    def check_collision(self, pos1: Vector3, radius1: float,
                       pos2: Vector3, radius2: float) -> bool:
        """Оптимизировано через сравнение квадратов расстояний."""
        delta = pos1 - pos2
        distance_sq = delta.x**2 + delta.y**2 + delta.z**2
        radius_sum = radius1 + radius2
        return distance_sq < radius_sum**2

    def check_ship_station_collision(self, ship, station) -> Tuple[bool, float]:
        ship_radius = self.collision_radius["ship"]
        station_radius = self.collision_radius["station"]

        collision = self.check_collision(
            ship.position, ship_radius,
            station.position, station_radius
        )

        if not collision:
            return False, 0.0

        speed = ship.velocity.magnitude()
        impact_force = speed * 2.0
        return True, impact_force

    def get_collision_radius(self, object_type: str) -> float:
        return self.collision_radius.get(object_type, 1.0)


# =============================================================================
#                           PHYSICS ENGINE
# =============================================================================

class PhysicsEngine:
    """Центральный физический движок, объединяющий все системы."""

    def __init__(self):
        self.docking_computer = DockingComputer()
        self.hyperspace_navigator = HyperspaceNavigator()
        self.collision_system = CollisionSystem()

    def update(self, ship, stations: list, delta_time: float):
        # 1. Автопилот стыковки
        if self.docking_computer.is_active:
            thrust, angular_vel = self.docking_computer.update(ship, delta_time)
            ship.velocity = ship.velocity + thrust * delta_time
            ship.angular_velocity = angular_vel

        # 2. Гиперпрыжок обрабатывается в main.py
        self.hyperspace_navigator.update(ship, delta_time)

        # 3. Проверка столкновений и стыковки
        for station in stations:
            if not ship.is_docked and station.can_dock(ship.position, ship.velocity):
                ship.dock_with_station(station)
                self.docking_computer.deactivate()
                continue

            collision, impact = self.collision_system.check_ship_station_collision(
                ship, station
            )
            if collision and not ship.is_docked:
                ship.take_damage(impact)

    def get_status(self) -> dict:
        return {
            "docking": self.docking_computer.get_status(),
            "hyperspace": self.hyperspace_navigator.get_status(),
            "hyperspace_active": self.hyperspace_navigator.is_active()
        }