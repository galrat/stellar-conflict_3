import copy
import uuid
from .discovery import (
    get_adjacent_tiles_with_units, get_available_units,
    init_virtual_areas, get_available_space_areas,
    validate_no_second_contest, get_reachable_planets_for_unit,
)
from .capacity import _resolve_post_moves


def apply_committed_moves(state, pending_advance):
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
        unit_uid = unit.get('_uid')

        if origin == 'source' and source_tile and from_area_idx is not None:
            troops = source_tile['areas'][from_area_idx]['troops']
            for i, t in enumerate(troops):
                if unit_uid and t.get('_uid') == unit_uid:
                    troops.pop(i)
                    break
                elif (t.get('player') == unit.get('player') and
                      t.get('unitType') == unit.get('unitType') and
                      t.get('tier') == unit.get('tier')):
                    troops.pop(i)
                    break

        elif origin == 'active' and from_area_idx is not None:
            troops = active_tile['areas'][from_area_idx]['troops']
            for i, t in enumerate(troops):
                if unit_uid and t.get('_uid') == unit_uid:
                    troops.pop(i)
                    break
                elif (t.get('player') == unit.get('player') and
                      t.get('unitType') == unit.get('unitType') and
                      t.get('tier') == unit.get('tier')):
                    troops.pop(i)
                    break

        unit_copy = copy.deepcopy(unit)
        active_tile['areas'][to_area_idx]['troops'].append(unit_copy)


def advance_play(state, player_id, tile_key) -> dict:
    new_state = copy.deepcopy(state)
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
        'instruction': 'Выберите соседнюю систему для подкрепления или пропустите' if adjacent_tiles else 'Нет соседних систем с вашими юнитами',
    }

    return new_state


def advance_choose_source(state, player_id, source_tile_key) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'choose_source':
        raise ValueError(f"Выбор source доступен только на шаге choose_source (текущий: {pa['step']})")

    if source_tile_key:
        adjacent = pa.get('adjacent_tiles', [])
        if source_tile_key not in adjacent:
            raise ValueError(f"Тайл {source_tile_key} не является соседним или не содержит ваших юнитов")

    pa['source_tile'] = source_tile_key

    tile_key = pa['tile_key']
    units = get_available_units(new_state, player_id, source_tile_key, tile_key)

    pa['available_ships'] = units['ships']
    pa['available_ground_units'] = units['ground_units']
    pa['virtual_active_areas'] = init_virtual_areas(new_state, tile_key)

    if source_tile_key:
        source_tile = new_state['map'][source_tile_key]
        for area in source_tile.get('areas', []):
            for troop in area.get('troops', []):
                if (troop.get('player') == player_id and
                        troop.get('unitType') in ('space', 'ground') and
                        troop.get('unit_status') != 'routed'):
                    if '_uid' not in troop:
                        troop['_uid'] = str(uuid.uuid4())
                    troop['ready_to_move'] = 1

    active_tile = new_state['map'][tile_key]
    for area in active_tile.get('areas', []):
        for troop in area.get('troops', []):
            if (troop.get('player') == player_id and
                    troop.get('unitType') in ('space', 'ground') and
                    troop.get('unit_status') != 'routed'):
                if '_uid' not in troop:
                    troop['_uid'] = str(uuid.uuid4())
                troop['ready_to_move'] = 1

    clickable_space_areas = get_available_space_areas(active_tile, player_id)
    pa['clickable_space_areas'] = clickable_space_areas
    pa['step'] = 'ships'
    pa['instruction'] = f'Переместите корабли в области космоса системы {tile_key}. Нажмите "Далее" для наземных юнитов.'

    return new_state


def advance_move_ship(state, player_id, ship_id, to_area_idx) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'ships':
        raise ValueError(f"Перемещение кораблей доступно только на шаге ships (текущий: {pa['step']})")

    tile_key = pa['tile_key']
    source_tile_key = pa.get('source_tile')

    ship = None
    origin = None
    from_area_idx = None
    for s in pa['available_ships']:
        if s.get('ship_id') == ship_id:
            ship = s['unit']
            origin = s['origin']
            from_area_idx = s['area_idx']
            break

    if not ship:
        raise ValueError(f"Нет доступного корабля с ID {ship_id}")

    clickable = pa.get('clickable_space_areas', [])
    if to_area_idx not in clickable:
        raise ValueError(f"Область {to_area_idx} недоступна для кораблей")

    virtual_areas = pa['virtual_active_areas']
    if to_area_idx not in virtual_areas:
        raise ValueError(f"Область {to_area_idx} не существует")

    if virtual_areas[to_area_idx]['type'] != 'space':
        raise ValueError(f"Корабли могут перемещаться только в космос (область {to_area_idx} — {virtual_areas[to_area_idx]['type']})")

    valid, error = validate_no_second_contest(
        virtual_areas, player_id,
        from_area_idx if origin == 'active' else None,
        to_area_idx, ship
    )
    if not valid:
        raise ValueError(error)

    move = {'origin': origin, 'from_area_idx': from_area_idx, 'to_area_idx': to_area_idx, 'unit': copy.deepcopy(ship)}
    pa['committed_moves'].append(move)

    if origin == 'active' and from_area_idx in virtual_areas:
        troops = virtual_areas[from_area_idx]['troops']
        for i, t in enumerate(troops):
            if (t.get('player') == player_id and
                    t.get('unitType') == ship.get('unitType') and
                    t.get('tier') == ship.get('tier')):
                troops.pop(i)
                break

    virtual_areas[to_area_idx]['troops'].append(copy.deepcopy(ship))
    pa['available_ships'] = [s for s in pa['available_ships'] if s.get('ship_id') != ship_id]

    ship_uid = ship.get('_uid')
    if origin == 'source' and source_tile_key:
        source_tile = new_state['map'][source_tile_key]
        troops = source_tile['areas'][from_area_idx]['troops']
        for troop in troops:
            if troop.get('_uid') == ship_uid:
                troop['ready_to_move'] = 0
                break
    elif origin == 'active':
        active_tile = new_state['map'][tile_key]
        troops = active_tile['areas'][from_area_idx]['troops']
        for troop in troops:
            if troop.get('_uid') == ship_uid:
                troop['ready_to_move'] = 0
                break

    return new_state


