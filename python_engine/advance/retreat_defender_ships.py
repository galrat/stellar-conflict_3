from ..map_graph import get_adjacent_tile_keys, _is_warp_storm_blocking
from .convert import _UNROTATE


def is_ships_retreating(state, tile_key, contested_idx, loser):
    game_map = state.get('map', {})
    active_tile = game_map.get(tile_key, {})
    areas = active_tile.get('areas', [])
    if contested_idx >= len(areas):
        return False
    return areas[contested_idx].get('type') == 'space'


def get_retreat_valid_areas_ships(state, tile_key, contested_idx, loser):
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

    friendly = []
    neutral = []

    for tk in allowed_tiles:
        tile = game_map.get(tk, {})
        for ai, area in enumerate(tile.get('areas', [])):
            if tk == tile_key and ai == contested_idx:
                continue
            if area.get('type') != 'space':
                continue
            if (tk, ai) in blocked_areas:
                continue
            troops = area.get('troops', [])
            if any(t.get('player') == opponent for t in troops):
                continue
            if any(t.get('player') == loser for t in troops):
                friendly.append((tk, ai))
            elif not troops:
                neutral.append((tk, ai))

    print(f"[RETREAT SHIPS] blocked_system={blocked_system}, blocked_areas={blocked_areas}")
    print(f"[RETREAT SHIPS] allowed_tiles={allowed_tiles}")
    print(f"[RETREAT SHIPS] friendly={friendly}, neutral={neutral}")

    return {'friendly': friendly, 'neutral': neutral if not friendly else []}
