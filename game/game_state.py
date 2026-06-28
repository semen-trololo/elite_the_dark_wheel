"""
game/game_state.py
Машина состояний игры (State Machine Pattern).

Совет от ментора:
Паттерн State Machine - один из самых важных в геймдеве!
Он позволяет cleanly разделить логику разных экранов:
- Полёт в космосе (SPACE_FLIGHT)
- Карта галактики (GALAXY_MAP)
- Гиперпрыжок (HYPERSPACE)
- Стыковка (DOCKING)
- Торговля (TRADE)
- Бой (COMBAT)

Без State Machine main.py превратится в спагетти из if/else.
"""

from enum import Enum, auto
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field


class GameState(Enum):
    """
    Все возможные состояния игры.
    
    Совет от ментора:
    В оригинальной Elite 1984 состояния были неявными - игра просто
    переключала разные экраны. Мы делаем это явно через Enum,
    что делает код более понятным и безопасным.
    """
    # === Основные состояния ===
    SPACE_FLIGHT = auto()      # Полёт в космосе (основной геймплей)
    GALAXY_MAP = auto()        # Карта галактики (выбор цели)
    HYPERSPACE = auto()        # Гиперпрыжок (анимация перехода)
    DOCKING = auto()           # Процесс стыковки со станцией
    
    # === Состояния на станции ===
    STATION_MENU = auto()      # Главное меню станции
    TRADE = auto()             # Экран торговли
    SHIP_UPGRADE = auto()      # Улучшение корабля
    MISSION_BOARD = auto()     # Доска миссий
    
    # === Системные состояния ===
    MAIN_MENU = auto()         # Главное меню игры
    PAUSED = auto()            # Пауза
    GAME_OVER = auto()         # Конец игры
    COMBAT = auto()            # Боевой режим (расширение SPACE_FLIGHT)


@dataclass
class StateContext:
    """
    Контекст игры, передаваемый между состояниями.
    
    Совет от ментора:
    Контекст хранит общие данные, которые нужны разным состояниям:
    - Текущий корабль
    - Текущая планета/система
    - Целевая планета для прыжка
    - Флаги событий (например, "игрок умер")
    
    Это позволяет состояниям обмениваться информацией без
    жёсткой связанности (low coupling).
    """
    # === Игровые объекты ===
    player_ship: Any = None                    # Корабль игрока
    current_planet: Any = None                 # Текущая планета
    target_planet: Any = None                  # Целевая планета для прыжка
    current_station: Any = None                # Текущая станция (если пристыкован)
    
    # === Состояние игры ===
    previous_state: Optional[GameState] = None # Предыдущее состояние
    is_game_over: bool = False                 # Флаг конца игры
    game_over_reason: str = ""                 # Причина конца игры
    
    # === Данные для переходов ===
    hyperspace_target: Any = None              # Цель гиперпрыжка
    docking_target: Any = None                 # Цель стыковки
    
    # === Дополнительные данные ===
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def set_extra(self, key: str, value: Any):
        """Установить дополнительное данное."""
        self.extra_data[key] = value
    
    def get_extra(self, key: str, default: Any = None) -> Any:
        """Получить дополнительное данное."""
        return self.extra_data.get(key, default)


class StateTransition:
    """
    Описывает переход между состояниями.
    
    Совет от ментора:
    Использование объектов для переходов позволяет:
    1. Валидировать переходы (нельзя перейти из HYPERSPACE в TRADE)
    2. Вызывать callback-и при входе/выходе
    3. Логировать историю переходов для отладки
    """
    
    def __init__(self, from_state: GameState, to_state: GameState,
                 on_enter: Optional[Callable] = None,
                 on_exit: Optional[Callable] = None,
                 condition: Optional[Callable] = None):
        """
        Args:
            from_state: исходное состояние
            to_state: целевое состояние
            on_enter: callback при входе в состояние
            on_exit: callback при выходе из состояния
            condition: функция проверки возможности перехода
        """
        self.from_state = from_state
        self.to_state = to_state
        self.on_enter = on_enter
        self.on_exit = on_exit
        self.condition = condition
    
    def can_transition(self, context: StateContext) -> bool:
        """Проверить возможность перехода."""
        if self.condition:
            return self.condition(context)
        return True
    
    def execute_enter(self, context: StateContext):
        """Выполнить callback входа."""
        if self.on_enter:
            self.on_enter(context)
    
    def execute_exit(self, context: StateContext):
        """Выполнить callback выхода."""
        if self.on_exit:
            self.on_exit(context)


