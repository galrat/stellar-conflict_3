"""
python_engine/advance.py — логика приказа Advance

Механика:
  1. Игрок выбирает соседнюю систему (источник) или пропускает
  2. Перемещает корабли из источника + активной системы в области космоса активной системы
  3. Перемещает наземные юниты из источника + активной системы на планеты активной системы
     - Доступность планеты: смежные дружественные планеты ИЛИ путь через космос с дружественными кораблями
  4. Проверка: не более одной спорной области (где оба игрока имеют юнитов)
  5. Бой: если ровно одна спорная область — каждый юнит кидает 1d6, сумма, проигравший теряет всех
  6. Орбитальный удар (опционально, если не было боя): игрок с кораблем может убрать 1 вражеского юнита с планеты
"""
import copy
import random
from typing import Optional


def get_adjacent_tile_keys(tile_key: str) -> list[str]:
    """Вернуть соседние тайлы (N/S/E/W) по координатной сетке."""
    parts = tile_key.split(',')
    if len(parts) != 2:
        return []
    try:
        col, row = int(parts[0]), int(parts[1])
    except ValueError:
        return []
    return [
        f'{col},{row-1}',  # N
        f'{col},{row+1}',  # S
        f'{col-1},{row}',  # W
        f'{col+1},{row}',  # E
    ]


def get_adjacent_tiles_with_units(state, tile_key, player_id) -> list[str]:
    """Вернуть соседние тайлы где у игрока есть хотя бы один юнит."""
    adjacent = get_adjacent_tile_keys(tile_key)
    result = []
    for tk in adjacent:
        tile = state.get('map', {}).get(tk)
        if not tile:
            continue
        has_unit = False
        for area in tile.get('areas', []):
            for troop in area.get('troops', []):
                if troop.get('player') == player_id:
                    has_unit = True
                    break
            if has_unit:
                break
        if has_unit:
            result.append(tk)
    return result


def get_available_units(state, player_id, source_tile_key, active_tile_key) -> dict:
    """
    Собрать доступные для перемещения юниты из source_tile и active_tile.

    Returns:
        {
            'ships': [{area_idx, unit, origin}],
            'ground_units': [{area_idx, unit, origin}]
        }

    origin: 'source' | 'active'
    """
    ships = []
    ground_units = []

    # Из активного тайла
    active_tile = state.get('map', {}).get(active_tile_key)
    if active_tile:
        for area_idx, area in enumerate(active_tile.get('areas', [])):
            for troop in area.get('troops', []):
                if troop.get('player') == player_id:
                    if troop.get('unitType') == 'space':
                        ships.append({
                            'area_idx': area_idx,
                            'unit': copy.deepcopy(troop),
                            'origin': 'active',
                        })
                    elif troop.get('unitType') == 'ground':
                        ground_units.append({
                            'area_idx': area_idx,
                            'unit': copy.deepcopy(troop),
                            'origin': 'active',
                        })

    # Из source тайла (если выбран)
    if source_tile_key:
        source_tile = state.get('map', {}).get(source_tile_key)
        if source_tile:
            for area_idx, area in enumerate(source_tile.get('areas', [])):
                for troop in area.get('troops', []):
                    if troop.get('player') == player_id:
                        if troop.get('unitType') == 'space':
                            ships.append({
                                'area_idx': area_idx,
                                'unit': copy.deepcopy(troop),
                                'origin': 'source',
                            })
                        elif troop.get('unitType') == 'ground':
                            ground_units.append({
                                'area_idx': area_idx,
                                'unit': copy.deepcopy(troop),
                                'origin': 'source',
                            })

    return {
        'ships': ships,
        'ground_units': ground_units,
    }


def init_virtual_areas(state, active_tile_key) -> dict:
    """
    Создать виртуальную копию областей активного тайла для валидации.

    Returns:
        {area_idx: {troops: [...], type: str, capacity: int}}
    """
    active_tile = state.get('map', {}).get(active_tile_key)
    if not active_tile:
        return {}

    virtual = {}
    for idx, area in enumerate(active_tile.get('areas', [])):
        virtual[idx] = {
            'troops': copy.deepcopy(area.get('troops', [])),
            'type': area.get('type', 'space'),
            'capacity': area.get('capacity', 99),
        }
    return virtual


