"""
faction_defs/eldar_data/dominate.py — особое свойство доминации фракции Eldar.

После стандартного Dominate игрок может переместить одного не-routed наземного
юнита из активной системы на любую дружественную планету карты.
"""
import copy


def _collect_movable_units(state, player_id, tile_key):
    tile = state.get('map', {}).get(tile_key)
    if not tile:
        return []
    units = []
    for area_idx, area in enumerate(tile.get('areas', [])):
        for troop_idx, t in enumerate(area.get('troops', [])):
            if (t.get('player') == player_id
                    and t.get('unitType') == 'ground'
                    and t.get('unit_status') != 'routed'):
                units.append({
                    'area_idx':  area_idx,
                    'troop_idx': troop_idx,
                    'unitType':  t.get('unitType'),
                    'tier':      t.get('tier', 0),
                })
    return units


def _collect_valid_targets(state, player_id):
    targets = []
    for tile_key, tile in state.get('map', {}).items():
        for area_idx, area in enumerate(tile.get('areas', [])):
            if area.get('type') != 'planet':
                continue
            has_unit      = any(t.get('player') == player_id for t in area.get('troops', []))
            has_structure = any(s.get('player') == player_id for s in area.get('structures', []))
            if has_unit or has_structure:
                targets.append({'tile_key': tile_key, 'area_idx': area_idx})
    return targets


def maybe_start(state, player_id, tile_key):
    if state['players'][player_id].get('faction', '') != 'eldar':
        return
    movable = _collect_movable_units(state, player_id, tile_key)
    if not movable:
        return
    targets = _collect_valid_targets(state, player_id)
    if not targets:
        return
    state['pending_eldar_dominate'] = {
        'player_id':       player_id,
        'source_tile_key': tile_key,
        'movable_units':   movable,
        'valid_targets':   targets,
    }


def handle_move(state, player_id, src_area_idx, src_troop_idx, target_tile_key, target_area_idx):
    new_state = copy.deepcopy(state)
    pending   = new_state.pop('pending_eldar_dominate', None)
    if not pending or pending.get('player_id') != player_id:
        return False, "Нет ожидающей способности Eldar", None

    source_tile_key = pending['source_tile_key']
    movable_units   = pending.get('movable_units', [])
    valid_targets   = pending.get('valid_targets', [])

    if not any(u['area_idx'] == src_area_idx and u['troop_idx'] == src_troop_idx
               for u in movable_units):
        return False, "Недопустимый юнит для перемещения", None

    if not any(t['tile_key'] == target_tile_key and t['area_idx'] == target_area_idx
               for t in valid_targets):
        return False, "Недопустимая цель для перемещения", None

    src_area = new_state['map'][source_tile_key]['areas'][src_area_idx]
    troops   = src_area.get('troops', [])
    if src_troop_idx < 0 or src_troop_idx >= len(troops):
        return False, "Неверный индекс юнита", None

    troop = troops[src_troop_idx]
    if troop.get('unit_status') == 'routed':
        return False, "Нельзя перемещать routed юнита", None
    troop = troops.pop(src_troop_idx)

    target_area   = new_state['map'][target_tile_key]['areas'][target_area_idx]
    target_troops = target_area.setdefault('troops', [])
    target_troops.append(troop)

    capacity = target_area.get('capacity', 4)
    if len(target_troops) > capacity:
        units_info = [
            {'troop_idx': i, 'unitType': t.get('unitType'), 'player': t.get('player'), 'tier': t.get('tier', 0)}
            for i, t in enumerate(target_troops)
        ]
        new_state['pending_eldar_retreat'] = {
            'player_id': player_id,
            'tile_key':  target_tile_key,
            'area_idx':  target_area_idx,
            'units':     units_info,
            'capacity':  capacity,
        }
        msg = f"Eldar: юнит перемещён в {target_tile_key}/{target_area_idx}, вместимость превышена — выберите юнита для удаления"
    else:
        msg = f"Eldar: юнит перемещён в систему {target_tile_key}, область {target_area_idx}"

    new_state.setdefault('log', []).append({'message': msg, 'player_id': player_id})
    return True, msg, new_state


def handle_retreat(state, player_id, tile_key, area_idx, troop_idx):
    new_state = copy.deepcopy(state)
    pending   = new_state.pop('pending_eldar_retreat', None)
    if not pending or pending.get('player_id') != player_id:
        return False, "Нет ожидающего выбора отступления", None
    if pending.get('tile_key') != tile_key or pending.get('area_idx') != area_idx:
        return False, "Неверная область для отступления", None

    area   = new_state['map'][tile_key]['areas'][area_idx]
    troops = area.get('troops', [])
    if troop_idx < 0 or troop_idx >= len(troops):
        return False, "Неверный индекс юнита", None

    removed = troops.pop(troop_idx)
    msg = f"Eldar: юнит игрока {removed.get('player', '?')} удалён из {tile_key}/{area_idx}"
    new_state.setdefault('log', []).append({'message': msg, 'player_id': player_id})
    return True, msg, new_state
