"""
The Green Tide (Strategize) — Orks order upgrade.
When revealed, can resolve it as one of the other orders instead. Once per round.
Command Level 1.
"""
import copy


def play(active_game, player_id, order_type, order_tile, upgrade):
    new_state = copy.deepcopy(active_game)
    new_state['pending_green_tide'] = {
        'player_id':       player_id,
        'order_tile':      order_tile,
        'available_orders': ['dominate', 'deploy', 'advance', 'strategize'],
    }
    return True, "The Green Tide: выберите тип приказа", new_state