class GameStateManager:
    """
    Менеджер состояний игры (State Machine).
    
    Совет от ментора:
    Это сердце управления потоком игры. Он:
    1. Хранит текущее состояние
    2. Валидирует переходы
    3. Вызывает callback-и при смене состояний
    4. Предоставляет единый API для всей игры
    
    Принцип Single Responsibility: менеджер только управляет
    переходами, не содержит бизнес-логики состояний.
    """
    
    def __init__(self, initial_state: GameState = GameState.MAIN_MENU):
        """
        Инициализация менеджера состояний.
        
        Args:
            initial_state: начальное состояние игры
        """
        self.current_state = initial_state
        self.context = StateContext()
        self.previous_states = []  # История состояний для отладки
        self.max_history = 20      # Максимальный размер истории
        
        # Регистрируем валидные переходы
        self._transitions = self._create_transition_table()
        
        # Callback-и для уведомлений о смене состояния
        self._on_state_change_callbacks = []
    
    def _create_transition_table(self) -> Dict[GameState, Dict[GameState, StateTransition]]:
        """
        Создать таблицу валидных переходов.
        
        Совет от ментора:
        Таблица переходов - это декларативное описание того,
        какие переходы разрешены. Это предотвращает ошибки типа
        "попытка открыть торговлю во время гиперпрыжка".
        
        Формат: {from_state: {to_state: StateTransition}}
        """
        transitions = {}
        
        # === Из MAIN_MENU ===
        transitions[GameState.MAIN_MENU] = {
            GameState.SPACE_FLIGHT: StateTransition(
                GameState.MAIN_MENU, 
                GameState.SPACE_FLIGHT,
                on_enter=self._on_enter_space_flight
            ),
        }
        
        # === Из SPACE_FLIGHT (полёт в космосе) ===
        transitions[GameState.SPACE_FLIGHT] = {
            GameState.GALAXY_MAP: StateTransition(
                GameState.SPACE_FLIGHT,
                GameState.GALAXY_MAP,
                on_enter=self._on_enter_galaxy_map,
                condition=self._can_open_galaxy_map
            ),
            GameState.HYPERSPACE: StateTransition(
                GameState.SPACE_FLIGHT,
                GameState.HYPERSPACE,
                on_enter=self._on_enter_hyperspace,
                condition=self._can_start_hyperspace
            ),
            GameState.DOCKING: StateTransition(
                GameState.SPACE_FLIGHT,
                GameState.DOCKING,
                on_enter=self._on_enter_docking,
                condition=self._can_start_docking
            ),
            GameState.GAME_OVER: StateTransition(
                GameState.SPACE_FLIGHT,
                GameState.GAME_OVER,
                on_enter=self._on_enter_game_over
            ),
            GameState.PAUSED: StateTransition(
                GameState.SPACE_FLIGHT,
                GameState.PAUSED
            ),
        }
        
        # === Из GALAXY_MAP (карта галактики) ===
        transitions[GameState.GALAXY_MAP] = {
            GameState.SPACE_FLIGHT: StateTransition(
                GameState.GALAXY_MAP,
                GameState.SPACE_FLIGHT,
                on_exit=self._on_exit_galaxy_map
            ),
            GameState.HYPERSPACE: StateTransition(
                GameState.GALAXY_MAP,
                GameState.HYPERSPACE,
                on_enter=self._on_enter_hyperspace,
                condition=self._can_start_hyperspace
            ),
        }
        
        # === Из HYPERSPACE (гиперпрыжок) ===
        transitions[GameState.HYPERSPACE] = {
            GameState.SPACE_FLIGHT: StateTransition(
                GameState.HYPERSPACE,
                GameState.SPACE_FLIGHT,
                on_enter=self._on_exit_hyperspace
            ),
            GameState.GAME_OVER: StateTransition(
                GameState.HYPERSPACE,
                GameState.GAME_OVER
            ),
        }
        
        # === Из DOCKING (стыковка) ===
        transitions[GameState.DOCKING] = {
            GameState.STATION_MENU: StateTransition(
                GameState.DOCKING,
                GameState.STATION_MENU,
                on_enter=self._on_enter_station_menu,
                condition=self._is_docking_successful
            ),
            GameState.SPACE_FLIGHT: StateTransition(
                GameState.DOCKING,
                GameState.SPACE_FLIGHT,
                on_enter=self._on_docking_failed
            ),
            GameState.GAME_OVER: StateTransition(
                GameState.DOCKING,
                GameState.GAME_OVER,
                on_enter=self._on_enter_game_over
            ),
        }
        
        # === Из STATION_MENU (меню станции) ===
        transitions[GameState.STATION_MENU] = {
            GameState.TRADE: StateTransition(
                GameState.STATION_MENU,
                GameState.TRADE,
                on_enter=self._on_enter_trade
            ),
            GameState.SHIP_UPGRADE: StateTransition(
                GameState.STATION_MENU,
                GameState.SHIP_UPGRADE
            ),
            GameState.MISSION_BOARD: StateTransition(
                GameState.STATION_MENU,
                GameState.MISSION_BOARD
            ),
            GameState.SPACE_FLIGHT: StateTransition(
                GameState.STATION_MENU,
                GameState.SPACE_FLIGHT,
                on_enter=self._on_undock
            ),
        }
        
        # === Из TRADE (торговля) ===
        transitions[GameState.TRADE] = {
            GameState.STATION_MENU: StateTransition(
                GameState.TRADE,
                GameState.STATION_MENU
            ),
        }
        
        # === Из PAUSED (пауза) ===
        transitions[GameState.PAUSED] = {
            GameState.SPACE_FLIGHT: StateTransition(
                GameState.PAUSED,
                GameState.SPACE_FLIGHT
            ),
            GameState.MAIN_MENU: StateTransition(
                GameState.PAUSED,
                GameState.MAIN_MENU
            ),
        }
        
        # === Из GAME_OVER (конец игры) ===
        transitions[GameState.GAME_OVER] = {
            GameState.MAIN_MENU: StateTransition(
                GameState.GAME_OVER,
                GameState.MAIN_MENU
            ),
        }
        
        return transitions
    
    # =========================================================================
    # Публичные методы
    # =========================================================================
    
    def change_state(self, new_state: GameState) -> bool:
        """
        Переключиться на новое состояние.
        
        Args:
            new_state: целевое состояние
        
        Returns:
            True если переход успешен, False если переход запрещён
        
        Совет от ментора:
        Этот метод - единственная точка входа для смены состояний.
        Все переходы проходят через него, что гарантирует:
        1. Валидацию перехода
        2. Вызов callback-ов
        3. Логирование истории
        4. Уведомление подписчиков
        """
        # Проверяем, что переход разрешён
        if not self.can_transition_to(new_state):
            print(f"⚠️ Переход {self.current_state.name} → {new_state.name} запрещён!")
            return False
        
        # Получаем объект перехода
        transition = self._transitions[self.current_state][new_state]
        
        # Выполняем callback выхода из текущего состояния
        transition.execute_exit(self.context)
        
        # Сохраняем историю
        self.previous_states.append(self.current_state)
        if len(self.previous_states) > self.max_history:
            self.previous_states.pop(0)
        
        # Переключаем состояние
        old_state = self.current_state
        self.current_state = new_state
        self.context.previous_state = old_state
        
        # Выполняем callback входа в новое состояние
        transition.execute_enter(self.context)
        
        # Уведомляем подписчиков
        self._notify_state_change(old_state, new_state)
        
        print(f"✅ Состояние: {old_state.name} → {new_state.name}")
        return True
    
    def can_transition_to(self, new_state: GameState) -> bool:
        """
        Проверить возможность перехода в новое состояние.
        
        Args:
            new_state: целевое состояние
        
        Returns:
            True если переход возможен
        """
        # Проверяем, есть ли такой переход в таблице
        if self.current_state not in self._transitions:
            return False
        
        if new_state not in self._transitions[self.current_state]:
            return False
        
        # Проверяем условие перехода
        transition = self._transitions[self.current_state][new_state]
        return transition.can_transition(self.context)
    
    def get_valid_transitions(self) -> list[GameState]:
        """
        Получить список всех доступных переходов из текущего состояния.
        
        Returns:
            Список доступных состояний
        """
        if self.current_state not in self._transitions:
            return []
        
        valid = []
        for target_state, transition in self._transitions[self.current_state].items():
            if transition.can_transition(self.context):
                valid.append(target_state)
        
        return valid
    
    def add_state_change_callback(self, callback: Callable[[GameState, GameState], None]):
        """
        Добавить callback для уведомления о смене состояния.
        
        Args:
            callback: функция(old_state, new_state)
        """
        self._on_state_change_callbacks.append(callback)
    
    def get_state_name(self) -> str:
        """Получить человекочитаемое имя текущего состояния."""
        state_names = {
            GameState.MAIN_MENU: "Главное меню",
            GameState.SPACE_FLIGHT: "Полёт в космосе",
            GameState.GALAXY_MAP: "Карта галактики",
            GameState.HYPERSPACE: "Гиперпрыжок",
            GameState.DOCKING: "Стыковка",
            GameState.STATION_MENU: "Меню станции",
            GameState.TRADE: "Торговля",
            GameState.SHIP_UPGRADE: "Улучшение корабля",
            GameState.MISSION_BOARD: "Доска миссий",
            GameState.PAUSED: "Пауза",
            GameState.GAME_OVER: "Конец игры",
            GameState.COMBAT: "Бой",
        }
        return state_names.get(self.current_state, "Неизвестно")
    
    # =========================================================================
    # Callback-и для переходов (внутренние методы)
    # =========================================================================
    
    def _on_enter_space_flight(self, context: StateContext):
        """Callback при входе в режим полёта."""
        print("🚀 Вход в режим полёта")
        # Сбрасываем флаги
        context.is_game_over = False
    
    def _on_enter_galaxy_map(self, context: StateContext):
        """Callback при открытии карты галактики."""
        print("🗺️ Открытие карты галактики")
    
    def _on_exit_galaxy_map(self, context: StateContext):
        """Callback при закрытии карты галактики."""
        print("🗺️ Закрытие карты галактики")
    
    def _on_enter_hyperspace(self, context: StateContext):
        """Callback при начале гиперпрыжка."""
        print("🌌 Начало гиперпрыжка")
        # Блокируем управление кораблём
        if context.player_ship:
            context.player_ship.is_in_hyperspace = True
    
    def _on_exit_hyperspace(self, context: StateContext):
        """Callback при завершении гиперпрыжка."""
        print("🌌 Завершение гиперпрыжка")
        # Разблокируем управление
        if context.player_ship:
            context.player_ship.is_in_hyperspace = False
        # Обновляем текущую планету
        if context.hyperspace_target:
            context.current_planet = context.hyperspace_target
            context.hyperspace_target = None
    
    def _on_enter_docking(self, context: StateContext):
        """Callback при начале стыковки."""
        print("🛬 Начало стыковки")
    
    def _on_enter_station_menu(self, context: StateContext):
        """Callback при входе в меню станции."""
        print("🏢 Вход в меню станции")
        if context.player_ship:
            context.player_ship.is_docked = True
    
    def _on_enter_trade(self, context: StateContext):
        """Callback при входе в экран торговли."""
        print("💰 Вход в экран торговли")
    
    def _on_undock(self, context: StateContext):
        """Callback при отстыковке."""
        print("🚀 Отстыковка от станции")
        if context.player_ship:
            context.player_ship.is_docked = False
            context.player_ship.undock()
        context.current_station = None
    
    def _on_enter_game_over(self, context: StateContext):
        """Callback при конце игры."""
        print("💀 Конец игры!")
        context.is_game_over = True
    
    def _on_docking_failed(self, context: StateContext):
        """Callback при неудачной стыковке."""
        print("❌ Стыковка не удалась, возврат в полёт")
    
    # =========================================================================
    # Условия переходов (validators)
    # =========================================================================
    
    def _can_open_galaxy_map(self, context: StateContext) -> bool:
        """Можно ли открыть карту галактики?"""
        if not context.player_ship:
            return False
        # Нельзя открыть карту во время стыковки или гиперпрыжка
        return (not context.player_ship.is_docked and 
                not context.player_ship.is_in_hyperspace)
    
    def _can_start_hyperspace(self, context: StateContext) -> bool:
        """Можно ли начать гиперпрыжок?"""
        if not context.player_ship or not context.hyperspace_target:
            return False
        # Проверяем возможность прыжка через корабль
        return context.player_ship.can_hyperspace_jump(context.hyperspace_target)
    
    def _can_start_docking(self, context: StateContext) -> bool:
        """Можно ли начать стыковку?"""
        if not context.player_ship or not context.docking_target:
            return False
        # Проверяем возможность стыковки через корабль
        return context.player_ship.can_dock_with_station(context.docking_target)
    
    def _is_docking_successful(self, context: StateContext) -> bool:
        """Была ли стыковка успешной?"""
        if not context.player_ship:
            return False
        return context.player_ship.is_docked
    
    # =========================================================================
    # Внутренние методы
    # =========================================================================
    
    def _notify_state_change(self, old_state: GameState, new_state: GameState):
        """Уведомить всех подписчиков о смене состояния."""
        for callback in self._on_state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                print(f"⚠️ Ошибка в callback смены состояния: {e}")
    
    def __str__(self) -> str:
        """Строковое представление менеджера."""
        return (
            f"GameStateManager(\n"
            f"  current_state={self.current_state.name},\n"
            f"  state_name='{self.get_state_name()}',\n"
            f"  history={[s.name for s in self.previous_states[-5:]]}\n"
            f")"
        )


# =========================================================================
# Singleton экземпляр для глобального доступа
# =========================================================================

# Создаём глобальный экземпляр менеджера
# Это позволяет обращаться к нему из любого места игры
_game_state_manager = None

def get_game_state_manager() -> GameStateManager:
    """
    Получить глобальный экземпляр менеджера состояний (Singleton).
    
    Совет от ментора:
    Singleton здесь уместен, потому что в игре должен быть только
    один менеджер состояний. Это классический пример использования
    паттерна Singleton в геймдеве.
    """
    global _game_state_manager
    if _game_state_manager is None:
        _game_state_manager = GameStateManager()
    return _game_state_manager