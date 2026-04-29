import copy
from .finalize import finalize_advance


def advance_orbital(state, player_id, ship_area_idx, target_area_idx) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'orbital':
        raise ValueError(f"Орбитальный удар доступен только на шаге orbital (текущий: {pa['step']})")

    tile_key = pa['tile_key']
    active_tile = new_state['map'][tile_key]

    if ship_area_idx >= len(active_tile['areas']):
        raise ValueError(f"Область {ship_area_idx} не существует")

    ship_area = active_tile['areas'][ship_area_idx]
    if ship_area.get('type') != 'space':
        raise ValueError(f"Область {ship_area_idx} не является космосом")

    has_ship = any(t.get('player') == player_id and t.get('unitType') == 'space'
                   for t in ship_area.get('troops', []))
    if not has_ship:
        raise ValueError(f"У вас нет корабля в области {ship_area_idx}")

    if target_area_idx >= len(active_tile['areas']):
        raise ValueError(f"Область {target_area_idx} не существует")

    target_area = active_tile['areas'][target_area_idx]
    if target_area.get('type') != 'planet':
        raise ValueError(f"Область {target_area_idx} не является планетой")

    opponent = 1 - player_id
    enemy_units = [t for t in target_area.get('troops', []) if t.get('player') == opponent]
    if not enemy_units:
        raise ValueError(f"На планете {target_area_idx} нет вражеских юнитов")

    pa['orbital_ship_area'] = ship_area_idx
    pa['orbital_target_area'] = target_area_idx
    pa['step'] = 'orbital_defend'
    pa['instruction'] = 'Защищающийся игрок выбирает, какого юнита потерять.'

    return new_state


def advance_orbital_remove(state, defender_player_id, area_idx, unit_idx) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa:
        raise ValueError("Нет активного приказа Advance")

    if pa['step'] != 'orbital_defend':
        raise ValueError(f"Удаление юнита доступно только на шаге orbital_defend (текущий: {pa['step']})")

    attacker = pa['player_id']
    if defender_player_id != (1 - attacker):
        raise ValueError("Это не ваша очередь удалять юнита")

    tile_key = pa['tile_key']
    target_area_idx = pa.get('orbital_target_area')

    if area_idx != target_area_idx:
        raise ValueError(f"Юнит должен быть удален из области {target_area_idx}")

    active_tile = new_state['map'][tile_key]
    target_area = active_tile['areas'][target_area_idx]

    troops = target_area['troops']
    defender_units = [i for i, t in enumerate(troops) if t.get('player') == defender_player_id]

    if unit_idx not in defender_units:
        raise ValueError(f"Юнит {unit_idx} не принадлежит защищающемуся игроку")

    removed_unit = troops.pop(unit_idx)
    new_state['players'][defender_player_id].setdefault('pool', []).append(removed_unit)

    new_state.setdefault('log', []).append({
        'message': f"Орбитальный удар: игрок {defender_player_id} потерял юнита на планете {target_area_idx}",
        'player_id': attacker
    })

    finalize_advance(new_state, attacker)
    return new_state


def advance_skip_orbital(state, player_id) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'orbital':
        raise ValueError(f"Пропуск орбитального удара доступен только на шаге orbital (текущий: {pa['step']})")

    pa['instruction'] = 'Орбитальный удар пропущен. Движение завершено.'
    finalize_advance(new_state, player_id)
    return new_state
