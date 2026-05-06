"""faction_defs/marine_data/dominate.py — особое свойство доминации фракции Space Marines."""
import copy


def _collect_upgradeable_units(state, player_id, tile_key):
    tile = state.get('map', {}).get(tile_key)
    if not tile:
        return []
    units = []
    for area_idx, area in enumerate(tile.get('areas', [])):
        for troop_idx, t in enumerate(area.get('troops', [])):
            if (t.get('player') == player_id
                    and t.get('unitType') == 'ground'
                    and t.get('tier', 0) in (0, 1)
                    and t.get('unit_status') != 'routed'):
                units.append({
                    'area_idx':  area_idx,
                    'troop_idx': troop_idx,
                    'unitType':  t.get('unitType'),
                    'tier':      t.get('tier', 0),
                })
    return units


def maybe_start(state, player_id, tile_key):
    if state['players'][player_id].get('faction', '') != 'marine':
        return
    movable = _collect_upgradeable_units(state, player_id, tile_key)
    if not movable:
        return
    state['pending_marine_dominate'] = {
        'player_id':       player_id,
        'source_tile_key': tile_key,
        'movable_units':   movable,
    }


def handle_upgrade(state, player_id, area_idx, troop_idx):
    new_state = copy.deepcopy(state)
    pending = new_state.pop('pending_marine_dominate', None)
    if not pending or pending.get('player_id') != player_id:
        return False, "Нет ожидающей способности Marine", None

    source_tile_key = pending['source_tile_key']
    movable_units   = pending.get('movable_units', [])

    if not any(u['area_idx'] == area_idx and u['troop_idx'] == troop_idx
               for u in movable_units):
        return False, "Недопустимый юнит для улучшения", None

    player  = new_state['players'][player_id]
    credits = player.get('credits', 0)
    if credits < 1:
        return False, "Недостаточно кредитов для улучшения", None

    area   = new_state['map'][source_tile_key]['areas'][area_idx]
    troops = area.get('troops', [])
    if troop_idx < 0 or troop_idx >= len(troops):
        return False, "Неверный индекс юнита", None

    troop = troops[troop_idx]
    if troop.get('unit_status') == 'routed':
        return False, "Нельзя улучшать routed юнита", None

    old_tier = troop.get('tier', 0)
    if old_tier not in (0, 1):
        return False, "Можно улучшать только юнитов tier 0 или tier 1", None

    troop['tier'] = old_tier + 1
    player['credits'] = credits - 1

    msg = f"Marine: юнит улучшен до tier {troop['tier']} в {source_tile_key}/{area_idx}"
    new_state.setdefault('log', []).append({'message': msg, 'player_id': player_id})
    return True, msg, new_state


def handle_skip(state, player_id):
    new_state = copy.deepcopy(state)
    new_state.pop('pending_marine_dominate', None)
    msg = "Marine: особое свойство доминации пропущено"
    new_state.setdefault('log', []).append({'message': msg, 'player_id': player_id})
    return True, msg, new_state
