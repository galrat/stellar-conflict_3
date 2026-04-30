import copy
import json
import os
import uuid
from .discovery import (
    get_adjacent_tiles_with_units, get_available_units,
    init_virtual_areas,
    validate_no_second_contest, get_reachable_planets_for_unit,
)
from .convert import state_to_areas, _UNROTATE


def _compute_areas_with_moves(state_map, tile_key, source_tile_key, committed_moves):
    map_copy = copy.deepcopy(state_map)
    active_tile = map_copy.get(tile_key)
    source_tile = map_copy.get(source_tile_key) if source_tile_key else None
    for move in committed_moves:
        origin = move['origin']
        from_area_idx = move.get('from_area_idx')
        to_area_idx = move['to_area_idx']
        unit = copy.deepcopy(move['unit'])
        uid = unit.get('_uid')
        if origin == 'source' and source_tile and from_area_idx is not None:
            troops = source_tile['areas'][from_area_idx]['troops']
            for i, t in enumerate(troops):
                if uid and t.get('_uid') == uid:
                    troops.pop(i)
                    break
        elif origin == 'active' and active_tile and from_area_idx is not None:
            troops = active_tile['areas'][from_area_idx]['troops']
            for i, t in enumerate(troops):
                if uid and t.get('_uid') == uid:
                    troops.pop(i)
                    break
        if active_tile:
            active_tile['areas'][to_area_idx]['troops'].append(unit)
    return state_to_areas({'map': map_copy})


def _save_advance_json(filename, areas):
    os.makedirs('advance', exist_ok=True)
    with open(f'advance/{filename}', 'w', encoding='utf-8') as f:
        json.dump(areas, f, ensure_ascii=False, indent=2)


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
        'moved_from_areas': [],
        'areas_snapshot': [],
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

    col, row = map(int, tile_key.split(','))
    all_areas = state_to_areas(new_state)
    clickable_space_areas = []
    for entry in all_areas:
        e_col, e_row = entry[0]
        area_type = entry[3]
        rotation = entry[6]
        if e_col == col and e_row == row and area_type == 'space':
            area_idx = _UNROTATE.get(rotation, _UNROTATE[0])[tuple(entry[1])]
            clickable_space_areas.append(area_idx)
    pa['areas_snapshot'] = all_areas
    pa['clickable_space_areas'] = clickable_space_areas
    pa['step'] = 'ships'
    pa['instruction'] = f'Переместите корабли в области космоса системы {tile_key}. Нажмите "Далее" для наземных юнитов.'

    _save_advance_json('advance_state_1.json', state_to_areas(new_state))

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

    src_tile_key = source_tile_key if origin == 'source' else tile_key
    if src_tile_key and from_area_idx is not None:
        src_col, src_row = map(int, src_tile_key.split(','))
        for entry in pa.get('areas_snapshot', []):
            e_col, e_row = entry[0]
            rotation = entry[6]
            if e_col == src_col and e_row == src_row:
                entry_area_idx = _UNROTATE.get(rotation, _UNROTATE[0])[tuple(entry[1])]
                if entry_area_idx == from_area_idx:
                    if entry[2] not in [e[2] for e in pa['moved_from_areas']]:
                        pa['moved_from_areas'].append(entry)
                    break

    dest_troops = virtual_areas[to_area_idx]['troops']
    if any(t.get('player') == 0 for t in dest_troops) and any(t.get('player') == 1 for t in dest_troops):
        pa['contest_area_idx'] = to_area_idx

    areas = _compute_areas_with_moves(new_state['map'], tile_key, source_tile_key, pa['committed_moves'])
    _save_advance_json('advance_state_1.json', areas)
    _save_advance_json('advance_state_2.json', areas)

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

    full_areas = _compute_areas_with_moves(new_state['map'], tile_key, source_tile_key, pa['committed_moves'])
    _save_advance_json('advance_state_2.json', full_areas)

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
            full_areas=full_areas,
        )
        reachable_by_id[gid] = reachable

    pa['reachable_planets_by_id'] = reachable_by_id
    pa['ground_origins'] = []
    pa['instruction'] = 'Переместите наземные юниты на планеты. Нажмите "Готово" для завершения движения.'

    return new_state
