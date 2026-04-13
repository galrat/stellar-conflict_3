# после открытия приказа deploy я должен попасть сюда

import json
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(_DIR) not in sys.path:
    sys.path.insert(0, os.path.dirname(_DIR))


def deploy_order(previous_state):
    '''
    previous_state - состояние state на момент открытия приказа, его нужно сохранить чтобы можно было сделать отмену

    в ходе приказа deploy нужно
    1. определить систему где открыт приказ,
    2. определить есть ли factory у игрока в этой системе и в какой области системы находится одна или больше factory
    3. если factory есть, то реализуется функция постройки юнитов, если factory нет, то реализуется функция постройки зданий.
    4. как построить юнитов - определить дружественные и нейтральные области в этой системе -
        те на которых нет юнитов или построек соперника
    5. определить сколько есть городов у пользователя на карте. общее количество городов равно уровню юнитов которые можно построить
    6. определить лимит постройки - capacity всех областей с factory то есть сумма этих capacity
    7. открыть окно покупки юнитов в окне должны быть показаны все юниты игрока с их уровнем и стоимостью с учетом денег и forge
    8. доступны для выбора должны быть только юниты уровня не выше количества городов, но если у пользователя есть forge
    то доступен +1 уровень, на компенсацию нехватки которого потребуется forge
    8. Дать игроку набрать корзину юнитов, под каждым юнитом в корзине должна быть галочка стоимости в деньгах, галочка использования
    одного cash токена, который дает скидку в 2 монеты, галочка использования forge, причем forge может понадобиться как для постройки юнита,
    так и для компенсации нехватки уровня. Использовать можно только 1 forge для компенсации нехватки уровня.
    когда все юниты оплачены активируется кнопка КУПИТЬ ЮНИТОВ, пользователь нажимает на кнопку КУПИТЬ, и размещает купленных юнитов
    9. юниты размещаются в ружественных областях, наземные на планетах, корабли в космосе.
    10. далее проверяется лимит вместимости каждой области, если в какой-то области юнитов слишком много
    то для каждой такой области открывается окошко выбора какой юнит нужно вернуть в запас.
    Любым образом уничтоженные юниты возвращаются в запас игрока
    11. далее появляется окошко покупки зданий factory bastion city точно такое же как и окошко покупки юнитов
    12 после покупки здания оно размещается на дружественной планете системы с приказом без других построек. заменить постройку нельзя.
    если для купленной постройки нет места, то об этом должно быть сообщение на этапе покупки и после нажатия кнопки ОК окошко покупки закрывается

    13. Если фабрики в системе не было на момент открытие приказа deploy то можно построить только здание
    14. при покупке юнитов нужно также указать сколько их доступно в запасе, нельзя купить больше юнитов чем есть в запасе.
    '''
    return None  # заглушка — реализация ниже по шагам


# =============================================================
# Общие константы и хелперы
# =============================================================

_UNIT_TYPE_MAP = {
    'infantry':   ('ground', 0),
    'marines':    ('ground', 1),
    'mechanized': ('ground', 2),
    'elite':      ('ground', 3),
    'fighter':    ('space',  0),
    'destroyer':  ('space',  2),
}
_KEY_BY_TYPE_TIER = {v: k for k, v in _UNIT_TYPE_MAP.items()}

STRUCTURE_COSTS = {'factory': 2, 'bastion': 2, 'city': 3}
STRUCTURE_MAX_COUNT = 9  # резерв каждого типа постройки на игрока


def _compute_structure_pool(state, player_id):
    """Пул построек = STRUCTURE_MAX_COUNT - количество на карте. Возвращает {type: count}."""
    on_map = {}
    for tile in state['map'].values():
        for area in tile['areas']:
            for s in area.get('structures', []):
                if s.get('player') == player_id:
                    t = s['type']
                    on_map[t] = on_map.get(t, 0) + 1
    return {stype: max(0, STRUCTURE_MAX_COUNT - on_map.get(stype, 0))
            for stype in STRUCTURE_COSTS}


def _load_state():
    with open(os.path.join(_DIR, 'test.json'), encoding='utf-8') as f:
        return json.load(f)


def _load_faction(state, player_id):
    from faction_defs import FACTIONS
    return FACTIONS[state['players'][player_id]['faction']].unit_config


def _analyze_tile(state, tile_key, player_id):
    """factory_areas / capacity / city_count / areas одного тайла."""
    areas = state['map'][tile_key]['areas']
    factory_areas = [
        {'idx': i, 'area': a}
        for i, a in enumerate(areas)
        for s in a.get('structures', [])
        if s.get('type') == 'factory' and s.get('player') == player_id
    ]
    capacity = sum(fa['area']['capacity'] for fa in factory_areas)
    city_count = sum(
        1
        for t in state['map'].values()
        for a in t['areas']
        for s in a.get('structures', [])
        if s.get('type') == 'city' and s.get('player') == player_id
    )
    return {
        'areas':         areas,
        'factory_areas': factory_areas,
        'has_factory':   len(factory_areas) > 0,
        'capacity':      capacity,
        'city_count':    city_count,
    }


