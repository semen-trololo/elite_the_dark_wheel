"""
gui/galaxy_screen.py
Экран карты галактики с выбором планет для гиперпрыжка.

Совет от ментора:
В оригинальной Elite 1984 года карта галактики была одним из ключевых экранов.
Игрок видел 256 точек-планет, мог выбрать цель и инициировать гиперпрыжок.
Стоимость прыжка зависела от расстояния и составляла 0.1 CR за световой год.

Мы сохраняем аутентичный стиль:
- Минималистичный wireframe-интерфейс
- Карта галактики в виде точек
- Информация о выбранной планете
- Расчет дистанции и стоимости прыжка
- Возможность переключения между галактиками
"""

import pygame
from typing import Optional, List
from universe.galaxy_generator import GalaxyGenerator
from universe.planet import Planet
from engine.math3d import Vector3


class GalaxyScreen:
    """
    Экран карты галактики для выбора цели гиперпрыжка.
    
    Атрибуты:
        generator: генератор галактик
        current_galaxy: номер текущей галактики (0-7)
        current_planet: текущая планета игрока
        selected_planet: выбранная планета-цель
        map_rect: прямоугольник области карты на экране
    
    Совет от ментора:
    В Elite 1984 карта была квадратной (256x256 координат).
    Мы сохраняем это соотношение и масштабируем под размер окна.
    Текущая позиция игрока отмечена крестиком, выбранная цель - кругом.
    """
    
    def __init__(self, generator: GalaxyGenerator, screen_width: int = 800, screen_height: int = 600):
        """
        Инициализация экрана карты галактики.
        
        Args:
            generator: генератор галактик
            screen_width: ширина экрана
            screen_height: высота экрана
        """
        self.generator = generator
        self.current_galaxy = 0
        self.current_planet: Optional[Planet] = None
        self.selected_planet: Optional[Planet] = None
        
        # Размеры экрана
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Область карты (оставляем место для информации справа)
        map_size = min(screen_width - 250, screen_height - 50)
        self.map_rect = pygame.Rect(20, 20, map_size, map_size)
        
        # Область информации о планете (справа от карты)
        self.info_rect = pygame.Rect(self.map_rect.right + 20, 20, 200, map_size)
        
        # Цвета в стиле Elite 1984 (зеленый на черном)
        self.color_background = (0, 0, 0)
        self.color_grid = (0, 64, 0)
        self.color_planet = (0, 255, 0)
        self.color_current = (255, 255, 0)
        self.color_selected = (255, 0, 0)
        self.color_text = (0, 255, 0)
        self.color_border = (0, 255, 0)
        
        # Шрифт
        self.font_small = pygame.font.Font(None, 20)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        
        # Состояние интерфейса
        self.hyperspace_cost = 0.0
        self.distance_to_target = 0.0
        self.can_jump = False
        
        # Кнопки
        self.button_jump_rect = pygame.Rect(self.info_rect.x, self.info_rect.bottom - 40, 200, 30)
        self.button_next_galaxy_rect = pygame.Rect(self.info_rect.x, self.info_rect.bottom - 80, 200, 30)
    
    def set_current_planet(self, planet: Planet):
        """
        Установить текущую планету игрока.
        
        Args:
            planet: текущая планета
        """
        self.current_planet = planet
    
    def set_current_galaxy(self, galaxy_number: int):
        """
        Установить текущую галактику.
        
        Args:
            galaxy_number: номер галактики (0-7)
        """
        if 0 <= galaxy_number <= 7:
            self.current_galaxy = galaxy_number
            self.selected_planet = None
            self._update_jump_info()
    
    def handle_events(self, events: List[pygame.event.Event]) -> Optional[str]:
        """
        Обработка событий ввода (мышь, клавиатура).
        
        Args:
            events: список событий pygame
        
        Returns:
            Строка-команда: "jump" (прыжок), "next_galaxy" (следующая галактика),
            "back" (возврат в полет), None (нет команды)
        
        Совет от ментора:
        В Elite 1984 управление было простым:
        - Клик мышью по планете - выбрать цель
        - J - инициировать прыжок
        - N - следующая галактика
        - ESC - вернуться в полет
        """
        for event in events:
            # Обработка кликов мыши
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Клик по карте - выбрать планету
                    if self.map_rect.collidepoint(mouse_pos):
                        planet = self._get_planet_at_position(mouse_pos)
                        if planet:
                            self.selected_planet = planet
                            self._update_jump_info()
                    
                    # Клик по кнопке прыжка
                    elif self.button_jump_rect.collidepoint(mouse_pos):
                        if self.can_jump and self.selected_planet:
                            return "jump"
                    
                    # Клик по кнопке следующей галактики
                    elif self.button_next_galaxy_rect.collidepoint(mouse_pos):
                        return "next_galaxy"
            
            # Обработка клавиатуры
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_j:  # J - прыжок
                    if self.can_jump and self.selected_planet:
                        return "jump"
                
                elif event.key == pygame.K_n:  # N - следующая галактика
                    return "next_galaxy"
                
                elif event.key == pygame.K_p:  # P - предыдущая галактика
                    return "prev_galaxy"
                
                elif event.key == pygame.K_ESCAPE:  # ESC - возврат
                    return "back"
        
        return None
    
    def _get_planet_at_position(self, screen_pos: tuple) -> Optional[Planet]:
        """
        Найти планету по координатам на экране.
        
        Args:
            screen_pos: позиция на экране (x, y)
        
        Returns:
            Планета или None, если клик был не по планете
        
        Совет от ментора:
        Мы проверяем все 256 планет и ищем ближайшую к клику.
        Если расстояние меньше порога (радиус клика) - возвращаем планету.
        """
        if not self.map_rect.collidepoint(screen_pos):
            return None
        
        # Преобразуем координаты экрана в координаты галактики
        rel_x = screen_pos[0] - self.map_rect.left
        rel_y = screen_pos[1] - self.map_rect.top
        
        # Масштабируем в координаты галактики (0-255)
        galaxy_x = (rel_x / self.map_rect.width) * 255
        galaxy_y = (rel_y / self.map_rect.height) * 255
        
        # Ищем ближайшую планету
        galaxy = self.generator.get_galaxy(self.current_galaxy)
        closest_planet = None
        min_distance = float('inf')
        click_radius = 10.0  # Радиус клика в координатах галактики
        
        for planet in galaxy:
            dx = planet.x - galaxy_x
            dy = planet.y - galaxy_y
            distance = (dx**2 + dy**2)**0.5
            
            if distance < min_distance and distance < click_radius:
                min_distance = distance
                closest_planet = planet
        
        return closest_planet
    
    def _update_jump_info(self):
        """
        Обновить информацию о прыжке (дистанция, стоимость, возможность прыжка).
        
        Совет от ментора:
        В оригинальной Elite 1984 стоимость прыжка была:
        distance (световые годы) * 0.1 CR
        
        Максимальная дальность прыжка была ограничена запасом топлива.
        Мы пока не реализуем топливо (это в Фазе 3), но оставляем задел.
        """
        if not self.current_planet or not self.selected_planet:
            self.hyperspace_cost = 0.0
            self.distance_to_target = 0.0
            self.can_jump = False
            return
        
        # Рассчитываем расстояние между планетами
        self.distance_to_target = self.current_planet.get_distance_to(self.selected_planet)
        
        # Стоимость прыжка: 0.1 CR за световой год
        self.hyperspace_cost = self.distance_to_target * 0.1
        
        # Прыжок возможен, если есть выбранная цель и она не текущая планета
        self.can_jump = (self.selected_planet != self.current_planet and 
                        self.distance_to_target > 0)
    
    def update(self, delta_time: float):
        """
        Обновление состояния экрана (анимации и т.д.).
        
        Args:
            delta_time: время с прошлого кадра в секундах
        
        Совет от ментора:
        В Elite 1984 карта была статичной, но мы можем добавить
        плавную анимацию выделения выбранной планеты.
        """
        # Пока не нужна сложная логика обновления
        pass
    
    def render(self, screen: pygame.Surface):
        """
        Отрисовка экрана карты галактики.
        
        Args:
            screen: поверхность pygame для отрисовки
        
        Совет от ментора:
        Отрисовка в стиле Elite 1984:
        - Черный фон
        - Зеленые точки-планеты
        - Желтый крестик - текущая позиция
        - Красный круг - выбранная цель
        - Рамка вокруг карты
        - Информация о планете справа
        """
        # Очистка экрана
        screen.fill(self.color_background)
        
        # Отрисовка рамки карты
        pygame.draw.rect(screen, self.color_border, self.map_rect, 2)
        
        # Отрисовка сетки (опционально, для стиля)
        grid_spacing = self.map_rect.width // 8
        for i in range(1, 8):
            x = self.map_rect.left + i * grid_spacing
            pygame.draw.line(screen, self.color_grid, (x, self.map_rect.top), 
                           (x, self.map_rect.bottom), 1)
            y = self.map_rect.top + i * grid_spacing
            pygame.draw.line(screen, self.color_grid, (self.map_rect.left, y), 
                           (self.map_rect.right, y), 1)
        
        # Получаем текущую галактику
        galaxy = self.generator.get_galaxy(self.current_galaxy)
        
        # Отрисовка всех планет
        for planet in galaxy:
            # Преобразуем координаты галактики (0-255) в координаты экрана
            screen_x = self.map_rect.left + (planet.x / 255.0) * self.map_rect.width
            screen_y = self.map_rect.top + (planet.y / 255.0) * self.map_rect.height
            
            # Определяем цвет и размер точки
            if planet == self.selected_planet:
                # Выбранная планета - красный круг
                color = self.color_selected
                radius = 5
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), radius, 2)
            elif planet == self.current_planet:
                # Текущая планета - желтый крестик
                color = self.color_current
                size = 6
                pygame.draw.line(screen, color, 
                               (int(screen_x - size), int(screen_y - size)),
                               (int(screen_x + size), int(screen_y + size)), 2)
                pygame.draw.line(screen, color,
                               (int(screen_x - size), int(screen_y + size)),
                               (int(screen_x + size), int(screen_y - size)), 2)
            else:
                # Обычная планета - зеленая точка
                color = self.color_planet
                radius = 2
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), radius)
        
        # Отрисовка линии от текущей планеты к выбранной (если есть)
        if self.current_planet and self.selected_planet:
            curr_x = self.map_rect.left + (self.current_planet.x / 255.0) * self.map_rect.width
            curr_y = self.map_rect.top + (self.current_planet.y / 255.0) * self.map_rect.height
            sel_x = self.map_rect.left + (self.selected_planet.x / 255.0) * self.map_rect.width
            sel_y = self.map_rect.top + (self.selected_planet.y / 255.0) * self.map_rect.height
            
            pygame.draw.line(screen, self.color_selected, 
                           (int(curr_x), int(curr_y)), 
                           (int(sel_x), int(sel_y)), 1)
        
        # Отрисовка информации о галактике
        galaxy_text = self.font_large.render(
            f"Галактика {self.current_galaxy + 1}", 
            True, self.color_text
        )
        screen.blit(galaxy_text, (self.map_rect.left, self.map_rect.bottom + 10))
        
        # Отрисовка информации о выбранной планете
        self._render_planet_info(screen)
        
        # Отрисовка кнопок
        self._render_buttons(screen)
    
    def _render_planet_info(self, screen: pygame.Surface):
        """
        Отрисовка информации о выбранной планете.
        
        Args:
            screen: поверхность pygame для отрисовки
        """
        # Рамка области информации
        pygame.draw.rect(screen, self.color_border, self.info_rect, 2)
        
        y_offset = self.info_rect.top + 10
        
        if self.selected_planet:
            # Название планеты
            name_text = self.font_medium.render(
                f"Планета: {self.selected_planet.name}", 
                True, self.color_text
            )
            screen.blit(name_text, (self.info_rect.left + 10, y_offset))
            y_offset += 30
            
            # Координаты
            coord_text = self.font_small.render(
                f"Координаты: ({self.selected_planet.x}, {self.selected_planet.y})",
                True, self.color_text
            )
            screen.blit(coord_text, (self.info_rect.left + 10, y_offset))
            y_offset += 25
            
            # Правительство
            gov_text = self.font_small.render(
                f"Правительство: {self.selected_planet.government.value}",
                True, self.color_text
            )
            screen.blit(gov_text, (self.info_rect.left + 10, y_offset))
            y_offset += 25
            
            # Экономика
            eco_text = self.font_small.render(
                f"Экономика: {self.selected_planet.economy.value}",
                True, self.color_text
            )
            screen.blit(eco_text, (self.info_rect.left + 10, y_offset))
            y_offset += 25
            
            # Население
            pop_text = self.font_small.render(
                f"Население: {self.selected_planet.population:.2f} млрд",
                True, self.color_text
            )
            screen.blit(pop_text, (self.info_rect.left + 10, y_offset))
            y_offset += 25
            
            # Технологии
            tech_text = self.font_small.render(
                f"Технологии: ур. {self.selected_planet.tech_level}",
                True, self.color_text
            )
            screen.blit(tech_text, (self.info_rect.left + 10, y_offset))
            y_offset += 35
            
            # Информация о прыжке
            if self.current_planet:
                dist_text = self.font_small.render(
                    f"Расстояние: {self.distance_to_target:.2f} св. лет",
                    True, self.color_text
                )
                screen.blit(dist_text, (self.info_rect.left + 10, y_offset))
                y_offset += 25
                
                cost_text = self.font_small.render(
                    f"Стоимость: {self.hyperspace_cost:.2f} CR",
                    True, self.color_text
                )
                screen.blit(cost_text, (self.info_rect.left + 10, y_offset))
                y_offset += 25
                
                if self.selected_planet == self.current_planet:
                    status_text = self.font_small.render(
                        "Это текущая планета",
                        True, (255, 255, 0)
                    )
                    screen.blit(status_text, (self.info_rect.left + 10, y_offset))
                elif not self.can_jump:
                    status_text = self.font_small.render(
                        "Прыжок невозможен",
                        True, (255, 0, 0)
                    )
                    screen.blit(status_text, (self.info_rect.left + 10, y_offset))
        else:
            # Нет выбранной планеты
            no_selection_text = self.font_medium.render(
                "Выберите планету",
                True, self.color_text
            )
            screen.blit(no_selection_text, (self.info_rect.left + 10, y_offset))
            y_offset += 30
            
            hint_text = self.font_small.render(
                "Кликните по точке на карте",
                True, self.color_text
            )
            screen.blit(hint_text, (self.info_rect.left + 10, y_offset))
    
    def _render_buttons(self, screen: pygame.Surface):
        """
        Отрисовка кнопок управления.
        
        Args:
            screen: поверхность pygame для отрисовки
        """
        # Кнопка прыжка
        jump_color = self.color_border if self.can_jump else (64, 64, 64)
        pygame.draw.rect(screen, jump_color, self.button_jump_rect, 2)
        
        jump_text = self.font_medium.render("Прыжок (J)", True, jump_color)
        text_rect = jump_text.get_rect(center=self.button_jump_rect.center)
        screen.blit(jump_text, text_rect)
        
        # Кнопка следующей галактики
        pygame.draw.rect(screen, self.color_border, self.button_next_galaxy_rect, 2)
        
        next_text = self.font_medium.render("След. галактика (N)", True, self.color_border)
        text_rect = next_text.get_rect(center=self.button_next_galaxy_rect.center)
        screen.blit(next_text, text_rect)
        
        # Подсказки по управлению внизу
        controls_y = self.screen_height - 30
        controls_text = self.font_small.render(
            "ESC - возврат | Клик - выбор | J - прыжок | N - след. галактика",
            True, self.color_text
        )
        screen.blit(controls_text, (20, controls_y))