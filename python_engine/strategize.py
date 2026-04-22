"""
Stage 2.2: Strategize order play (Стратегизирование)

Фаза разыгрыша приказа Strategize:
1. Игрок обменивает одну боевую карту из руки на одну из доступных
   - Карта из руки -> пул доступных карт
   - Карта из пула -> рука
   - Стоимость карты из пула вычитается из кредитов
2. Затем игрок покупает одно улучшение приказа
   - Улучшение из пула -> рука
   - Стоимость улучшения вычитается из кредитов
"""
import copy


def _count_player_cities(active_game, player_id):
    """Посчитать количество городов (структур) у игрока на карте."""
    city_count = 0
    map_data = active_game.get('map', {})
    for tile_key, tile in map_data.items():
        areas = tile.get('areas', [])
        for area in areas:
            structures = area.get('structures', [])
            for struct in structures:
                if struct.get('type') == 'city' and struct.get('player') == player_id:
                    city_count += 1
    return city_count


def strategize_play(active_game, player_id, order_tile):
    """Инициализировать фазу разыгрыша приказа Strategize."""
    new_state = copy.deepcopy(active_game)
    player_level = _count_player_cities(active_game, player_id)

    new_state['pending_strategize'] = {
        'player_id': player_id,
        'step': 'buy_combat_card',
        'player_level': player_level,
    }
    return new_state


def strategize_buy_combat_card(active_game, player_id, card_to_buy_name, card_from_hand_name):
    """Обменять одну боевую карту на другую."""
    new_state = copy.deepcopy(active_game)
    player = new_state['players'][player_id]

    # Найти карту в руке
    card_from_hand = None
    card_from_hand_idx = -1
    for idx, card in enumerate(player.get('hand_battle_cards', [])):
        if card.get('name') == card_from_hand_name:
            card_from_hand = card
            card_from_hand_idx = idx
            break

    if card_from_hand is None:
        return False, f"Карта '{card_from_hand_name}' не найдена в руке", None

    # Найти карту в доступных
    card_to_buy = None
    card_to_buy_idx = -1
    for idx, card in enumerate(player.get('available_battle_cards', [])):
        if card.get('name') == card_to_buy_name:
            card_to_buy = card
            card_to_buy_idx = idx
            break

    if card_to_buy is None:
        return False, f"Карта '{card_to_buy_name}' не доступна для покупки", None

    # Проверить уровень карты (используем кэшированное значение из pending_strategize)
    pending = active_game.get('pending_strategize', {})
    card_tier = card_to_buy.get('tier', 0)
    player_level = pending.get('player_level', 0)
    if card_tier > player_level:
        return False, f"Карта недоступна (требуется T{card_tier}, у вас {player_level} городов)", None

    # Проверить кредиты
    cost = card_to_buy.get('cost', 0)
    credits = player.get('credits', 0)
    if credits < cost:
        return False, f"Недостаточно кредитов (нужно: {cost}, есть: {credits})", None

    # Выполнить обмен
    player['hand_battle_cards'].pop(card_from_hand_idx)
    if 'available_battle_cards' not in player:
        player['available_battle_cards'] = []
    player['available_battle_cards'].append(copy.deepcopy(card_from_hand))
    player['available_battle_cards'].pop(card_to_buy_idx)
    player['hand_battle_cards'].append(copy.deepcopy(card_to_buy))
    player['credits'] = credits - cost

    # Перейти к следующему шагу
    new_state['pending_strategize']['step'] = 'buy_order_upgrade'

    return True, None, new_state


def strategize_buy_order_upgrade(active_game, player_id, upgrade_name):
    """Купить одно улучшение приказа."""
    new_state = copy.deepcopy(active_game)
    player = new_state['players'][player_id]

    # Найти улучшение в доступных
    upgrade_to_buy = None
    upgrade_to_buy_idx = -1
    for idx, upgrade in enumerate(player.get('available_order_upgrades', [])):
        if upgrade.get('name') == upgrade_name:
            upgrade_to_buy = upgrade
            upgrade_to_buy_idx = idx
            break

    if upgrade_to_buy is None:
        return False, f"Улучшение '{upgrade_name}' не доступно для покупки", None

    # Проверить уровень улучшения (используем кэшированное значение)
    pending = active_game.get('pending_strategize', {})
    upgrade_tier = upgrade_to_buy.get('tier', 0)
    player_level = pending.get('player_level', 0)
    if upgrade_tier > player_level:
        return False, f"Улучшение недоступно (требуется T{upgrade_tier}, у вас {player_level} городов)", None

    # Проверить кредиты
    cost = upgrade_to_buy.get('cost', 0)
    credits = player.get('credits', 0)
    if credits < cost:
        return False, f"Недостаточно кредитов (нужно: {cost}, есть: {credits})", None

    # Выполнить покупку
    player['available_order_upgrades'].pop(upgrade_to_buy_idx)
    if 'hand_order_upgrades' not in player:
        player['hand_order_upgrades'] = []
    player['hand_order_upgrades'].append(copy.deepcopy(upgrade_to_buy))
    player['credits'] = credits - cost

    # Завершить приказ
    del new_state['pending_strategize']

    return True, None, new_state