def count_contested_areas(virtual_areas, player_id) -> int:
    """Подсчитать количество областей где есть юниты обоих игроков."""
    opponent = 1 - player_id
    count = 0
    for area in virtual_areas.values():
        has_player = any(t.get('player') == player_id for t in area['troops'])
        has_opponent = any(t.get('player') == opponent for t in area['troops'])
        if has_player and has_opponent:
            count += 1
    return count


def validate_no_second_contest(virtual_areas, player_id, from_area_idx, to_area_idx, unit) -> tuple[bool, str]:
    """
    Проверить что перемещение не создаст вторую спорную область.

    Returns:
        (True, '') если OK
        (False, error_msg) если будет вторая спорная область
    """
    # Создать копию виртуальных областей
    test_virtual = copy.deepcopy(virtual_areas)

    # Применить перемещение
    # Убрать юнита из from_area (если from_area_idx валиден)
    if from_area_idx is not None and from_area_idx in test_virtual:
        troops = test_virtual[from_area_idx]['troops']
        for i, t in enumerate(troops):
            if (t.get('player') == player_id and
                t.get('unitType') == unit.get('unitType') and
                t.get('tier') == unit.get('tier')):
                troops.pop(i)
                break

    # Добавить юнита в to_area
    if to_area_idx in test_virtual:
        test_virtual[to_area_idx]['troops'].append(copy.deepcopy(unit))

    # Подсчитать спорные области
    contested = count_contested_areas(test_virtual, player_id)

    if contested > 1:
        return False, "Нельзя создать вторую спорную область"

    return True, ""


def is_ground_reachable(virtual_areas, active_tile, from_area_idx, to_area_idx, player_id, origin) -> bool:
    """
    Проверить доступность планеты для наземного юнита.

    origin='source': из source тайла — все планеты активного тайла считаются точками входа
    origin='active': из области в активном тайле — BFS по смежным планетам и через космос с кораблями
    """
    if origin == 'source':
        # Упрощение: из source тайла можно попасть на любую планету активного тайла
        return virtual_areas.get(to_area_idx, {}).get('type') == 'planet'

    # origin == 'active': проверка через BFS
    if from_area_idx == to_area_idx:
        return True  # перемещение в ту же область (нет смысла, но технически валидно)

    # BFS: найти путь от from_area_idx до to_area_idx
    # Путь может быть через:
    # 1. Смежные планеты (если обе планеты и нет вражеских юнитов)
    # 2. Через космос с дружественным кораблем

    areas_list = active_tile.get('areas', [])
    visited = set()
    queue = [from_area_idx]
    visited.add(from_area_idx)

    opponent = 1 - player_id

    while queue:
        current_idx = queue.pop(0)

        if current_idx == to_area_idx:
            return True

        current_area_def = areas_list[current_idx] if current_idx < len(areas_list) else {}

        # Собрать соседние области
        neighbors = current_area_def.get('neighbors', [])

        for neighbor_idx in neighbors:
            if neighbor_idx in visited or neighbor_idx >= len(areas_list):
                continue

            neighbor_area_def = areas_list[neighbor_idx]
            neighbor_virtual = virtual_areas.get(neighbor_idx, {})
            neighbor_type = neighbor_virtual.get('type', neighbor_area_def.get('type', 'space'))

            # Проверка: нельзя пройти через область с вражескими юнитами
            has_enemy = any(t.get('player') == opponent for t in neighbor_virtual.get('troops', []))

            if neighbor_type == 'planet':
                # Можно пройти если нет врага (можно остановиться на спорной планете, но не пройти через неё)
                if not has_enemy or neighbor_idx == to_area_idx:
                    visited.add(neighbor_idx)
                    queue.append(neighbor_idx)

            elif neighbor_type == 'space':
                # Можно пройти через космос если там есть дружественный корабль
                has_friendly_ship = any(
                    t.get('player') == player_id and t.get('unitType') == 'space'
                    for t in neighbor_virtual.get('troops', [])
                )
                if has_friendly_ship:
                    visited.add(neighbor_idx)
                    queue.append(neighbor_idx)

    return False


