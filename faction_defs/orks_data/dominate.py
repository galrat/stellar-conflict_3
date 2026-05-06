"""faction_defs/orks_data/dominate.py — особое свойство Dominate фракции Orks."""

import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_DIR))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_UNIT_TYPE_MAP = {
    'infantry':   ('ground', 0),
    'marines':    ('ground', 1),
    'mechanized': ('ground', 2),
    'elite':      ('ground', 3),
    'fighter':    ('space',  0),
    'destroyer':  ('space',  2),
}

ORKS_CAPACITY = 1


def _friendly_areas(areas, player_id):
    """Области без соперника И с хотя бы одним юнитом/постройкой игрока."""
    opponent = 1 - player_id
    result = {}
    for i, area in enumerate(areas):
        if any(t['player'] == opponent for t in area.get('troops', [])):
            continue
        if any(s.get('player') == opponent for s in area.get('structures', [])):
            continue
        has_unit   = any(t.get('player') == player_id for t in area.get('troops', []))
        has_struct = any(s.get('player') == player_id for s in area.get('structures', []))
        if has_unit or has_struct:
            result[i] = area
    return result


def _has_friendly_planets(state, player_id, tile_key):
    tile = state.get('map', {}).get(tile_key)
    if not tile:
        return False
    for area in tile.get('areas', []):
        if area.get('type') != 'planet':
            continue
        has_unit   = any(t.get('player') == player_id for t in area.get('troops', []))
        has_struct = any(s.get('player') == player_id for s in area.get('structures', []))
        if has_unit or has_struct:
            return True
    return False


def _get_deploy_info(state, player_id, tile_key):
    from python_engine.deploy import _analyze_tile, _compute_pool, _unit_forge_cost
    from faction_defs import FACTIONS

    faction_id   = state['players'][player_id]['faction']
    uc           = FACTIONS[faction_id].unit_config
    player       = state['players'][player_id]
    tokens       = player.get('tokens', {})
    forge_tokens = tokens.get('forge', 0)
    cash_tokens  = tokens.get('discount', 0)
    credits      = player.get('credits', 0)

    tile_info  = _analyze_tile(state, tile_key, player_id)
    pool_count = _compute_pool(state, uc, player_id)
    areas      = tile_info['areas']
    city_count = tile_info['city_count']
    avail_areas = _friendly_areas(areas, player_id)

    unit_type_tier_map = {}
    unit_catalog = []
    for unit_key, stats in uc.unit_stats.items():
        if unit_key not in _UNIT_TYPE_MAP:
            continue
        unit_type, tier = _UNIT_TYPE_MAP[unit_key]
        unit_type_tier_map[f'{unit_type},{tier}'] = unit_key
        in_pool          = pool_count.get((unit_type, tier), 0)
        tier_gap         = max(0, tier - city_count)
        needs_tier_forge = tier_gap == 1 and forge_tokens >= 1
        can_buy_tier     = tier <= city_count or needs_tier_forge
        available        = in_pool > 0 and can_buy_tier

        reason = None
        if in_pool == 0:
            reason = f'Нет в пуле (макс {stats["max_count"]})'
        elif not can_buy_tier:
            if tier_gap > 1:
                reason = f'Требуется {tier} городов (есть {city_count})'
            elif tier_gap == 1:
                reason = 'Требуется forge для этого уровня'
            else:
                reason = 'Недоступен'

        total_forge_cost = (1 if needs_tier_forge else 0) + stats.get('cost_forge', 0)

        unit_catalog.append({
            'unit_key':         unit_key,
            'name':             stats['name'],
            'unitType':         unit_type,
            'tier':             tier,
            'cost':             stats['cost'],
            'cost_forge':       stats.get('cost_forge', 0),
            'total_forge_cost': total_forge_cost,
            'max_count':        stats['max_count'],
            'pool_available':   in_pool,
            'available':        available,
            'reason':           reason,
            'lock_reason':      reason,
        })

    return {
        'unit_catalog':       unit_catalog,
        'unit_type_tier_map': unit_type_tier_map,
        'capacity':           ORKS_CAPACITY,
        'credits':            credits,
        'forge_tokens':       forge_tokens,
        'cash_tokens':        cash_tokens,
        'city_count':         city_count,
        'available_areas': [
            {
                'idx':           i,
                'type':          a['type'],
                'capacity':      a['capacity'],
                'current_units': len(a.get('troops', [])),
            }
            for i, a in avail_areas.items()
        ],
    }


