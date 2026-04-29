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
                has_friendly_ship = any(
                    t.get('player') == player_id and t.get('unitType') == 'space'
                    for t in neighbor_virtual.get('troops', [])
                )
                if has_friendly_ship:
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
    map_slice = {active_tile_key: active_tile}
    if source_tile and source_tile_key:
        map_slice[source_tile_key] = source_tile

    graph = build_graph(map_slice, virtual_override={active_tile_key: virtual_areas})

    start_tile_key = active_tile_key if start_tile_type == 'active' else source_tile_key
    start_id = f"{start_tile_key}:{start_area_idx}"

    node_ids = get_reachable(
        graph, start_id, "ground",
        steps=3, player_id=player_id, target_tile_key=active_tile_key,
    )
    return [graph[nid]["area_idx"] for nid in node_ids]


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
