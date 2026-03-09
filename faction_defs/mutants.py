"""
faction_defs/mutants.py — фракция «Мутанты»
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

MUTANTS = Faction(
    id   = "mutants",
    name = "Мутанты",
    icon = "⚗",
    flavor = (
        "Жертвы экспериментов, ставшие оружием. "
        "Непредсказуемые в бою, регенерируют быстрее, чем их успевают убивать."
    ),
    special_ability_name = "Мутагенез",
    special_ability_desc = (
        "TODO: описание особой способности"
    ),
    unit_config = UnitConfig(
        infantry=5, marines=1, mechanized=0, elite=0,
        fighters=2, destroyers=0,
    ),
    battle_cards = [
        BattleCard(
            name     = "Берсерк",
            level    = CardLevel.INITIAL,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Токсичное облако",
            level    = CardLevel.ZERO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Регенерация",
            level    = CardLevel.TWO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Хаотичная эволюция",
            level    = CardLevel.THREE,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Заражение территории",
            order_type = "dominate",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
        OrderUpgrade(
            name       = "Мутировавший натиск",
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