def _available_areas(areas, player_id, kind='any'):
    """
    kind:
      'any'         — дружественные/нейтральные области (нет войск/построек соперника)
      'planet_free' — только планеты без каких-либо построек
    Возвращает {idx: area}.
    """
    opponent = 1 - player_id
    result = {}
    for i, area in enumerate(areas):
        if any(t['player'] == opponent for t in area.get('troops', [])):
            continue
        if any(s.get('player') == opponent for s in area.get('structures', [])):
            continue
        if kind == 'planet_free':
            if area['type'] != 'planet' or area.get('structures'):
                continue
            # Только дружественные планеты: у игрока должны быть войска в этой области
            if not any(t.get('player') == player_id for t in area.get('troops', [])):
                continue
        result[i] = area
    return result


def _compute_pool(state, uc, player_id):
    """Пул = max_count минус юниты этого игрока на карте. Ключ: (unitType, tier)."""
    on_map = {}
    for t in state['map'].values():
        for a in t['areas']:
            for troop in a.get('troops', []):
                if troop.get('player') == player_id:
                    key = (troop['unitType'], troop['tier'])
                    on_map[key] = on_map.get(key, 0) + 1
    pool = {}
    for uk, st in uc.unit_stats.items():
        if uk not in _UNIT_TYPE_MAP:
            continue
        ut, ti = _UNIT_TYPE_MAP[uk]
        pool[(ut, ti)] = max(0, st.get('max_count', 0) - on_map.get((ut, ti), 0))
    return pool


def _load_context(tile_key, player_id):
    """Полный контекст шага: state, uc, тайл-метрики, ресурсы игрока, пул."""
    state     = _load_state()
    tile_info = _analyze_tile(state, tile_key, player_id)
    uc        = _load_faction(state, player_id)
    player    = state['players'][player_id]
    tokens    = player.get('tokens', {})
    return {
        'state':         state,
        'uc':            uc,
        'faction_id':    player['faction'],
        'areas':         tile_info['areas'],
        'factory_areas': tile_info['factory_areas'],
        'has_factory':   tile_info['has_factory'],
        'capacity':      tile_info['capacity'],
        'city_count':    tile_info['city_count'],
        'credits':       player.get('credits', 0),
        'forge_tokens':  tokens.get('forge', 0),
        'cash_tokens':   tokens.get('discount', 0),  # ключ в state исторически 'discount'
        'pool_count':    _compute_pool(state, uc, player_id),
    }


def _unit_forge_cost(unit_key, city_count, stats):
    """Сколько forge нужно за этого юнита: за тир + за стоимость."""
    _, tier    = _UNIT_TYPE_MAP[unit_key]
    tier_gap   = max(0, tier - city_count)
    forge_tier = 1 if tier_gap == 1 else 0
    forge_cost = stats.get('cost_forge', 0)
    return forge_tier, forge_cost


# =============================================================
# ШАГ 1: Анализ тайла
# =============================================================

def step1_analyze_tile():
    # --- входные данные (менять для теста) ---
    tile_key  = '0,0'
    player_id = 0
    # -----------------------------------------

    state = _load_state()
    t     = _analyze_tile(state, tile_key, player_id)
    avail = _available_areas(t['areas'], player_id)

    print(f'=== Deploy Step 1: тайл {tile_key}, игрок {player_id} ===')
    print(f'Фабрика есть: {t["has_factory"]}')
    if t['factory_areas']:
        print(f'  Области с factory: {[fa["idx"] for fa in t["factory_areas"]]}')
    print(f'Лимит постройки (capacity factory): {t["capacity"]}')
    print(f'Городов на карте (tier limit): {t["city_count"]}')
    print(f'Доступных областей для юнитов: {len(avail)}')
    for i, a in avail.items():
        print(f'  area[{i}] type={a["type"]} capacity={a["capacity"]} юнитов={len(a.get("troops", []))}')


# =============================================================
# ШАГ 2: Доступные юниты для покупки
# =============================================================

