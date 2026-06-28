"""
main.py
Точка входа в игру. Игровой цикл с pygame.
Управление в стиле оригинальной Elite (1984).
"""

import pygame
import sys
import random  # <-- ИСПРАВЛЕНО: используем стандартный модуль random

from engine.math3d import Vector3, Matrix3x3
from engine.renderer import WireframeRenderer
from ship.models import create_sidewinder


class Game:
    """Главный класс игры."""
    
    def __init__(self):
        # Инициализация pygame
        pygame.init()
        
        # Настройки экрана
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Elite Clone - Sidewinder")
        
        # Часы для ограничения FPS
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Создаём рендерер
        self.renderer = WireframeRenderer(self.width, self.height, fov=500)
        
        # Создаём корабль (Sidewinder)
        self.ship_mesh = create_sidewinder()
        
        # Позиция и вращение корабля
        self.ship_position = Vector3(0, 0, 0)
        self.ship_rotation_x = 0.0  # Pitch (тангаж)
        self.ship_rotation_y = 0.0  # Yaw (рыскание)
        self.ship_rotation_z = 0.0  # Roll (крен)
        
        # Физика движения
        self.ship_velocity = Vector3(0, 0, 0)
        self.max_speed = 10.0
        self.acceleration = 5.0
        
        # Скорость вращения (радианы в секунду)
        self.rotation_speed = 2.0
        
        # Цвета
        self.color_background = (0, 0, 0)
        self.color_ship = (0, 255, 0)
        
        # Создаём звёзды для фона (ИСПРАВЛЕНО: random вместо pygame.random)
        self.stars = []
        for _ in range(100):
            star = Vector3(
                random.randint(-500, 500),
                random.randint(-500, 500),
                random.randint(10, 500)
            )
            self.stars.append(star)
    
    def handle_input(self, delta_time):
        """Обработка ввода в стиле оригинальной Elite."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        keys = pygame.key.get_pressed()
        
        # === ВРАЩЕНИЕ КОРАБЛЯ ===
        
        # Тангаж (вверх/вниз носа) - W/S
        if keys[pygame.K_w]:
            self.ship_rotation_x -= self.rotation_speed * delta_time
        if keys[pygame.K_s]:
            self.ship_rotation_x += self.rotation_speed * delta_time
        
        # Рыскание (влево/вправо носа) - A/D
        if keys[pygame.K_a]:
            self.ship_rotation_y -= self.rotation_speed * delta_time
        if keys[pygame.K_d]:
            self.ship_rotation_y += self.rotation_speed * delta_time
        
        # Крен (наклон корабля) - Q/E
        if keys[pygame.K_q]:
            self.ship_rotation_z -= self.rotation_speed * delta_time
        if keys[pygame.K_e]:
            self.ship_rotation_z += self.rotation_speed * delta_time
        
        # === ДВИЖЕНИЕ (в направлении носа) ===
        
        # Получаем направление "вперёд" корабля
        forward = Vector3(0, 0, -1)
        rotation_matrix = (Matrix3x3.rotation_z(self.ship_rotation_z) * 
                  Matrix3x3.rotation_y(self.ship_rotation_y) * 
                  Matrix3x3.rotation_x(self.ship_rotation_x))
        forward = rotation_matrix * forward
        
        # Ускорение (Space)
        if keys[pygame.K_SPACE]:
            self.ship_velocity = self.ship_velocity + forward * self.acceleration * delta_time
        
        # Замедление (Shift)
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            decel_force = forward * self.acceleration * delta_time
            speed = self.ship_velocity.magnitude()
            if decel_force.magnitude() > speed:
                self.ship_velocity = Vector3(0, 0, 0)
            else:
                self.ship_velocity = self.ship_velocity - decel_force
        
        # Ограничение максимальной скорости
        speed = self.ship_velocity.magnitude()
        if speed > self.max_speed:
            self.ship_velocity = self.ship_velocity.normalize() * self.max_speed
        
        # Выход по ESC
        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()
    
    def update(self, delta_time):
        """Обновление состояния игры."""
        # Обновляем позицию корабля на основе скорости
        self.ship_position = self.ship_position + self.ship_velocity * delta_time
        
        # Ограничиваем позицию
        max_distance = 100
        if self.ship_position.magnitude() > max_distance:
            self.ship_position = self.ship_position.normalize() * max_distance
    
    
    def render(self):
        """Отрисовка кадра."""
        # Очищаем экран
        self.screen.fill(self.color_background)
        
        # === ОТРИСОВКА ЗВЁЗД ===
        # (код звёзд оставляем как есть)
        for star in self.stars:
            star_relative = star - self.ship_position
            projected = self.renderer.project(star_relative)
            if projected:
                x, y = projected
                pygame.draw.circle(self.screen, (200, 200, 200), (x, y), 1)
        
        # === ОТРИСОВКА КОРАБЛЯ ===
        # ПРИБЛИЗИЛИ камеру с 15 до 8, чтобы корабль был крупнее
        camera_offset = Vector3(0, 0, 8)
        
        rotation_matrix = (Matrix3x3.rotation_z(self.ship_rotation_z) * 
                  Matrix3x3.rotation_y(self.ship_rotation_y) * 
                  Matrix3x3.rotation_x(self.ship_rotation_x))
        
        lines = self.renderer.render_mesh(
            self.ship_mesh,
            position=camera_offset,
            rotation_matrix=rotation_matrix
        )
        
        for line in lines:
            x1, y1, x2, y2 = line
            pygame.draw.line(self.screen, self.color_ship, (x1, y1), (x2, y2), 1)
        
        # === HUD ===
        font = pygame.font.Font(None, 24)
        
        speed_text = font.render(f"Speed: {self.ship_velocity.magnitude():.1f}", True, (0, 255, 0))
        self.screen.blit(speed_text, (10, 10))
        
        pos_text = font.render(f"Pos: ({self.ship_position.x:.1f}, {self.ship_position.y:.1f}, {self.ship_position.z:.1f})", True, (0, 255, 0))
        self.screen.blit(pos_text, (10, 35))
        
        controls_text = font.render("W/S: Pitch | A/D: Yaw | Q/E: Roll | Space: Thrust | Shift: Decelerate", True, (100, 100, 100))
        self.screen.blit(controls_text, (10, self.height - 30))
        
        pygame.display.flip()
    
    def run(self):
        """Главный игровой цикл."""
        running = True
        
        while running:
            delta_time = self.clock.tick(self.fps) / 1000.0
            
            self.handle_input(delta_time)
            self.update(delta_time)
            self.render()


if __name__ == '__main__':
    game = Game()
    game.run()