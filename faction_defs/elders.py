"""
faction_defs/elders.py — фракция «Предтечи»
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

ELDERS = Faction(
    id   = "elders",
    name = "Предтечи",
    icon = "◎",
    flavor = (
        "Древнейшая цивилизация галактики, ушедшая в тень. "
        "Малочисленны, но каждый их юнит — произведение утраченных технологий."
    ),
    special_ability_name = "Реликвии прошлого",
    special_ability_desc = (
        "TODO: описание особой способности"
    ),
    unit_config = UnitConfig(
        infantry=0, marines=0, mechanized=1, elite=3,
        fighters=1, destroyers=2,
    ),
    battle_cards = [
        BattleCard(
            name     = "Древнее знание",
            level    = CardLevel.INITIAL,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Технологическое превосходство",
            level    = CardLevel.ZERO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Искажение реальности",
            level    = CardLevel.TWO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Апофеоз",
            level    = CardLevel.THREE,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Телепортация",
            order_type = "move",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
        OrderUpgrade(
            name       = "Ментальное доминирование",
            order_type = "dominate",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
    ],
    extra = {
        "homeworld":    "TODO: название родной планеты",
        "color_scheme": "#TODO",
    },
)
