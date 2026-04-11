"""
round_end.py — Логика конца раунда (Stellar Conflict)

Шаги:
  1. collect_objectives  — сбор жетонов целей
  2. collect_income      — сбор дохода с дружественных планет
  3. recover_units       — восстановление войск (routed → active)
  4. prepare_event_draw  — подготовка карт событий для выбора
  5. init_unit_statuses  — инициализация unit_status при старте игры
"""
import random
from typing import Any


def _area_has_player(area: dict, player_id: int) -> bool:
    """Есть ли у игрока войска или постройки в данной области."""
    for troop in area.get('troops', []):
        if troop.get('player') == player_id:
            return True
    for structure in area.get('structures', []):
        if structure.get('player') == player_id:
            return True
    return False


def collect_objectives(state: dict) -> dict:
    """
    Шаг 1: Сбор жетонов целей.

    Игрок забирает objectiveMarker с тайла если:
      - marker.owner == player_id  (это его маркер)
      - areas[realAreaIdx] содержит войска или постройки этого игрока
        (он захватил планету, где стоял его маркер)

    Маркер убирается с тайла, счётчик collected_objectives увеличивается.
    """
    map_data = state.get('map', {})
    players = state.get('players', [])
    log = state.get('log', [])

    for tile_key, tile in map_data.items():
        marker = tile.get('objectiveMarker')
        if not marker:
            continue

        owner = marker.get('owner')
        area_idx = marker.get('realAreaIdx', 0)
        areas = tile.get('areas', [])

        if owner is None or owner >= len(players):
            continue

        if area_idx < len(areas) and _area_has_player(areas[area_idx], owner):
            tile.pop('objectiveMarker', None)
            tile['needsObjective'] = False

            if 'collected_objectives' not in players[owner]:
                players[owner]['collected_objectives'] = 0
            players[owner]['collected_objectives'] += 1

            p_name = players[owner].get('name', f'P{owner}')
            log.append({
                'message': f'{p_name} собрал жетон цели на {tile_key}',
                'player_id': owner
            })

    return state


def collect_income(state: dict) -> dict:
    """
    Шаг 2: Сбор дохода.

    За каждую дружественную планету (есть войска или постройки игрока)
    игрок получает area.income кредитов. Максимум 14.
    """
    map_data = state.get('map', {})
    players = state.get('players', [])
    log = state.get('log', [])

    for pid, player in enumerate(players):
        total_income = 0

        for tile in map_data.values():
            for area in tile.get('areas', []):
                if area.get('type') != 'planet':
                    continue
                if not _area_has_player(area, pid):
                    continue
                total_income += area.get('income', 0)

        old_credits = player.get('credits', 0)
        new_credits = min(14, old_credits + total_income)
        player['credits'] = new_credits

        p_name = player.get('name', f'P{pid}')
        log.append({
            'message': f'{p_name}: доход +{total_income} (итого {new_credits} кредитов)',
            'player_id': pid
        })

    return state


def recover_units(state: dict) -> dict:
    """
    Шаг 3: Восстановление войск.

    Все войска со статусом 'routed' становятся 'active'.
    """
    players = state.get('players', [])
    log = state.get('log', [])
    recovered = [0] * len(players)

    for tile in state.get('map', {}).values():
        for area in tile.get('areas', []):
            for troop in area.get('troops', []):
                if troop.get('unit_status') == 'routed':
                    troop['unit_status'] = 'active'
                    pid = troop.get('player')
                    if pid is not None and pid < len(recovered):
                        recovered[pid] += 1

    for pid, count in enumerate(recovered):
        if count > 0 and pid < len(players):
            p_name = players[pid].get('name', f'P{pid}')
            log.append({
                'message': f'{p_name}: восстановлено {count} войск',
                'player_id': pid
            })

    return state


def prepare_event_draw(state: dict, dropped_counts: list = None) -> dict:
    """
    Шаг 4: Подготовка карт событий для выбора.

    Для каждого игрока случайно выбирается N карт из available_event_cards,
    где N = кол-во сброшенных приказов (минимум 1).
    Карты с возвратом — колода не убывает.

    dropped_counts: [count_p0, count_p1] — посчитано ДО очистки dropped_orders.

    Результат сохраняется в:
      state.event_cards_offered  = [[cards_p0], [cards_p1]]
      state.event_selection_done = [False, False]
    """
    players = state.get('players', [])

    offered = []
    for pid, player in enumerate(players):
        player_dropped = dropped_counts[pid] if (dropped_counts and pid < len(dropped_counts)) else 0
        draw_count = max(1, player_dropped)

        available = player.get('available_event_cards', [])
        if not available:
            offered.append([])
            continue

        cards = random.choices(available, k=draw_count)
        offered.append(cards)

    state['event_cards_offered'] = offered
    state['event_selection_done'] = [False, False]

    return state


def run_end_of_round(state: dict, dropped_counts: list = None) -> dict:
    """
    Запустить все авто-шаги конца раунда (1-4).
    dropped_counts: [count_p0, count_p1] — сколько приказов сбросил каждый игрок.
    Вызывается при переходе в фазу 'end-round'.
    """
    state = collect_objectives(state)
    state = collect_income(state)
    state = recover_units(state)
    state = prepare_event_draw(state, dropped_counts)
    return state


def init_unit_statuses(state: dict) -> dict:
    """
    Инициализация: добавить unit_status='active' всем войскам на карте.
    Вызывается при /api/game/init (после Stage 1).
    """
    for tile in state.get('map', {}).values():
        for area in tile.get('areas', []):
            for troop in area.get('troops', []):
                if 'unit_status' not in troop:
                    troop['unit_status'] = 'active'
    return state
