"""
faction_defs/chaos.py — фракция «Хаос»

Союз свободных миров. Сбалансированная фракция с акцентом на координацию
и адаптивность. Сильна в обороне и логистике.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel, EventCard

CHAOS = Faction(
    id    = "chaos",
    name  = "Хаос",
    icon  = "⬡",
    color         = "#FF0000", # #E53935 #FF3B30 #E53935
    home_tile_id  = "home_chaos",
    flavor = (
        "Особое свойство доминации:"
        "вы можете переместить культиста на свободный или дружественный мир соседней системы "

    ),
    special_ability_name = "Особое свойство",
    special_ability_desc = (
        "Вы можете переместить культиста на свободный или дружественный мир соседней системы"
    ),
    unit_config = UnitConfig(
        # ── Стартовый состав войск (по базе данных Forbidden Stars) ─────────
        infantry=2, marines=2, mechanized=0, elite=0,
        fighters=1, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        factories=1, cities=0, bastions=0,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=0, discount_tokens=0, forge_tokens=0,
        # ── Характеристики юнитов (источник: Forbidden_Stars_Unit_and_Card_Database) ──
        unit_stats={
            # name — название; cost — стоимость; max_count — макс. резерв
            "infantry":   dict(name="Cultist",                   cost=2,               combat_strength=1, health=2, morale=2, max_count=9),
            "marines":    dict(name="Chaos Space Marine",        cost=3,               combat_strength=3, health=3, morale=2, max_count=6),
            "mechanized": dict(name="Helbrute",                   cost=4,               combat_strength=3, health=4, morale=3, max_count=3),
            "elite":      dict(name="Chaos Reaver Titan",         cost=5, cost_forge=1, combat_strength=4, health=5, morale=3, max_count=3),
            "fighter":    dict(name="Iconoclast Destroyer",       cost=2,               combat_strength=2, health=2, morale=2, max_count=3),
            "destroyer":  dict(name="Repulsive Cruiser",          cost=5, cost_forge=1, combat_strength=4, health=5, morale=4, max_count=3),
        },
        # ── Стартовая колода боевых карт ──────────────────────────────────────
        battle_card_deck = '''Dark Faith
Foul Worship
Impure Zeal
Khorne's Rage
Lure of Chaos
Mark of Khorne
Mark of Nurgle
Mark of Slaanesh
Mark of Tzeentch
Chaos United
Daemonic Resilience
Inhuman Strength
Chaos Victorious
Death and Despair
'''.split('\n')
    ),
    battle_cards=[
        BattleCard(
            name="Dark Faith",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 0, "M": 1},
            primary="Gain 1 [M].",
            secondary={"requires": ["Cultist", "Iconoclast"],
                       "effect": "If more [M] than enemy, place free Cultist on another friendly or uncontrolled world in system."},
        ),
        BattleCard(
            name="Foul Worship",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 1, "M": 0},
            primary="Gain 1 [?].",
            secondary={"requires": ["Cultist", "Iconoclast"],
                       "effect": "If enemy has routed unit, gain 1 (s) per unrouted Cultist or Iconoclast."},
        ),
        BattleCard(
            name="Impure Zeal",
            tier=-1,
            cost=0,
            icons={"G": 1, "S": 1, "M": 0},
            primary="If more [M] than enemy, rally 1 unit.",
            secondary={"requires": ["Cultist", "Iconoclast"],
                       "effect": "Enemy routs 1 unit, or you gain 1 (g) per unrouted Cultist or Iconoclast."},
        ),
        BattleCard(
            name="Khorne's Rage",
            tier=-1,
            cost=0,
            icons={"G": 1, "S": 0, "M": 0},
            primary="Spend 1 [G] to gain 3 (g).",
            secondary={"requires": ["Marine", "Iconoclast"],
                       "effect": "Enemy spends 1 [S] or routs unit of his choosing."},
        ),
        BattleCard(
            name="Lure of Chaos",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 0, "M": 1},
            primary="Enemy may choose a unit to rout to gain 1 [?]. Otherwise, place a free Cultist or Iconoclast in the area.",
        secondary = {"requires": ["Cultist", "Iconoclast"], "effect": "Gain 2 (g) or 2 (s)."},
),
BattleCard(
    name="Mark of Khorne",
    tier=0,
    cost=2,
    icons={"G": 2, "S": 0, "M": 0},
    primary="Spend 1 [G] or 1 [M] to gain 3 (g).",
    secondary={"requires": ["Marine", "Iconoclast"], "effect": "Enemy spends 1 [S] or destroys 1 routed unit."},
),
BattleCard(
    name="Mark of Nurgle",
    tier=0,
    cost=2,
    icons={"G": 0, "S": 2, "M": 0},
    primary="Spend 1 [S] or 1 [M] to gain 3 (s).",
    secondary={"requires": ["Marine", "Iconoclast"], "effect": "Enemy destroys 1 routed unit, otherwise gain 2 (s)."},
),
BattleCard(
    name="Mark of Slaanesh",
    tier=0,
    cost=2,
    icons={"G": 1, "S": 1, "M": 0},
    primary="Gain 1 [?]. If more [M] than enemy, he routs 1 unit of his choice.",
    secondary={"requires": ["Marine"], "effect": "If enemy has routed unit, place free Cultist on this world."},
),
BattleCard(
    name="Mark of Tzeentch",
    tier=0,
    cost=2,
    icons={"G": 0, "S": 0, "M": 2},
    primary="Gain 1 [M]. If more [M] than enemy, upgrade 1 Cultist / (R) to Chaos Marine.",
    secondary = {"requires": ["Marine", "Iconoclast"], "effect": "Convert up to 2 [M] to [G] and/or [S]."},
),
BattleCard(
    name="Chaos United",
    tier=2,
    cost=4,
    icons={"G": 1, "S": 1, "M": 1},
    primary="Enemy may rout 1 of its units.  If not, gain a die of your choice.",
    secondary={"requires": ["Cultist", "Marine", "Helbrute"], "effect": "Take 1 unit from any world and place it on this world.Command level cannot exceed number of Cultists in this system."},
),
BattleCard(
    name="Daemonic Resilience",
    tier=2,
    cost=4,
    icons={"G": 0, "S": 2, "M": 1},
    primary="Gain 1 [M] or 1 [S].",
    secondary={"requires": ["Helbrute", "Cruiser"], "effect": "Gain 4 (s) unless enemy destroys 1 unit of his choice."},
),
BattleCard(
    name="Inhuman Strength",
    tier=2,
    cost=4,
    icons={"G": 2, "S": 0, "M": 1},
    primary="Gain 1 [G] or 1 [M].",
    secondary={"requires": ["Helbrute", "Cruiser"], "effect": "Destroy 1 unit to gain 4 (g)."},
),
BattleCard(
    name="Chaos Victorious",
    tier=3,
    cost=6,
    icons={"G": 1, "S": 1, "M": 1},
    primary="Gain 2 [?]. If more [M] than enemy, rout all his Tier 0 units.",
    secondary={"requires": ["Titan", "Cruiser"], "effect": "Rout 1 enemy unit."},
),
BattleCard(
    name="Death and Despair",
    tier=3,
    cost=6,
    icons={"G": 2, "S": 0, "M": 1},
    primary="Gain 2 [G] or 2 [M]. Spend any [M], each destroys 1 Tier 0 unit.",
    secondary={"requires": ["Titan", "Cruiser"], "effect": "If more [M] than enemy, destroy 1 routed unit."},
),
]
,
    order_upgrades = [
        OrderUpgrade(
            name       = "Fear from Above",
            order_type = "advance",
            tier       = 0,
            cost       = 1,
            primary   = "Gain [?], spend 1 [M] to force any unit taking damage to rout.",

        ),
        OrderUpgrade(
            name       = "Dread Ritual",
            order_type = "deploy",
            tier       = 1,
            cost       = 2,
            primary   = "Purchase 1 Tier 0–2 unit; reduce cost by 1 per Cultist in active system.",

        ),
        OrderUpgrade(
            name       = "Favour of the Dark Gods",
            order_type = "strategize",
            tier       = 1,
            cost       = 2,
            primary   = "Place 2 order tokens from play area onto top of event deck.",

        ),
        OrderUpgrade(
            name       = "From the Warp",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            primary   = "Ships can move through Warp Storms."

        ),
        OrderUpgrade(
            name       = "Complete Destruction",
            order_type = "advance",
            tier       = 2,
            cost       = 3,
            primary   = "Bastions do not prevent orbital strike. Spend 2 [S] to force enemy to choose unit or structure to destroy",

        ),
    ],
    event_cards = [
        EventCard(name="Blight of Nurgle",        warp_storm_move="Across",           card_type="Scheme", effect="Instead of playing an order, discard to rout an enemy unit in a system containing 1+ of your units."),
        EventCard(name="Incantation of Tzeentch", warp_storm_move="Across",           card_type="Tactic", effect="Draw 3 cards from Event Deck, choose 1 and resolve its ability (not Warp Storm move)."),
        EventCard(name="Prayer to the Dark Gods", warp_storm_move="Top Rgt/Bot Left", card_type="Scheme", effect="When a player moves a Warp Storm, discard to prevent this, and move the Warp Storm in any direction."),
        EventCard(name="Prophets and Signs",      warp_storm_move="Top Rgt/Bot Left", card_type="Tactic", effect="Place 2 free Cultists on friendly world not containing Cultists, or 1 free Cultist on any friendly world."),
        EventCard(name="Seduced by Chaos",        warp_storm_move="Sideways",         card_type="Scheme", effect="At end of assess damage in a Chaos combat, discard to rout 1 unit in combat."),
        EventCard(name="Spoils of War",           warp_storm_move="Top Left/Bot Rgt", card_type="Tactic", effect="Gain 1 (F) and 1 (R)."),
        EventCard(name="Through the Warp",        warp_storm_move="Top Left/Bot Rgt", card_type="Scheme", effect="When resolving Advance Order, discard to allow units to move through Warp Storms. If combat occurs, gain 1 [M] at start."),
        EventCard(name="Touched by the Warp",     warp_storm_move="Sideways",         card_type="Tactic", effect="Destroy 1 Cultist to gain 1 upgrade card. Tier cannot exceed number of Warp Storms bordering the system."),
    ],
    extra = {
        "homeworld":    "Терра Федерация",
        "color_scheme": "#4A90D9",
    },
)
