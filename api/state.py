"""
api/state.py — глобальное состояние игры и блокировки
"""
import asyncio
from typing import Optional

# Активная игра на сервере
_active_game: Optional[dict] = None
_game_lock = asyncio.Lock()

# Поля с дефолтами, которые должны быть в state
STATE_DEFAULTS = {
    'dropped_orders': [],
    'ordersPlaced': [0, 0],
    'orders': [],
    'order_placed_this_turn': [False, False],
    'execution_order_played': [False, False],
    'round': 1,
    'event_cards_offered': [[], []],
    'event_selection_done': [False, False],
}


def get_active_game() -> Optional[dict]:
    """Получить текущую активную игру."""
    return _active_game


def set_active_game(game: Optional[dict]):
    """Установить активную игру."""
    global _active_game
    _active_game = game


def get_game_lock() -> asyncio.Lock:
    """Получить блокировку игры."""
    return _game_lock
