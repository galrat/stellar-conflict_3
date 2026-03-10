"""
faction_defs/orks.py — фракция «Орки»
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

ORKS = Faction(
    id    = "orks",          # ключ в игре — менять осторожно
    name  = "Орки",          # отображаемое название
    icon  = "💀",             # иконка в UI
    color        = "#2E7D32",
    home_tile_id = "home_orks",
    flavor = (
        "Особое свойство фракции:",
        "вы можете купить один отряд и поместить его в дружественный мир активнйо системы"

    ),
    special_ability_name = "Особое свойство фракции:",
    special_ability_desc = "вы можете купить один отряд и поместить его в дружественный мир активнйо системы",
    unit_config = UnitConfig(
        infantry=4, marines=1, mechanized=1, elite=0,
        fighters=2, destroyers=0,
    ),
    battle_cards = [
        BattleCard(
            name     = "Вааааgh!",
            level    = CardLevel.INITIAL,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Больше пушек",
            level    = CardLevel.ZERO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Орочий напор",
            level    = CardLevel.TWO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Зелёный прилив",
            level    = CardLevel.THREE,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Орочий марш",
            order_type = "move",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
        OrderUpgrade(
            name       = "Безумная атака",
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