def step2_available_units():
    # --- входные данные (менять для теста) ---
    tile_key  = '0,0'
    player_id = 0
    # -----------------------------------------

    ctx = _load_context(tile_key, player_id)
    uc  = ctx['uc']

    unit_catalog = []
    for unit_key, stats in uc.unit_stats.items():
        if unit_key not in _UNIT_TYPE_MAP:
            continue
        unit_type, tier = _UNIT_TYPE_MAP[unit_key]
        in_pool   = ctx['pool_count'].get((unit_type, tier), 0)
        cost_forge = stats.get('cost_forge', 0)

        tier_gap         = max(0, tier - ctx['city_count'])
        needs_tier_forge = tier_gap == 1 and ctx['forge_tokens'] >= 1
        can_buy_tier     = tier <= ctx['city_count'] or needs_tier_forge
        can_buy          = in_pool > 0 and can_buy_tier

        unit_catalog.append({
            'unit_key':         unit_key,
            'name':             stats['name'],
            'unitType':         unit_type,
            'tier':             tier,
            'cost':             stats['cost'],
            'cost_forge':       cost_forge,
            'max_count':        stats['max_count'],
            'pool_available':   in_pool,
            'needs_tier_forge': needs_tier_forge,
            'can_buy_tier':     can_buy_tier,
            'can_buy':          can_buy,
        })

    print(f'=== Deploy Step 2: юниты игрока {player_id} ({ctx["faction_id"]}) ===')
    print(f'Фабрика: {ctx["has_factory"]}  |  city_count (tier_limit): {ctx["city_count"]}  '
          f'|  forge: {ctx["forge_tokens"]}  |  credits: {ctx["credits"]}')
    print()

    if not ctx['has_factory']:
        print('Фабрики нет — покупка юнитов недоступна')
        return []

    for u in unit_catalog:
        tier_note  = ' [+1 forge на тир]' if u['needs_tier_forge'] else ''
        forge_note = f' +{u["cost_forge"]} forge' if u['cost_forge'] else ''
        if u['can_buy']:
            status = 'ДОСТУПЕН'
        elif not u['can_buy_tier']:
            status = 'тир недоступен'
        else:
            status = 'нет в пуле'
        print(
            f'  [{u["unitType"]:6s} T{u["tier"]}] {u["name"]:<25s} '
            f'cost={u["cost"]}{forge_note}{tier_note}  '
            f'пул={u["pool_available"]}/{u["max_count"]}  -> {status}'
        )

    purchasable = [u for u in unit_catalog if u['can_buy']]
    print(f'\nДоступно для покупки: {len(purchasable)} типов юнитов')
    return purchasable


# =============================================================
# ШАГ 3: Корзина (добавление + подтверждение)
# =============================================================

def step3_add_unit():
    # --- входные данные (менять для теста) ---
    tile_key  = '0,0'
    player_id = 0

    current_basket = [
        {'unit_key': 'infantry', 'use_cash': False},
    ]

    unit_key = 'marines'
    use_cash = True
    # -----------------------------------------

    ctx = _load_context(tile_key, player_id)
    uc  = ctx['uc']

    stats = uc.unit_stats.get(unit_key)
    if stats is None:
        print(f'ОШИБКА: юнит {unit_key} недоступен во фракции {ctx["faction_id"]}')
        return None

    _, tier                = _UNIT_TYPE_MAP[unit_key]
    tier_gap               = max(0, tier - ctx['city_count'])
    forge_tier, forge_cost = _unit_forge_cost(unit_key, ctx['city_count'], stats)

    warnings = []
    if tier_gap > 1:
        warnings.append(f'тир {tier} недоступен (city_count={ctx["city_count"]}, разница > 1)')
    cash_used_so_far = sum(1 for item in current_basket if item['use_cash'])
    if use_cash and cash_used_so_far >= ctx['cash_tokens']:
        warnings.append(f'не хватает cash токенов: уже использовано {cash_used_so_far}, есть {ctx["cash_tokens"]}')

    updated_basket = current_basket + [{'unit_key': unit_key, 'use_cash': use_cash}]

    print(f'=== Deploy Step 3a: добавление юнита в корзину ===')
    print(f'Добавляем: {stats["name"]} (tier={tier})')
    print(f'  Стоимость:    {stats["cost"]} кредитов')
    if forge_tier:  print(f'  Forge за тир: {forge_tier}')
    if forge_cost:  print(f'  Forge за юнита: {forge_cost}')
    print(f'  Cash -2:      {"да" if use_cash else "нет"}')
    if warnings:
        print('  Предупреждения:')
        for w in warnings:
            print(f'    ! {w}')

    print(f'Корзина после добавления ({len(updated_basket)}/{ctx["capacity"]}):')
    for i, item in enumerate(updated_basket):
        s      = uc.unit_stats[item['unit_key']]
        ft, fc = _unit_forge_cost(item['unit_key'], ctx['city_count'], s)
        info   = []
        if ft:               info.append(f'forge(тир)={ft}')
        if fc:               info.append(f'forge(цена)={fc}')
        if item['use_cash']: info.append('cash')
        print(f'  [{i+1}] {s["name"]}  cost={s["cost"]}  {" | ".join(info) or "-"}')

    return updated_basket