def _validate_basket(state, player_id, basket):
    from python_engine.deploy import _analyze_tile, _compute_pool, _unit_forge_cost
    from faction_defs import FACTIONS

    faction_id   = state['players'][player_id]['faction']
    uc           = FACTIONS[faction_id].unit_config
    player       = state['players'][player_id]
    tokens       = player.get('tokens', {})
    credits      = player.get('credits', 0)
    forge_tokens = tokens.get('forge', 0)
    cash_tokens  = tokens.get('discount', 0)
    pool_count   = _compute_pool(state, uc, player_id)

    pending    = state.get('pending_orks_dominate', {})
    tile_key   = pending.get('tile_key', '')
    city_count = 0
    if tile_key:
        tile_info  = _analyze_tile(state, tile_key, player_id)
        city_count = tile_info.get('city_count', 0)

    errors        = []
    total_credits = 0
    forge_spent   = 0
    cash_spent    = 0
    basket_pool   = {}

    if len(basket) > ORKS_CAPACITY:
        errors.append(f'Можно купить максимум {ORKS_CAPACITY} юнита')

    for item in basket:
        unit_key = item.get('unit_key')
        use_cash = item.get('use_cash', False)
        stats    = uc.unit_stats.get(unit_key)
        if stats is None:
            errors.append(f'Неизвестный юнит: {unit_key}')
            continue
        if unit_key not in _UNIT_TYPE_MAP:
            errors.append(f'Юнит {unit_key} не поддерживается')
            continue

        _, tier  = _UNIT_TYPE_MAP[unit_key]
        tier_gap = max(0, tier - city_count)
        ft, fc   = _unit_forge_cost(unit_key, city_count, stats)

        if tier_gap > 1:
            errors.append(f'{stats["name"]}: тир недоступен')

        forge_spent   += ft + fc
        cash_spent    += int(use_cash)
        total_credits += stats['cost'] - (2 if use_cash else 0)
        basket_pool[unit_key] = basket_pool.get(unit_key, 0) + 1

    total_credits = max(0, total_credits)

    if cash_spent > cash_tokens:
        errors.append(f'Не хватает cash токенов: нужно {cash_spent}, есть {cash_tokens}')
    if forge_spent > forge_tokens:
        errors.append(f'Не хватает forge: нужно {forge_spent}, есть {forge_tokens}')
    if total_credits > credits:
        errors.append(f'Не хватает кредитов: нужно {total_credits}, есть {credits}')

    for unit_key, count in basket_pool.items():
        unit_type, tier = _UNIT_TYPE_MAP[unit_key]
        available = pool_count.get((unit_type, tier), 0)
        if count > available:
            errors.append(f'{uc.unit_stats[unit_key]["name"]}: в пуле {available}, куплено {count}')

    costs = {'credits': total_credits, 'forge': forge_spent, 'cash': cash_spent}
    return len(errors) == 0, errors, costs


def maybe_start(state, player_id, tile_key):
    if not _has_friendly_planets(state, player_id, tile_key):
        return
    state['pending_orks_dominate'] = {
        'player_id':        player_id,
        'tile_key':         tile_key,
        'step':             'ask',
        'deploy_info':      _get_deploy_info(state, player_id, tile_key),
        'hand':             [],
        'placed':           [],
        'removed_from_map': [],
        'unit_costs':       {},
    }


def handle_ask_yes(state, player_id):
    pending = state.get('pending_orks_dominate')
    if not pending or pending.get('player_id') != player_id:
        return False, 'Нет ожидающей способности Orks'
    if pending['step'] != 'ask':
        return False, 'Неверный шаг'
    pending['deploy_info'] = _get_deploy_info(state, player_id, pending['tile_key'])
    pending['step'] = 'buy_unit'
    return True, 'Orks: переход к покупке юнита'


def handle_skip(state, player_id):
    pending = state.get('pending_orks_dominate')
    if not pending or pending.get('player_id') != player_id:
        return False, 'Нет ожидающей способности Orks'
    state.pop('pending_orks_dominate', None)
    return True, 'Orks: особое свойство доминации пропущено'


