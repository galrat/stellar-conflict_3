"""Direct the Faithful (Strategize) — Space Marines order upgrade."""
import copy
from python_engine.strategize import _count_player_cities


def play(active_game, player_id, order_type, order_tile, upgrade):
    new_state = copy.deepcopy(active_game)
    player_level = _count_player_cities(active_game, player_id)

    # Order was just moved to hand_orders by play_order — take the last strategize one
    hand_orders = new_state['players'][player_id].get('hand_orders', [])
    strat_orders = [o for o in hand_orders if o.get('type') == 'strategize']
    order_id = strat_orders[-1].get('id') if strat_orders else None

    new_state['pending_strategize'] = {
        'player_id': player_id,
        'step': 'buy_combat_card',
        'player_level': player_level,
        'order_id': order_id,
        'order_type': order_type,
    }
    new_state['pending_direct_the_faithful'] = {
        'player_id': player_id,
        'order_tile': order_tile,
        'replacement_done': False,
    }

    return True, "Direct the Faithful: доступна замена здания и обычный Strategize", new_state
