"""
faction_defs/eldar.py — фракция «Эльдары»

Хитрые и маневренные.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel, EventCard

ELDAR = Faction(
    id    = "eldar",
    name  = "Eldar",
    icon  = "◉",
    color        = "#F2C94C",
    home_tile_id = "home_eldar",
    flavor = (
        "По доминации вы можете переместить одного юнита из мира активной системы в дружественный мир."
            ),
    special_ability_name = "Телепорт",
    special_ability_desc = (
        " Особое свойство доминации:"
        "вы можете переместить одного юнита из мира активной системы в дружественный мир"
    ),
    unit_config = UnitConfig(
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=3, marines=1, mechanized=0, elite=0,
        fighters=2, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        # Характеристики построек — см. STRUCTURE_CATALOG в player_hand.py.
        factories=1, cities=0, bastions=0,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=0, discount_tokens=0, forge_tokens=0,
        # ── Характеристики юнитов (cost 2–5 + forge, strength 0–6, health 1–6, morale 0–6) ──
        # Эльдары: хрупкие, но с высокой моралью и точностью. Истребители — ударная сила.
        unit_stats={
            # name — отображаемое название; cost — стоимость; max_count — максимальный резерв
            "infantry":   dict(name="Aspect Warriors",    cost=2,               combat_strength=2, health=1, morale=2, max_count=6),
            "marines":    dict(name="Wraithguard",        cost=3,               combat_strength=2, health=4, morale=2, max_count=3),
            "mechanized": dict(name="Falcons",            cost=4,               combat_strength=3, health=4, morale=3, max_count=3),
            "elite":      dict(name="Warlock Titans",     cost=5, cost_forge=1, combat_strength=4, health=5, morale=3, max_count=3),
            "fighter":    dict(name="Hellebore Frigates", cost=2,               combat_strength=3, health=2, morale=1, max_count=6),
            "destroyer":  dict(name="Void Stalkers",      cost=4, cost_forge=1, combat_strength=4, health=5, morale=4, max_count=3),
        },
        # ── Стартовая колода боевых карт ──────────────────────────────────────
        battle_card_deck = '''Command of the Autarch
Hit and Run
Howling Banshees
Ranger Support
Striking Scorpions
Fire Dragon's Vengeance
Swooping Hawks
Wraithguard Advance
Wraithguard Support
Fire Prism
Spiritseer's Guidance
Wave Serpent
Holofield Emitter
Psychic Lance
'''.split('\n'),
    ),

    battle_cards=[
        BattleCard(
            name="Command of the Autarch",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 0, "M": 0},
            primary="Either rally 1 unit or gain 1 [M]. Play 1 card from your hand - gain its combat icons but not its abilities.",
        secondary = {"requires": ["-"], "effect": "-"},
),
BattleCard(
    name="Hit and Run",
    tier=-1,
    cost=0,
    icons={"G": 1, "S": 0, "M": 0},
    primary="Gain 2 (g).",
    secondary={"requires": ["Aspect", "Frigate"], "effect": "Spend 1 [M] to move 1 unit to adjacent friendly or uncontrolled area."},
),
BattleCard(
    name="Howling Banshees",
    tier=-1,
    cost=0,
    icons={"G": 1, "S": 0, "M": 0},
    primary="Gain 1 [?].",
    secondary={"requires": ["Aspect", "Frigate"], "effect": "Spend 1 [M] to force enemy to rout a unit of his choice."},
),
BattleCard(
    name="Ranger Support",
    tier=-1,
    cost=0,
    icons={"G": 0, "S": 1, "M": 1},
    primary="If attacking, gain 1 (g) and 1 (s). If defending, you may retreat 1 unit.",
    secondary={"requires": ["-"], "effect": "-"},
),
BattleCard(
    name="Striking Scorpions",
    tier=-1,
    cost=0,
    icons={"G": 0, "S": 1, "M": 0},
    primary="Gain 1 [?].",
    secondary={"requires": ["Aspect", "Frigate"], "effect": "Enemy loses 1 die of his choice."},
),
BattleCard(
    name="Fire Dragon's Vengeance",
    tier=0,
    cost=2,
    icons={"G": 2, "S": 0, "M": 0},
    primary="If you are attacking, enemy cannot gain (s) this execution round.",
    secondary={"requires": ["Aspect", "Frigate"], "effect": "Gain 2 (s)."},
),
BattleCard(
    name="Swooping Hawks",
    tier=0,
    cost=2,
    icons={"G": 0, "S": 2, "M": 0},
    primary="If you are defending, enemy loses 3 (g).",
    secondary={"requires": ["Aspect", "Frigate"], "effect": "Spend 1 [M] to gain 2 (g)."},
),
BattleCard(
    name="Wraithguard Advance",
    tier=0,
    cost=2,
    icons={"G": 1, "S": 0, "M": 1},
    primary="Gain 1 [?] or 1 [M]. Convert up to 2 [S] into [G].",
    secondary={"requires": ["Wraithguard", "Frigate", "Stalker"],
               "effect": "Enemy spends 1 [M] or routs unit of his choosing."},
),
BattleCard(
    name="Wraithguard Support",
    tier=0,
    cost=2,
    icons={"G": 0, "S": 1, "M": 1},
    primary="Gain 1 [?] or 1 [M]. Convert up to 2 [G] into [S].",
    secondary={"requires": ["Wraithguard", "Frigate", "Stalker"], "effect": "Spend 1 [M] to rally 1 unit."},
),
BattleCard(
    name="Fire Prism",
    tier=2,
    cost=4,
    icons={"G": 2, "S": 1, "M": 0},
    primary="Convert any [M] into [G].",
    secondary={"requires": ["Falcon", "Stalker"], "effect": "If attacking, gain 2 (g). If defending, force enemy to lose 5(s)."},
),
BattleCard(
    name="Spiritseer's Guidance",
    tier=2,
    cost=4,
    icons={"G": 1, "S": 1, "M": 1},
    primary="Gain 1 [M]. Rout 1 unit; units cannot suffer any damage this execution",
    secondary={"requires": ["-"], "effect": "-"},
),
BattleCard(
    name="Wave Serpent",
    tier=2,
    cost=4,
    icons={"G": 1, "S": 2, "M": 0},
    primary="Gain 1 [?]. Gain 3 (s) unless enemy spends 1 [M].",
    secondary={"requires": ["Falcon", "Stalker"],
               "effect": "Spend 1 [M] to move any number of Tier 0 and Tier 1 units to an adjacent area - may start a new combat.Same area if card is played again."},
),
BattleCard(
    name="Holofield Emitter",
    tier=3,
    cost=6,
    icons={"G": 1, "S": 2, "M": 1},
    primary="Gain 1 [?]. Draw 1 combat card.",
    secondary={"requires": ["Titan", "Stalker"], "effect": "Play 1 card from your hand - gain its combat icons but not its abilities."},
),
BattleCard(
    name="Psychic Lance",
    tier=3,
    cost=6,
    icons={"G": 2, "S": 1, "M": 0},
    primary="Gain 1 [?]. Enemy discards 1 random combat card from his hand.",
    secondary={"requires": ["Titan", "Stalker"], "effect": "Gain 4 (g) unless enemy discards 1 face up card of your choice."},
),
],

order_upgrades = [
        OrderUpgrade(
            name       = "Tactical Strikes",
            order_type = "advance",
            tier       = 0,
            cost       = 1,
            effect_1   = "Orbital Strike, once per round. Gain 1 [?].",
            effect_2   = "Spend 1 [M] to choose enemy unit on the world — this must suffer damage first.",
        ),
        OrderUpgrade(
            name       = "Wraithbone Singers",
            order_type = "deploy",
            tier       = 1,
            cost       = 2,
            effect_1   = "When purchasing structure, may place it on world containing exactly 1 different structure. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Farseer",
            order_type = "strategize",
            tier       = 1,
            cost       = 2,
            effect_1   = "This order can be resolved even if there are no units in the active system. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Corsair Raid",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            effect_1   = "After resolving a combat with this order, you may perform 1 orbital strike in the active system. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Strafing Run",
            order_type = "advance",
            tier       = 2,
            cost       = 3,
            effect_1   = "Orbital Strike, once per round. Bastions do not prevent orbital strike.",
            effect_2   = "Spend 1 [S] to move any ships in active system to friendly or empty voids in adjacent system. Command Level 2.",
        ),
    ],

    event_cards = [
        EventCard(name="Exodite Colony",    warp_storm_move="Top Rgt/Bot Left", card_type="Tactic", effect="Spend 1 materiel to place 1 free city on a friendly or uncontrolled world not containing a structure or Eldar objective token."),
        EventCard(name="Farsight",          warp_storm_move="Across",           card_type="Scheme", effect="At start of assess damage, discard to take all units in this combat and place on any friendly area."),
        EventCard(name="Legacy of Vaul",    warp_storm_move="Sideways",         card_type="Tactic", effect="Gain 2 (F)."),
        EventCard(name="Outcasts Returned", warp_storm_move="Across",           card_type="Tactic", effect="Either place 1 free Frigate in any uncontrolled void, or take 1 Frigate from any void and place it in any uncontrolled void."),
        EventCard(name="Outmanoeuvre",      warp_storm_move="Sideways",         card_type="Scheme", effect="At end of Planning Phase, discard to look at 1 of your order tokens anywhere in a stack. Then place on top or bottom of the stack."),
        EventCard(name="Path of the Warrior",warp_storm_move="Top Left/Bot Rgt",card_type="Tactic", effect="Purchase 1 combat upgrade, reducing its cost by 1 per friendly world with a city."),
        EventCard(name="Vicious Raids",     warp_storm_move="Top Left/Bot Rgt", card_type="Scheme", effect="When resolving an orbital strike, discard to reroll any dice, then gain 1 die of your choice."),
        EventCard(name="Warp Gate",         warp_storm_move="Top Rgt/Bot Left", card_type="Scheme", effect="Instead of revealing Order, discard to take any units from 1 area and place on any 1 area (friendly or uncontrolled)."),
    ],
    extra = {
        "homeworld":    "Umbra Station",
        "color_scheme": "#8E44AD",
    },
)
