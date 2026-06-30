"""
game/game_state.py
Машина состояний игры (State Machine Pattern).

ИСПРАВЛЕНИЯ:
1. Убрано condition из перехода SPACE_FLIGHT → DOCKING (устраняет race condition)
2. Добавлен переход HYPERSPACE → GALAXY_MAP для возврата при ошибке прыжка.
3. Добавлен on_exit callback для HYPERSPACE, сбрасывающий флаг is_in_hyperspace.
"""

from enum import Enum, auto
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field


class GameState(Enum):
    """Все возможные состояния игры."""
    SPACE_FLIGHT = auto()
    GALAXY_MAP = auto()
    HYPERSPACE = auto()
    DOCKING = auto()
    STATION_MENU = auto()
    TRADE = auto()
    SHIP_UPGRADE = auto()
    MISSION_BOARD = auto()
    MAIN_MENU = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    COMBAT = auto()


@dataclass
class StateContext:
    """Контекст игры, передаваемый между состояниями."""
    player_ship: Any = None
    current_planet: Any = None
    target_planet: Any = None
    current_station: Any = None
    previous_state: Optional[GameState] = None
    is_game_over: bool = False
    game_over_reason: str = ""
    hyperspace_target: Any = None
    docking_target: Any = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def set_extra(self, key: str, value: Any):
        self.extra_data[key] = value
    
    def get_extra(self, key: str, default: Any = None) -> Any:
        return self.extra_data.get(key, default)


class StateTransition:
    """Описывает переход между состояниями."""
    
    def __init__(self, from_state: GameState, to_state: GameState,
                 on_enter: Optional[Callable] = None,
                 on_exit: Optional[Callable] = None,
                 condition: Optional[Callable] = None):
        self.from_state = from_state
        self.to_state = to_state
        self.on_enter = on_enter
        self.on_exit = on_exit
        self.condition = condition
    
    def can_transition(self, context: StateContext) -> bool:
        if self.condition:
            return self.condition(context)
        return True
    
    def execute_enter(self, context: StateContext):
        if self.on_enter:
            self.on_enter(context)
    
    def execute_exit(self, context: StateContext):
        if self.on_exit:
            self.on_exit(context)


