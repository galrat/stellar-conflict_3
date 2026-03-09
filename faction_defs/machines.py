"""
faction_defs/machines.py — фракция «Машины»
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

MACHINES = Faction(
    id   = "machines",
    name = "Машины",
    icon = "⚙",
    flavor = (
        "Древний искусственный интеллект, пробудившийся спустя тысячелетия. "
        "Не знают страха и усталости — каждый юнит заменяем."
    ),
    special_ability_name = "Самовосстановление",
    special_ability_desc = (
        "TODO: описание особой способности"
    ),
    unit_config = UnitConfig(
        infantry=2, marines=0, mechanized=3, elite=1,
        fighters=2, destroyers=0,
    ),
    battle_cards = [
        BattleCard(
            name     = "Протокол подавления",
            level    = CardLevel.INITIAL,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Перегрузка систем",
            level    = CardLevel.ZERO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Рой дронов",
            level    = CardLevel.TWO,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
        BattleCard(
            name     = "Апокалипсис-протокол",
            level    = CardLevel.THREE,
            effect_1 = "TODO: описание эффекта 1",
            effect_2 = "TODO: описание эффекта 2",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Оптимальный маршрут",
            order_type = "move",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
        OrderUpgrade(
            name       = "Производственный цикл",
            order_type = "build",
            effect_1   = "TODO: описание эффекта 1",
            effect_2   = "TODO: описание эффекта 2",
        ),
    ],
    extra = {
        "homeworld":    "TODO: название родной планеты",
        "color_scheme": "#TODO",
    },
)