def apply_committed_moves(state, pending_advance):
    """Применить все зафиксированные перемещения к реальному state."""
    tile_key = pending_advance['tile_key']
    source_tile_key = pending_advance.get('source_tile')
    committed_moves = pending_advance.get('committed_moves', [])

    active_tile = state['map'][tile_key]
    source_tile = state['map'].get(source_tile_key) if source_tile_key else None

    for move in committed_moves:
        origin = move['origin']
        from_area_idx = move.get('from_area_idx')
        to_area_idx = move['to_area_idx']
        unit = move['unit']

        # Убрать юнита из источника
        if origin == 'source' and source_tile and from_area_idx is not None:
            troops = source_tile['areas'][from_area_idx]['troops']
            for i, t in enumerate(troops):
                if (t.get('player') == unit.get('player') and
                    t.get('unitType') == unit.get('unitType') and
                    t.get('tier') == unit.get('tier')):
                    troops.pop(i)
                    break

        elif origin == 'active' and from_area_idx is not None:
            troops = active_tile['areas'][from_area_idx]['troops']
            for i, t in enumerate(troops):
                if (t.get('player') == unit.get('player') and
                    t.get('unitType') == unit.get('unitType') and
                    t.get('tier') == unit.get('tier')):
                    troops.pop(i)
                    break

        # Добавить юнита в целевую область (всегда в active_tile)
        active_tile['areas'][to_area_idx]['troops'].append(copy.deepcopy(unit))


def find_contested_area(state, active_tile_key, player_id) -> Optional[int]:
    """Найти единственную спорную область (или None)."""
    active_tile = state['map'].get(active_tile_key)
    if not active_tile:
        return None

    opponent = 1 - player_id
    contested_idx = None

    for idx, area in enumerate(active_tile.get('areas', [])):
        has_player = any(t.get('player') == player_id for t in area.get('troops', []))
        has_opponent = any(t.get('player') == opponent for t in area.get('troops', []))

        if has_player and has_opponent:
            if contested_idx is not None:
                # Больше одной спорной области — не должно быть
                return None
            contested_idx = idx

    return contested_idx


def roll_combat(state, active_tile_key, area_idx, player_id):
    """
    Провести бой в указанной области.

    Каждый юнит кидает 1d6 (1-6).
    Суммы сравниваются. Проигравший теряет всех юнитов.
    При ничье — оба теряют всех юнитов.

    Returns:
        {
            'winner': int | None,
            'rolls': {player_id: [int], opponent_id: [int]},
            'totals': {player_id: int, opponent_id: int},
            'log': str
        }
    """
    active_tile = state['map'][active_tile_key]
    area = active_tile['areas'][area_idx]

    opponent = 1 - player_id

    # Собрать юнитов
    player_units = [t for t in area['troops'] if t.get('player') == player_id]
    opponent_units = [t for t in area['troops'] if t.get('player') == opponent]

    # Бросить кубики
    player_rolls = [random.randint(1, 6) for _ in player_units]
    opponent_rolls = [random.randint(1, 6) for _ in opponent_units]

    player_total = sum(player_rolls)
    opponent_total = sum(opponent_rolls)

    # Определить победителя
    if player_total > opponent_total:
        winner = player_id
        loser = opponent
    elif opponent_total > player_total:
        winner = opponent
        loser = player_id
    else:
        winner = None
        loser = None

    # Убрать юнитов проигравшего (или обоих при ничье)
    remaining_troops = []
    removed = []

    for troop in area['troops']:
        if winner is None:
            # Ничья — все теряют
            removed.append(troop)
        elif troop.get('player') == loser:
            removed.append(troop)
        else:
            remaining_troops.append(troop)

    area['troops'] = remaining_troops

    # Вернуть убитых юнитов в пул
    for troop in removed:
        p_id = troop.get('player')
        if p_id is not None and p_id < len(state['players']):
            state['players'][p_id].setdefault('pool', []).append(troop)

    # Сформировать лог
    if winner is None:
        result_str = f"Ничья ({player_total} vs {opponent_total}). Обе стороны теряют всех юнитов."
    else:
        result_str = f"Игрок {winner} победил ({player_total if winner == player_id else opponent_total} vs {opponent_total if winner == player_id else player_total}). Игрок {loser} теряет всех юнитов."

    log_msg = f"БОЙ в области {area_idx} тайла {active_tile_key}: {result_str}"

    return {
        'winner': winner,
        'rolls': {player_id: player_rolls, opponent: opponent_rolls},
        'totals': {player_id: player_total, opponent: opponent_total},
        'log': log_msg,
    }


# =========================================================================
# PUBLIC API — вызываемые из game_server.py
# =========================================================================