def step3_confirm_basket():
    # --- входные данные (менять для теста) ---
    tile_key  = '0,0'
    player_id = 0

    basket = [
        {'unit_key': 'infantry', 'use_cash': True},
        {'unit_key': 'infantry', 'use_cash': False},
        {'unit_key': 'marines',  'use_cash': True},
    ]
    # -----------------------------------------

    ctx = _load_context(tile_key, player_id)
    uc  = ctx['uc']

    errors        = []
    total_credits = 0
    forge_spent   = 0
    cash_spent    = 0
    basket_pool   = {}

    for item in basket:
        unit_key = item['unit_key']
        stats    = uc.unit_stats.get(unit_key)
        if stats is None:
            errors.append(f'неизвестный юнит: {unit_key}')
            continue

        _, tier  = _UNIT_TYPE_MAP[unit_key]
        tier_gap = max(0, tier - ctx['city_count'])
        ft, fc   = _unit_forge_cost(unit_key, ctx['city_count'], stats)

        if tier_gap > 1:
            errors.append(f'{stats["name"]}: тир недоступен (разница > 1)')

        forge_spent   += ft + fc
        cash_spent    += int(item['use_cash'])
        total_credits += stats['cost'] - (2 if item['use_cash'] else 0)
        basket_pool[unit_key] = basket_pool.get(unit_key, 0) + 1

    total_credits = max(0, total_credits)

    if cash_spent > ctx['cash_tokens']:
        errors.append(f'не хватает cash токенов: нужно {cash_spent}, есть {ctx["cash_tokens"]}')
    if len(basket) > ctx['capacity']:
        errors.append(f'превышен capacity factory: {len(basket)} > {ctx["capacity"]}')
    for unit_key, count in basket_pool.items():
        unit_type, tier = _UNIT_TYPE_MAP[unit_key]
        available = ctx['pool_count'].get((unit_type, tier), 0)
        if count > available:
            errors.append(f'{uc.unit_stats[unit_key]["name"]}: в пуле {available}, куплено {count}')
    if forge_spent > ctx['forge_tokens']:
        errors.append(f'не хватает forge: нужно {forge_spent}, есть {ctx["forge_tokens"]}')
    if total_credits > ctx['credits']:
        errors.append(f'не хватает кредитов: нужно {total_credits}, есть {ctx["credits"]}')

    print(f'=== Deploy Step 3b: подтверждение корзины ({ctx["faction_id"]}) ===')
    for i, item in enumerate(basket):
        s      = uc.unit_stats[item['unit_key']]
        ft, fc = _unit_forge_cost(item['unit_key'], ctx['city_count'], s)
        info   = []
        if ft:               info.append(f'forge(тир)={ft}')
        if fc:               info.append(f'forge(цена)={fc}')
        if item['use_cash']: info.append('cash')
        print(f'  [{i+1}] {s["name"]}  cost={s["cost"]}  {" | ".join(info) or "-"}')
    print(f'Итого: {total_credits} кредитов  |  forge: {forge_spent}  |  cash токенов: {cash_spent}')
    print(f'Ресурсы: кредитов={ctx["credits"]}  forge={ctx["forge_tokens"]}  cash={ctx["cash_tokens"]}')
    print()
    if errors:
        print('ОШИБКИ:')
        for e in errors:
            print(f'  - {e}')
        print('ПОКУПКА НЕВОЗМОЖНА')
        return []

    bought = [item['unit_key'] for item in basket]
    print('ПОКУПКА ПОДТВЕРЖДЕНА')
    print(f'Юниты в руку: {bought}')
    print()
    print(f'Потрачено:  кредитов={total_credits}  forge={forge_spent}  cash={cash_spent}')
    print(f'Осталось:   кредитов={ctx["credits"] - total_credits}  '
          f'forge={ctx["forge_tokens"] - forge_spent}  cash={ctx["cash_tokens"] - cash_spent}')
    return bought


# =============================================================
# ШАГ 4: Размещение юнитов
# =============================================================

def _calc_area_counts(areas, placed_list):
    counts = {i: len(a.get('troops', [])) for i, a in enumerate(areas)}
    for p in placed_list:
        counts[p['area_idx']] = counts.get(p['area_idx'], 0) + 1
    return counts


def _overflow_areas(areas, counts):
    return {i: counts[i] for i, area in enumerate(areas) if counts[i] > area['capacity']}


