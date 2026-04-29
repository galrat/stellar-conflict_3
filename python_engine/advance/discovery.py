import copy
import uuid
from typing import Optional

from ..map_graph import (
    get_tile_area_neighbors,
    get_adjacent_tile_keys,
    _is_warp_storm_blocking,
    _compute_border_pairs,
    build_graph,
    get_reachable,
)
from .convert import state_to_areas, _UNROTATE


def get_adjacent_tiles_with_units(state, tile_key, player_id) -> list[str]:
    adjacent = get_adjacent_tile_keys(tile_key)
    result = []
    for tk in adjacent:
        tile = state.get('map', {}).get(tk)
        if not tile:
            continue
        has_unit = False
        for area in tile.get('areas', []):
            for troop in area.get('troops', []):
                if troop.get('player') == player_id:
                    has_unit = True
                    break
            if has_unit:
                break
        if has_unit:
            result.append(tk)
    return result


def get_available_units(state, player_id, source_tile_key, active_tile_key) -> dict:
    ships = []
    ground_units = []
    ship_id = 0
    ground_id = 0

    active_tile = state.get('map', {}).get(active_tile_key)
    if active_tile:
        for area_idx, area in enumerate(active_tile.get('areas', [])):
            for unit_idx, troop in enumerate(area.get('troops', [])):
                if troop.get('player') != player_id:
                    continue
                if troop.get('unit_status') == 'routed':
                    continue
                unit_copy = copy.deepcopy(troop)
                unit_copy['_uid'] = str(uuid.uuid4())
                if troop.get('unitType') == 'space':
                    ships.append({'ship_id': ship_id, 'area_idx': area_idx, 'unit_index': unit_idx, 'unit': unit_copy, 'origin': 'active'})
                    ship_id += 1
                elif troop.get('unitType') == 'ground':
                    ground_units.append({'ground_id': ground_id, 'area_idx': area_idx, 'unit_index': unit_idx, 'unit': unit_copy, 'origin': 'active'})
                    ground_id += 1

    if source_tile_key:
        source_tile = state.get('map', {}).get(source_tile_key)
        if source_tile:
            for area_idx, area in enumerate(source_tile.get('areas', [])):
                for unit_idx, troop in enumerate(area.get('troops', [])):
                    if troop.get('player') != player_id:
                        continue
                    if troop.get('unit_status') == 'routed':
                        continue
                    unit_copy = copy.deepcopy(troop)
                    unit_copy['_uid'] = str(uuid.uuid4())
                    if troop.get('unitType') == 'space':
                        ships.append({'ship_id': ship_id, 'area_idx': area_idx, 'unit_index': unit_idx, 'unit': unit_copy, 'origin': 'source'})
                        ship_id += 1
                    elif troop.get('unitType') == 'ground':
                        ground_units.append({'ground_id': ground_id, 'area_idx': area_idx, 'unit_index': unit_idx, 'unit': unit_copy, 'origin': 'source'})
                        ground_id += 1

    return {'ships': ships, 'ground_units': ground_units}


def init_virtual_areas(state, active_tile_key) -> dict:
    active_tile = state.get('map', {}).get(active_tile_key)
    if not active_tile:
        return {}
    virtual = {}
    for idx, area in enumerate(active_tile.get('areas', [])):
        virtual[idx] = {
            'troops': copy.deepcopy(area.get('troops', [])),
            'type': area.get('type', 'space'),
            'capacity': area.get('capacity', 99),
        }
    return virtual


def count_contested_areas(virtual_areas, player_id) -> int:
    opponent = 1 - player_id
    count = 0
    for area in virtual_areas.values():
        has_player = any(t.get('player') == player_id for t in area['troops'])
        has_opponent = any(t.get('player') == opponent for t in area['troops'])
        if has_player and has_opponent:
            count += 1
    return count


def validate_no_second_contest(virtual_areas, player_id, from_area_idx, to_area_idx, unit) -> tuple[bool, str]:
    test_virtual = copy.deepcopy(virtual_areas)
    if from_area_idx is not None and from_area_idx in test_virtual:
        troops = test_virtual[from_area_idx]['troops']
        for i, t in enumerate(troops):
            if (t.get('player') == player_id and
                    t.get('unitType') == unit.get('unitType') and
                    t.get('tier') == unit.get('tier')):
                troops.pop(i)
                break
    if to_area_idx in test_virtual:
        test_virtual[to_area_idx]['troops'].append(copy.deepcopy(unit))
    contested = count_contested_areas(test_virtual, player_id)
    if contested > 1:
        return False, "Нельзя создать вторую спорную область"
    return True, ""


