"""
python_engine/upgraded_order.py — dispatcher for playing upgraded orders.

Called when a player plays an order using one or more order upgrades from
hand_order_upgrades. Dispatches to faction-specific implementations.
"""
import copy
import importlib
from python_engine.order_play import play_order

_FACTION_MODULES = {
    'chaos':          'faction_defs.chaos_data.upgraded_order',
    'eldar':          'faction_defs.eldar_data.upgraded_order',
    'imperial_guard': 'faction_defs.imperial_guard_data.upgraded_order',
    'marine':         'faction_defs.marine_data.upgraded_order',
    'necrons':        'faction_defs.necrons_data.upgraded_order',
    'orks':           'faction_defs.orks_data.upgraded_order',
    'tau':            'faction_defs.tau_data.upgraded_order',
    'tyranids':       'faction_defs.tyranids_data.upgraded_order',
}


def _get_module(faction_id):
    path = _FACTION_MODULES.get(faction_id)
    if not path:
        return None
    try:
        return importlib.import_module(path)
    except ImportError:
        return None


def play_upgraded_order(active_game, player_id, order_id, upgrade_ids):
    """
    Play an order using one or more of the player's order upgrades.

    Args:
        active_game: current game state
        player_id:   player index (0 or 1)
        order_id:    id of the order being played
        upgrade_ids: list of upgrade ids to apply (1 or 2)

    Returns:
        tuple: (success: bool, message: str, new_state: dict or None)
    """
    players = active_game.get('players', [])
    if player_id >= len(players):
        return False, "Игрок не найден", None
    player = players[player_id]
    faction_id = player.get('faction', '')

    order = next(
        (o for o in active_game.get('orders', [])
         if o.get('id') == order_id and o.get('owner') == player_id),
        None
    )
    if not order:
        return False, "Приказ не найден или не ваш", None

    all_tile_orders = sorted(
        [o for o in active_game.get('orders', []) if o.get('tile') == order.get('tile')],
        key=lambda o: o.get('position', 0), reverse=True
    )
    if all_tile_orders and all_tile_orders[0].get('id') != order_id:
        return False, "Приказ перекрыт другим приказом в стопке", None

    order_type = order.get('type')
    order_tile = order.get('tile')

    hand_upgrades = {u['id']: u for u in player.get('hand_order_upgrades', [])}
    applied = []
    for uid in upgrade_ids:
        if uid not in hand_upgrades:
            return False, f"Улучшение '{uid}' не найдено в руке", None
        u = hand_upgrades[uid]
        if u.get('order_type') != order_type:
            return False, f"Улучшение '{uid}' не подходит для приказа '{order_type}'", None
        applied.append(u)

    # Standard cleanup: remove order from field, return to hand
    ok, msg, base_state = play_order(active_game, player_id, order_id)
    if not ok:
        return False, msg, None

    mod = _get_module(faction_id)
    if mod and hasattr(mod, 'play_upgraded_order'):
        result = mod.play_upgraded_order(base_state, player_id, order_type, order_tile, applied)
        if result is not None:
            return result

    upgrade_names = ', '.join(u.get('name', u.get('id', '?')) for u in applied)
    return True, f"Улучшенный {order_type} ({upgrade_names}) — заготовка", base_state
