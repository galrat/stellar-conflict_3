import copy
from .discovery import validate_no_second_contest
from .capacity import _resolve_post_moves
from .convert import _UNROTATE


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

    origin_tile_key = source_tile_key if origin == 'source' else tile_key
    origins = pa.setdefault('ground_origins', [])
    if not any(o['tile_key'] == origin_tile_key and o['area_idx'] == from_area_idx for o in origins):
        origins.append({'tile_key': origin_tile_key, 'area_idx': from_area_idx})

    dest_troops = virtual_areas[to_area_idx]['troops']
    if any(t.get('player') == 0 for t in dest_troops) and any(t.get('player') == 1 for t in dest_troops):
        pa['contest_area_idx'] = to_area_idx

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