def is_ground_reachable(virtual_areas, active_tile, from_area_idx, to_area_idx, player_id, origin) -> bool:
    if origin == 'source':
        return virtual_areas.get(to_area_idx, {}).get('type') == 'planet'
    if from_area_idx == to_area_idx:
        return True
    areas_list = active_tile.get('areas', [])
    visited = set()
    queue = [from_area_idx]
    visited.add(from_area_idx)
    opponent = 1 - player_id
    while queue:
        current_idx = queue.pop(0)
        if current_idx == to_area_idx:
            return True
        current_area_def = areas_list[current_idx] if current_idx < len(areas_list) else {}
        neighbors = current_area_def.get('neighbors', [])
        for neighbor_idx in neighbors:
            if neighbor_idx in visited or neighbor_idx >= len(areas_list):
                continue
            neighbor_area_def = areas_list[neighbor_idx]
            neighbor_virtual = virtual_areas.get(neighbor_idx, {})
            neighbor_type = neighbor_virtual.get('type', neighbor_area_def.get('type', 'space'))
            has_enemy = any(t.get('player') == opponent for t in neighbor_virtual.get('troops', []))
            if neighbor_type == 'planet':
                if not has_enemy or neighbor_idx == to_area_idx:
                    visited.add(neighbor_idx)
                    queue.append(neighbor_idx)
            elif neighbor_type == 'space':
                neighbor_troops = neighbor_virtual.get('troops', [])
                opponent = 1 - player_id
                has_friendly_ship = any(
                    t.get('player') == player_id and t.get('unitType') == 'space'
                    for t in neighbor_troops
                )
                has_enemy = any(t.get('player') == opponent for t in neighbor_troops)
                if has_friendly_ship and not has_enemy:
                    visited.add(neighbor_idx)
                    queue.append(neighbor_idx)
    return False


def find_contested_area(state, active_tile_key, player_id) -> Optional[int]:
    active_tile = state['map'].get(active_tile_key)
    if not active_tile:
        return None
    opponent = 1 - player_id
    contested_idx = None
    for idx, area in enumerate(active_tile.get('areas', [])):
        has_player = any(t.get('player') == player_id for t in area.get('troops', []))
        has_opponent = any(t.get('player') == opponent for t in area.get('troops', []))
        if has_player and has_opponent:
            if contested_idx is not None:
                return None
            contested_idx = idx
    return contested_idx


def get_available_space_areas(active_tile, player_id, exclude_from_area=None) -> list[int]:
    available = []
    for idx, area in enumerate(active_tile.get('areas', [])):
        if area.get('type') != 'space':
            continue
        if exclude_from_area is not None and idx == exclude_from_area:
            continue
        available.append(idx)
    return available


def get_reachable_planets_for_unit(
    active_tile_key, source_tile_key,
    active_tile, source_tile,
    virtual_areas,
    start_tile_type, start_area_idx,
    player_id,
) -> list[int]:
    active_copy = copy.deepcopy(active_tile)
    for idx, vdata in virtual_areas.items():
        if idx < len(active_copy.get('areas', [])):
            active_copy['areas'][idx]['troops'] = list(vdata.get('troops', []))

    mini_map = {active_tile_key: active_copy}
    if source_tile and source_tile_key:
        mini_map[source_tile_key] = source_tile

    areas = state_to_areas({'map': mini_map})
    my_owner = player_id + 1

    area_meta = {}
    pos_map = {}
    for entry in areas:
        tile_coords, area_vis, unique_num, area_type, owner, capacity, rotation = entry
        tile_col, tile_row = tile_coords
        area_row, area_col = area_vis
        area_idx = _UNROTATE.get(rotation, _UNROTATE[0])[(area_row, area_col)]
        global_pos = (tile_row * 2 + area_row, tile_col * 2 + area_col)
        tk = f"{tile_col},{tile_row}"
        area_meta[unique_num] = {
            'pos': global_pos, 'type': area_type, 'owner': owner,
            'tile_key': tk, 'area_idx': area_idx,
        }
        pos_map[global_pos] = unique_num

    adj = {uid: [] for uid in area_meta}
    for uid, meta in area_meta.items():
        gr, gc = meta['pos']
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nb_uid = pos_map.get((gr + dr, gc + dc))
            if nb_uid is not None:
                adj[uid].append(nb_uid)

    start_tk = active_tile_key if start_tile_type == 'active' else source_tile_key
    start_uid = next(
        (uid for uid, m in area_meta.items()
         if m['tile_key'] == start_tk and m['area_idx'] == start_area_idx),
        None
    )
    if start_uid is None:
        return []

    zone = {start_uid}
    frontier = {start_uid}
    for _ in range(3):
        nxt = set()
        for uid in frontier:
            for nb in adj[uid]:
                if nb not in zone and area_meta[nb]['owner'] == my_owner:
                    nxt.add(nb)
        zone |= nxt
        frontier = nxt

    result = []
    for uid in zone:
        for cid in [uid] + adj[uid]:
            m = area_meta[cid]
            if m['tile_key'] == active_tile_key and m['type'] == 'planet':
                if m['area_idx'] not in result:
                    result.append(m['area_idx'])
    return result


def get_areas_within_steps_ground(state, start_tile_key: str, start_area_idx: int, steps: int = 3) -> list:
    graph = build_graph(state.get('map', {}), state.get('warpStorms', []))
    start_id = f"{start_tile_key}:{start_area_idx}"
    node_ids = get_reachable(graph, start_id, "ground_steps", steps=steps)
    return [(graph[nid]["tile_key"], graph[nid]["area_idx"]) for nid in node_ids]


def get_areas_space_reachable(state, start_tile_key: str) -> list:
    graph = build_graph(state.get('map', {}), state.get('warpStorms', []))
    start_id = f"{start_tile_key}:0"
    if start_id not in graph:
        return []
    node_ids = get_reachable(graph, start_id, "space")
    return [(graph[nid]["tile_key"], graph[nid]["area_idx"]) for nid in node_ids]