def handle_confirm_basket(state, player_id, basket):
    pending = state.get('pending_orks_dominate')
    if not pending or pending.get('player_id') != player_id:
        return False, 'Нет ожидающей способности Orks', None
    if pending['step'] != 'buy_unit':
        return False, 'Неверный шаг', None

    if not basket:
        state.pop('pending_orks_dominate', None)
        return True, 'Orks: покупка пропущена', state

    ok, errors, costs = _validate_basket(state, player_id, basket)
    if not ok:
        return False, '; '.join(errors), None

    pending['hand']       = [item['unit_key'] for item in basket]
    pending['unit_costs'] = costs
    pending['step']       = 'place_unit'
    return True, 'Orks: юнит куплен', state


def handle_place_unit(state, player_id, unit_key, area_idx):
    from python_engine.deploy import validate_place_unit_for_state
    pending = state.get('pending_orks_dominate')
    if not pending or pending.get('player_id') != player_id:
        return False, 'Нет ожидающей способности Orks', None
    if pending['step'] != 'place_unit':
        return False, 'Неверный шаг', None

    tile_key = pending['tile_key']
    hand     = pending['hand']
    placed   = pending['placed']

    ok, error, overflow = validate_place_unit_for_state(
        state, player_id, tile_key, hand, placed, unit_key, area_idx
    )
    if not ok:
        return False, error, None

    areas = state['map'][tile_key]['areas']
    friendly = _friendly_areas(areas, player_id)
    if area_idx not in friendly:
        return False, 'Orks Dominate: размещение только в дружественной области', None

    pending['placed'] = placed + [{'unit_key': unit_key, 'area_idx': area_idx}]

    if overflow:
        pending['step'] = 'resolve_overflow'
    else:
        hand_rem = list(hand)
        for p in pending['placed']:
            if p['unit_key'] in hand_rem:
                hand_rem.remove(p['unit_key'])
        if not hand_rem:
            _apply_and_finish(state, player_id)

    return True, 'Orks: юнит размещён', state


def handle_undo_place(state, player_id):
    pending = state.get('pending_orks_dominate')
    if not pending or pending.get('player_id') != player_id:
        return False, 'Нет ожидающей способности Orks'
    placed = pending.get('placed', [])
    if not placed:
        return False, 'Нечего отменять'
    pending['placed'] = placed[:-1]
    pending['step']   = 'place_unit'
    return True, 'Orks: последнее размещение отменено'


def handle_resolve_overflow(state, player_id, remove_area_idx, remove_unit_key):
    from python_engine.deploy import validate_and_remove_overflow
    pending = state.get('pending_orks_dominate')
    if not pending or pending.get('player_id') != player_id:
        return False, 'Нет ожидающей способности Orks', None
    if pending['step'] != 'resolve_overflow':
        return False, 'Неверный шаг', None

    tile_key = pending['tile_key']
    placed   = pending['placed']

    ok, error, new_placed, removed_from_map, overflow_after = validate_and_remove_overflow(
        state, player_id, tile_key, placed, remove_area_idx, remove_unit_key
    )
    if not ok:
        return False, error, None

    pending['placed'] = new_placed
    if removed_from_map:
        pending['removed_from_map'] = pending.get('removed_from_map', []) + [
            {'unit_key': remove_unit_key, 'area_idx': remove_area_idx}
        ]

    if not overflow_after:
        hand_rem = list(pending['hand'])
        for p in new_placed:
            if p['unit_key'] in hand_rem:
                hand_rem.remove(p['unit_key'])
        if not hand_rem:
            _apply_and_finish(state, player_id)
        else:
            pending['step'] = 'place_unit'

    return True, 'Orks: overflow разрешён', state


def _apply_and_finish(state, player_id):
    from python_engine.deploy import apply_deploy_to_state
    pending = state.pop('pending_orks_dominate')
    apply_deploy_to_state(
        state,
        player_id,
        pending['tile_key'],
        pending['placed'],
        pending.get('unit_costs', {}),
        building=None,
        removed_from_map=pending.get('removed_from_map', []),
    )
