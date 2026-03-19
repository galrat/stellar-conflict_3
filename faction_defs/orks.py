"""
faction_defs/orks.py — фракция «Орки»

Орды зелёных варваров. Самая многочисленная фракция — много дешёвой пехоты
с высокой боевой силой, но низкой моралью. Сила в числе.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

ORKS = Faction(
    id    = "orks",
    name  = "Orks",
    icon  = "💀",
    color        = "#2E7D32",
    home_tile_id = "home_orks",
    flavor = (
        "Dominate"
        "Purchase 1 unit and place it on a world in the active system"
    ),
    special_ability_name = "Dominate",
    special_ability_desc = "Purchase 1 unit and place it on a world in the active system",
    unit_config = UnitConfig(
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=4, marines=1, mechanized=0, elite=0,
        fighters=0, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        # Характеристики построек — см. STRUCTURE_CATALOG в player_hand.py.
        factories=1, cities=0, bastions=0,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=1, discount_tokens=0, forge_tokens=0,
        # ── Характеристики юнитов (cost 2–5 + forge, strength 0–6, health 1–6, morale 0–6) ──
        # Орки: высокая боевая сила, крепкое телосложение, но слабая дисциплина.
        unit_stats={
            # name — отображаемое название; cost — стоимость; max_count — максимальный резерв
            "infantry":   dict(name="Ork Boyz",                  cost=2,               combat_strength=2, health=2, morale=1, max_count=9),
            "marines":    dict(name="Nobz",                      cost=3,               combat_strength=2, health=4, morale=2, max_count=6),
            "mechanized": dict(name="Battlewagons",              cost=4,               combat_strength=3, health=5, morale=3, max_count=3),
            "elite":      dict(name="Gargants",                  cost=5, cost_forge=1, combat_strength=3, health=6, morale=3, max_count=3),
            "fighter":    dict(name="Onslaught Attack Ships",    cost=2,               combat_strength=1, health=3, morale=2, max_count=3),
            "destroyer":  dict(name="Kill Kroozers",             cost=4, cost_forge=1, combat_strength=3, health=6, morale=4, max_count=3),
        },
    ),
    battle_cards = [
        # ── Начальные (бесплатные) ──────────────────────────────────────────
        BattleCard(
            name     = "'Ard Boyz",
            level    = CardLevel.INITIAL,
            effect_1 = "You must reroll all of your [G]. Requires: Boyz.",
            effect_2 = "Enemy must reroll 1 [G] for each unrouted Boyz.",
        ),
        BattleCard(
            name     = "Gretchin",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 1 (g) and 1 (s). Enemy rerolls 1 die of your choice. Requires: Onslaught.",
            effect_2 = "Destroy 1 Onslaught to force enemy to choose & destroy one of his units.",
        ),
        BattleCard(
            name     = "Mek Boyz",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 1 [?]. Requires: Boyz / Onslaught.",
            effect_2 = "Enemy discards top card of his combat deck. You gain the card's combat icons until end of this execution round.",
        ),
        BattleCard(
            name     = "Shoota Boyz",
            level    = CardLevel.INITIAL,
            effect_1 = "You must reroll all of your [S]. Requires: Boyz.",
            effect_2 = "Enemy must reroll 1 [S] for each unrouted Boyz.",
        ),
        BattleCard(
            name     = "Slugga Boyz",
            level    = CardLevel.INITIAL,
            effect_1 = "Both sides must reroll all [M]. Requires: Boyz / Onslaught.",
            effect_2 = "Rally 1 unit.",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Biker Nobz",
            level    = CardLevel.ZERO,
            effect_1 = "Enemy must reroll all [G]. Requires: Nobz / Onslaught.",
            effect_2 = "Gain 1 (g).",
        ),
        BattleCard(
            name     = "Mega Nobz",
            level    = CardLevel.ZERO,
            effect_1 = "Enemy must reroll all [S]. Requires: Nobz / Onslaught.",
            effect_2 = "Gain 1 (s).",
        ),
        BattleCard(
            name     = "Sea of Green",
            level    = CardLevel.ZERO,
            effect_1 = "Place free (R) in this area. If you have more unrouted units, enemy spends 1 [M] or routs 1 unit of his choice.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Waaagh!!!!",
            level    = CardLevel.ZERO,
            effect_1 = "Rally 1 unit. Requires: Boyz / Onslaught.",
            effect_2 = "Gain 1 (g) per unrouted Boyz / Onslaught.",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Party Wagon",
            level    = CardLevel.TWO,
            effect_1 = "Place free (R) in this area. Requires: Wagon / Kroozer.",
            effect_2 = "If you have more unrouted units, gain 2 (g) and 2 (s).",
        ),
        BattleCard(
            name     = "Rokkit Wagon",
            level    = CardLevel.TWO,
            effect_1 = "Requires: Wagon / Kroozer.",
            effect_2 = "Gain 3 (g). Enemy may retreat 1 unit.",
        ),
        BattleCard(
            name     = "Weirdboyz",
            level    = CardLevel.TWO,
            effect_1 = "Both sides must reroll all dice. Requires: Boyz / Onslaught.",
            effect_2 = "In this combat, each time enemy gets (g) or (s), you gain the same tokens as well.",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Smasher Gargant",
            level    = CardLevel.THREE,
            effect_1 = "Requires: Gargant / Kroozer.",
            effect_2 = "Choose enemy unit. Destroy unit unless enemy spends dice equal to its Tier.",
        ),
        BattleCard(
            name     = "Snapper Gargant",
            level    = CardLevel.THREE,
            effect_1 = "Requires: Gargant / Kroozer.",
            effect_2 = "Discard 1 of enemy face up combat cards.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Lootin'",
            order_type = "advance",
            effect_1   = "Orbital Strike, once per round. Gain 1 [?].",
            effect_2   = "Spend 1 die to gain 1 materiel and force enemy to lose 1 materiel.",
        ),
        OrderUpgrade(
            name       = "Werk Fasta!",
            order_type = "deploy",
            effect_1   = "May purchase structure before purchasing units. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "The Green Tide",
            order_type = "strategize",
            effect_1   = "When revealed, can resolve it as one of the other orders instead. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Ork Roks",
            order_type = "advance",
            effect_1   = "Can move up to 2 units through 1 uncontrolled void as if it were a friendly area. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Stealin'!",
            order_type = "advance",
            effect_1   = "Orbital Strike, once per round. Bastions do not prevent orbital strike.",
            effect_2   = "Spend 1 [M] to discard an enemy asset token; you gain that token. Command Level 2.",
        ),
    ],
    extra = {
        "homeworld":    "Гхазгхулл",
        "color_scheme": "#2E7D32",
    },
)
