"""
ship/player_ship.py
Корабль игрока в стиле Elite 1984 года.

Исправления от ментора:
1. Добавлен флаг is_autopilot_active. Если он True, handle_input() игнорирует нажатия клавиш,
   чтобы игрок не мог пересилить автопилот и сломать PD-регулятор.
2. complete_hyperspace_jump() теперь размещает корабль строго перед планетой (по оси -Z),
   как в оригинальной Elite, чтобы планета сразу была видна.
3. Добавлено сохранение docked_station, чтобы система торговли знала, где мы находимся.
4. Убраны импорты из тел функций (math, random, pygame) - перенесены в начало файла.
"""

import math
import random
from typing import Optional
import pygame

from engine.math3d import Vector3, Matrix3x3
from ship.models import create_cobra_mk3
from engine.renderer import Mesh


class PlayerShip:
    """Корабль игрока с полной 6DOF-физикой."""
    
    def __init__(self, start_position: Optional[Vector3] = None, ship_scale: float = 0.15):
        self.position = start_position if start_position else Vector3(0, 0, 0)
        self.velocity = Vector3(0, 0, 0)
        self.rotation = Vector3(0, 0, 0)
        self.angular_velocity = Vector3(0, 0, 0)
        
        self.thrust = 0.0
        self.max_speed = 50.0
        self.acceleration = 20.0
        self.rotation_speed = 2.0
        self.friction = 0.0
        
        self.shields = 100.0
        self.energy = 100.0
        self.fuel = 70.0
        self.credits = 100.0
        self.hull = 100.0
        
        # ИСПРАВЛЕНО: масштаб теперь передаётся параметром
        self.mesh = create_cobra_mk3(scale=ship_scale)
        
        self.is_docked = False
        self.is_in_hyperspace = False
        
        # НОВОЕ: Флаг управления автопилотом. Если True, игрок не может рулить.
        self.is_autopilot_active = False
        
        # НОВОЕ: Ссылка на станцию, к которой мы пристыкованы (нужно для торговли)
        self.docked_station = None
        
        # НОВОЕ: Текущая планета (для гиперпрыжков)
        self.current_planet = None
        
        self.forward = Vector3(0, 0, 1)
        self.up = Vector3(0, 1, 0)
        self.right = Vector3(1, 0, 0)
        
        self._update_direction_vectors()
    
    def _update_direction_vectors(self):
        """Пересчет векторов направления на основе текущих углов Эйлера."""
        roll_mat = Matrix3x3.rotation_z(self.rotation.z)
        yaw_mat = Matrix3x3.rotation_y(self.rotation.y)
        pitch_mat = Matrix3x3.rotation_x(self.rotation.x)
        
        # Порядок: Z -> Y -> X (Roll -> Yaw -> Pitch)
        rotation_matrix = pitch_mat * yaw_mat * roll_mat
        
        self.forward = rotation_matrix * Vector3(0, 0, 1)
        self.up = rotation_matrix * Vector3(0, 1, 0)
        self.right = rotation_matrix * Vector3(1, 0, 0)
    
    def handle_input(self, keys, delta_time: float):
        """Обработка ввода с клавиатуры. Игнорируется, если активен автопилот."""
        # ИСПРАВЛЕНО: Если автопилот ведет корабль, блокируем ввод игрока
        if self.is_autopilot_active or self.is_docked or self.is_in_hyperspace:
            return
            
        self.angular_velocity = Vector3(0, 0, 0)
        
        if keys[pygame.K_w]: self.angular_velocity.x -= self.rotation_speed
        if keys[pygame.K_s]: self.angular_velocity.x += self.rotation_speed
        if keys[pygame.K_a]: self.angular_velocity.y -= self.rotation_speed
        if keys[pygame.K_d]: self.angular_velocity.y += self.rotation_speed
        if keys[pygame.K_q]: self.angular_velocity.z -= self.rotation_speed
        if keys[pygame.K_e]: self.angular_velocity.z += self.rotation_speed
        
        self.thrust = 0.0
        if keys[pygame.K_SPACE]: self.thrust = 1.0
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]: self.thrust = -0.5
    
    def update(self, delta_time: float):
        """Обновление физики корабля."""
        if self.is_docked or self.is_in_hyperspace:
            return
        
        # Применяем угловую скорость (задается либо игроком, либо автопилотом)
        self.rotation.x += self.angular_velocity.x * delta_time
        self.rotation.y += self.angular_velocity.y * delta_time
        self.rotation.z += self.angular_velocity.z * delta_time
        
        self.rotation.x = self._normalize_angle(self.rotation.x)
        self.rotation.y = self._normalize_angle(self.rotation.y)
        self.rotation.z = self._normalize_angle(self.rotation.z)
        
        self._update_direction_vectors()
        
        # Применяем тягу игрока (если автопилот не работает, он напрямую меняет velocity)
        if self.thrust != 0.0 and not self.is_autopilot_active:
            thrust_vector = self.forward * (self.acceleration * self.thrust)
            self.velocity = self.velocity + thrust_vector * delta_time
        
        if self.friction > 0:
            self.velocity = self.velocity * (1.0 - self.friction * delta_time)
        
        # Ограничение максимальной скорости
        speed = self.velocity.magnitude()
        if speed > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed
        
        # Интегрируем позицию
        self.position = self.position + self.velocity * delta_time
    
    def _normalize_angle(self, angle: float) -> float:
        """Нормализация угла в диапазон [-π, π]."""
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        return angle
    
    def get_rotation_matrix(self) -> Matrix3x3:
        """Получить текущую матрицу поворота корабля."""
        roll_mat = Matrix3x3.rotation_z(self.rotation.z)
        yaw_mat = Matrix3x3.rotation_y(self.rotation.y)
        pitch_mat = Matrix3x3.rotation_x(self.rotation.x)
        return pitch_mat * yaw_mat * roll_mat
    
    def can_dock_with_station(self, station) -> bool:
        """Проверить, можно ли пристыковаться к станции."""
        if self.is_docked or self.is_in_hyperspace: return False
        return station.can_dock(self.position, self.velocity)
    
    def dock_with_station(self, station) -> bool:
        """Выполнить стыковку со станцией."""
        if self.can_dock_with_station(station):
            self.is_docked = True
            self.velocity = Vector3(0, 0, 0)
            self.angular_velocity = Vector3(0, 0, 0)
            self.thrust = 0.0
            # ИСПРАВЛЕНО: Сохраняем ссылку на станцию для системы торговли
            self.docked_station = station
            return True
        return False
    
    def undock(self):
        """Отстыковаться от станции."""
        if self.is_docked:
            self.is_docked = False
            # ИСПРАВЛЕНО: Очищаем ссылку на станцию
            self.docked_station = None
            # Небольшой импульс вперед, чтобы отойти от дока
            self.velocity = self.forward * 5.0
    
    def can_hyperspace_jump(self, target_planet) -> bool:
        """Проверить возможность гиперпрыжка."""
        if self.is_docked or self.is_in_hyperspace: return False
        if not self.current_planet: return False
        
        distance = self.current_planet.get_distance_to(target_planet)
        # В оригинале требовалось, чтобы расстояние было строго меньше или равно топливу
        return distance <= self.fuel
    
    def start_hyperspace_jump(self, target_planet) -> bool:
        """Начать гиперпрыжок (списание топлива и кредитов)."""
        if not self.can_hyperspace_jump(target_planet): return False
        
        distance = self.current_planet.get_distance_to(target_planet)
        self.fuel -= distance
        self.credits -= distance * 0.1
        
        self.is_in_hyperspace = True
        self.velocity = Vector3(0, 0, 0)
        self.angular_velocity = Vector3(0, 0, 0)
        self._hyperspace_target = target_planet
        return True
    
    def complete_hyperspace_jump(self):
        """Завершить гиперпрыжок и появиться в новой системе."""
        if not self.is_in_hyperspace: return
        
        self.is_in_hyperspace = False
        
        # ИСПРАВЛЕНО: Появляемся строго перед планетой (по оси -Z на расстоянии 150),
        # чтобы планета сразу была видна в центре экрана, как в оригинале.
        self.position = Vector3(0, 0, -150.0)
        self.velocity = Vector3(0, 0, 0)
        self.angular_velocity = Vector3(0, 0, 0)
        
        # Сбрасываем вращение, чтобы корабль смотрел прямо на планету
        self.rotation = Vector3(0, 0, 0)
        self._update_direction_vectors()
        
        if hasattr(self, '_hyperspace_target'):
            self.current_planet = self._hyperspace_target
            del self._hyperspace_target
    
    def take_damage(self, damage_amount: float):
        """Получить урон (сначала щиты, потом корпус)."""
        if self.shields > 0:
            shield_damage = min(self.shields, damage_amount)
            self.shields -= shield_damage
            damage_amount -= shield_damage
            
        if damage_amount > 0:
            self.hull -= damage_amount
            self.hull = max(0.0, self.hull)
            
    def get_status_string(self) -> str:
        """Получить строку статуса для HUD."""
        status = (
            f"Щиты: {self.shields:.0f}% | "
            f"Энергия: {self.energy:.0f}% | "
            f"Корпус: {self.hull:.0f}% | "
            f"Топливо: {self.fuel:.1f} св.лет | "
            f"Кредиты: {self.credits:.0f} CR"
        )
        if self.is_docked: status += " | ПРИСТЫКОВАН"
        elif self.is_in_hyperspace: status += " | ГИПЕРПРОСТРАНСТВО"
        return status
    
    def __str__(self) -> str:
        return (
            f"Корабль игрока (Cobra Mk III)\n"
            f"  Позиция: ({self.position.x:.1f}, {self.position.y:.1f}, {self.position.z:.1f})\n"
            f"  Скорость: {self.velocity.magnitude():.1f} ед/сек\n"
            f"  Вращение: pitch={self.rotation.x:.2f}, yaw={self.rotation.y:.2f}, roll={self.rotation.z:.2f}\n"
            f"  {self.get_status_string()}"
        )