def advance_play(state, player_id, tile_key) -> dict:
    """
    Инициализировать pending_advance при розыгрыше приказа Advance.

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)

    # Найти соседние тайлы с юнитами игрока
    adjacent_tiles = get_adjacent_tiles_with_units(new_state, tile_key, player_id)

    new_state['pending_advance'] = {
        'player_id': player_id,
        'tile_key': tile_key,
        'source_tile': None,
        'step': 'choose_source',
        'available_ships': [],
        'available_ground_units': [],
        'committed_moves': [],
        'virtual_active_areas': {},
        'adjacent_tiles': adjacent_tiles,
        'contest_area_idx': None,
        'orbital_ship_area': None,
        'orbital_target_area': None,
    }

    return new_state


def advance_choose_source(state, player_id, source_tile_key) -> dict:
    """
    Выбрать source тайл (или None чтобы пропустить).

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'choose_source':
        raise ValueError(f"Выбор source доступен только на шаге choose_source (текущий: {pa['step']})")

    # Валидировать source_tile_key
    if source_tile_key:
        adjacent = pa.get('adjacent_tiles', [])
        if source_tile_key not in adjacent:
            raise ValueError(f"Тайл {source_tile_key} не является соседним или не содержит ваших юнитов")

    pa['source_tile'] = source_tile_key

    # Получить доступные юниты
    tile_key = pa['tile_key']
    units = get_available_units(new_state, player_id, source_tile_key, tile_key)

    pa['available_ships'] = units['ships']
    pa['available_ground_units'] = units['ground_units']

    # Инициализировать виртуальные области
    pa['virtual_active_areas'] = init_virtual_areas(new_state, tile_key)

    # Переход к шагу перемещения кораблей
    pa['step'] = 'ships'

    return new_state


def advance_move_ship(state, player_id, from_area_idx, to_area_idx) -> dict:
    """
    Переместить корабль из from_area_idx в to_area_idx (оба в активном тайле или from source).

    Параметры:
        from_area_idx: индекс области откуда перемещать (может быть из source или active)
        to_area_idx: индекс области куда перемещать (всегда в active)

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'ships':
        raise ValueError(f"Перемещение кораблей доступно только на шаге ships (текущий: {pa['step']})")

    tile_key = pa['tile_key']
    source_tile_key = pa.get('source_tile')

    # Найти корабль в доступных
    ship = None
    origin = None
    for s in pa['available_ships']:
        if s['area_idx'] == from_area_idx:
            ship = s['unit']
            origin = s['origin']
            break

    if not ship:
        raise ValueError(f"Нет доступного корабля в области {from_area_idx}")

    # Проверить что целевая область — космос
    virtual_areas = pa['virtual_active_areas']
    if to_area_idx not in virtual_areas:
        raise ValueError(f"Область {to_area_idx} не существует")

    if virtual_areas[to_area_idx]['type'] != 'space':
        raise ValueError(f"Корабли могут перемещаться только в космос (область {to_area_idx} — {virtual_areas[to_area_idx]['type']})")

    # Проверить что не создается вторая спорная область
    valid, error = validate_no_second_contest(
        virtual_areas, player_id,
        from_area_idx if origin == 'active' else None,
        to_area_idx, ship
    )

    if not valid:
        raise ValueError(error)

    # Зафиксировать перемещение
    move = {
        'origin': origin,
        'from_area_idx': from_area_idx,
        'to_area_idx': to_area_idx,
        'unit': copy.deepcopy(ship),
    }
    pa['committed_moves'].append(move)

    # Обновить виртуальные области
    # Убрать из from (если origin=active)
    if origin == 'active' and from_area_idx in virtual_areas:
        troops = virtual_areas[from_area_idx]['troops']
        for i, t in enumerate(troops):
            if (t.get('player') == player_id and
                t.get('unitType') == ship.get('unitType') and
                t.get('tier') == ship.get('tier')):
                troops.pop(i)
                break

    # Добавить в to
    virtual_areas[to_area_idx]['troops'].append(copy.deepcopy(ship))

    # Убрать корабль из доступных
    pa['available_ships'] = [s for s in pa['available_ships']
                              if not (s['area_idx'] == from_area_idx and s['origin'] == origin)]

    return new_state


def advance_move_ground(state, player_id, from_area_idx, to_area_idx) -> dict:
    """
    Переместить наземного юнита из from_area_idx на планету to_area_idx.

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'ground':
        raise ValueError(f"Перемещение наземных юнитов доступно только на шаге ground (текущий: {pa['step']})")

    tile_key = pa['tile_key']

    # Найти юнита в доступных
    unit = None
    origin = None
    for g in pa['available_ground_units']:
        if g['area_idx'] == from_area_idx:
            unit = g['unit']
            origin = g['origin']
            break

    if not unit:
        raise ValueError(f"Нет доступного наземного юнита в области {from_area_idx}")

    # Проверить что целевая область — планета
    virtual_areas = pa['virtual_active_areas']
    if to_area_idx not in virtual_areas:
        raise ValueError(f"Область {to_area_idx} не существует")

    if virtual_areas[to_area_idx]['type'] != 'planet':
        raise ValueError(f"Наземные юниты могут перемещаться только на планеты (область {to_area_idx} — {virtual_areas[to_area_idx]['type']})")

    # Проверить доступность планеты
    active_tile = new_state['map'][tile_key]
    reachable = is_ground_reachable(
        virtual_areas, active_tile,
        from_area_idx, to_area_idx, player_id, origin
    )

    if not reachable:
        raise ValueError(f"Планета {to_area_idx} недоступна из области {from_area_idx}")

    # Проверить что не создается вторая спорная область
    valid, error = validate_no_second_contest(
        virtual_areas, player_id,
        from_area_idx if origin == 'active' else None,
        to_area_idx, unit
    )

    if not valid:
        raise ValueError(error)

    # Зафиксировать перемещение
    move = {
        'origin': origin,
        'from_area_idx': from_area_idx,
        'to_area_idx': to_area_idx,
        'unit': copy.deepcopy(unit),
    }
    pa['committed_moves'].append(move)

    # Обновить виртуальные области
    if origin == 'active' and from_area_idx in virtual_areas:
        troops = virtual_areas[from_area_idx]['troops']
        for i, t in enumerate(troops):
            if (t.get('player') == player_id and
                t.get('unitType') == unit.get('unitType') and
                t.get('tier') == unit.get('tier')):
                troops.pop(i)
                break

    virtual_areas[to_area_idx]['troops'].append(copy.deepcopy(unit))

    # Убрать юнита из доступных
    pa['available_ground_units'] = [g for g in pa['available_ground_units']
                                     if not (g['area_idx'] == from_area_idx and g['origin'] == origin)]

    return new_state




