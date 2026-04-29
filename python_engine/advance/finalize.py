def finalize_advance(state, player_id):
    pa = state.get('pending_advance')
    if pa:
        tile_key = pa.get('tile_key')
        source_tile_key = pa.get('source_tile')

        if tile_key and tile_key in state.get('map', {}):
            active_tile = state['map'][tile_key]
            for area in active_tile.get('areas', []):
                for troop in area.get('troops', []):
                    if troop.get('player') == player_id:
                        troop.pop('ready_to_move', None)
                        troop.pop('_uid', None)

        if source_tile_key and source_tile_key in state.get('map', {}):
            source_tile = state['map'][source_tile_key]
            for area in source_tile.get('areas', []):
                for troop in area.get('troops', []):
                    if troop.get('player') == player_id:
                        troop.pop('ready_to_move', None)
                        troop.pop('_uid', None)

        del state['pending_advance']

    state['execution_order_played'][player_id] = True
