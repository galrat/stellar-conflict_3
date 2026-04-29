"""
python_engine/map_graph.py — навигационный граф карты.

Узел: "col,row:area_idx"
Граф строится один раз, скрывает геометрию rotation внутри.
"""

# ── Geometry constants ───────────────────────────────────────────────────────

_DISPLAY_NEIGHBORS: dict[int, tuple] = {0: (1, 2), 1: (0, 3), 2: (0, 3), 3: (1, 2)}

_RMAP = [
    [0, 1, 2, 3],
    [1, 3, 0, 2],
    [3, 2, 1, 0],
    [2, 0, 3, 1],
]


def get_tile_area_neighbors(tile: dict, area_idx: int) -> list[int]:
    rot = int(tile.get('rotation', 0))
    rmap = _RMAP[(rot // 90) % 4]
    disp = rmap[area_idx]
    adj_displays = _DISPLAY_NEIGHBORS[disp]
    return [i for i, d in enumerate(rmap) if d in adj_displays]


def get_adjacent_tile_keys(tile_key: str) -> list[str]:
    parts = tile_key.split(',')
    if len(parts) != 2:
        return []
    try:
        col, row = int(parts[0]), int(parts[1])
    except ValueError:
        return []
    return [
        f'{col},{row-1}',
        f'{col},{row+1}',
        f'{col-1},{row}',
        f'{col+1},{row}',
    ]


def _is_warp_storm_blocking(state: dict, tile_key_a: str, tile_key_b: str) -> bool:
    storms = state.get('warpStorms', [])
    if not storms:
        return False
    try:
        a_col, a_row = map(int, tile_key_a.split(','))
        b_col, b_row = map(int, tile_key_b.split(','))
    except (ValueError, AttributeError):
        return False
    dc, dr = b_col - a_col, b_row - a_row
    if   (dc, dr) == (0, -1): dir_ab, dir_ba = 'top',    'bottom'
    elif (dc, dr) == (0,  1): dir_ab, dir_ba = 'bottom', 'top'
    elif (dc, dr) == (-1, 0): dir_ab, dir_ba = 'left',   'right'
    elif (dc, dr) == (1,  0): dir_ab, dir_ba = 'right',  'left'
    else: return False
    for storm in storms:
        if storm.get('status') != 'active':
            continue
        if storm.get('tile') == tile_key_a and storm.get('side') == dir_ab:
            return True
        if storm.get('tile') == tile_key_b and storm.get('side') == dir_ba:
            return True
    return False


def _compute_border_pairs(active_tile_key, source_tile_key, active_tile, source_tile) -> list[tuple]:
    """Returns [(source_area_idx, active_area_idx)] for border areas between two adjacent tiles."""
    try:
        a_col, a_row = map(int, active_tile_key.split(','))
        s_col, s_row = map(int, source_tile_key.split(','))
    except (ValueError, AttributeError):
        return []
    active_rmap = _RMAP[(int(active_tile.get('rotation', 0)) // 90) % 4]
    source_rmap = _RMAP[(int(source_tile.get('rotation', 0)) // 90) % 4]
    if s_row < a_row:    dp_pairs = [(2, 0), (3, 1)]
    elif s_row > a_row:  dp_pairs = [(0, 2), (1, 3)]
    elif s_col < a_col:  dp_pairs = [(1, 0), (3, 2)]
    else:                dp_pairs = [(0, 1), (2, 3)]
    n_src = len(source_tile.get('areas', []))
    n_act = len(active_tile.get('areas', []))
    result = []
    for src_dp, act_dp in dp_pairs:
        for si, d in enumerate(source_rmap):
            if d == src_dp and si < n_src:
                for ai, d2 in enumerate(active_rmap):
                    if d2 == act_dp and ai < n_act:
                        result.append((si, ai))
    return result


# ── Graph API ────────────────────────────────────────────────────────────────

def build_graph(
    map_data: dict,
    warp_storms: list = None,
    virtual_override: dict = None,
) -> dict:
    """
    Builds a flat graph from map_data.

    map_data: state['map']
    warp_storms: state.get('warpStorms', []) — blocked cross-tile edges are omitted
    virtual_override: {tile_key: {area_idx: {type, troops, ...}}} — replaces area data
                      for specific tiles (used to reflect committed ship moves)

    Returns: {node_id: {tile_key, area_idx, type, troops, neighbors}}
    """
    mock_state = {'warpStorms': warp_storms or []}
    graph: dict = {}

    for tile_key, tile in map_data.items():
        areas = tile.get('areas', [])
        for area_idx, area in enumerate(areas):
            node_id = f"{tile_key}:{area_idx}"
            if virtual_override and tile_key in virtual_override:
                vdata = (virtual_override[tile_key] or {}).get(area_idx, {})
                troops = vdata.get('troops', area.get('troops', []))
                atype = vdata.get('type', area.get('type', 'space'))
            else:
                troops = area.get('troops', [])
                atype = area.get('type', 'space')
            graph[node_id] = {
                "tile_key": tile_key,
                "area_idx": area_idx,
                "type": atype,
                "troops": troops,
                "neighbors": [],
            }

    # Internal edges
    for tile_key, tile in map_data.items():
        n = len(tile.get('areas', []))
        for area_idx in range(n):
            node_id = f"{tile_key}:{area_idx}"
            for ni in get_tile_area_neighbors(tile, area_idx):
                if ni < n:
                    nb_id = f"{tile_key}:{ni}"
                    if nb_id not in graph[node_id]["neighbors"]:
                        graph[node_id]["neighbors"].append(nb_id)

    # Cross-tile edges
    checked: set = set()
    for tile_key in list(map_data.keys()):
        tile = map_data[tile_key]
        for adj_tk in get_adjacent_tile_keys(tile_key):
            pair = tuple(sorted([tile_key, adj_tk]))
            if pair in checked:
                continue
            checked.add(pair)
            adj_tile = map_data.get(adj_tk)
            if not adj_tile:
                continue
            if _is_warp_storm_blocking(mock_state, tile_key, adj_tk):
                continue
            for si, ai in _compute_border_pairs(tile_key, adj_tk, tile, adj_tile):
                n1, n2 = f"{tile_key}:{ai}", f"{adj_tk}:{si}"
                if n1 in graph and n2 in graph:
                    if n2 not in graph[n1]["neighbors"]:
                        graph[n1]["neighbors"].append(n2)
                    if n1 not in graph[n2]["neighbors"]:
                        graph[n2]["neighbors"].append(n1)

    return graph


def get_reachable(
    graph: dict,
    start_id: str,
    move_type: str,
    steps: int = 3,
    player_id: int = None,
    target_tile_key: str = None,
) -> list[str]:
    """
    BFS on the graph.

    move_type="ground": expand friendly zone for `steps` iterations, return
                        planet node IDs adjacent to or within zone in target_tile_key.
    move_type="ground_steps": unconstrained BFS for `steps` steps.
    move_type="space": all space nodes in start tile + warp-storm-unblocked adjacent tiles.
    """
    if start_id not in graph:
        return []
    if move_type == "ground":
        ttk = target_tile_key or graph[start_id]["tile_key"]
        return _ground_zone(graph, start_id, steps, player_id, ttk)
    if move_type == "ground_steps":
        return _ground_steps(graph, start_id, steps)
    if move_type == "space":
        return _space_reach(graph, start_id)
    return []


def sync_back(graph: dict, map_data: dict):
    """Writes troops from graph nodes back into map_data."""
    for node in graph.values():
        tile = map_data.get(node["tile_key"])
        if tile:
            areas = tile.get('areas', [])
            if node["area_idx"] < len(areas):
                areas[node["area_idx"]]['troops'] = node['troops']


# ── BFS helpers ──────────────────────────────────────────────────────────────

def _is_friendly(node: dict, player_id: int) -> bool:
    if node['type'] == 'planet':
        return any(t.get('player') == player_id for t in node['troops'])
    if node['type'] == 'space':
        return any(
            t.get('player') == player_id and t.get('unitType') == 'space'
            for t in node['troops']
        )
    return False


def _ground_zone(graph, start_id, steps, player_id, target_tile_key) -> list[str]:
    """Expand friendly zone; return planet node IDs in target_tile_key reachable from boundary."""
    zone = {start_id}
    frontier = {start_id}
    for _ in range(steps):
        nxt = set()
        for nid in frontier:
            for nb in graph[nid]["neighbors"]:
                if nb not in zone and _is_friendly(graph[nb], player_id):
                    nxt.add(nb)
        zone |= nxt
        frontier = nxt

    result = []
    for nid in zone:
        for cid in [nid] + graph[nid]["neighbors"]:
            node = graph.get(cid)
            if node and node["tile_key"] == target_tile_key and node["type"] == "planet":
                if cid not in result:
                    result.append(cid)
    return result


def _ground_steps(graph, start_id, steps) -> list[str]:
    """Unconstrained BFS for `steps` steps."""
    visited = {start_id}
    frontier = {start_id}
    for _ in range(steps):
        nxt = {nb for nid in frontier for nb in graph[nid]["neighbors"] if nb not in visited}
        visited |= nxt
        frontier = nxt
    return list(visited)


def _space_reach(graph, start_id) -> list[str]:
    """All space nodes in start tile + tiles connected via cross-tile edges (warp storms already filtered)."""
    start_tile = graph[start_id]["tile_key"]
    connected_tiles = {start_tile}
    for node in graph.values():
        if node["tile_key"] != start_tile:
            continue
        for nb_id in node["neighbors"]:
            if graph[nb_id]["tile_key"] != start_tile:
                connected_tiles.add(graph[nb_id]["tile_key"])
    return [
        nid for nid, node in graph.items()
        if node["tile_key"] in connected_tiles and node["type"] == "space"
    ]
