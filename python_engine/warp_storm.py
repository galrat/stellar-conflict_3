"""
python_engine/warp_storm.py — Логика перемещения варп-штормов (конец раунда).

Направления на картах событий:
  Across           — через тайл на противоположную сторону
  Sideways         — параллельное перемещение к соседнему тайлу
  Top Rgt/Bot Left — по часовой стрелке
  Top Left/Bot Rgt — против часовой стрелки
"""

_OPPOSITE = {'top': 'bottom', 'bottom': 'top', 'left': 'right', 'right': 'left'}
_CW  = {'top': 'right',  'right': 'bottom', 'bottom': 'left',  'left': 'top'}
_CCW = {'top': 'left',   'left':  'bottom', 'bottom': 'right', 'right': 'top'}


def _adj_tile(tile_key: str, side: str) -> str:
    col, row = map(int, tile_key.split(','))
    if side == 'top':    return f'{col},{row - 1}'
    if side == 'bottom': return f'{col},{row + 1}'
    if side == 'left':   return f'{col - 1},{row}'
    return f'{col + 1},{row}'  # right


def _normalize_border(tile_key: str, side: str) -> tuple:
    """Canonical border representation — one form for each physical border."""
    col, row = map(int, tile_key.split(','))
    if side == 'top':  return (f'{col},{row - 1}', 'bottom')
    if side == 'left': return (f'{col - 1},{row}', 'right')
    return (tile_key, side)


def _compute_move_targets(tile_key: str, side: str, direction: str) -> list:
    """Returns [(tile_key, side)] candidate positions for the given direction."""
    if not tile_key or ',' not in tile_key:
        return []
    adj = _adj_tile(tile_key, side)

    if direction == 'Across':
        return [(tile_key, _OPPOSITE[side]), (adj, side)]

    if direction == 'Sideways':
        col, row = map(int, tile_key.split(','))
        if side in ('top', 'bottom'):
            return [(f'{col - 1},{row}', side), (f'{col + 1},{row}', side)]
        else:
            return [(f'{col},{row - 1}', side), (f'{col},{row + 1}', side)]

    if direction == 'Top Rgt/Bot Left':  # clockwise
        return [(tile_key, _CW[side]), (tile_key, _CCW[side])]

    if direction == 'Top Left/Bot Rgt':  # counterclockwise
        return [(adj, _CW[_OPPOSITE[side]]), (adj, _CCW[_OPPOSITE[side]])]

    return []


def _is_valid_border(state: dict, tile_key: str, side: str) -> bool:
    """Border is valid if both adjacent tiles exist in the map."""
    if not tile_key or ',' not in tile_key:
        return False
    game_map = state.get('map', {})
    return tile_key in game_map and _adj_tile(tile_key, side) in game_map


def _occupied_borders(state: dict, exclude_idx: int = None) -> set:
    """Set of normalized borders occupied by warp storms (optionally excluding one)."""
    result = set()
    for i, storm in enumerate(state.get('warpStorms', [])):
        if storm and (exclude_idx is None or i != exclude_idx):
            tk = storm.get('tileKey', '')
            sd = storm.get('side', '')
            if tk and sd:
                result.add(_normalize_border(tk, sd))
    return result


def get_moveable_storms(state: dict, direction: str) -> list:
    """
    Returns indices of warp storms that can be moved in the given direction.
    A storm is moveable if it is active, not yet moved this round,
    and has at least one valid target position.
    """
    if not direction:
        return []
    result = []
    for i, storm in enumerate(state.get('warpStorms', [])):
        if not storm:
            continue
        if storm.get('status') != 'active':
            continue
        occupied = _occupied_borders(state, exclude_idx=i)
        tk, sd = storm.get('tileKey', ''), storm.get('side', '')
        for t_tile, t_side in _compute_move_targets(tk, sd, direction):
            if _is_valid_border(state, t_tile, t_side) and _normalize_border(t_tile, t_side) not in occupied:
                result.append(i)
                break
    return result


def get_storm_valid_positions(state: dict, storm_idx: int, direction: str) -> list:
    """Returns valid target positions [{tileKey, side}] for the selected storm."""
    storms = state.get('warpStorms', [])
    if storm_idx >= len(storms) or not storms[storm_idx]:
        return []
    storm = storms[storm_idx]
    occupied = _occupied_borders(state, exclude_idx=storm_idx)
    result = []
    for t_tile, t_side in _compute_move_targets(storm.get('tileKey', ''), storm.get('side', ''), direction):
        if _is_valid_border(state, t_tile, t_side) and _normalize_border(t_tile, t_side) not in occupied:
            result.append({'tileKey': t_tile, 'side': t_side})
    return result


def do_move_storm(state: dict, storm_idx: int, new_tile: str, new_side: str, player_id: int) -> dict:
    """Move a warp storm to the new position and advance the warp turn to the other player."""
    storms = state.get('warpStorms', [])
    if storm_idx < len(storms) and storms[storm_idx]:
        storms[storm_idx]['tileKey'] = new_tile
        storms[storm_idx]['side'] = new_side
        storms[storm_idx]['moved_by'] = player_id
    do_pass_warp_turn(state, player_id)
    return state


def do_pass_warp_turn(state: dict, player_id: int) -> dict:
    """Mark player's warp storm turn as done and advance curP."""
    done = state.setdefault('warp_storm_phase_done', [False, False])
    done[player_id] = True
    other = 1 - player_id
    selection_done = state.get('event_selection_done', [False, False])
    if not selection_done[other] or not done[other]:
        state['curP'] = other
    return state
