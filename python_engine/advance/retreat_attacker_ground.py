from .convert import _UNROTATE


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
        troops = area.get('troops', [])
        if any(t.get('player') == opponent for t in troops):
            continue
        if any(t.get('player') == loser for t in troops):
            friendly.append((tk, ai))
        elif not troops:
            neutral.append((tk, ai))

    print(f"[RETREAT ATTACKER GROUND] source_areas={source_areas}")
    print(f"[RETREAT ATTACKER GROUND] friendly={friendly}, neutral={neutral}")

    return {'friendly': friendly, 'neutral': neutral}
