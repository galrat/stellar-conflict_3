"""
faction_defs/tau_data/upgraded_order/__init__.py

Dispatcher: loads the matching file by upgrade name and calls play().
File naming: "{upgrade name} ({order_type}).py"
"""
import importlib.util
from pathlib import Path

_DIR = Path(__file__).parent


def _load(upgrade_name, order_type):
    path = _DIR / f"{upgrade_name} ({order_type}).py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"tau_upgrade_{upgrade_name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def play_upgraded_order(active_game, player_id, order_type, order_tile, upgrades):
    """
    Called by python_engine.upgraded_order dispatcher.
    Iterates applied upgrades, loads the matching file, calls play().
    Returns first non-None result, or None to fall back to default.
    """
    for upgrade in upgrades:
        name = upgrade.get('name', '')
        mod = _load(name, order_type)
        if mod and hasattr(mod, 'play'):
            result = mod.play(active_game, player_id, order_type, order_tile, upgrade)
            if result is not None:
                return result
    return None
