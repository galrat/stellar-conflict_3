"""
order_dominate.py — Приказ DOMINATE (Доминирование)
====================================================
Этот файл описывает механику приказа Dominate в игре Stellar Conflict.
Используется как справочник при реализации логики в game_engine.html.

ПОРЯДОК ИСПОЛНЕНИЯ
------------------
1. Открывается модальное окно Dominate.
2. Игрок получает ЦЕННЫЕ РЕСУРСЫ (joker-токены) за каждую планету в системе
   где есть его войска или постройка. Доход = сумма доходов планет.
3. Дополнительно можно использовать ОСОБУЮ СПОСОБНОСТЬ фракции (бесплатно).
4. Завершить ход.

БАЗОВЫЙ ДОХОД
-------------
За каждую ПЛАНЕТАРНУЮ область в системе приказа где есть хотя бы:
- один юнит игрока, ИЛИ
- одна постройка игрока
→ игрок получает income-значение этой планеты (обычно 1, но бывает больше).

ОСОБЫЕ СПОСОБНОСТИ ПО ФРАКЦИЯМ
-------------------------------

Хаос (Chaos):
  Переместить одного культиста (T0 наземный) из активной системы
  на свободную или дружественную планету СОСЕДНЕЙ системы.
  Условия: культист есть в активной системе, есть подходящая соседняя планета.
  Стоимость: бесплатно.

Space Marines (marine):
  Улучшить одного юнита T0→T1 или T1→T2 в активной системе.
  Условия: есть юнит T0 или T1 в системе.
  Стоимость: 1₡ (НЕ молоток!).
  Реализация: игрок кликает юнита прямо на карте.

Орки (orks):
  Купить 1 юнита и разместить его на дружественной планете активной системы.
  Условия: есть дружественная планета (с юнитами игрока).
  Стоимость: по стандартной цене юнита.
  Реализация: открывается отдельное deploy-окно с max_cart_size=1.

Элдары (eldar):
  Переместить одного юнита из любой области активной системы
  на любую дружественную планету (в любой системе).
  Условия: есть юниты в активной системе.
  Стоимость: бесплатно.

ПРОПУСК СПОСОБНОСТИ
-------------------
Игрок может получить доход и не использовать способность → это нормально.
Если вообще ничего не сделано (нет дохода, нет способности) → в стек событий.
Но доход считается автоматически при открытии Dominate → пропуск невозможен
если есть хотя бы одна дружественная планета.

СТЕК СОБЫТИЙ
------------
Приказ Dominate уходит в стек событий только если:
- Игрок ничего не получил (нет дружественных планет) И
- Не использовал особую способность.

ОТМЕНА ХОДА
-----------
"Отменить ход" → возврат к снапшоту до открытия приказа.
Перемещённые юниты (культист, элдар) возвращаются на место.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class DominateResult:
    """Результат выполнения приказа Dominate."""
    income_gained: int = 0           # получено ценных ресурсов (joker)
    planets_dominated: int = 0       # планет с доходом
    ability_used: bool = False       # была ли использована особая способность
    skipped: bool = False            # в стек событий


def calc_dominate_income(game_state, player_idx: int, tile_key: str) -> int:
    """
    Подсчитывает доход с планет активной системы.

    Для каждой планетарной области в тайле:
    - Если есть войска или постройки игрока → прибавить area.income.
    """
    tile = game_state.map.get(tile_key)
    if not tile:
        return 0
    total = 0
    for area in tile.areas:
        if area.type != 'planet':
            continue
        has_presence = (
            any(u.player == player_idx for u in area.troops) or
            any(s.player == player_idx for s in getattr(area, 'structures', []))
        )
        if has_presence:
            total += getattr(area, 'income', 1)
    return total


def marine_can_upgrade(game_state, player_idx: int, tile_key: str) -> bool:
    """
    Проверяет, может ли Space Marine использовать способность доминации.
    Нужен: T0 или T1 юнит в системе + 1₡.
    """
    p = game_state.players[player_idx]
    tile = game_state.map.get(tile_key)
    if not tile or p.credits < 1:
        return False
    return any(
        u.player == player_idx and u.tier in (0, 1)
        for area in tile.areas
        for u in area.troops
    )


def marine_upgrade_unit(game_state, player_idx: int, tile_key: str,
                        area_idx: int) -> Optional[str]:
    """
    Выполняет улучшение юнита Space Marine (T0→T1 или T1→T2).
    Стоимость: 1₡.
    Возвращает строку с описанием улучшения или None при ошибке.
    """
    p = game_state.players[player_idx]
    tile = game_state.map.get(tile_key)
    if not tile or p.credits < 1:
        return None
    area = tile.areas[area_idx]
    unit = next(
        (u for u in area.troops if u.player == player_idx and u.tier in (0, 1)),
        None
    )
    if not unit:
        return None
    old_tier = unit.tier
    unit.tier += 1
    p.credits -= 1
    return f"T{old_tier} → T{unit.tier} (−1₡)"


def chaos_move_cultist(game_state, player_idx: int,
                       from_key: str, from_area_idx: int,
                       to_key: str, to_area_idx: int) -> bool:
    """
    Перемещает культиста (T0 наземный) из активной системы
    на планету соседней системы (без врагов).
    """
    from_tile = game_state.map.get(from_key)
    to_tile = game_state.map.get(to_key)
    if not from_tile or not to_tile:
        return False

    from_area = from_tile.areas[from_area_idx]
    cultist = next(
        (u for u in from_area.troops
         if u.player == player_idx and u.unit_type == 'ground' and u.tier == 0),
        None
    )
    if not cultist:
        return False

    to_area = to_tile.areas[to_area_idx]
    if to_area.type != 'planet':
        return False
    has_enemy = (
        any(u.player != player_idx for u in to_area.troops) or
        any(s.player != player_idx for s in getattr(to_area, 'structures', []))
    )
    if has_enemy:
        return False

    from_area.troops.remove(cultist)
    to_area.troops.append(cultist)
    return True


def eldar_teleport_unit(game_state, player_idx: int,
                        from_key: str, from_area_idx: int,
                        to_key: str, to_area_idx: int) -> bool:
    """
    Перемещает любого юнита элдаров из активной системы
    на дружественную планету (в любой системе).
    """
    from_tile = game_state.map.get(from_key)
    to_tile = game_state.map.get(to_key)
    if not from_tile or not to_tile:
        return False

    from_area = from_tile.areas[from_area_idx]
    unit = next(
        (u for u in from_area.troops if u.player == player_idx),
        None
    )
    if not unit:
        return False

    to_area = to_tile.areas[to_area_idx]
    if to_area.type != 'planet':
        return False
    is_friendly = (
        any(u.player == player_idx for u in to_area.troops) or
        any(s.player == player_idx for s in getattr(to_area, 'structures', []))
    )
    if not is_friendly:
        return False

    from_area.troops.remove(unit)
    to_area.troops.append(unit)
    return True
