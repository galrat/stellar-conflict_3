"""
faction_defs/crusaders.py — фракция «Крестоносцы»
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

CRUSADERS = Faction(
    id   = "crusaders",
    name = "Крестоносцы",
    icon = "⚔",
    flavor = (
        "Рыцарский орден звёздного фронтира. "
        "Предпочитают честный бой и никогда не отступают."
    ),
    special_ability_name = "Кодекс чести",
    special_ability_desc = (
        "TODO: описание особой способности"
    ),
    unit_config = UnitConfig(
        infantry=1, marines=2, mechanized=2, elite=1,
        fighters=1, destroyers=1,
    ),
    battle_cards = [
        BattleCard(
            name     = "Рыцарская атака",
            level    = CardLevel.INITIAL,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Стена щитов",
            level    = CardLevel.ZERO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Праведный удар",
            level    = CardLevel.TWO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Последний рыцарь",
            level    = CardLevel.THREE,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Рыцарский марш",
            order_type = "move",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
        OrderUpgrade(
            name       = "Осада",
            order_type = "attack",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
    ],
    extra = {
        "homeworld":    "TODO: название родной планеты",
        "color_scheme": "#TODO",
    },
)
