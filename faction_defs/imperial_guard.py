"""
faction_defs/imperial_guard.py — фракция «Имперская Гвардия»

Многочисленная пехота (max 12 Guardsmen!). Dominance позволяет развёртывать
2+ одинаковых юнита со скидкой. Warhound Titans поставляются с 3 жетонами подкрепления.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

IMPERIAL_GUARD = Faction(
    id    = "imperial_guard",
    name  = "Imperial Guard",
    icon  = "⚜",
    color        = "#795548",
    home_tile_id = "home_imperial_guard",
    flavor = (
        "Dominate: When you resolve a dominate order, you may resolve a deploy order, "
        "only to purchase 2 or more identical units and placing them on either 1 friendly world "
        "containing a structure or 1 friendly or uncontrolled void. Reduce the materiel cost of each unit by 1."
    ),
    special_ability_name = "Dominate",
    special_ability_desc = (
        "When you resolve a dominate order, you may resolve a deploy order, "
        "only to purchase 2 or more identical units and placing them on either 1 friendly world "
        "containing a structure or 1 friendly or uncontrolled void. Reduce the materiel cost of each unit by 1."
    ),
    unit_config = UnitConfig(
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=3, marines=2, mechanized=0, elite=0,
        fighters=1, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        factories=1, cities=0, bastions=0,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=0, discount_tokens=0, forge_tokens=0,
        # ── Характеристики юнитов ───────────────────────────────────────────
        unit_stats={
            "infantry":   dict(name="Guardsmen",                    cost=2,               combat_strength=1, health=1, morale=2, max_count=12),
            "marines":    dict(name="Ogryns",                       cost=3,               combat_strength=2, health=4, morale=2, max_count=6),
            "mechanized": dict(name="Leman Russ Battle Tanks",      cost=4,               combat_strength=3, health=4, morale=3, max_count=6),
            "elite":      dict(name="Warhound Titans",              cost=5, cost_forge=1, combat_strength=3, health=5, morale=4, max_count=3),
            "fighter":    dict(name="Lunar-Class Cruisers",         cost=2,               combat_strength=2, health=2, morale=2, max_count=3),
            "destroyer":  dict(name="Emperor-Class Battleships",    cost=5, cost_forge=1, combat_strength=4, health=6, morale=3, max_count=3),
        },
    ),
    battle_cards = [
        # ── Начальные (бесплатные) ──────────────────────────────────────────
        BattleCard(
            name     = "Fire Support",
            level    = CardLevel.INITIAL,
            effect_1 = "If you are defending, gain 2 (s). Otherwise, opponent loses 2 (s). Requires: Guardsman / Cruiser.",
            effect_2 = "Reroll 1 [S].",
        ),
        BattleCard(
            name     = "For the Emperor!",
            level    = CardLevel.INITIAL,
            effect_1 = "Reroll 1 of your dice. Requires: Guardsman / Cruiser.",
            effect_2 = "Gain 1 (g) for each unrouted Guardsman or Cruiser, to a maximum of 3.",
        ),
        BattleCard(
            name     = "Incoming!",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 1 [?]. Requires: Guardsman / Cruiser.",
            effect_2 = "Gain 1 (s) for each unrouted Guardsman or Cruiser, to a maximum of 3.",
        ),
        BattleCard(
            name     = "Iron Discipline",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 1 [?] for each of your unrouted units of a different Tier. Requires: Guardsman / Cruiser.",
            effect_2 = "Rally 1 of your units.",
        ),
        BattleCard(
            name     = "Ratling Marksmen",
            level    = CardLevel.INITIAL,
            effect_1 = "At the start of the assess damage step of this execution round, your enemy loses 2 (g). Requires: Guardsman / Cruiser.",
            effect_2 = "Your enemy chooses and routs 1 of his units unless he spends 1 die of his choice.",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Bullgryn Bulwark",
            level    = CardLevel.ZERO,
            effect_1 = "You must reroll 2 [G] or [M]. Requires: Ogryn / Cruiser.",
            effect_2 = "Gain 1 (g) for each unrouted Guardsman or Cruiser, to a maximum of 3.",
        ),
        BattleCard(
            name     = "Mechanised Combat Group",
            level    = CardLevel.ZERO,
            effect_1 = "At the start of the assess damage step of this execution round, your enemy loses either 3 (g) or 3 (s) for each pairing of unrouted Guardsmen with Ogryns or Cruisers with Battleships.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Ogryn Shock Troops",
            level    = CardLevel.ZERO,
            effect_1 = "You must reroll 2 [S] or [M]. Requires: Ogryn / Cruiser.",
            effect_2 = "Gain 1 (s) for each unrouted Guardsman or Cruiser, to a maximum of 3.",
        ),
        BattleCard(
            name     = "Sentinel Reconnaissance",
            level    = CardLevel.ZERO,
            effect_1 = "If you have more unrouted units than your enemy, your enemy chooses and routs 1 of his units unless he spends 1 [M]. Requires: Ogryn / Cruiser.",
            effect_2 = "If you are attacking, look at your enemy's facedown combat card. Gain either 2 [G] or 2 [S].",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Armoured Spearhead",
            level    = CardLevel.TWO,
            effect_1 = "Either destroy up to 2 unrouted Guardsmen to force your enemy to lose 2 dice of his choice for each destroyed Guardsman, or destroy 1 unrouted Cruiser to force your enemy to lose 3 dice of his choice. Requires: Leman Russ / Battleship.",
            effect_2 = "Choose 1 of your enemy's Tier 2 or Tier 3 units or bastions. That unit or bastion suffers damage first during this execution round.",
        ),
        BattleCard(
            name     = "Combined Arms",
            level    = CardLevel.TWO,
            effect_1 = "For each of your unrouted ground units of a different Tier, gain either 1 (g) or 1 (s). For each of your unrouted ships of a different Tier, gain either 2 (g) or 2 (s). Gain 1 [?]. Rally 1 of your units.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Wyvern Suppression Fire",
            level    = CardLevel.TWO,
            effect_1 = "If you have more unrouted Tier 0 units than your enemy, your enemy chooses and routs 1 of his units. Requires: Leman Russ / Battleship.",
            effect_2 = "Your enemy chooses and destroys 1 of his routed Tier 0 or Tier 1 units.",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Hammer of the Emperor",
            level    = CardLevel.THREE,
            effect_1 = "Force your enemy to lose 1 [S]. Requires: Warhound Titan / Battleship.",
            effect_2 = "Warhound Titan: Gain 2 (g) for each of your unrouted units of a different Tier, to a maximum of 6. Battleship: Gain 3 (g) for each of your unrouted units of a different Tier.",
        ),
        BattleCard(
            name     = "Titan Support",
            level    = CardLevel.THREE,
            effect_1 = "Your enemy must reroll 1 [G] for each of your unrouted units of a different Tier. Requires: Warhound Titan / Battleship.",
            effect_2 = "During this execution round, your units of Tier 2 or less cannot become routed.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Saturation Bombing",
            order_type = "advance",
            effect_1   = "Orbital Strike, once per round. Gain 1 [?].",
            effect_2   = "You may convert 1 of your [M] into 1 [G].",
        ),
        OrderUpgrade(
            name       = "Adeptus Astronomica",
            order_type = "advance",
            effect_1   = "While resolving this order, you may move up to 6 units to a world, if at least 1 of those units is a Guardsman. Once per round.",
            effect_2   = "After you resolve this order, you may retreat any Guardsmen in excess of that world's unit capacity. Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Departmento Munitorum",
            order_type = "strategize",
            effect_1   = "While resolving this order, you may purchase 1 upgrade only. Then resolve a limited Deploy, Advance, or Dominate order in the active system. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Forced Recruitment",
            order_type = "deploy",
            effect_1   = "While resolving this order, you may treat all your cities in the active system as factories capable of deploying Guardsmen only. The unit capacity of friendly worlds containing a city is increased by 2, to a maximum of 4 (Guardsmen only). Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Virus Bombs",
            order_type = "advance",
            effect_1   = "Orbital Strike, once per round. Enemy bastions do not prevent orbital strike.",
            effect_2   = "During this orbital strike, the health value of your enemy's units is reduced to 3. Command Level 2.",
        ),
    ],
    extra = {
        "homeworld":    "Cadia",
        "color_scheme": "#795548",
    },
)