def step4_place_unit():
    # --- входные данные (менять для теста) ---
    tile_key  = '0,0'
    player_id = 0

    hand = ['infantry', 'infantry', 'marines', 'marines']

    placed = [
        {'unit_key': 'infantry', 'area_idx': 0},
    ]

    unit_key = 'infantry'
    area_idx = 1
    # -----------------------------------------

    state = _load_state()
    uc    = _load_faction(state, player_id)
    areas = state['map'][tile_key]['areas']
    avail = _available_areas(areas, player_id)

    errors   = []
    warnings = []

    # юнит в руке с учётом уже размещённых
    hand_remaining = list(hand)
    for p in placed:
        if p['unit_key'] in hand_remaining:
            hand_remaining.remove(p['unit_key'])

    if unit_key not in hand_remaining:
        errors.append(f'{unit_key} нет в руке (уже размещён или не куплен)')

    if area_idx not in avail:
        errors.append(f'область {area_idx} недоступна (занята соперником или не существует)')
    else:
        area         = avail[area_idx]
        unit_type, _ = _UNIT_TYPE_MAP.get(unit_key, (None, None))
        expected     = 'planet' if unit_type == 'ground' else 'space'
        if area['type'] != expected:
            name = uc.unit_stats[unit_key]['name']
            need = 'planet' if unit_type == 'ground' else 'space'
            kind = 'наземный' if unit_type == 'ground' else 'космический'
            errors.append(f'{name} — {kind} юнит, нужна {need}')

    area_counts = _calc_area_counts(areas, placed)
    if not errors:
        area_counts[area_idx] = area_counts.get(area_idx, 0) + 1

    for i, area in enumerate(areas):
        if area_counts.get(i, 0) > area['capacity']:
            warnings.append(
                f'область {i} ({area["type"]}): {area_counts[i]} юнитов > capacity {area["capacity"]} — overflow!'
            )

    new_placed = placed + ([{'unit_key': unit_key, 'area_idx': area_idx}] if not errors else [])
    hand_after = list(hand)
    for p in new_placed:
        if p['unit_key'] in hand_after:
            hand_after.remove(p['unit_key'])

    print(f'=== Deploy Step 4: размещение юнита ===')
    if errors:
        print('ОШИБКИ:')
        for e in errors:
            print(f'  - {e}')
    else:
        print(f'Размещён: {uc.unit_stats[unit_key]["name"]} -> область {area_idx} ({areas[area_idx]["type"]})')

    print(f'\nОстаток в руке: {hand_after if hand_after else "все размещены"}')
    print(f'\nСостояние областей тайла {tile_key}:')
    for i, area in enumerate(areas):
        cap   = area['capacity']
        count = area_counts.get(i, 0)
        over  = ' <<OVERFLOW>>' if count > cap else ''
        mark  = 'доступна' if i in avail else 'недоступна'
        print(f'  area[{i}] {area["type"]:6s}  capacity={cap}  юнитов={count}{over}  [{mark}]')

    if warnings:
        print()
        for w in warnings:
            print(f'  ! {w}')

    return new_placed


# =============================================================
# ШАГ 5: Разрешение overflow
# =============================================================

def _area_player_units(area, player_id, placed_list, area_idx):
    """Все юниты игрока в области: map-юниты + placed-юниты (с пометкой source)."""
    result = []
    for t in area.get('troops', []):
        if t.get('player') != player_id:
            continue
        key = _KEY_BY_TYPE_TIER.get((t['unitType'], t['tier']))
        if key:
            result.append({'unit_key': key, 'source': 'map'})
    for p in placed_list:
        if p['area_idx'] == area_idx:
            result.append({'unit_key': p['unit_key'], 'source': 'placed'})
    return result


def step5_resolve_overflow():
    # --- входные данные (менять для теста) ---
    tile_key  = '0,0'
    player_id = 0

    placed = [
        {'unit_key': 'infantry', 'area_idx': 0},
        {'unit_key': 'infantry', 'area_idx': 0},
        {'unit_key': 'infantry', 'area_idx': 0},
        {'unit_key': 'marines',  'area_idx': 1},
    ]

    remove_area_idx = 0
    remove_unit_key = 'infantry'
    # -----------------------------------------

    state = _load_state()
    uc    = _load_faction(state, player_id)
    areas = state['map'][tile_key]['areas']

    counts_before   = _calc_area_counts(areas, placed)
    overflow_before = _overflow_areas(areas, counts_before)

    errors = []
    if remove_area_idx not in overflow_before:
        errors.append(f'область {remove_area_idx} не в overflow — убирать не нужно')
    else:
        all_in_area = _area_player_units(areas[remove_area_idx], player_id, placed, remove_area_idx)
        if not any(u['unit_key'] == remove_unit_key for u in all_in_area):
            errors.append(f'{remove_unit_key} не найден в области {remove_area_idx}')

    new_placed       = list(placed)
    removed_from_map = False
    if not errors:
        removed = False
        for i, p in enumerate(new_placed):
            if p['area_idx'] == remove_area_idx and p['unit_key'] == remove_unit_key:
                new_placed.pop(i)
                removed = True
                break
        if not removed:
            removed_from_map = True  # юнит был на карте до deploy

    counts_after = _calc_area_counts(areas, new_placed)
    if removed_from_map:
        counts_after[remove_area_idx] = max(0, counts_after[remove_area_idx] - 1)
    overflow_after = _overflow_areas(areas, counts_after)

    print(f'=== Deploy Step 5: разрешение overflow ===')
    if overflow_before:
        print(f'Области с overflow до:')
        for i, cnt in overflow_before.items():
            print(f'  area[{i}] {areas[i]["type"]}  юнитов={cnt}  capacity={areas[i]["capacity"]}')
    else:
        print('Overflow нет — шаг не нужен')
        return placed

    if errors:
        print('ОШИБКИ:')
        for e in errors:
            print(f'  - {e}')
        return placed

    src_label = 'с карты' if removed_from_map else 'из размещённых'
    print(f'Убран: {uc.unit_stats[remove_unit_key]["name"]} из области {remove_area_idx} ({src_label})')

    print(f'\nСостояние областей после:')
    for i, area in enumerate(areas):
        cap   = area['capacity']
        count = counts_after.get(i, 0)
        over  = ' <<OVERFLOW>>' if count > cap else ''
        print(f'  area[{i}] {area["type"]:6s}  capacity={cap}  юнитов={count}{over}')

    if overflow_after:
        print(f'\nЕщё есть overflow — нужно убрать ещё:')
        for i, cnt in overflow_after.items():
            removable = [u['unit_key'] for u in _area_player_units(areas[i], player_id, new_placed, i)]
            print(f'  area[{i}]: лишних {cnt - areas[i]["capacity"]}  убрать можно: {removable}')
    else:
        print('\nOverflow разрешён')

    if removed_from_map:
        print(f'\nУбран с карты (возвращён в резерв): {remove_unit_key}')

    return new_placed


