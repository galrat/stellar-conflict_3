"""
faction_defs/theocracy.py — фракция «Теократия»
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

THEOCRACY = Faction(
    id   = "theocracy",
    name = "Теократия",
    icon = "✝",
    flavor = (
        "Фанатичные крестоносцы, несущие волю Бога-Императора. "
        "Сильны в обороне священных миров и массированных атаках."
    ),
    special_ability_name = "Священная война",
    special_ability_desc = (
        "TODO: описание особой способности"
    ),
    unit_config = UnitConfig(
        infantry=4, marines=1, mechanized=0, elite=1,
        fighters=1, destroyers=1,
    ),
    battle_cards = [
        BattleCard(
            name     = "Праведный гнев",
            level    = CardLevel.INITIAL,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Мученичество",
            level    = CardLevel.ZERO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Крестовый поход",
            level    = CardLevel.TWO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Воля Императора",
            level    = CardLevel.THREE,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Священный марш",
            order_type = "move",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
        OrderUpgrade(
            name       = "Доминирование веры",
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
