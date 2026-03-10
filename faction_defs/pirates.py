"""
faction_defs/pirates.py — фракция «Пираты»
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

PIRATES = Faction(
    id    = "pirates",
    name  = "Пираты",
    icon  = "☠",
    color        = "#E74C3C",
    home_tile_id = "home_pirates",
    flavor = (
        "Вольные капитаны звёздного океана. Живут грабежом, "
        "умирают в абордажных схватках. Никакой дисциплины — только удача и смелость."
    ),
    special_ability_name = "Абордаж",
    special_ability_desc = (
        "TODO: описание особой способности"
    ),
    unit_config = UnitConfig(
        infantry=1, marines=3, mechanized=0, elite=0,
        fighters=4, destroyers=0,
    ),
    battle_cards = [
        BattleCard(
            name     = "Пиратский натиск",
            level    = CardLevel.INITIAL,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Грязный трюк",
            level    = CardLevel.ZERO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Флот головорезов",
            level    = CardLevel.TWO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Чёрная метка",
            level    = CardLevel.THREE,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Пиратский рейд",
            order_type = "attack",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
        OrderUpgrade(
            name       = "Захват трофеев",
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