# =============================================================
# ШАГ 6: Покупка и размещение здания
# =============================================================

def step6_buy_and_place_building():
    # --- входные данные (менять для теста) ---
    tile_key  = '0,0'
    player_id = 0

    building_type = 'city'
    use_cash      = False
    area_idx      = 0
    # -----------------------------------------

    state   = _load_state()
    player  = state['players'][player_id]
    areas   = state['map'][tile_key]['areas']

    credits     = player.get('credits', 0)
    cash_tokens = player.get('tokens', {}).get('discount', 0)

    pool_counts = _compute_structure_pool(state, player_id)

    available_planets = _available_areas(areas, player_id, kind='planet_free')

    errors = []

    if not available_planets:
        errors.append('нет свободных планет для постройки в этой системе')
    if pool_counts.get(building_type, 0) == 0:
        errors.append(f'{building_type} нет в резерве построек')

    cost       = STRUCTURE_COSTS.get(building_type, 0)
    final_cost = max(0, cost - (2 if use_cash else 0))

    if use_cash and cash_tokens < 1:
        errors.append('нет cash токена')
    if final_cost > credits:
        errors.append(f'не хватает кредитов: нужно {final_cost}, есть {credits}')

    # границы и детализация недоступной области
    if not (0 <= area_idx < len(areas)):
        errors.append(f'область {area_idx} вне диапазона')
    elif area_idx not in available_planets:
        area = areas[area_idx]
        if area['type'] != 'planet':
            errors.append(f'область {area_idx} не является планетой')
        elif area.get('structures'):
            errors.append(f'область {area_idx} уже занята постройкой')
        else:
            errors.append(f'область {area_idx} недоступна (занята соперником)')

    print(f'=== Deploy Step 6: покупка и размещение здания ===')
    print(f'Резерв построек: {pool_counts if pool_counts else "пусто"}')
    print(f'Свободные планеты: {list(available_planets.keys()) if available_planets else "нет"}')
    print()
    print(f'Покупаем:  {building_type}  стоимость={cost}' +
          (f'  cash -2 -> {final_cost}' if use_cash else ''))
    print(f'Кредитов:  {credits}')
    print(f'Ставим в:  область {area_idx}')
    print()

    if errors:
        print('ОШИБКИ:')
        for e in errors:
            print(f'  - {e}')
        print('ПОКУПКА НЕВОЗМОЖНА')
        return False

    print('ЗДАНИЕ КУПЛЕНО И РАЗМЕЩЕНО')
    print(f'Потрачено:  кредитов={final_cost}  cash={1 if use_cash else 0}')
    print(f'Осталось:   кредитов={credits - final_cost}  cash={cash_tokens - (1 if use_cash else 0)}')
    return True


# =============================================================
# ИНТЕГРАЦИОННЫЕ ФУНКЦИИ (для game_server.py)
# Принимают state как аргумент — без I/O.
# =============================================================

def get_deploy_info(state, player_id, tile_key):
    """Анализ тайла + каталог юнитов для UI deploy."""
    tile_info = _analyze_tile(state, tile_key, player_id)
    uc = _load_faction(state, player_id)
    player = state['players'][player_id]
    tokens = player.get('tokens', {})
    forge_tokens = tokens.get('forge', 0)
    cash_tokens = tokens.get('discount', 0)
    credits = player.get('credits', 0)

    pool_count = _compute_pool(state, uc, player_id)
    areas = tile_info['areas']
    avail_areas = _available_areas(areas, player_id)
    avail_planets = list(_available_areas(areas, player_id, kind='planet_free').keys())

    unit_catalog = []
    for unit_key, stats in uc.unit_stats.items():
        if unit_key not in _UNIT_TYPE_MAP:
            continue
        unit_type, tier = _UNIT_TYPE_MAP[unit_key]
        in_pool = pool_count.get((unit_type, tier), 0)
        tier_gap = max(0, tier - tile_info['city_count'])
        needs_tier_forge = tier_gap == 1 and forge_tokens >= 1
        can_buy_tier = tier <= tile_info['city_count'] or needs_tier_forge
        unit_catalog.append({
            'unit_key':         unit_key,
            'name':             stats['name'],
            'unitType':         unit_type,
            'tier':             tier,
            'cost':             stats['cost'],
            'cost_forge':       stats.get('cost_forge', 0),
            'max_count':        stats['max_count'],
            'pool_available':   in_pool,
            'needs_tier_forge': needs_tier_forge,
            'can_buy_tier':     can_buy_tier,
            'can_buy':          in_pool > 0 and can_buy_tier,
        })

    return {
        'has_factory':     tile_info['has_factory'],
        'capacity':        tile_info['capacity'],
        'city_count':      tile_info['city_count'],
        'unit_catalog':    unit_catalog,
        'available_areas': [
            {
                'idx':           i,
                'type':          a['type'],
                'capacity':      a['capacity'],
                'current_units': len(a.get('troops', [])),
            }
            for i, a in avail_areas.items()
        ],
        'available_planets': avail_planets,
        'credits':         credits,
        'forge_tokens':    forge_tokens,
        'cash_tokens':     cash_tokens,
        'structure_pool':  [
            {'type': t}
            for t, cnt in _compute_structure_pool(state, player_id).items()
            for _ in range(cnt)
        ],
    }