class GameStateManager:
    """Менеджер состояний игры (State Machine)."""
    
    def __init__(self, initial_state: GameState = GameState.MAIN_MENU):
        self.current_state = initial_state
        self.context = StateContext()
        self.previous_states = []
        self.max_history = 20
        self._transitions = self._create_transition_table()
        self._on_state_change_callbacks = []
    
    def _create_transition_table(self) -> Dict[GameState, Dict[GameState, StateTransition]]:
        """Создать таблицу валидных переходов."""
        transitions = {}
        
        # === Из MAIN_MENU ===
        transitions[GameState.MAIN_MENU] = {
            GameState.SPACE_FLIGHT: StateTransition(
                GameState.MAIN_MENU, 
                GameState.SPACE_FLIGHT,
                on_enter=self._on_enter_space_flight
            ),
        }
        
        # === Из SPACE_FLIGHT ===
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
            # =================================================================
            # ВАЖНО: Без condition! Валидация стыковки уже выполнена в PhysicsEngine.
            # =================================================================
            GameState.DOCKING: StateTransition(
                GameState.SPACE_FLIGHT,
                GameState.DOCKING,
                on_enter=self._on_enter_docking
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
        
        # === Из GALAXY_MAP ===
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
        
        # === Из HYPERSPACE ===
        transitions[GameState.HYPERSPACE] = {
            GameState.SPACE_FLIGHT: StateTransition(
                GameState.HYPERSPACE,
                GameState.SPACE_FLIGHT,
                on_exit=self._on_exit_hyperspace,
                on_enter=self._on_exit_hyperspace_to_space_flight
            ),
            GameState.GALAXY_MAP: StateTransition(
                GameState.HYPERSPACE,
                GameState.GALAXY_MAP,
                on_exit=self._on_exit_hyperspace,
                on_enter=self._on_enter_galaxy_map
            ),
            GameState.GAME_OVER: StateTransition(
                GameState.HYPERSPACE,
                GameState.GAME_OVER,
                on_exit=self._on_exit_hyperspace
            ),
        }
        
        # === Из DOCKING ===
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
        
        # === Из STATION_MENU ===
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
        
        # === Из TRADE ===
        transitions[GameState.TRADE] = {
            GameState.STATION_MENU: StateTransition(
                GameState.TRADE,
                GameState.STATION_MENU
            ),
        }
        
        # === Из PAUSED ===
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
        
        # === Из GAME_OVER ===
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
        """Переключиться на новое состояние."""
        if not self.can_transition_to(new_state):
            print(f"⚠️ Переход {self.current_state.name} → {new_state.name} запрещён!")
            return False
        
        transition = self._transitions[self.current_state][new_state]
        transition.execute_exit(self.context)
        
        self.previous_states.append(self.current_state)
        if len(self.previous_states) > self.max_history:
            self.previous_states.pop(0)
        
        old_state = self.current_state
        self.current_state = new_state
        self.context.previous_state = old_state
        
        transition.execute_enter(self.context)
        self._notify_state_change(old_state, new_state)
        
        print(f"✅ Состояние: {old_state.name} → {new_state.name}")
        return True
    
    def can_transition_to(self, new_state: GameState) -> bool:
        """Проверить возможность перехода в новое состояние."""
        if self.current_state not in self._transitions:
            return False
        
        if new_state not in self._transitions[self.current_state]:
            return False
        
        transition = self._transitions[self.current_state][new_state]
        return transition.can_transition(self.context)
    
    def get_valid_transitions(self) -> list:
        """Получить список всех доступных переходов из текущего состояния."""
        if self.current_state not in self._transitions:
            return []
        
        valid = []
        for target_state, transition in self._transitions[self.current_state].items():
            if transition.can_transition(self.context):
                valid.append(target_state)
        
        return valid
    
    def add_state_change_callback(self, callback: Callable[[GameState, GameState], None]):
        """Добавить callback для уведомления о смене состояния."""
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
    # Callback-и для переходов
    # =========================================================================
    
    def _on_enter_space_flight(self, context: StateContext):
        """Callback при входе в режим полёта."""
        print("🚀 Вход в режим полёта")
        context.is_game_over = False
    
    def _on_enter_galaxy_map(self, context: StateContext):
        """Callback при открытии карты галактики."""
        print("🗺️ Открытие карты галактики")
    
    def _on_exit_galaxy_map(self, context: StateContext):
        """Callback при закрытии карты галактики."""
        print("🔙 Закрытие карты галактики")
    
    def _on_enter_hyperspace(self, context: StateContext):
        """Callback при начале гиперпрыжка."""
        print("🌌 Начало гиперпрыжка")
    
    def _on_exit_hyperspace(self, context: StateContext):
        """Callback при выходе из состояния гиперпрыжка."""
        print("🔙 Выход из гиперпространства (сброс флага)")
        if context.player_ship:
            context.player_ship.is_in_hyperspace = False
    
    def _on_exit_hyperspace_to_space_flight(self, context: StateContext):
        """Callback при успешном завершении гиперпрыжка и переходе в полёт."""
        print("🌍 Завершение гиперпрыжка")
        if context.hyperspace_target:
            context.current_planet = context.hyperspace_target
            context.hyperspace_target = None
    
    def _on_enter_docking(self, context: StateContext):
        """Callback при начале стыковки."""
        print("🛬 Начало анимации стыковки")
    
    def _on_enter_station_menu(self, context: StateContext):
        """Callback при входе в меню станции."""
        print("🏢 Вход в меню станции")
        if context.player_ship:
            context.player_ship.is_docked = True
    
    def _on_enter_trade(self, context: StateContext):
        """Callback при входе в экран торговли."""
        print("📦 Вход в экран торговли")
    
    def _on_undock(self, context: StateContext):
        """Callback при отстыковке."""
        print("🚀 Отстыковка от станции")
        if context.player_ship:
            context.player_ship.is_docked = False
            if hasattr(context.player_ship, 'undock'):
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
    # Условия переходов
    # =========================================================================
    
    def _can_open_galaxy_map(self, context: StateContext) -> bool:
        """Можно ли открыть карту галактики?"""
        if not context.player_ship:
            return False
        return (not context.player_ship.is_docked and 
                not context.player_ship.is_in_hyperspace)
    
    def _can_start_hyperspace(self, context: StateContext) -> bool:
        """Можно ли начать гиперпрыжок?"""
        if not context.player_ship or not context.hyperspace_target:
            return False
        return context.player_ship.can_hyperspace_jump(context.hyperspace_target)
    
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
        return (
            f"GameStateManager(\n"
            f"  current_state={self.current_state.name},\n"
            f"  state_name='{self.get_state_name()}',\n"
            f"  history={[s.name for s in self.previous_states[-5:]]}\n"
            f")"
        )


# Singleton экземпляр
_game_state_manager = None


def get_game_state_manager() -> GameStateManager:
    """Получить глобальный экземпляр менеджера состояний (Singleton)."""
    global _game_state_manager
    if _game_state_manager is None:
        _game_state_manager = GameStateManager()
    return _game_state_manager