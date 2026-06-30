"""
main.py
Точка входа в игру. Игровой цикл с pygame.

ИСПРАВЛЕНИЯ:
1. Флаг is_in_hyperspace устанавливается только после успешного start_jump().
2. Добавлена обработка ошибок гиперпрыжка с возвратом на карту галактики.
3. Добавлена защита от зависания в состоянии HYPERSPACE.
4. ✅ ИСПРАВЛЕНО: Race condition при стыковке — отслеживаем МОМЕНТ перехода is_docked
   (False → True), а не просто проверяем текущее состояние.
5. ✅ ИСПРАВЛЕНО: Убрана дублирующая проверка can_dock_with_station() — 
   PhysicsEngine уже обрабатывает стыковку.
"""

import pygame
import sys
import random
import math

from engine.math3d import Vector3, Matrix3x3
from engine.renderer import WireframeRenderer
from ship.player_ship import PlayerShip
from ship.physics import PhysicsEngine
from universe.galaxy_generator import GalaxyGenerator
from universe.station import Station, StationType
from gui.galaxy_screen import GalaxyScreen
from game.game_state import GameStateManager, GameState, get_game_state_manager


class Game:
    """Главный класс игры."""
    
    def __init__(self):
        pygame.init()
        
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Elite Clone - Cobra Mk III (Фаза 2)")
        
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        self.renderer = WireframeRenderer(self.width, self.height, fov=500)
        
        # === ИНИЦИАЛИЗАЦИЯ ИГРОВЫХ ОБЪЕКТОВ ===
        self.player_ship = PlayerShip(start_position=Vector3(0, 0, 0), ship_scale=0.025)
        
        self.galaxy_generator = GalaxyGenerator(base_seed=0)
        self.current_planet = self.galaxy_generator.get_planet(0, 0)
        self.player_ship.current_planet = self.current_planet
        
        self.current_station = Station(
            station_id=0,
            name=f"{self.current_planet.name} Station",
            station_type=StationType.CORIOLIS,
            position=Vector3(0, 0, 150),
            planet_name=self.current_planet.name
        )
        
        self.physics_engine = PhysicsEngine()
        
        # === ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА СОСТОЯНИЙ ===
        self.state_manager = get_game_state_manager()
        self.state_manager.context.player_ship = self.player_ship
        self.state_manager.context.current_planet = self.current_planet
        
        self.state_manager.add_state_change_callback(self._on_state_change)
        self.state_manager.change_state(GameState.SPACE_FLIGHT)
        
        # === ЭКРАНЫ ===
        self.galaxy_screen = GalaxyScreen(
            self.galaxy_generator,
            screen_width=self.width,
            screen_height=self.height
        )
        self.galaxy_screen.set_current_planet(self.current_planet)
        
        # === ВИЗУАЛЬНЫЕ ЭФФЕКТЫ ===
        self.color_background = (0, 0, 0)
        self.color_ship = (0, 255, 0)
        self.color_hud = (0, 255, 0)
        self.color_hud_dim = (0, 128, 0)
        
        self.stars = []
        for _ in range(200):
            star = Vector3(
                random.randint(-1000, 1000),
                random.randint(-1000, 1000),
                random.randint(10, 1000)
            )
            self.stars.append(star)
        
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Анимация стыковки
        self._docking_timer = 0.0
        self._docking_duration = 2.0
        
        # =====================================================================
        # ✅ НОВОЕ: Отслеживание момента стыковки (для избежания race condition)
        # =====================================================================
        self._was_docked = False
    
    # =========================================================================
    # CALLBACK ПРИ СМЕНЕ СОСТОЯНИЯ
    # =========================================================================
    def _on_state_change(self, old_state: GameState, new_state: GameState):
        """Callback при смене состояния."""
        if new_state == GameState.GALAXY_MAP:
            self.galaxy_screen.set_current_planet(self.current_planet)
        elif new_state == GameState.HYPERSPACE:
            if self.state_manager.context.hyperspace_target:
                jump_started = self.physics_engine.hyperspace_navigator.start_jump(
                    self.player_ship,
                    self.state_manager.context.hyperspace_target
                )
                
                if jump_started:
                    self.player_ship.is_in_hyperspace = True
                    print(f"✅ Гиперпрыжок запущен! Топливо: {self.player_ship.fuel:.1f} св. лет")
                else:
                    print("❌ Гиперпрыжок невозможен! Недостаточно топлива или цель слишком далеко.")
                    print(f"   Топливо: {self.player_ship.fuel:.1f} св. лет")
                    if self.state_manager.context.hyperspace_target:
                        distance = self.current_planet.get_distance_to(
                            self.state_manager.context.hyperspace_target
                        )
                        print(f"   Расстояние: {distance:.2f} св. лет")
                    self.state_manager.context.hyperspace_target = None
                    self.state_manager.change_state(GameState.GALAXY_MAP)
        elif new_state == GameState.DOCKING:
            self._docking_timer = 0.0
        elif new_state == GameState.STATION_MENU:
            print(f"🏪 Добро пожаловать на станцию: {self.current_station.name}")
        elif new_state == GameState.SPACE_FLIGHT and old_state == GameState.STATION_MENU:
            # Возврат из станции — обновляем флаг, чтобы не триггерилась повторная стыковка
            self._was_docked = self.player_ship.is_docked
    
    # =========================================================================
    # ОБРАБОТКА ВВОДА
    # =========================================================================
    def handle_input(self, delta_time):
        """Обработка ввода с учётом текущего состояния."""
        current_state = self.state_manager.current_state
        
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_state == GameState.SPACE_FLIGHT:
                        pygame.quit()
                        sys.exit()
                    elif current_state == GameState.GALAXY_MAP:
                        self.state_manager.change_state(GameState.SPACE_FLIGHT)
                    elif current_state == GameState.PAUSED:
                        self.state_manager.change_state(GameState.SPACE_FLIGHT)
                    elif current_state == GameState.STATION_MENU:
                        self.player_ship.undock()
                        self.state_manager.change_state(GameState.SPACE_FLIGHT)
                
                elif event.key == pygame.K_m and current_state == GameState.SPACE_FLIGHT:
                    self.state_manager.change_state(GameState.GALAXY_MAP)
                
                elif event.key == pygame.K_p and current_state == GameState.SPACE_FLIGHT:
                    self.state_manager.change_state(GameState.PAUSED)
                
                elif event.key == pygame.K_f and current_state == GameState.SPACE_FLIGHT:
                    if self.physics_engine.docking_computer.is_active:
                        self.physics_engine.docking_computer.deactivate()
                        self.player_ship.is_autopilot_active = False
                        print("🛑 Автопилот деактивирован")
                    else:
                        if self.physics_engine.docking_computer.activate(self.current_station):
                            self.player_ship.is_autopilot_active = True
        
        keys = pygame.key.get_pressed()
        
        if current_state == GameState.SPACE_FLIGHT:
            self.player_ship.handle_input(keys, delta_time)
        
        elif current_state == GameState.GALAXY_MAP:
            command = self.galaxy_screen.handle_events(events)
            
            if command == "jump":
                target = self.galaxy_screen.selected_planet
                if target:
                    self.state_manager.context.hyperspace_target = target
                    self.state_manager.change_state(GameState.HYPERSPACE)
            elif command == "next_galaxy":
                next_galaxy = (self.galaxy_screen.current_galaxy + 1) % 8
                self.galaxy_screen.set_current_galaxy(next_galaxy)
            elif command == "prev_galaxy":
                prev_galaxy = (self.galaxy_screen.current_galaxy - 1) % 8
                self.galaxy_screen.set_current_galaxy(prev_galaxy)
            elif command == "back":
                self.state_manager.change_state(GameState.SPACE_FLIGHT)
        
        elif current_state == GameState.PAUSED:
            if keys[pygame.K_p]:
                self.state_manager.change_state(GameState.SPACE_FLIGHT)
        
        elif current_state == GameState.STATION_MENU:
            if keys[pygame.K_4]:
                self.player_ship.undock()
                self.state_manager.change_state(GameState.SPACE_FLIGHT)
    
    # =========================================================================
    # ОБНОВЛЕНИЕ СОСТОЯНИЯ
    # =========================================================================
    def update(self, delta_time):
        """Обновление состояния с учётом текущего режима."""
        current_state = self.state_manager.current_state
        
        # =====================================================================
        # РЕЖИМ: ПОЛЁТ В КОСМОСЕ
        # =====================================================================
        if current_state == GameState.SPACE_FLIGHT:
            self.player_ship.update(delta_time)
            
            # Останавливаем вращение станции, если работает автопилот
            # (аутентично оригинальной Elite 1984 — посадочный порт статичен при стыковке)
            if not self.physics_engine.docking_computer.is_active:
                self.current_station.update(delta_time)
            
            # Физика: движение, автопилот, столкновения
            self.physics_engine.update(
                self.player_ship,
                [self.current_station],
                delta_time
            )
            
            self.player_ship.is_autopilot_active = self.physics_engine.docking_computer.is_active
            
            # =================================================================
            # ✅ ИСПРАВЛЕНО: Отслеживаем МОМЕНТ стыковки (переход False → True)
            # =================================================================
            # PhysicsEngine вызывает ship.dock_with_station() внутри update()
            # Мы должны зафиксировать это событие и переключиться в DOCKING
            if self.player_ship.is_docked and not self._was_docked:
                # Стыковка только что произошла!
                print("🔗 Стыковка обнаружена — переход в DOCKING")
                self.physics_engine.docking_computer.deactivate()
                self.player_ship.is_autopilot_active = False
                self.state_manager.change_state(GameState.DOCKING)
            
            # Обновляем предыдущее состояние
            self._was_docked = self.player_ship.is_docked
            
            # Ограничение дистанции от центра вселенной
            max_distance = 500
            if self.player_ship.position.magnitude() > max_distance:
                self.player_ship.position = self.player_ship.position.normalize() * max_distance
        
        # =====================================================================
        # РЕЖИМ: ГИПЕРПРЫЖОК
        # =====================================================================
        elif current_state == GameState.HYPERSPACE:
            # Защита от зависания, если навигатор в IDLE
            if not self.physics_engine.hyperspace_navigator.is_active():
                print("⚠️ Навигатор неактивен в состоянии HYPERSPACE! Возврат в полёт.")
                self.state_manager.context.hyperspace_target = None
                self.state_manager.change_state(GameState.SPACE_FLIGHT)
                return
            
            jump_complete = self.physics_engine.hyperspace_navigator.update(
                self.player_ship,
                delta_time
            )
            
            if jump_complete:
                target = self.state_manager.context.hyperspace_target
                if target:
                    self.current_planet = target
                    self.player_ship.current_planet = target
                    
                    self.current_station = Station(
                        station_id=random.randint(1, 1000),
                        name=f"{target.name} Station",
                        station_type=StationType.CORIOLIS,
                        position=Vector3(0, 0, 150),
                        planet_name=target.name
                    )
                    
                    self.state_manager.context.current_planet = target
                    self.state_manager.context.hyperspace_target = None
                    
                    print(f"🌍 Прибытие в систему: {target.name}")
                
                self.state_manager.change_state(GameState.SPACE_FLIGHT)
        
        # =====================================================================
        # РЕЖИМ: АНИМАЦИЯ СТЫКОВКИ
        # =====================================================================
        elif current_state == GameState.DOCKING:
            self._docking_timer += delta_time
            if self._docking_timer >= self._docking_duration:
                self._docking_timer = 0.0
                self.state_manager.change_state(GameState.STATION_MENU)
        
        # =====================================================================
        # РЕЖИМ: КАРТА ГАЛАКТИКИ
        # =====================================================================
        elif current_state == GameState.GALAXY_MAP:
            self.galaxy_screen.update(delta_time)
    
    # =========================================================================
    # ОТРИСОВКА
    # =========================================================================
    def render(self):
        """Отрисовка с учётом текущего состояния."""
        current_state = self.state_manager.current_state
        
        self.screen.fill(self.color_background)
        
        if current_state == GameState.SPACE_FLIGHT:
            self._render_space_flight()
        elif current_state == GameState.GALAXY_MAP:
            self.galaxy_screen.render(self.screen)
        elif current_state == GameState.HYPERSPACE:
            self._render_hyperspace()
        elif current_state == GameState.DOCKING:
            self._render_docking()
        elif current_state == GameState.PAUSED:
            self._render_paused()
        elif current_state == GameState.STATION_MENU:
            self._render_station_menu()
        
        pygame.display.flip()
    
    # -------------------------------------------------------------------------
    # ПОЛЁТ В КОСМОСЕ
    # -------------------------------------------------------------------------
    def _render_space_flight(self):
        """Отрисовка режима полёта в космосе."""
        # Звёзды
        for star in self.stars:
            star_relative = star - self.player_ship.position
            projected = self.renderer.project(star_relative)
            if projected:
                x, y = projected
                pygame.draw.circle(self.screen, (200, 200, 200), (x, y), 1)
        
        # Станция (если близко)
        station_distance = (self.current_station.position - self.player_ship.position).magnitude()
        if station_distance < 1000:
            station_mesh = self.current_station.get_mesh(scale=0.4)
            station_relative = self.current_station.position - self.player_ship.position
            
            # Инверсное вращение камеры
            inv_rotation = Matrix3x3.rotation_z(-self.player_ship.rotation.z)
            inv_rotation = inv_rotation * Matrix3x3.rotation_y(-self.player_ship.rotation.y)
            inv_rotation = inv_rotation * Matrix3x3.rotation_x(-self.player_ship.rotation.x)
            
            station_rotated = inv_rotation * station_relative
            station_rotation_matrix = Matrix3x3.rotation_y(self.current_station.rotation_angle)
            
            lines = self.renderer.render_mesh(
                station_mesh,
                position=station_rotated,
                rotation_matrix=station_rotation_matrix
            )
            
            for line in lines:
                x1, y1, x2, y2 = line
                pygame.draw.line(self.screen, (0, 200, 255), (x1, y1), (x2, y2), 1)
        
        # Корабль игрока (вид от первого лица — корабль в центре)
        camera_offset = Vector3(0, 0, 8)
        rotation_matrix = self.player_ship.get_rotation_matrix()
        
        lines = self.renderer.render_mesh(
            self.player_ship.mesh,
            position=camera_offset,
            rotation_matrix=rotation_matrix
        )
        
        for line in lines:
            x1, y1, x2, y2 = line
            pygame.draw.line(self.screen, self.color_ship, (x1, y1), (x2, y2), 1)
        
        # HUD и подсказки
        self._render_hud()
        
        controls_text = self.font_small.render(
            "W/S: Тангаж | A/D: Рыскание | Q/E: Крен | Space: Тяга | F: Автопилот | M: Карта | ESC: Выход",
            True, (100, 100, 100)
        )
        self.screen.blit(controls_text, (10, self.height - 25))
    
    # -------------------------------------------------------------------------
    # ГИПЕРПРЫЖОК
    # -------------------------------------------------------------------------
    def _render_hyperspace(self):
        """Отрисовка режима гиперпрыжка."""
        tunnel_stars = self.physics_engine.hyperspace_navigator.get_tunnel_stars()
        
        for star_data in tunnel_stars:
            star = star_data[0]
            velocity = star_data[1]
            projected = self.renderer.project(star)
            if projected:
                x, y = projected
                center_x, center_y = self.width // 2, self.height // 2
                
                dx = x - center_x
                dy = y - center_y
                line_length = velocity * 2
                
                end_x = x + int(dx * line_length / 100)
                end_y = y + int(dy * line_length / 100)
                
                phase = self.physics_engine.hyperspace_navigator.phase
                if phase == "CHARGING":
                    color = (255, 255, 0)
                elif phase == "TUNNEL":
                    color = (0, 255, 255)
                elif phase == "EXIT":
                    color = (255, 255, 255)
                else:
                    color = (200, 200, 200)
                
                pygame.draw.line(self.screen, color, (x, y), (end_x, end_y), 2)
        
        # Прогресс-бар
        progress = self.physics_engine.hyperspace_navigator.get_progress()
        status = self.physics_engine.hyperspace_navigator.get_status()
        
        bar_width = 300
        bar_height = 20
        bar_x = (self.width - bar_width) // 2
        bar_y = self.height // 2 + 50
        
        pygame.draw.rect(self.screen, (64, 64, 64), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 255, 255), (bar_x, bar_y, int(bar_width * progress), bar_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Текст статуса
        status_text = self.font_large.render(f"ГИПЕРПРЫЖОК: {status}", True, (0, 255, 255))
        text_rect = status_text.get_rect(center=(self.width // 2, self.height // 2 - 50))
        self.screen.blit(status_text, text_rect)
        
        # Цель прыжка
        if self.state_manager.context.hyperspace_target:
            target_name = self.state_manager.context.hyperspace_target.name
            target_text = self.font_medium.render(f"Цель: {target_name}", True, (200, 200, 200))
            target_rect = target_text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(target_text, target_rect)
    
    # -------------------------------------------------------------------------
    # СТЫКОВКА (анимация)
    # -------------------------------------------------------------------------
    def _render_docking(self):
        """Отрисовка режима стыковки (анимация тоннеля)."""
        self._render_space_flight()
        
        # Затемнение
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Расходящиеся линии (эффект влёта в порт)
        center_x, center_y = self.width // 2, self.height // 2
        num_lines = 20
        for i in range(num_lines):
            angle = (2 * math.pi * i / num_lines) + (self._docking_timer * 2)
            radius = 50 + self._docking_timer * 100
            end_x = center_x + int(radius * 3 * math.cos(angle))
            end_y = center_y + int(radius * 3 * math.sin(angle))
            pygame.draw.line(self.screen, (0, 255, 0), (center_x, center_y), (end_x, end_y), 2)
        
        # Текст
        docking_text = self.font_large.render("СТЫКОВКА...", True, (0, 255, 0))
        text_rect = docking_text.get_rect(center=(self.width // 2, self.height // 2 - 50))
        self.screen.blit(docking_text, text_rect)
        
        # Прогресс-бар
        progress = self._docking_timer / self._docking_duration
        bar_width = 300
        bar_height = 20
        bar_x = (self.width - bar_width) // 2
        bar_y = self.height // 2 + 50
        
        pygame.draw.rect(self.screen, (64, 64, 64), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
    
    # -------------------------------------------------------------------------
    # ПАУЗА
    # -------------------------------------------------------------------------
    def _render_paused(self):
        """Отрисовка режима паузы."""
        self._render_space_flight()
        
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        paused_text = self.font_large.render("ПАУЗА", True, (255, 255, 0))
        text_rect = paused_text.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(paused_text, text_rect)
        
        continue_text = self.font_medium.render("Нажмите P для продолжения", True, (200, 200, 200))
        continue_rect = continue_text.get_rect(center=(self.width // 2, self.height // 2 + 30))
        self.screen.blit(continue_text, continue_rect)
    
    # -------------------------------------------------------------------------
    # МЕНЮ СТАНЦИИ
    # -------------------------------------------------------------------------
    def _render_station_menu(self):
        """Отрисовка меню станции."""
        title_text = self.font_large.render(
            f"СТАНЦИЯ: {self.current_station.name}",
            True, (0, 255, 0)
        )
        title_rect = title_text.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Информация о планете
        planet_text = self.font_medium.render(
            f"Планета: {self.current_planet.name}",
            True, (0, 200, 0)
        )
        planet_rect = planet_text.get_rect(center=(self.width // 2, 90))
        self.screen.blit(planet_text, planet_rect)
        
        # Меню
        menu_items = [
            "1. Торговля (скоро — Фаза 3)",
            "2. Улучшение корабля (скоро)",
            "3. Доска миссий (скоро)",
            "4. Отстыковаться"
        ]
        
        y_offset = 150
        for item in menu_items:
            item_text = self.font_medium.render(item, True, (200, 200, 200))
            self.screen.blit(item_text, (self.width // 2 - 150, y_offset))
            y_offset += 40
        
        # Информация о корабле
        ship_info_y = 380
        info_items = [
            f"Кредиты: {self.player_ship.credits:.0f} CR",
            f"Топливо: {self.player_ship.fuel:.1f} св. лет",
            f"Щиты: {self.player_ship.shields:.0f}%",
            f"Корпус: {self.player_ship.hull:.0f}%"
        ]
        
        info_title = self.font_medium.render("--- СОСТОЯНИЕ КОРАБЛЯ ---", True, (0, 255, 0))
        self.screen.blit(info_title, (self.width // 2 - 120, ship_info_y))
        ship_info_y += 30
        
        for info in info_items:
            info_text = self.font_small.render(info, True, (0, 200, 0))
            self.screen.blit(info_text, (self.width // 2 - 80, ship_info_y))
            ship_info_y += 20
        
        # Подсказка
        hint_text = self.font_small.render(
            "Нажмите 4 для отстыковки или ESC для выхода",
            True, (100, 100, 100)
        )
        self.screen.blit(hint_text, (self.width // 2 - 200, self.height - 50))
    
    # -------------------------------------------------------------------------
    # HUD
    # -------------------------------------------------------------------------
    def _render_hud(self):
        """Отрисовка HUD в режиме полёта."""
        y_offset = 10
        
        # Скорость
        speed = self.player_ship.velocity.magnitude()
        speed_text = self.font_medium.render(f"Скорость: {speed:.1f} ед/сек", True, self.color_hud)
        self.screen.blit(speed_text, (10, y_offset))
        y_offset += 25
        
        # Статус корабля
        status = self.player_ship.get_status_string()
        status_parts = status.split(" | ")
        for part in status_parts:
            status_text = self.font_small.render(part, True, self.color_hud_dim)
            self.screen.blit(status_text, (10, y_offset))
            y_offset += 18
        
        y_offset += 10
        
        # Информация о текущей планете
        if self.player_ship.current_planet:
            planet_text = self.font_medium.render(
                f"Планета: {self.player_ship.current_planet.name}",
                True, self.color_hud
            )
            self.screen.blit(planet_text, (10, y_offset))
            y_offset += 25
            
            gov_text = self.font_small.render(
                f"Правительство: {self.player_ship.current_planet.government.value}",
                True, self.color_hud_dim
            )
            self.screen.blit(gov_text, (10, y_offset))
        
        # Правая часть HUD: статус систем
        physics_status = self.physics_engine.get_status()
        x_right = self.width - 250
        y_right = 10
        
        docking_status = self.font_small.render(
            f"Стыковка: {physics_status['docking']}",
            True, self.color_hud_dim
        )
        self.screen.blit(docking_status, (x_right, y_right))
        y_right += 18
        
        hyperspace_status = self.font_small.render(
            f"Гиперпрыжок: {physics_status['hyperspace']}",
            True, self.color_hud_dim
        )
        self.screen.blit(hyperspace_status, (x_right, y_right))
    
    # =========================================================================
    # ГЛАВНЫЙ ЦИКЛ
    # =========================================================================
    def run(self):
        """Главный игровой цикл."""
        running = True
        
        print("=" * 60)
        print(" Elite Clone - Фаза 2 (с GameStateManager)")
        print("=" * 60)
        print(f"Корабль: Cobra Mk III")
        print(f"Стартовая планета: {self.current_planet.name}")
        print(f"Начальное топливо: {self.player_ship.fuel:.1f} св. лет")
        print("=" * 60)
        print("Управление:")
        print("  W/S/A/D/Q/E - Управление кораблём")
        print("  Space/Shift   - Тяга/Торможение")
        print("  F             - Автопилот стыковки")
        print("  M             - Карта галактики")
        print("  P             - Пауза")
        print("  ESC           - Выход")
        print("=" * 60)
        
        while running:
            delta_time = self.clock.tick(self.fps) / 1000.0
            self.handle_input(delta_time)
            self.update(delta_time)
            self.render()


if __name__ == '__main__':
    game = Game()
    game.run()