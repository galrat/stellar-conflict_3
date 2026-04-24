"""
faction_defs/marine.py — фракция «marine»

Тяжёлая бронированная держава. Опирается на механизированные войска
и эсминцы. Медленная, но сокрушительная в прямом столкновении.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel, EventCard

MARINE = Faction(
    id    = "marine",
    name  = "Space marine",
    icon  = "◆",
    color        = "1F4E9E",
    home_tile_id = "home_marine",
    flavor = (
         "Особое свойство доминации:"
        "вы можете заменить Т0 на Т1 или Т1 на Т2 за 1 материал "
    ),
    special_ability_name = "Тренировка",
    special_ability_desc = (
        "вы можете заменить Т0 на Т1 или Т1 на Т2 за 1 материал "
    ),
    unit_config = UnitConfig(
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=4, marines=1, mechanized=0, elite=0,
        fighters=1, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        # Характеристики построек — см. STRUCTURE_CATALOG в player_hand.py.
        factories=1, cities=0, bastions=0,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=0, discount_tokens=0, forge_tokens=0,
        # ── Характеристики юнитов (cost 2–5 + forge, strength 0–6, health 1–6, morale 0–6) ──
        # Элитные солдаты: высокое здоровье и мораль, умеренная боевая сила.
        unit_stats={
            # name — отображаемое название; cost — стоимость; max_count — максимальный резерв
            "infantry":   dict(name="Scout",              cost=2,               combat_strength=1, health=2, morale=2, max_count=6),
            "marines":    dict(name="Space Marine",       cost=3,               combat_strength=2, health=3, morale=3, max_count=6),
            "mechanized": dict(name="Land Raider",        cost=4,               combat_strength=3, health=4, morale=3, max_count=6),
            "elite":      dict(name="Warlord Titan",      cost=5, cost_forge=1, combat_strength=3, health=5, morale=4, max_count=3),
            "fighter":    dict(name="Strike Cruiser",     cost=2,               combat_strength=2, health=2, morale=2, max_count=3),
            "destroyer":  dict(name="Battle Barge",       cost=5, cost_forge=1, combat_strength=4, health=5, morale=4, max_count=3),
        },
        # ── Стартовая колода боевых карт ──────────────────────────────────────
        battle_card_deck = '''Ambush
Blessed Power Armour
Faith in the Emperor
Fury of the Ultramar
Reconnaissance
Drop Pod Assault
Glory and Death
Hold the Line
Veteran Scouts
Armoured Advance
Break the Line
Show No Fear
Emperor's Glory
Emperor's Might
'''.split('\n'),
    ),

    battle_cards=[
        BattleCard(
            name="Ambush",
            tier=-1,
            cost=0,
            icons={"G": 1, "S": 0, "M": 0},
            primary="Gain 2 (g).",
            secondary={"requires": ["Scout", "Cruiser"], "effect": "When enemy is routed this round, must spend [M] or be destroyed."},
        ),
        BattleCard(
            name="Blessed Power Armour",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 1, "M": 0},
            primary="Gain 2 (s).",
            secondary={"requires": ["Bastion", "Marine", "Cruiser"], "effect": "Convert up to 2 dice to [S]."},
        ),
        BattleCard(
            name="Faith in the Emperor",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 0, "M": 1},
            primary="Gain 1 [?].",
            secondary={"requires": ["Scout", "Marine", "Cruiser"], "effect": "Rally 1 unit or gain 1 [M]."},
        ),
        BattleCard(
            name="Fury of the Ultramar",
            tier=-1,
            cost=0,
            icons={"G": 1, "S": 0, "M": 0},
            primary="Enemy rerolls 1 [S]. You may reroll 1 [S].",
            secondary={"requires": ["Marine", "Cruiser"], "effect": "Force enemy to lose 1 [S] or 2 (s)."},
        ),
        BattleCard(
            name="Reconnaissance",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 1, "M": 0},
            primary="If attacking, look at enemy card first.",
            secondary={"requires": ["Scout", "Cruiser"], "effect": "Spend 1 [M] to retreat 1 unit."},
        ),
        BattleCard(
            name="Drop Pod Assault",
            tier=0,
            cost=2,
            icons={"G": 1, "S": 1, "M": 0},
            primary="Gain 1 [?].",
            secondary={"requires": ["Marine"], "effect": "Spend 1 [M] to take 1 scout or 1 marine from any world to this world."},
        ),
        BattleCard(
            name="Glory and Death",
            tier=0,
            cost=2,
            icons={"G": 1, "S": 0, "M": 1},
            primary="Gain 2 (g). If attacking, rally 1 unit.",
            secondary={"requires": ["Marine", "Cruiser"], "effect": "Force enemy to lose 1 [S] or 1 [M]."},
        ),
        BattleCard(
            name="Hold the Line",
            tier=0,
            cost=2,
            icons={"G": 0, "S": 1, "M": 1},
            primary="Gain 2 (s). If defending, rally 1 unit.",
            secondary={"requires": ["Bastion", "Marine", "Cruiser"], "effect": "Gain 1 [S] or 1 [M]."},
        ),
        BattleCard(
            name="Veteran Scouts",
            tier=0,
            cost=2,
            icons={"G": 1, "S": 1, "M": 1},
            primary="For each morale dice, gain 1 (g) or (s).",
            secondary={"requires": ["Scout", "Cruiser"], "effect": "Spend any [M]; retreat 1 unit per die."},
        ),
        BattleCard(
            name="Armoured Advance",
            tier=2,
            cost=4,
            icons={"G": 2, "S": 1, "M": 0},
            primary="Gain 1 [?].",
            secondary={"requires": ["Land Raider", "Battle Barge"],
                       "effect": "Resolve 1 additional assess damage step this round (including tokens etc)."},
),
         BattleCard(
             name="Break the Line",
             tier=2,
             cost=4,
             icons={"G": 1, "S": 2, "M": 0},
             primary="Convert up to 3 [M] to [G] and/or [S].",
             secondary={"requires": ["Land Raider", "Battle Barge"],
                        "effect": "Enemy choses 1 face up combat card to discard."},
         ),
         BattleCard(
             name="Show No Fear",
             tier=2,
             cost=4,
             icons={"G": 0, "S": 2, "M": 1},
             primary="Own units cannot become routed this round.",
             secondary={"requires": ["Bastion", "Marine", "Cruiser"], "effect": "Spend 1 [M] rally all units."},
         ),
         BattleCard(
             name="Emperor's Glory",
             tier=3,
             cost=6,
             icons={"G": 0, "S": 2, "M": 2},
             primary="Gain 2 [?].",
             secondary={"requires": ["Titan", "Battle Barge"], "effect": "Rally all units. Convert any dice to [M]."},
         ),
         BattleCard(
             name="Emperor's Might",
             tier=3,
             cost=6,
             icons={"G": 3, "S": 0, "M": 0},
             primary="Gain 2 [?].",
             secondary={"requires": ["Titan", "Battle Barge"], "effect": "Spend any [G]; gain 2 (g) per die."},
         ),
],

order_upgrades = [
        OrderUpgrade(
            name       = "Reign of Fire",
            order_type = "advance",
            tier       = 0,
            cost       = 1,
            effect_1   = "Orbital Strike, once per round. Gain [?].",
            effect_2   = "Convert 1 [M] into [G].",
        ),
        OrderUpgrade(
            name       = "Crusade",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            effect_1   = "If no friendly worlds in system, gain 1 (R). Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Direct the Faithful",
            order_type = "strategize",
            tier       = 1,
            cost       = 2,
            effect_1   = "May change 1 structure to a different structure. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Recruitment Worlds",
            order_type = "deploy",
            tier       = 1,
            cost       = 2,
            effect_1   = "Treat Bastions as Factories, lower deployment limit by 1 each. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Drop Pods",
            order_type = "advance",
            tier       = 2,
            cost       = 3,
            effect_1   = "Orbital Strike, once per round. Bastions do not prevent orbital strike.",
            effect_2   = "Spend 2 [S] to place free Marine (may start combat). Command Level 2.",
        ),
    ],

event_cards = [
        EventCard(name="Adeptus Mechanicus",  warp_storm_move="Across",           card_type="Scheme", effect="At start of assess damage, discard to gain 2 (s), plus 1 (s) per (F) you have."),
        EventCard(name="Emperor's Champion",  warp_storm_move="Sideways",         card_type="Scheme", effect="At start of assess damage, discard to rally 1 unit."),
        EventCard(name="Exterminatus",        warp_storm_move="Top Left/Bot Rgt", card_type="Scheme", effect="Before orbital strike, discard to convert all dice to [G]."),
        EventCard(name="Heroic Intervention", warp_storm_move="Across",           card_type="Tactic", effect="Place free Marine on friendly structure or free Scout on any friendly world."),
        EventCard(name="Rites of Battle",     warp_storm_move="Top Left/Bot Rgt", card_type="Tactic", effect="Purchase 1 order upgrade, reduce by 1 materiel per Bastion."),
        EventCard(name="The Emperor Protects",warp_storm_move="Sideways",         card_type="Tactic", effect="Place Bastion on friendly world. Free if no other structure there, otherwise cost 2 materiel."),
        EventCard(name="Unwavering Resolve",  warp_storm_move="Top Rgt/Bot Left", card_type="Scheme", effect="Instead of revealing an order, discard to rally all units in a system."),
        EventCard(name="Work of the Righteous",warp_storm_move="Top Rgt/Bot Left",card_type="Tactic", effect="Gain assets or materiel from a friendly world."),
    ],
    extra = {
        "homeworld":    "Трон-Прайм",
        "color_scheme": "#C0392B",
    },
)
