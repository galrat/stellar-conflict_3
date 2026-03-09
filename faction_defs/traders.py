"""
faction_defs/traders.py — фракция «Торговый союз»
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

TRADERS = Faction(
    id   = "traders",
    name = "Торговый союз",
    icon = "₿",
    flavor = (
        "Межзвёздные купцы, контролирующие торговые пути. "
        "Армия небольшая, но лучшая, которую можно купить за деньги."
    ),
    special_ability_name = "Наёмники",
    special_ability_desc = (
        "TODO: описание особой способности"
    ),
    unit_config = UnitConfig(
        infantry=1, marines=1, mechanized=1, elite=1,
        fighters=2, destroyers=2,
    ),
    battle_cards = [
        BattleCard(
            name     = "Наёмный отряд",
            level    = CardLevel.INITIAL,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Торговое эмбарго",
            level    = CardLevel.ZERO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Частная армия",
            level    = CardLevel.TWO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Монополия",
            level    = CardLevel.THREE,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Логистическая сеть",
            order_type = "reinforce",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
        OrderUpgrade(
            name       = "Экономическое давление",
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
