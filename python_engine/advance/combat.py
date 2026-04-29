import copy
import random
from .discovery import get_tile_area_neighbors, get_adjacent_tile_keys
from ..map_graph import build_graph
from .finalize import finalize_advance
from .capacity import _find_all_overflow_areas
from .retreat_defender import retreat_defender
from .retreat_attacker import retreat_attacker


def roll_combat(state, active_tile_key, area_idx, player_id):
    active_tile = state['map'][active_tile_key]
    area = active_tile['areas'][area_idx]
    opponent = 1 - player_id

    player_units = [t for t in area['troops'] if t.get('player') == player_id]
    opponent_units = [t for t in area['troops'] if t.get('player') == opponent]

    player_rolls = [random.randint(1, 6) for _ in player_units]
    opponent_rolls = [random.randint(1, 6) for _ in opponent_units]

    player_total = sum(player_rolls)
    opponent_total = sum(opponent_rolls)

    if player_total > opponent_total:
        winner = player_id
        loser = opponent
    elif opponent_total > player_total:
        winner = opponent
        loser = player_id
    else:
        winner = None
        loser = None

    remaining_troops = []
    removed = []
    for troop in area['troops']:
        if winner is None:
            removed.append(troop)
        elif troop.get('player') == loser:
            removed.append(troop)
        else:
            remaining_troops.append(troop)

    area['troops'] = remaining_troops

    for troop in removed:
        p_id = troop.get('player')
        if p_id is not None and p_id < len(state['players']):
            state['players'][p_id].setdefault('pool', []).append(troop)

    if winner is None:
        result_str = f"Ничья ({player_total} vs {opponent_total}). Обе стороны теряют всех юнитов."
    else:
        result_str = f"Игрок {winner} победил ({player_total if winner == player_id else opponent_total} vs {opponent_total if winner == player_id else player_total}). Игрок {loser} теряет всех юнитов."

    return {
        'winner': winner,
        'rolls': {player_id: player_rolls, opponent: opponent_rolls},
        'totals': {player_id: player_total, opponent: opponent_total},
        'log': f"БОЙ в области {area_idx} тайла {active_tile_key}: {result_str}",
    }


def _get_retreat_valid_areas(state, tile_key, contested_idx, loser) -> dict:
    game_map = state.get('map', {})
    active_tile = game_map.get(tile_key, {})
    areas_list = active_tile.get('areas', [])
    opponent = 1 - loser

    contested_type = areas_list[contested_idx].get('type') if contested_idx < len(areas_list) else 'space'
    print(f"\n[RETREAT] Место битвы: {tile_key}:{contested_idx}, тип: {contested_type}, проигравший: игрок {loser}")

    graph = build_graph(game_map, state.get('warpStorms', []))
    start_id = f"{tile_key}:{contested_idx}"
    allowed_tiles = {tile_key} | set(get_adjacent_tile_keys(tile_key))
    print(f"[RETREAT] Разрешённые системы: {allowed_tiles}")

    if contested_type == 'space':
        # Космос: любая космическая область в активной или соседней системе
        candidates = [
            (node['tile_key'], node['area_idx'])
            for nid, node in graph.items()
            if node['tile_key'] in allowed_tiles
            and node['type'] == 'space'
            and nid != start_id
        ]
        print(f"[RETREAT] Космос — кандидаты ({len(candidates)}): {candidates}")
    else:
        # Планета: BFS из места битвы через дружественные области
        visited = {start_id}
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            node = graph.get(current)
            if not node:
                continue
            for nb_id in node['neighbors']:
                if nb_id in visited:
                    continue
                nb_node = graph.get(nb_id)
                if not nb_node:
                    continue
                if nb_node['tile_key'] not in allowed_tiles:
                    continue
                nb_areas = game_map.get(nb_node['tile_key'], {}).get('areas', [])
                nb_area = nb_areas[nb_node['area_idx']] if nb_node['area_idx'] < len(nb_areas) else {}
                has_loser = (
                    any(t.get('player') == loser for t in nb_node['troops']) or
                    any(s.get('player') == loser for s in nb_area.get('structures', []))
                )
                if has_loser:
                    visited.add(nb_id)
                    queue.append(nb_id)

        reachable = visited - {start_id}
        print(f"[RETREAT] Планета — достижимые через дружественные ({len(reachable)}): {reachable}")

        # Кандидаты: дружественные планетные области + планеты соседние с кораблями
        candidate_set = set()
        for nid in visited:
            if nid == start_id:
                continue
            node = graph.get(nid)
            if not node:
                continue
            if node['type'] != 'space':
                candidate_set.add((node['tile_key'], node['area_idx']))
            else:
                # Из космической области с кораблями достижимы соседние планеты
                for nb_id in node['neighbors']:
                    nb_node = graph.get(nb_id)
                    if not nb_node or nb_id == start_id:
                        continue
                    if nb_node['tile_key'] not in allowed_tiles:
                        continue
                    if nb_node['type'] != 'space':
                        candidate_set.add((nb_node['tile_key'], nb_node['area_idx']))

        candidates = list(candidate_set)
        print(f"[RETREAT] Планета — кандидаты без космоса ({len(candidates)}): {candidates}")

    # Делим на дружественные / нейтральные, исключаем занятые врагом
    friendly = []
    neutral = []
    for (tk, ai) in candidates:
        tile = game_map.get(tk, {})
        tile_areas = tile.get('areas', [])
        if ai >= len(tile_areas):
            continue
        area = tile_areas[ai]
        troops = area.get('troops', [])
        structures = area.get('structures', [])
        if any(t.get('player') == opponent for t in troops):
            continue
        has_loser = (
            any(t.get('player') == loser for t in troops) or
            any(s.get('player') == loser for s in structures)
        )
        if has_loser:
            friendly.append((tk, ai))
        elif not troops:
            neutral.append((tk, ai))

    print(f"[RETREAT] Дружественные: {friendly}")
    print(f"[RETREAT] Нейтральные: {neutral}")

    return {'friendly': friendly, 'neutral': neutral}