def advance_move_ground(state, player_id, ground_id, to_area_idx) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'ground':
        raise ValueError(f"Перемещение наземных юнитов доступно только на шаге ground (текущий: {pa['step']})")

    tile_key = pa['tile_key']
    source_tile_key = pa.get('source_tile')

    unit = None
    origin = None
    from_area_idx = None
    for g in pa['available_ground_units']:
        if g.get('ground_id') == ground_id:
            unit = g['unit']
            origin = g['origin']
            from_area_idx = g['area_idx']
            break

    if not unit:
        raise ValueError(f"Нет доступного наземного юнита с ID {ground_id}")

    reachable_by_id = pa.get('reachable_planets_by_id', {})
    reachable = reachable_by_id.get(ground_id, [])
    if to_area_idx not in reachable:
        raise ValueError(f"Планета {to_area_idx} недоступна для юнита {ground_id}")

    virtual_areas = pa['virtual_active_areas']
    valid, error = validate_no_second_contest(
        virtual_areas, player_id,
        from_area_idx if origin == 'active' else None,
        to_area_idx, unit
    )
    if not valid:
        raise ValueError(error)

    move = {'origin': origin, 'from_area_idx': from_area_idx, 'to_area_idx': to_area_idx, 'unit': copy.deepcopy(unit)}
    pa['committed_moves'].append(move)

    if origin == 'active' and from_area_idx in virtual_areas:
        troops = virtual_areas[from_area_idx]['troops']
        for i, t in enumerate(troops):
            if (t.get('player') == player_id and
                    t.get('unitType') == unit.get('unitType') and
                    t.get('tier') == unit.get('tier')):
                troops.pop(i)
                break

    virtual_areas[to_area_idx]['troops'].append(copy.deepcopy(unit))
    pa['available_ground_units'] = [g for g in pa['available_ground_units'] if g.get('ground_id') != ground_id]

    unit_uid = unit.get('_uid')
    if origin == 'source' and source_tile_key:
        source_tile = new_state['map'][source_tile_key]
        troops = source_tile['areas'][from_area_idx]['troops']
        for troop in troops:
            if troop.get('_uid') == unit_uid:
                troop['ready_to_move'] = 0
                break
    elif origin == 'active':
        active_tile = new_state['map'][tile_key]
        troops = active_tile['areas'][from_area_idx]['troops']
        for troop in troops:
            if troop.get('_uid') == unit_uid:
                troop['ready_to_move'] = 0
                break

    return new_state


def advance_next_step(state, player_id) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'ships':
        raise ValueError(f"Переход доступен только с шага ships (текущий: {pa['step']})")

    pa['step'] = 'ground'

    tile_key = pa['tile_key']
    active_tile = new_state['map'][tile_key]
    virtual_areas = pa['virtual_active_areas']

    source_tile_key = pa.get('source_tile')
    source_tile = new_state['map'].get(source_tile_key) if source_tile_key else None

    reachable_by_id = {}
    for ground in pa['available_ground_units']:
        gid = ground['ground_id']
        origin = ground['origin']
        from_area_idx = ground['area_idx']
        start_tile_type = 'active' if origin == 'active' else 'source'

        reachable = get_reachable_planets_for_unit(
            tile_key, source_tile_key,
            active_tile, source_tile,
            virtual_areas,
            start_tile_type, from_area_idx,
            player_id,
        )
        reachable_by_id[gid] = reachable

    pa['reachable_planets_by_id'] = reachable_by_id
    pa['instruction'] = 'Переместите наземные юниты на планеты. Нажмите "Готово" для завершения движения.'

    return new_state


def advance_commit(state, player_id) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] not in ('ships', 'ground'):
        raise ValueError(f"Фиксация доступна только на шагах ships/ground (текущий: {pa['step']})")

    apply_committed_moves(new_state, pa)
    pa['committed_moves'] = []
    _resolve_post_moves(new_state, pa, player_id)
    return new_state