def advance_commit(state, player_id) -> dict:
    """
    Зафиксировать все перемещения и перейти к бою или орбитальному удару.

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] not in ('ships', 'ground'):
        raise ValueError(f"Фиксация доступна только на шагах ships/ground (текущий: {pa['step']})")

    # Применить перемещения к реальному state
    apply_committed_moves(new_state, pa)

    # Найти спорную область
    tile_key = pa['tile_key']
    contested_idx = find_contested_area(new_state, tile_key, player_id)

    if contested_idx is not None:
        # Есть спорная область — перейти к бою
        pa['contest_area_idx'] = contested_idx
        pa['step'] = 'combat'
    else:
        # Нет боя — проверить возможность орбитального удара
        # Орбитальный удар доступен если у игрока есть корабль в active_tile
        active_tile = new_state['map'][tile_key]
        has_ship = False
        for area in active_tile.get('areas', []):
            if area.get('type') == 'space':
                if any(t.get('player') == player_id and t.get('unitType') == 'space'
                       for t in area.get('troops', [])):
                    has_ship = True
                    break

        if has_ship:
            pa['step'] = 'orbital'
        else:
            # Нет кораблей — завершить
            finalize_advance(new_state, player_id)

    return new_state


def advance_fight(state, player_id) -> dict:
    """
    Провести бой в спорной области.

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'combat':
        raise ValueError(f"Бой доступен только на шаге combat (текущий: {pa['step']})")

    tile_key = pa['tile_key']
    area_idx = pa.get('contest_area_idx')

    if area_idx is None:
        raise ValueError("Нет спорной области для боя")

    # Провести бой
    result = roll_combat(new_state, tile_key, area_idx, player_id)

    # Добавить в лог
    new_state.setdefault('log', []).append({
        'message': result['log'],
        'player_id': player_id
    })

    # После боя проверить возможность орбитального удара
    active_tile = new_state['map'][tile_key]
    has_ship = False
    for area in active_tile.get('areas', []):
        if area.get('type') == 'space':
            if any(t.get('player') == player_id and t.get('unitType') == 'space'
                   for t in area.get('troops', [])):
                has_ship = True
                break

    if has_ship:
        pa['step'] = 'orbital'
    else:
        # Завершить
        finalize_advance(new_state, player_id)

    return new_state


