import copy
from .capacity import _find_all_overflow_areas_global
from .finalize import finalize_advance


def retreat_defender(state, player_id, retreat_tile_key, retreat_area_idx) -> dict:
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
        'message': f'{loser_name} (защитник) отступил в область {retreat_area_idx} ({len(loser_units)} юн.). Статус: разбит.',
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
