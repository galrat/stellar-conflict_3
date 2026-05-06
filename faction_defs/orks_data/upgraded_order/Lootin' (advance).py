"""
Lootin' (Advance) — Orks order upgrade.
Orbital Strike, once per round. Gain 1 [?].
Spend 1 die to gain 1 materiel and force enemy to lose 1 materiel.
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
    # TODO: implement — orbital strike + resource gain
    return None
