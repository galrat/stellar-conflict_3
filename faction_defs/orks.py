"""
faction_defs/orks.py — фракция «Орки»

Орды зелёных варваров. Самая многочисленная фракция — много дешёвой пехоты
с высокой боевой силой, но низкой моралью. Сила в числе.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel, EventCard

ORKS = Faction(
    id    = "orks",
    name  = "Orks",
    icon  = "💀",
    color        = "#2E7D32",
    home_tile_id = "home_orks",
    flavor = (
        "Dominate: Purchase 1 unit and place it on a world in the active system"
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
            "mechanized": dict(name="Battlewagon",              cost=4,               combat_strength=3, health=5, morale=3, max_count=3),
            "elite":      dict(name="Gargant",                  cost=5, cost_forge=1, combat_strength=3, health=6, morale=3, max_count=3),
            "fighter":    dict(name="Onslaught Attack Ship",    cost=2,               combat_strength=1, health=3, morale=2, max_count=3),
            "destroyer":  dict(name="Kill Kroozer",             cost=4, cost_forge=1, combat_strength=3, health=6, morale=4, max_count=3),
        },
        # ── Стартовая колода боевых карт ──────────────────────────────────────
        battle_card_deck = ''''Ard Boyz
Gretchin
Mek Boyz
Shoota Boyz
Slugga Boyz
Biker Nobz
Mega Nobz
Sea of Green
Waaagh!!!!
Party Wagon
Rokkit Wagon
Weirdboyz
Smasher Gargant
Snapper Gargant
'''.split('\n'),
    ),

    battle_cards=[
        BattleCard(
            name="'Ard Boyz",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 2, "M": 0},
            primary="You must reroll all of your [G].",
            secondary={"requires": ["Boyz"], "effect": "Enemy must reroll 1 [G] for each unrouted Boyz."},
            image="faction_defs/orks_data/battle/'Ard Boyz.jpg",
        ),
        BattleCard(
            name="Gretchin",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 0, "M": 0},
            primary="Gain 1 (g) and 1 (s). Enemy rerolls 1 die of your choice.",
            secondary={"requires": ["Onslaught"],
                       "effect": "Destroy 1 Onslaught to force enemy to choose & destroy one of his units."},
            image="faction_defs/orks_data/battle/Gretchin.jpg",
        ),
        BattleCard(
            name="Mek Boyz",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 0, "M": 1},
            primary="Gain 1 [?].",
            secondary={"requires": ["Boyz", "Onslaught"],
                       "effect": "Enemy discards top card of his combat deck.  You gain the cards combat icons until end of this execution round."},
            image="faction_defs/orks_data/battle/Mek Boyz.jpg",
        ),
        BattleCard(
            name="Shoota Boyz",
            tier=-1,
            cost=0,
            icons={"G": 2, "S": 0, "M": 0},
            primary="You must reroll all of your [S].",
            secondary={"requires": ["Boyz"], "effect": "Enemy must reroll 1 [S] for each unrouted Boyz."},
            image="faction_defs/orks_data/battle/Shoota Boyz.jpg",
        ),
        BattleCard(
            name="Slugga Boyz",
            tier=-1,
            cost=0,
            icons={"G": 1, "S": 1, "M": 0},
            primary="Both sides must reroll all [M].",
            secondary={"requires": ["Boyz", "Onslaught"], "effect": "Rally 1 unit."},
            image="faction_defs/orks_data/battle/Slugga Boyz.jpg",
        ),
        BattleCard(
            name="Biker Nobz",
            tier=0,
            cost=2,
            icons={"G": 2, "S": 1, "M": 0},
            primary="Enemy must reroll all [G].",
            secondary={"requires": ["Nobz", "Onslaught"], "effect": "Gain 1 (g)."},
            image="faction_defs/orks_data/battle/Biker Nobz.jpg",
        ),
        BattleCard(
            name="Mega Nobz",
            tier=0,
            cost=2,
            icons={"G": 1, "S": 2, "M": 0},
            primary="Enemy must reroll all [S].",
            secondary={"requires": ["Nobz", "Onslaught"], "effect": "Gain 1 (s)."},
            image="faction_defs/orks_data/battle/Mega Nobz.jpg",
        ),
        BattleCard(
            name="Sea of Green",
            tier=0,
            cost=2,
            icons={"G": 1, "S": 1, "M": 0},
            primary="Place free (R) in this area. If you have more unrouted units, enemy spends 1[M] or routs 1 unit of his choice.",
            secondary={"requires": ["-"], "effect": "-"},
        ),
        BattleCard(
            name="Waaagh!!!!",
            tier=0,
            cost=2,
            icons={"G": 0, "S": 0, "M": 3},
            primary="Rally 1 unit.",
            secondary={"requires": ["Boyz", "Onslaught"], "effect": "Gain 1 (g) per unrouted Boyz/ Onslaught."},
            image="faction_defs/orks_data/battle/Waaagh!!!!.jpg",
        ),
        BattleCard(
            name="Party Wagon",
            tier=2,
            cost=4,
            icons={"G": 1, "S": 2, "M": 0},
            primary="Place free (R) in this area.",
            secondary={"requires": ["Wagon", "Kroozer"],
                       "effect": "If you have more unrouted units, gain 2 (g) and 2 (s)."},
            image="faction_defs/orks_data/battle/Party Wagon.jpg",
        ),
        BattleCard(
            name="Rokkit Wagon",
            tier=2,
            cost=4,
            icons={"G": 3, "S": 0, "M": 0},
            primary="-",
            secondary={"requires": ["Wagon", "Kroozer"], "effect": "Gain 3 (g). enemy may retreat 1 unit."},
            image="faction_defs/orks_data/battle/Rokkit Wagon.jpg",
        ),
        BattleCard(
            name="Weirdboyz",
            tier=2,
            cost=4,
            icons={"G": 1, "S": 1, "M": 1},
            primary="Both sides must reroll all dice",
            secondary={"requires": ["Boyz", "Onslaught"],
                       "effect": "In this combat, each time enemy gets (g) or (s), you gain the same tokens as well."},
            image="faction_defs/orks_data/battle/Weirdboyz.jpg",
        ),
        BattleCard(
            name="Smasher Gargant",
            tier=3,
            cost=6,
            icons={"G": 2, "S": 3, "M": 0},
            primary="-",
            secondary={"requires": ["Gargant", "Kroozer"],
                       "effect": "Choose enemy unit. Destroy unit unless enemy spends dice equal to its Tier."},
            image="faction_defs/orks_data/battle/Smasher Gargant.jpg",
        ),
        BattleCard(
            name="Snapper Gargant",
            tier=3,
            cost=6,
            icons={"G": 4, "S": 1, "M": 0},
            primary="-",
            secondary={"requires": ["Gargant", "Kroozer"], "effect": "Discard 1 of enemy face up combat cards"},
            image="faction_defs/orks_data/battle/Snapper Gargant.jpg",
        ),
    ],

    order_upgrades=[
        OrderUpgrade(
            name="Lootin'",
            order_type="advance",
            tier=0,
            cost=1,
            primary="Orbital Strike, once per round. Gain 1 [?].",
            secondary="Spend 1 die to gain 1 materiel and force enemy to lose 1 materiel.",
            image="faction_defs/orks_data/order/Lootin'.jpg",
        ),
        OrderUpgrade(
            name="Werk Fasta!",
            order_type="deploy",
            tier=1,
            cost=2,
            primary="May purchase structure before purchasing units. Once per round.",
            secondary="Command Level 1.",
            image="faction_defs/orks_data/order/Werk Fasta!.jpg",
        ),
        OrderUpgrade(
            name="The Green Tide",
            order_type="strategize",
            tier=1,
            cost=2,
            primary="When revealed, can resolve it as one of the other orders instead. Once per round.",
            secondary="Command Level 1.",
            image="faction_defs/orks_data/order/The Green Tide.jpg",
        ),
        OrderUpgrade(
            name="Ork Roks",
            order_type="advance",
            tier=0,
            cost=2,
            primary="Can move up to 2 units through 1 uncontrolled void as if it were a friendly area. Once per round.",
            secondary="Command Level 1.",
            image="faction_defs/orks_data/order/Ork Roks.jpg",
        ),
        OrderUpgrade(
            name="Stealin'!",
            order_type="advance",
            tier=2,
            cost=3,
            primary="Orbital Strike, once per round. Bastions do not prevent orbital strike.",
            secondary="Spend 1 [M] to discard an enemy asset token; you gain that token. Command Level 2.",
            image="faction_defs/orks_data/order/Stealin'!.jpg",
        ),
    ],

    event_cards=[
        EventCard(name="Gitz Dem!", warp_storm_move="Top Rgt/Bot Left", card_type="Scheme",
                  effect="When an enemy unit routs in combat, discard to destroy that unit.",
                  image="faction_defs/orks_data/events/Gitz Dem!.jpg"),
        EventCard(name="How We Getz Here?", warp_storm_move="Top Rgt/Bot Left", card_type="Tactic",
                  effect="Take 1 unit from any world and place on any uncontrolled world.",
                  image="faction_defs/orks_data/events/How We Getz Here?.jpg"),
        EventCard(name="Letz Get Fightin'", warp_storm_move="Across", card_type="Tactic",
                  effect="Either place 2 free Boyz on a world containing a Nob, or 1 free Boyz on a friendly world.",
                  image="faction_defs/orks_data/events/Letz Get Fightin'.jpg"),
        EventCard(name="Lootin' 'n Stealin'", warp_storm_move="Top Left/Bot Rgt", card_type="Tactic",
                  effect="Gain 2 materiel. Choose a player to lose 1 asset of your choice.",
                  image="faction_defs/orks_data/events/Lootin' 'n Stealin'.jpg"),
        EventCard(name="Moar Boyz!", warp_storm_move="Sideways", card_type="Tactic", effect="Gain 2 (R).",
                  image="faction_defs/orks_data/events/Moar Boyz!.jpg"),
        EventCard(name="Mob Up!", warp_storm_move="Sideways", card_type="Scheme",
                  effect="Instead of revealing Order, discard to resolve an Advance Order in a system with at least 2 of your own units.",
                  image="faction_defs/orks_data/events/Mob Up!.jpg"),
        EventCard(name="Teer it Down!", warp_storm_move="Top Left/Bot Rgt", card_type="Scheme",
                  effect="End of assess damage step in Ork combat, discard to destroy 1 structure on that world.",
                  image="faction_defs/orks_data/events/Teer it Down!.jpg"),
        EventCard(name="Warboss", warp_storm_move="Across", card_type="Scheme",
                  effect="When purchasing, reduce cost by 1 per (R) you have.",
                  image="faction_defs/orks_data/events/Warboss.jpg"),
    ],
    extra = {
        "homeworld":    "Гхазгхулл",
        "color_scheme": "#2E7D32",
    },
)
