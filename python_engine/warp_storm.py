"""
warp_storm.py — Логика перемещения варп-штормов (Stellar Conflict)

Варп-шторм занимает границу между тайлами: {tileKey, side}.
Внутреннее представление — канонические рёбра сетки:
  H(c, r) — горизонтальное ребро между строкой r-1 и строкой r, столбец c
  V(c, r) — вертикальное ребро между столбцом c-1 и столбцом c, строка r

4 направления из карты событий, у каждого до 2 допустимых ходов:
  Across           — перпендикулярно, через соседний тайл или на другую границу текущего тайла
  Sideways         — параллельно, на соседний тайл влево или вправо
  Top Rgt/Bot Left — диагональ / (clockwise) в две стороны то есть диагональ внутри тайла или на соседний тайл
  Top Left/Bot Rgt — диагональ \\ (counterclockwise) то есть диагональ внутри тайла или на соседний тайл
"""

# ── Canonical edge helpers ────────────────────────────────────────────────────

def _to_canonical(tile_key: str, side: str) -> tuple:
    """(tileKey, side) → ('h'|'v', c, r) canonical edge form."""
    c, r = map(int, tile_key.split(','))
    if side == 'top':    return ('h', c, r)
    if side == 'bottom': return ('h', c, r + 1)
    if side == 'left':   return ('v', c, r)
    if side == 'right':  return ('v', c + 1, r)
    raise ValueError(f"Unknown side: {side}")


def _from_canonical(orient: str, c: int, r: int, map_data: dict):
    """('h'|'v', c, r) → (tile_key, side) using first existing tile, or None if off-map."""
    if orient == 'h':
        if f'{c},{r}' in map_data:
            return (f'{c},{r}', 'top')
        if f'{c},{r - 1}' in map_data:
            return (f'{c},{r - 1}', 'bottom')
    else:  # 'v'
        if f'{c},{r}' in map_data:
            return (f'{c},{r}', 'left')
        if f'{c - 1},{r}' in map_data:
            return (f'{c - 1},{r}', 'right')
    return None


# ── Movement tables ───────────────────────────────────────────────────────────
# Each delta: (new_orient, dc, dr) → destination canonical = (new_orient, c+dc, r+dr)
#
# Derivation (for horizontal border H(c,r)):
#   Across:           through tile above → H(c,r-1); through tile below → H(c,r+1)
#   Sideways:         slide left → H(c-1,r); slide right → H(c+1,r)
#   Top Rgt/Bot Left: upper-right corner → V(c+1,r-1); lower-left corner → V(c,r)
#   Top Left/Bot Rgt: upper-left corner → V(c,r-1);   lower-right corner → V(c+1,r)
#
# Verification: each destination shares exactly one vertex with H(c,r), except Across
# which hops over one tile (2-step in edge distance).

_DELTAS = {
    'Across': {
        'h': [('h',  0, -1), ('h',  0, +1)],
        'v': [('v', -1,  0), ('v', +1,  0)],
    },
    'Sideways': {
        'h': [('h', -1,  0), ('h', +1,  0)],
        'v': [('v',  0, -1), ('v',  0, +1)],
    },
    'Top Rgt/Bot Left': {
        'h': [('v', +1, -1), ('v',  0,  0)],
        'v': [('h',  0,  0), ('h', -1, +1)],
    },
    'Top Left/Bot Rgt': {
        'h': [('v',  0, -1), ('v', +1,  0)],
        'v': [('h', -1,  0), ('h',  0, +1)],
    },
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_storm_valid_positions(state: dict, storm_idx: int, direction: str) -> list:
    """
    Returns valid target positions [{tileKey, side}] for the selected storm.

    storm_idx: index into state['warpStorms']
    direction: 'Across' | 'Sideways' | 'Top Rgt/Bot Left' | 'Top Left/Bot Rgt'
    """
    storms = state.get('warpStorms', [])
    if storm_idx >= len(storms) or not storms[storm_idx]:
        return []

    storm = storms[storm_idx]
    map_data = state.get('map', {})
    orient, c, r = _to_canonical(storm['tileKey'], storm['side'])
    src_canon = (orient, c, r)

    # Canonical positions occupied by other storms
    other_canon = set()
    for i, s in enumerate(storms):
        if s and i != storm_idx:
            other_canon.add(_to_canonical(s['tileKey'], s['side']))

    results = []
    for (new_orient, dc, dr) in _DELTAS.get(direction, {}).get(orient, []):
        dest_canon = (new_orient, c + dc, r + dr)
        if dest_canon == src_canon or dest_canon in other_canon:
            continue
        result = _from_canonical(new_orient, c + dc, r + dr, map_data)
        if result is None:
            continue
        results.append({'tileKey': result[0], 'side': result[1]})

    return results


def get_moveable_storms(state: dict, direction: str) -> list:
    """Returns indices of warp storms that have at least one valid move in the given direction."""
    if not direction:
        return []
    return [
        i for i, storm in enumerate(state.get('warpStorms', []))
        if storm and get_storm_valid_positions(state, i, direction)
    ]


def do_move_storm(state: dict, storm_idx: int, new_tile: str, new_side: str, player_id: int) -> dict:
    """Move a warp storm to the new position. Mutates state in place."""
    storms = state.get('warpStorms', [])
    if storm_idx < len(storms) and storms[storm_idx]:
        storms[storm_idx]['tileKey'] = new_tile
        storms[storm_idx]['side'] = new_side
        storms[storm_idx]['moved_by'] = player_id
    state.get('log', []).append({
        'message': f'{state["players"][player_id].get("name", f"P{player_id}")} переместил варп-шторм → [{new_tile}] {new_side}',
        'player_id': player_id,
    })
    do_pass_warp_turn(state, player_id)
    return state


def do_pass_warp_turn(state: dict, player_id: int) -> dict:
    """Mark player's warp storm turn as done and advance curP if needed."""
    done = state.setdefault('warp_storm_phase_done', [False, False])
    done[player_id] = True
    other = 1 - player_id
    if not done[other]:
        state['curP'] = other
    return state