def advance_fight(state, player_id) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'combat':
        raise ValueError(f"Бой доступен только на шаге combat (текущий: {pa['step']})")

    tile_key = pa['tile_key']
    area_idx = pa.get('contest_area_idx')

    if area_idx is None:
        raise ValueError("Нет спорной области для боя")

    result = roll_combat(new_state, tile_key, area_idx, player_id)
    new_state.setdefault('log', []).append({'message': result['log'], 'player_id': player_id})

    active_tile = new_state['map'][tile_key]
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
        pa['instruction'] = 'Бой завершён. Движение окончено.'
        finalize_advance(new_state, player_id)

    return new_state


def advance_declare_winner(state, player_id, winner_id) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'combat_declare':
        raise ValueError(f"Объявление победителя доступно только на шаге combat_declare (текущий: {pa['step']})")

    if winner_id not in (0, 1):
        raise ValueError("winner_id должен быть 0 или 1")

    loser = 1 - winner_id
    pa['combat_winner'] = winner_id
    pa['combat_loser'] = loser

    winner_name = new_state['players'][winner_id].get('name', f'Игрок {winner_id}')
    loser_name = new_state['players'][loser].get('name', f'Игрок {loser}')

    tile_key = pa['tile_key']
    contested_idx = pa['contest_area_idx']
    active_tile = new_state['map'][tile_key]

    retreat_info = _get_retreat_valid_areas(new_state, tile_key, contested_idx, loser)
    friendly_areas = retreat_info['friendly']
    neutral_areas = retreat_info['neutral']
    retreat_areas = friendly_areas if friendly_areas else neutral_areas

    new_state.setdefault('log', []).append({
        'message': f'БОЙ в области {contested_idx} тайла {tile_key}: победил {winner_name}. {loser_name} отступает.',
        'player_id': player_id,
    })

    if not retreat_areas:
        contested_area = active_tile['areas'][contested_idx]
        loser_units = [t for t in contested_area.get('troops', []) if t.get('player') == loser]
        contested_area['troops'] = [t for t in contested_area.get('troops', []) if t.get('player') != loser]
        for unit in loser_units:
            new_state['players'][loser].setdefault('pool', []).append(unit)
        new_state['log'].append({
            'message': f'{loser_name} не имеет куда отступить — юниты уничтожены.',
            'player_id': player_id,
        })
        pa['instruction'] = 'Бой завершён. Advance окончен.'
        finalize_advance(new_state, player_id)
    else:
        pa['step'] = 'combat_retreat'
        pa['retreat_valid_areas'] = retreat_areas
        retreat_type = 'дружественную' if friendly_areas else 'нейтральную'
        pa['instruction'] = f'Выберите {retreat_type} область для отступления ({loser_name}). Кликните по области на карте.'

    return new_state


def advance_retreat(state, player_id, retreat_tile_key, retreat_area_idx) -> dict:
    new_state = copy.deepcopy(state)
    pa = new_state.get('pending_advance')

    if not pa or pa['player_id'] != player_id:
        raise ValueError("Нет активного приказа Advance для этого игрока")

    if pa['step'] != 'combat_retreat':
        raise ValueError(f"Отступление доступно только на шаге combat_retreat (текущий: {pa['step']})")

    loser = pa['combat_loser']
    opponent = 1 - player_id

    if loser == opponent:
        return retreat_defender(new_state, player_id, retreat_tile_key, retreat_area_idx)
    else:
        return retreat_attacker(new_state, player_id, retreat_tile_key, retreat_area_idx)
