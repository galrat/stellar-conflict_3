"""
Werk Fasta! (Deploy) — Orks order upgrade.
May purchase structure before purchasing units. Once per round.
Command Level 1.
"""


def play(active_game, player_id, order_type, order_tile, upgrade):
    """
    Args:
        active_game: state after the order has been removed from the field
        player_id:   player index
        order_type:  'deploy'
        order_tile:  tile key where the order was placed
        upgrade:     upgrade dict from hand_order_upgrades

    Returns:
        tuple (success, message, new_state) or None for default stub
    """
    # TODO: implement — deploy with building-first step order
    return None
