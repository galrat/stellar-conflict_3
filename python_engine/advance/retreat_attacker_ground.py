import copy
from collections import deque

from .convert import _UNROTATE
from ..map_graph import build_graph
from .capacity import _find_all_overflow_areas_global
from .finalize import finalize_advance


def _area_is_friendly(area: dict, player: int) -> bool:
    if any(t.get('player') == player for t in area.get('troops', [])):
        return True
    if any(b.get('player') == player for b in area.get('buildings', [])):
        return True
    return False


def _find_reachable_via_friendly(state, start_tile_key, start_area_idx, player):
    """BFS от стартовой области через дружественные области (наземные и космические)."""
    game_map = state.get('map', {})
    graph = build_graph(game_map, state.get('warpStorms', []))

    start_id = f"{start_tile_key}:{start_area_idx}"
    if start_id not in graph:
        return set()

    visited = {start_id}
    queue = deque([start_id])

    while queue:
        node_id = queue.popleft()
        node = graph[node_id]
        for nb_id in node['neighbors']:
            if nb_id in visited:
                continue
            nb_node = graph[nb_id]
            nb_areas = game_map.get(nb_node['tile_key'], {}).get('areas', [])
            if nb_node['area_idx'] >= len(nb_areas):
                continue
            nb_area = nb_areas[nb_node['area_idx']]
            if _area_is_friendly(nb_area, player):
                visited.add(nb_id)
                queue.append(nb_id)

    return visited


def get_retreat_valid_areas_attacker_ground(state, tile_key, contested_idx, loser):
    game_map = state.get('map', {})
    pa = state.get('pending_advance', {})
    opponent = 1 - loser

    seen = set()
    source_areas = []
    for entry in pa.get('moved_from_areas', []):
        entry_tile_key = f"{entry[0][0]},{entry[0][1]}"
        rotation = entry[6]
        local_area_idx = _UNROTATE.get(rotation, _UNROTATE[0]).get(tuple(entry[1]))
        if local_area_idx is not None:
            key = (entry_tile_key, local_area_idx)
            if key not in seen:
                seen.add(key)
                source_areas.append(key)

    reachable = _find_reachable_via_friendly(state, tile_key, contested_idx, loser)

    friendly = []
    neutral = []

    for (tk, ai) in source_areas:
        tile = game_map.get(tk, {})
        tile_areas = tile.get('areas', [])
        if ai >= len(tile_areas):
            continue
        area = tile_areas[ai]
        if area.get('type') == 'space':
            continue
        if any(t.get('player') == opponent for t in area.get('troops', [])):
            continue
        if f"{tk}:{ai}" not in reachable:
            continue
        if _area_is_friendly(area, loser):
            friendly.append((tk, ai))
        elif not area.get('troops', []):
            neutral.append((tk, ai))

    print(f"[RETREAT ATTACKER GROUND] source_areas={source_areas}")
    print(f"[RETREAT ATTACKER GROUND] reachable={reachable}")
    print(f"[RETREAT ATTACKER GROUND] friendly={friendly}, neutral={neutral}")

    return {'friendly': friendly, 'neutral': neutral}


def retreat_attacker_ground(state, player_id, retreat_tile_key, retreat_area_idx):
    pa = state['pending_advance']
    loser = pa['combat_loser']
    tile_key = pa['tile_key']
    contested_idx = pa['contest_area_idx']

    origin_tile = state['map'][tile_key]
    retreat_tile = state['map'].get(retreat_tile_key)
    if not retreat_tile or retreat_area_idx >= len(retreat_tile.get('areas', [])):
        raise ValueError(f"Область {retreat_area_idx} в системе {retreat_tile_key} не существует")

    contested_area = origin_tile['areas'][contested_idx]
    retreat_area = retreat_tile['areas'][retreat_area_idx]

    loser_units = [t for t in contested_area.get('troops', []) if t.get('player') == loser]
    contested_area['troops'] = [t for t in contested_area.get('troops', []) if t.get('player') != loser]

    for unit in loser_units:
        unit_copy = copy.deepcopy(unit)
        unit_copy['unit_status'] = 'routed'
        retreat_area.setdefault('troops', []).append(unit_copy)

    loser_name = state['players'][loser].get('name', f'Игрок {loser}')
    state.setdefault('log', []).append({
        'message': f'{loser_name} (нападавший, наземные) отступил в {retreat_tile_key}:{retreat_area_idx} ({len(loser_units)} юн.). Статус: разбит.',
        'player_id': player_id,
    })

    overflow_all = _find_all_overflow_areas_global(state)
    if overflow_all:
        first = overflow_all[0]
        pa['step'] = 'capacity_overflow'
        pa['overflow_areas'] = [{'area_idx': first['area_idx'], 'excess': first['excess']}]
        pa['overflow_player'] = first['player_id']
        pa['overflow_tile_key'] = first['tile_key']
        pa['overflow_context'] = 'post_retreat'
        pa['instruction'] = 'Превышена вместимость. Выберите юнита для возврата в запас.'
    else:
        pa['instruction'] = 'Отступление завершено. Advance окончен.'
        finalize_advance(state, player_id)

    return state
