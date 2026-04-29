import copy
from .discovery import find_contested_area
from .finalize import finalize_advance


def _find_overflow_areas(state, tile_key, player_id) -> list[dict]:
    active_tile = state['map'].get(tile_key, {})
    result = []
    for area_idx, area in enumerate(active_tile.get('areas', [])):
        capacity = area.get('capacity', 99)
        friendly = [t for t in area.get('troops', []) if t.get('player') == player_id]
        if len(friendly) > capacity:
            result.append({'area_idx': area_idx, 'excess': len(friendly) - capacity})
    return result


def _find_all_overflow_areas(state, tile_key) -> list[dict]:
    active_tile = state['map'].get(tile_key, {})
    result = []
    for area_idx, area in enumerate(active_tile.get('areas', [])):
        capacity = area.get('capacity', 99)
        for pid in (0, 1):
            units = [t for t in area.get('troops', []) if t.get('player') == pid]
            if len(units) > capacity:
                result.append({'area_idx': area_idx, 'player_id': pid, 'excess': len(units) - capacity})
    return result


def _resolve_post_moves(state, pa, player_id):
    tile_key = pa['tile_key']
    contested_idx = find_contested_area(state, tile_key, player_id)

    if contested_idx is not None:
        pa['contest_area_idx'] = contested_idx
        pa['step'] = 'combat_declare'
        pa['instruction'] = f'Выберите победителя боя в области {contested_idx}.'
        return

    overflow = _find_overflow_areas(state, tile_key, player_id)
    if overflow:
        pa['step'] = 'capacity_overflow'
        pa['overflow_areas'] = overflow
        pa['overflow_player'] = player_id
        pa['overflow_context'] = 'pre_combat'
        pa['instruction'] = 'Превышена вместимость. Выберите юнита для возврата в запас.'
        return

    active_tile = state['map'][tile_key]
    orbital_ships = [
        idx for idx, area in enumerate(active_tile.get('areas', []))
        if area.get('type') == 'space' and
           any(t.get('player') == player_id and t.get('unitType') == 'space'
               for t in area.get('troops', []))
    ]

    if orbital_ships:
        pa['step'] = 'orbital'
        pa['orbital_ships'] = orbital_ships
        pa['instruction'] = 'Выберите корабль и целевую планету для орбитального удара или пропустите.'
    else:
        pa['instruction'] = 'Движение завершено.'
        finalize_advance(state, player_id)


def advance_remove_overflow_unit(state, player_id, area_idx, unit_idx) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa:
        raise ValueError("Нет активного приказа Advance")
    overflow_player = pa.get('overflow_player', pa['player_id'])
    if player_id not in (pa['player_id'], overflow_player):
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'capacity_overflow':
        raise ValueError(f"Удаление юнита доступно только на шаге capacity_overflow (текущий: {pa['step']})")

    tile_key = pa['tile_key']
    area = new_state['map'][tile_key]['areas'][area_idx]
    troops = area.get('troops', [])

    friendly = [(i, t) for i, t in enumerate(troops) if t.get('player') == overflow_player]
    if unit_idx < 0 or unit_idx >= len(friendly):
        raise ValueError(f"Нет юнита с индексом {unit_idx} в области {area_idx}")

    actual_idx, removed = friendly[unit_idx]
    troops.pop(actual_idx)
    new_state['players'][overflow_player].setdefault('pool', []).append(removed)

    overflow_context = pa.get('overflow_context', 'pre_combat')
    if overflow_context == 'post_retreat':
        overflow_all = _find_all_overflow_areas(new_state, tile_key)
        if overflow_all:
            first = overflow_all[0]
            pa['overflow_areas'] = [{'area_idx': first['area_idx'], 'excess': first['excess']}]
            pa['overflow_player'] = first['player_id']
            pa['instruction'] = 'Превышена вместимость. Выберите юнита для возврата в запас.'
        else:
            pa.pop('overflow_areas', None)
            pa['instruction'] = 'Отступление завершено. Advance окончен.'
            finalize_advance(new_state, pa['player_id'])
    else:
        overflow = _find_overflow_areas(new_state, tile_key, overflow_player)
        if overflow:
            pa['overflow_areas'] = overflow
            pa['instruction'] = 'Превышена вместимость. Выберите юнита для возврата в запас.'
        else:
            pa.pop('overflow_areas', None)
            _resolve_post_moves(new_state, pa, pa['player_id'])

    return new_state
