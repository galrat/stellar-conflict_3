from collections import deque

from ..map_graph import build_graph, get_adjacent_tile_keys, _is_warp_storm_blocking
from .convert import _UNROTATE


def is_ground_retreating(state, tile_key, contested_idx, loser):
    game_map = state.get('map', {})
    active_tile = game_map.get(tile_key, {})
    areas = active_tile.get('areas', [])
    if contested_idx >= len(areas):
        return False
    return areas[contested_idx].get('type') == 'planet'


def _area_is_friendly_ground(area: dict, player: int) -> bool:
    if any(t.get('player') == player for t in area.get('troops', [])):
        return True
    if any(b.get('player') == player for b in area.get('buildings', [])):
        return True
    return False


def _find_reachable_via_friendly(state, start_tile_key, start_area_idx, player):
    """BFS от стартовой области через дружественные области (войска или постройки игрока)."""
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
            if _area_is_friendly_ground(nb_area, player):
                visited.add(nb_id)
                queue.append(nb_id)

    return visited


def get_retreat_valid_areas_ground(state, tile_key, contested_idx, loser):
    game_map = state.get('map', {})
    pa = state.get('pending_advance', {})
    opponent = 1 - loser

    blocked_system = pa.get('source_tile')

    blocked_areas = set()
    for entry in pa.get('moved_from_areas', []):
        entry_tile_key = f"{entry[0][0]},{entry[0][1]}"
        rotation = entry[6]
        local_area_idx = _UNROTATE.get(rotation, _UNROTATE[0]).get(tuple(entry[1]))
        if local_area_idx is not None:
            blocked_areas.add((entry_tile_key, local_area_idx))

    allowed_tiles = {tile_key}
    for adj_tk in get_adjacent_tile_keys(tile_key):
        if adj_tk == blocked_system:
            continue
        if adj_tk not in game_map:
            continue
        if _is_warp_storm_blocking({'warpStorms': state.get('warpStorms', [])}, tile_key, adj_tk):
            continue
        allowed_tiles.add(adj_tk)

    # Базовые кандидаты: планеты без войск противника
    candidates = []
    for tk in allowed_tiles:
        tile = game_map.get(tk, {})
        for ai, area in enumerate(tile.get('areas', [])):
            if tk == tile_key and ai == contested_idx:
                continue
            if area.get('type') == 'space':
                continue
            if (tk, ai) in blocked_areas:
                continue
            if any(t.get('player') == opponent for t in area.get('troops', [])):
                continue
            candidates.append((tk, ai))

    # Фильтр: только планеты, достижимые через дружественные области
    reachable = _find_reachable_via_friendly(state, tile_key, contested_idx, loser)

    friendly = []
    neutral = []
    for (tk, ai) in candidates:
        if f"{tk}:{ai}" not in reachable:
            continue
        area = game_map.get(tk, {}).get('areas', [])[ai]
        if _area_is_friendly_ground(area, loser):
            friendly.append((tk, ai))
        else:
            neutral.append((tk, ai))

    print(f"[RETREAT GROUND] blocked_system={blocked_system}, blocked_areas={blocked_areas}")
    print(f"[RETREAT GROUND] allowed_tiles={allowed_tiles}, candidates={candidates}")
    print(f"[RETREAT GROUND] reachable={reachable}")
    print(f"[RETREAT GROUND] friendly={friendly}, neutral={neutral}")

    return {'friendly': friendly, 'neutral': neutral}