def validate_basket_for_state(state, player_id, tile_key, basket):
    """
    Валидация корзины юнитов.
    basket: [{'unit_key': str, 'use_cash': bool}]
    Returns: (success: bool, errors: list[str], costs: dict)
    """
    tile_info = _analyze_tile(state, tile_key, player_id)
    uc = _load_faction(state, player_id)
    player = state['players'][player_id]
    tokens = player.get('tokens', {})
    credits = player.get('credits', 0)
    forge_tokens = tokens.get('forge', 0)
    cash_tokens = tokens.get('discount', 0)
    pool_count = _compute_pool(state, uc, player_id)
    city_count = tile_info['city_count']

    if not tile_info['has_factory'] and basket:
        return False, ['В системе нет фабрики — покупка юнитов недоступна'], \
               {'credits': 0, 'forge': 0, 'cash': 0}

    errors = []
    total_credits = 0
    forge_spent = 0
    cash_spent = 0
    basket_pool = {}

    if len(basket) > tile_info['capacity']:
        errors.append(f'Превышен лимит фабрики: {len(basket)} > {tile_info["capacity"]}')

    for item in basket:
        unit_key = item.get('unit_key')
        use_cash = item.get('use_cash', False)
        stats = uc.unit_stats.get(unit_key)
        if stats is None:
            errors.append(f'Неизвестный юнит: {unit_key}')
            continue

        _, tier = _UNIT_TYPE_MAP[unit_key]
        tier_gap = max(0, tier - city_count)
        ft, fc = _unit_forge_cost(unit_key, city_count, stats)

        if tier_gap > 1:
            errors.append(f'{stats["name"]}: тир недоступен (разница > 1)')

        forge_spent += ft + fc
        cash_spent += int(use_cash)
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


def validate_place_unit_for_state(state, player_id, tile_key, hand, placed_so_far, unit_key, area_idx):
    """
    Валидация размещения одного юнита.
    Returns: (success: bool, error: str|None, overflow: dict)
    overflow = {area_idx: count} для областей с overflow
    """
    tile_info = _analyze_tile(state, tile_key, player_id)
    uc = _load_faction(state, player_id)
    areas = tile_info['areas']

    hand_remaining = list(hand)
    for p in placed_so_far:
        if p['unit_key'] in hand_remaining:
            hand_remaining.remove(p['unit_key'])

    if unit_key not in hand_remaining:
        return False, f'{unit_key} нет в руке (уже размещён или не куплен)', {}

    avail = _available_areas(areas, player_id)
    if area_idx not in avail:
        return False, f'Область {area_idx} недоступна', {}

    unit_type, _ = _UNIT_TYPE_MAP.get(unit_key, (None, None))
    if unit_type is None:
        return False, f'Неизвестный тип юнита: {unit_key}', {}

    expected = 'planet' if unit_type == 'ground' else 'space'
    if avail[area_idx]['type'] != expected:
        name = uc.unit_stats[unit_key]['name']
        kind = 'наземный' if unit_type == 'ground' else 'космический'
        return False, f'{name} — {kind} юнит, нужна {expected}', {}

    new_placed = placed_so_far + [{'unit_key': unit_key, 'area_idx': area_idx}]
    counts = _calc_area_counts(areas, new_placed)
    overflow = _overflow_areas(areas, counts)
    return True, None, overflow


def validate_and_remove_overflow(state, player_id, tile_key, placed_so_far, remove_area_idx, remove_unit_key):
    """
    Убрать одного юнита из overflow области.
    Returns: (success, error, new_placed, removed_from_map: bool, remaining_overflow: dict)
    """
    tile_info = _analyze_tile(state, tile_key, player_id)
    areas = tile_info['areas']

    counts = _calc_area_counts(areas, placed_so_far)
    overflow = _overflow_areas(areas, counts)

    if remove_area_idx not in overflow:
        return False, f'Область {remove_area_idx} не в overflow', placed_so_far, False, overflow

    all_in_area = _area_player_units(areas[remove_area_idx], player_id, placed_so_far, remove_area_idx)
    if not any(u['unit_key'] == remove_unit_key for u in all_in_area):
        return False, f'{remove_unit_key} не найден в области {remove_area_idx}', placed_so_far, False, overflow

    new_placed = list(placed_so_far)
    removed_from_map = False
    removed = False
    for i, p in enumerate(new_placed):
        if p['area_idx'] == remove_area_idx and p['unit_key'] == remove_unit_key:
            new_placed.pop(i)
            removed = True
            break
    if not removed:
        removed_from_map = True

    counts_after = _calc_area_counts(areas, new_placed)
    if removed_from_map:
        counts_after[remove_area_idx] = max(0, counts_after[remove_area_idx] - 1)
    overflow_after = _overflow_areas(areas, counts_after)
    return True, None, new_placed, removed_from_map, overflow_after


