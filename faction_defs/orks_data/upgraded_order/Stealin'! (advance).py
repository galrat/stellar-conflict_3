"""
Stealin'! (Advance) — Orks order upgrade.
Orbital Strike, once per round. Bastions do not prevent orbital strike.
Spend 1 [M] to discard an enemy asset token; you gain that token. Command Level 2.
"""


def play(active_game, player_id, order_type, order_tile, upgrade):
    """
    Args:
        active_game: state after the order has been removed from the field
        player_id:   player index
        order_type:  'advance'
        order_tile:  tile key where the order was placed
        upgrade:     upgrade dict from hand_order_upgrades

    Returns:
        tuple (success, message, new_state) or None for default stub
    """
    # TODO: implement — orbital strike ignoring bastions + steal enemy token
    return None
