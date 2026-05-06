"""
faction_defs/chaos_data/dominate.py — особое свойство доминации фракции Хаос.

После стандартного Dominate игрок может переместить одного не-routed культиста
из активной системы в нейтральную или дружественную планету соседней системы.
"""
import copy


def _collect_movable_cultists(state, player_id, tile_key):
    """Все не-routed культисты (tier 0 ground) игрока в активной системе."""
    tile = state.get('map', {}).get(tile_key)
    if not tile:
        return []
    units = []
    for area_idx, area in enumerate(tile.get('areas', [])):
        for troop_idx, t in enumerate(area.get('troops', [])):
            if (t.get('player') == player_id
                    and t.get('unitType') == 'ground'
                    and t.get('tier', 0) == 0
                    and t.get('unit_status') != 'routed'):
                units.append({
                    'area_idx':  area_idx,
                    'troop_idx': troop_idx,
                    'unitType':  t.get('unitType'),
                    'tier':      t.get('tier', 0),
                })
    return units


def _is_neutral_or_friendly_planet(area, player_id):
    if area.get('type') != 'planet':
        return False
    enemy_id = 1 - player_id
    has_enemy        = any(t.get('player') == enemy_id for t in area.get('troops', []))
    has_enemy_struct = any(s.get('player') == enemy_id for s in area.get('structures', []))
    return not has_enemy and not has_enemy_struct


def _get_chaos_valid_targets(state, player_id, source_tile_key):
    from python_engine.map_graph import get_adjacent_tile_keys
    targets = []
    for adj_key in get_adjacent_tile_keys(source_tile_key):
        tile = state.get('map', {}).get(adj_key)
        if not tile:
            continue
        for area_idx, area in enumerate(tile.get('areas', [])):
            if not _is_neutral_or_friendly_planet(area, player_id):
                continue
            targets.append({'tile_key': adj_key, 'area_idx': area_idx})
    return targets


def maybe_start(state, player_id, tile_key):
    if state['players'][player_id].get('faction', '') != 'chaos':
        return
    movable = _collect_movable_cultists(state, player_id, tile_key)
    if not movable:
        return
    targets = _get_chaos_valid_targets(state, player_id, tile_key)
    if not targets:
        return
    state['pending_chaos_dominate'] = {
        'player_id':       player_id,
        'source_tile_key': tile_key,
        'movable_units':   movable,
        'valid_targets':   targets,
    }


def handle_move(state, player_id, src_area_idx, src_troop_idx, target_tile_key, target_area_idx):
    new_state = copy.deepcopy(state)
    pending   = new_state.pop('pending_chaos_dominate', None)
    if not pending or pending.get('player_id') != player_id:
        return False, "Нет ожидающей способности Хаоса", None

    source_tile_key = pending['source_tile_key']
    movable_units   = pending.get('movable_units', [])
    valid_targets   = pending.get('valid_targets', [])

    if not any(u['area_idx'] == src_area_idx and u['troop_idx'] == src_troop_idx
               for u in movable_units):
        return False, "Недопустимый юнит для перемещения", None

    if not any(t['tile_key'] == target_tile_key and t['area_idx'] == target_area_idx
               for t in valid_targets):
        return False, "Недопустимая цель для культиста", None

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
        new_state['pending_chaos_retreat'] = {
            'player_id': player_id,
            'tile_key':  target_tile_key,
            'area_idx':  target_area_idx,
            'units':     units_info,
            'capacity':  capacity,
        }
        msg = f"Хаос: культист перемещён в {target_tile_key}/{target_area_idx}, вместимость превышена — выберите юнита для удаления"
    else:
        msg = f"Хаос: культист перемещён в систему {target_tile_key}, область {target_area_idx}"

    new_state.setdefault('log', []).append({'message': msg, 'player_id': player_id})
    return True, msg, new_state


def handle_retreat(state, player_id, tile_key, area_idx, troop_idx):
    new_state = copy.deepcopy(state)
    pending   = new_state.pop('pending_chaos_retreat', None)
    if not pending or pending.get('player_id') != player_id:
        return False, "Нет ожидающего выбора отступления", None
    if pending.get('tile_key') != tile_key or pending.get('area_idx') != area_idx:
        return False, "Неверная область для отступления", None

    area   = new_state['map'][tile_key]['areas'][area_idx]
    troops = area.get('troops', [])
    if troop_idx < 0 or troop_idx >= len(troops):
        return False, "Неверный индекс юнита", None

    removed = troops.pop(troop_idx)
    msg = f"Хаос: юнит игрока {removed.get('player', '?')} удалён из {tile_key}/{area_idx}"
    new_state.setdefault('log', []).append({'message': msg, 'player_id': player_id})
    return True, msg, new_state
