"""
order_advance.py — Приказ ADVANCE (Move / Продвижение)
=======================================================
Этот файл описывает механику приказа Advance в игре Stellar Conflict.
Используется как справочник при реализации логики в game_engine.html.

ПОРЯДОК ИСПОЛНЕНИЯ
------------------
1. Игрок выбирает тайл с жетоном Advance.
2. Вначале двигаются КОРАБЛИ (space units).
3. Затем двигается СУХОПУТНАЯ АРМИЯ (ground units).
4. Если в итоге в какой-либо области встречаются войска разных игроков — БИТВА.

ДВИЖЕНИЕ КОРАБЛЕЙ
-----------------
- Корабли могут переместиться в любую соседнюю систему (1 переход).
- Блокируется ВАРП-ШТОРМОМ на общей границе двух тайлов.
- Корабли из любых соседних систем могут войти в систему с приказом.
- После движения кораблей фиксируется «оспариваемая» область кораблей:
  contested_space = области где теперь есть и свои и чужие корабли.

ДВИЖЕНИЕ СУХОПУТНЫХ ВОЙСК
-------------------------
- Двигаются только после кораблей.
- Маршрут — непрерывная линия ДРУЖЕСТВЕННЫХ ОБЛАСТЕЙ.
- Дружественная область = область где стоят войска ИЛИ постройки текущего игрока.
- Корабли игрока, вставшие в незанятую область, делают её дружественной.
- Нельзя проходить через вражескую или нейтральную область (только финишировать там).
- Если корабли СОЗДАЛИ оспариваемую область (contested_space):
  → сухопутные войска НЕ МОГУТ зайти ни в какую вражескую область.
- Если корабли НЕ создали оспариваемую область:
  → сухопутные войска могут зайти в ОДНУ вражескую/нейтральную область.

ВМЕСТИМОСТЬ ПЛАНЕТЫ
-------------------
- Максимум юнитов в планетарной области:
  * HOME тайл: capacity = 3
  * NORMAL тайл: capacity = 2
- Перед битвой: если юнитов > 5, лишние удаляются (сначала атакующие).
- После битвы/движения: если юнитов > capacity, лишние удаляются.

ВАРП-ШТОРМ
-----------
- Стоит на границе между двумя тайлами или на внешнем крае тайла.
- Запрещает переброску войск из одной системы в другую через эту границу.
- Не влияет на приказ Advance сам по себе — приказ можно поставить.
- Только при исполнении движения граница с варп-штормом непроходима.

ПРОПУСК ПРИКАЗА
---------------
- Игрок может открыть приказ и ничего не сделать → приказ уходит в стек событий.
- Стек событий каждого игрока независим (G.eventStacks[pi]).

ОТМЕНА ХОДА
-----------
- До совершения каких-либо действий: кнопка "Отменить ход" доступна.
- После отмены: состояние возвращается к снапшоту начала хода (_turnSnap).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AdvanceOrderResult:
    """Результат выполнения приказа Advance."""
    ships_moved: int = 0          # количество переместившихся кораблей
    ground_moved: int = 0         # количество переместившихся сухопутных
    contested_created: bool = False  # были ли созданы оспариваемые области
    battles: list = field(default_factory=list)  # список BattleResult
    blocked_by_warp_storm: list = field(default_factory=list)  # заблокированные переходы
    skipped: bool = False         # игрок ничего не сделал → в стек событий


def can_cross_border(game_state, from_key: str, to_key: str) -> bool:
    """
    Проверяет, не заблокирован ли переход между двумя тайлами варп-штормом.

    Алгоритм:
    - Находим общую границу двух тайлов (col/row разница = 1).
    - Ищем запись в game_state.warp_storms совпадающую с этой границей.
    - Если есть — переход заблокирован.
    """
    warp_storms = getattr(game_state, 'warp_storms', [])
    for storm in warp_storms:
        if (storm.get('tileA') == from_key and storm.get('tileB') == to_key) or \
           (storm.get('tileA') == to_key and storm.get('tileB') == from_key):
            return False
    return True


def get_friendly_areas(game_state, player_idx: int) -> set:
    """
    Возвращает set из строк 'tileKey:areaIdx' — все области где есть
    войска или постройки игрока player_idx.
    """
    friendly = set()
    for tile_key, tile in game_state.map.items():
        for area_idx, area in enumerate(tile.areas):
            has_units = any(u.player == player_idx for u in area.troops)
            has_structs = any(s.player == player_idx for s in area.structures)
            if has_units or has_structs:
                friendly.add(f"{tile_key}:{area_idx}")
    return friendly


def trim_area_to_capacity(area, attacker_pi: int) -> int:
    """
    Обрезает количество юнитов в области до вместимости.
    Сначала удаляет лишних атакующих, затем лишних защищающихся.
    Возвращает количество удалённых юнитов.
    """
    capacity = getattr(area, 'capacity', 2)
    removed = 0
    # Ограничение перед битвой: не более 5
    pre_battle_cap = min(5, capacity)
    while len(area.troops) > pre_battle_cap:
        # Удалить сначала атакующего (player == attacker_pi)
        attackers = [u for u in area.troops if u.player == attacker_pi]
        if attackers:
            area.troops.remove(attackers[-1])
        else:
            area.troops.pop()
        removed += 1
    return removed
