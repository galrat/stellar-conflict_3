"""
factions.py — точка входа для системы фракций Stellar Conflict.

Этот файл является тонким re-export слоем: все реальные данные находятся в:
  faction_base.py         — базовые классы (Faction, Player, BattleCard и т.д.)
  faction_defs/__init__.py — реестр фракций (FACTIONS, FACTION_CONFIGS)
  faction_defs/<id>.py    — данные конкретных фракций

Все существующие импорты вида «from factions import ...» продолжают работать
без изменений.
"""
from faction_base import (
    CardLevel,
    BattleCard,
    OrderUpgrade,
    UnitConfig,
    Faction,
    Player,
)
from faction_defs import FACTIONS, FACTION_CONFIGS

__all__ = [
    "CardLevel",
    "BattleCard",
    "OrderUpgrade",
    "UnitConfig",
    "Faction",
    "Player",
    "FACTIONS",
    "FACTION_CONFIGS",
]
