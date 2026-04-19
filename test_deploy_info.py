#!/usr/bin/env python3
"""Быстрый тест get_deploy_info()"""

import json
import sys
sys.path.insert(0, '/c/Users/Airat/Desktop/fs_2_clean')

from python_engine.deploy import get_deploy_info

# Загрузить текущее состояние
with open('/c/Users/Airat/Desktop/fs_2_clean/current_state.txt', 'r', encoding='utf-8') as f:
    state = json.load(f)

# Найти тайл с deploy приказом (попробуем первый тайл)
tile_keys = list(state.get('map', {}).keys())
if tile_keys:
    tile_key = tile_keys[0]
    player_id = 0

    print(f"Testing get_deploy_info for tile {tile_key}, player {player_id}")
    print()

    try:
        info = get_deploy_info(state, player_id, tile_key)

        print(f"has_factory: {info['has_factory']}")
        print(f"capacity: {info['capacity']}")
        print(f"credits: {info['credits']}")
        print(f"forge_tokens: {info['forge_tokens']}")
        print(f"cash_tokens: {info['cash_tokens']}")
        print()

        catalog = info.get('unit_catalog', [])
        print(f"unit_catalog length: {len(catalog)}")
        if catalog:
            print("First 3 units:")
            for u in catalog[:3]:
                print(f"  - {u['name']:20s} tier={u['tier']} available={u['available']:5s} reason={u['reason']}")
        else:
            print("  ⚠️  catalog пуст!")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No tiles found in state!")