def advance_orbital(state, player_id, ship_area_idx, target_area_idx) -> dict:
    """
    Игрок выбирает корабль и целевую планету для орбитального удара.

    Returns: обновленный state (переход к orbital_defend)
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'orbital':
        raise ValueError(f"Орбитальный удар доступен только на шаге orbital (текущий: {pa['step']})")

    tile_key = pa['tile_key']
    active_tile = new_state['map'][tile_key]

    # Проверить что ship_area — космос с кораблем игрока
    if ship_area_idx >= len(active_tile['areas']):
        raise ValueError(f"Область {ship_area_idx} не существует")

    ship_area = active_tile['areas'][ship_area_idx]
    if ship_area.get('type') != 'space':
        raise ValueError(f"Область {ship_area_idx} не является космосом")

    has_ship = any(t.get('player') == player_id and t.get('unitType') == 'space'
                   for t in ship_area.get('troops', []))

    if not has_ship:
        raise ValueError(f"У вас нет корабля в области {ship_area_idx}")

    # Проверить что target_area — планета с вражескими юнитами
    if target_area_idx >= len(active_tile['areas']):
        raise ValueError(f"Область {target_area_idx} не существует")

    target_area = active_tile['areas'][target_area_idx]
    if target_area.get('type') != 'planet':
        raise ValueError(f"Область {target_area_idx} не является планетой")

    opponent = 1 - player_id
    enemy_units = [t for t in target_area.get('troops', []) if t.get('player') == opponent]

    if not enemy_units:
        raise ValueError(f"На планете {target_area_idx} нет вражеских юнитов")

    # Сохранить выбор и перейти к шагу защиты
    pa['orbital_ship_area'] = ship_area_idx
    pa['orbital_target_area'] = target_area_idx
    pa['step'] = 'orbital_defend'

    return new_state


def advance_orbital_remove(state, defender_player_id, area_idx, unit_idx) -> dict:
    """
    Защищающийся игрок убирает один юнит с планеты после орбитального удара.

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa:
        raise ValueError("Нет активного приказа Advance")

    if pa['step'] != 'orbital_defend':
        raise ValueError(f"Удаление юнита доступно только на шаге orbital_defend (текущий: {pa['step']})")

    attacker = pa['player_id']

    if defender_player_id != (1 - attacker):
        raise ValueError("Это не ваша очередь удалять юнита")

    tile_key = pa['tile_key']
    target_area_idx = pa.get('orbital_target_area')

    if area_idx != target_area_idx:
        raise ValueError(f"Юнит должен быть удален из области {target_area_idx}")

    active_tile = new_state['map'][tile_key]
    target_area = active_tile['areas'][target_area_idx]

    # Найти и убрать юнита
    troops = target_area['troops']
    defender_units = [i for i, t in enumerate(troops) if t.get('player') == defender_player_id]

    if unit_idx not in defender_units:
        raise ValueError(f"Юнит {unit_idx} не принадлежит защищающемуся игроку")

    removed_unit = troops.pop(unit_idx)

    # Вернуть в пул
    new_state['players'][defender_player_id].setdefault('pool', []).append(removed_unit)

    # Добавить в лог
    new_state.setdefault('log', []).append({
        'message': f"Орбитальный удар: игрок {defender_player_id} потерял юнита на планете {target_area_idx}",
        'player_id': attacker
    })

    # Завершить
    finalize_advance(new_state, attacker)

    return new_state


def advance_skip_orbital(state, player_id) -> dict:
    """
    Пропустить орбитальный удар.

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'orbital':
        raise ValueError(f"Пропуск орбитального удара доступен только на шаге orbital (текущий: {pa['step']})")

    finalize_advance(new_state, player_id)

    return new_state


def advance_next_step(state, player_id) -> dict:
    """
    Перейти от ships к ground.

    Returns: обновленный state
    """
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] == 'ships':
        pa['step'] = 'ground'
    else:
        raise ValueError(f"Переход доступен только с шага ships (текущий: {pa['step']})")

    return new_state


def finalize_advance(state, player_id):
    """Очистить pending_advance и отметить что приказ разыгран."""
    if 'pending_advance' in state:
        del state['pending_advance']
    state['execution_order_played'][player_id] = True