def validate_buy_building_for_state(state, player_id, tile_key, building_type, area_idx, use_cash):
    """
    Валидация покупки здания.
    Returns: (success: bool, errors: list[str], final_cost: int)
    """
    player = state['players'][player_id]
    areas = state['map'][tile_key]['areas']

    # Учитываем уже зарезервированные ресурсы за юнитов (ещё не списаны из state)
    unit_costs = state.get('pending_deploy', {}).get('unit_costs', {})
    credits     = player.get('credits', 0) - unit_costs.get('credits', 0)
    cash_tokens = player.get('tokens', {}).get('discount', 0) - unit_costs.get('cash', 0)

    pool_counts = _compute_structure_pool(state, player_id)

    avail_planets = _available_areas(areas, player_id, kind='planet_free')
    cost = STRUCTURE_COSTS.get(building_type, 0)
    final_cost = max(0, cost - (2 if use_cash else 0))

    errors = []
    if not avail_planets:
        errors.append('Нет свободных планет для постройки')
    if pool_counts.get(building_type, 0) == 0:
        errors.append(f'{building_type} нет в резерве построек')
    if use_cash and cash_tokens < 1:
        errors.append('Нет cash токена')
    if final_cost > credits:
        errors.append(f'Не хватает кредитов: нужно {final_cost}, есть {credits}')
    if not (0 <= area_idx < len(areas)):
        errors.append(f'Область {area_idx} вне диапазона')
    elif area_idx not in avail_planets:
        area = areas[area_idx]
        if area['type'] != 'planet':
            errors.append(f'Область {area_idx} не является планетой')
        elif area.get('structures'):
            errors.append(f'Область {area_idx} уже занята постройкой')
        else:
            errors.append(f'Область {area_idx} недоступна (занята соперником)')

    return len(errors) == 0, errors, final_cost


def apply_deploy_to_state(state, player_id, tile_key, placed, unit_costs,
                          building=None, removed_from_map=None):
    """
    Применить результаты deploy к state.

    placed:            [{'unit_key': str, 'area_idx': int}] — новые юниты на карту
    unit_costs:        {'credits': int, 'forge': int, 'cash': int}
    building:          {'type': str, 'area_idx': int, 'final_cost': int, 'use_cash': bool} | None
    removed_from_map:  [{'unit_key': str, 'area_idx': int}] | None — overflow удаление с карты

    Модифицирует state in-place. Возвращает state.
    """
    player = state['players'][player_id]
    areas = state['map'][tile_key]['areas']

    # 1. Добавить новых юнитов на карту
    for p in placed:
        unit_type, tier = _UNIT_TYPE_MAP[p['unit_key']]
        areas[p['area_idx']].setdefault('troops', []).append({
            'unitType':    unit_type,
            'tier':        tier,
            'player':      player_id,
            'unit_status': 'active',
        })

    # 2. Удалить overflow-юнитов с карты
    for r in (removed_from_map or []):
        unit_type, tier = _UNIT_TYPE_MAP[r['unit_key']]
        troops = areas[r['area_idx']].get('troops', [])
        for i, t in enumerate(troops):
            if (t.get('player') == player_id
                    and t.get('unitType') == unit_type
                    and t.get('tier') == tier):
                troops.pop(i)
                break

    # 3. Вычесть стоимость юнитов
    player['credits'] = player.get('credits', 0) - unit_costs.get('credits', 0)
    tokens = player.setdefault('tokens', {})
    tokens['forge']    = tokens.get('forge', 0)    - unit_costs.get('forge', 0)
    tokens['discount'] = tokens.get('discount', 0) - unit_costs.get('cash', 0)

    # 4. Применить здание
    if building:
        btype      = building['type']
        b_area_idx = building['area_idx']
        final_cost = building['final_cost']

        areas[b_area_idx].setdefault('structures', []).append({
            'type':   btype,
            'player': player_id,
        })

        player['credits'] = player.get('credits', 0) - final_cost
        if building.get('use_cash'):
            tokens['discount'] = tokens.get('discount', 0) - 1

    return state


if __name__ == '__main__':
    step1_analyze_tile()
    print()
    step2_available_units()
    print()
    step3_add_unit()
    print()
    step3_confirm_basket()
    print()
    step4_place_unit()
    print()
    step5_resolve_overflow()
    print()
    step6_buy_and_place_building()
