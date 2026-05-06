"""
Ork Roks (Advance) — Orks order upgrade.
Can move up to 2 units through 1 uncontrolled void as if it were a friendly area. Once per round.
Command Level 1.
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
    # TODO: implement — allow movement through 1 uncontrolled void
    return None
