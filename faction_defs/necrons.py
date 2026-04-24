"""
faction_defs/necrons.py — фракция «Некроны»

Бессмертные машины-воины. Неуязвимы к морали — Warriors имеют morale 0.
Низкий максимальный резерв, но высокое здоровье. C'tan — уникальный юнит (max 1).
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel, EventCard

NECRONS = Faction(
    id    = "necrons",
    name  = "Necrons",
    icon  = "☥",
    color        = "#00BCD4",
    home_tile_id = "home_necrons",
    flavor = (
        "Dominate: Take any of your units from 1 world and place them on a friendly world "
        "containing a structure in the active system."
    ),
    special_ability_name = "Dominate",
    special_ability_desc = (
        "Take any of your units from 1 world and place them on a friendly world "
        "containing a structure in the active system."
    ),
    unit_config = UnitConfig(
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=4, marines=1, mechanized=0, elite=0,
        fighters=0, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        factories=1, cities=0, bastions=0,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=0, discount_tokens=0, forge_tokens=0,
        # ── Характеристики юнитов ───────────────────────────────────────────
        unit_stats={
            "infantry":   dict(name="Warriors",                   cost=2,               combat_strength=2, health=3, morale=0, max_count=4),
            "marines":    dict(name="Immortals",                  cost=3,               combat_strength=3, health=4, morale=1, max_count=3),
            "mechanized": dict(name="Monoliths",                  cost=4,               combat_strength=3, health=5, morale=2, max_count=2),
            "elite":      dict(name="C'tan Star God Shard",       cost=5, cost_forge=1, combat_strength=3, health=6, morale=3, max_count=1),
            "fighter":    dict(name="Scythe-Class Harvest Ships", cost=2,               combat_strength=2, health=3, morale=1, max_count=2),
            "destroyer":  dict(name="Cairn-Class Tomb Ships",     cost=5, cost_forge=1, combat_strength=3, health=6, morale=4, max_count=2),
        },
        # ── Стартовая колода боевых карт ──────────────────────────────────────
        battle_card_deck = [
            "Attack Subroutines",
            "Everlasting Conquest",
            "Flayed Ones",
            "Foretelling Cryptek",
            "Warrior Phalanx",
        ],
    ),
    battle_cards=[
        BattleCard(
            name="Attack Subroutines",
            tier=-1,
            cost=0,
            icons={"G": 2, "S": 0, "M": 0},
            primary="-",
            secondary={"requires": ["Warrior", "Harvest Ship"], "effect": "Gain 1 [M]."},
        ),
        BattleCard(
            name="Everlasting Conquest",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 0, "M": 0},
            primary="Gain 1 [M]. Rally 1 of your units.",
            secondary={"requires": ["Warrior", "Immortal", "Harvest Ship"],
                       "effect": "For each [M] you have, gain either 1 [G] or 1 [S]."},
        ),
        BattleCard(
            name="Flayed Ones",
            tier=-1,
            cost=0,
            icons={"G": 1, "S": 0, "M": 0},
            primary="Gain 2 (g).",
            secondary={"requires": ["Warrior", "Harvest Ship"],
                       "effect": "If enemy has any [M], gain 1 [M] and force enemy to lose 1[M]."},
        ),
        BattleCard(
            name="Foretelling Cryptek",
            tier=-1,
            cost=0,
            icons={"G": 0, "S": 0, "M": 1},
            primary="Gain 1 [G], 1 [S] or 1 [M]. Spend 1 [M] to either take 1 of your units and place it routed on a friendly world containing a structure or take 1 of your Tier 0 or Tier 1 units from a world containing a structure and place it on this world.",
        secondary = {"requires": ["-"], "effect": "-"},
),
BattleCard(
    name="Warrior Phalanx",
    tier=-1,
    cost=0,
    icons={"G": 0, "S": 2, "M": 0},
    primary="-",
    secondary={"requires": ["Warrior", "Harvest Ship"], "effect": "Gain 1 [M]."},
),
BattleCard(
    name="Canoptek Swarm",
    tier=0,
    cost=2,
    icons={"G": 1, "S": 0, "M": 1},
    primary="Gain 1 [?]. Place 1 free reinforcement token in this area.",
    secondary={"requires": ["-"], "effect": "-"},
),
BattleCard(
    name="Destroyers",
    tier=0,
    cost=2,
    icons={"G": 2, "S": 0, "M": 1},
    primary="Spend either 1 [S] or 1 [M] to gain 2 (s).",
    secondary={"requires": ["Immortal", "Harvest Ship"],
               "effect": "If your enemy has at least 1 routed unit, gain 2 (g)."},
),
BattleCard(
    name="Lychguard",
    tier=0,
    cost=2,
    icons={"G": 0, "S": 2, "M": 1},
    primary="Rout 1 of your units. If you do, your enemy chooses and routs 1 of his units.",
secondary = {"requires": ["Immortal", "Harvest Ship"],
             "effect": "If your enemy has at least 1 routed unit, gain 2 (s)."},
),
BattleCard(
    name="Overlord's Will",
    tier=0,
    cost=2,
    icons={"G": 0, "S": 0, "M": 3},
    primary="Rally 1 of your units. Reroll up to 2 of your dice.",
    secondary={"requires": ["-"], "effect": "-"},
),
BattleCard(
    name="Doomsday Phalanx",
    tier=2,
    cost=4,
    icons={"G": 3, "S": 0, "M": 0},
    primary="Force your enemy to lose 1 [S].",
    secondary={"requires": ["Monolith", "Tomb Ship"],
               "effect": "When an enemy unit is routed during the assess damage step of this execution round, it is destroyed unless your enemy spends 1[S]."},
),
BattleCard(
    name="Monolith Phalanx",
    tier=2,
    cost=4,
    icons={"G": 2, "S": 1, "M": 0},
    primary="If your units or bastions suffer no damage during this execution round, your enemy chooses and retreats 1 of his units.",
    secondary={"requires": ["Monolith", "Tomb Ship"], "effect": "Gain 3 (s)."},
),
BattleCard(
    name="Triarch Praetorians",
    tier=2,
    cost=4,
    icons={"G": 1, "S": 1, "M": 1},
    primary="Either rally 1 of your units or place 1 free reinforcement token in this area.",
secondary = {"requires": ["Warrior", "Harvest Ship"], "effect": "For each unrouted Warrior or Harvest Ship, spend up to 1 die to gain 1[G], 1[S] or 1[M]."},
),
BattleCard(
    name="Shard of the Nightbringer",
    tier=3,
    cost=6,
    icons={"G": 2, "S": 1, "M": 0},
    primary="Either gain 3 (g) or destroy 1 Tier 0 unit.",
    secondary={"requires": ["C'tan Shard", "Tomb Ship"], "effect": "Destroy 1 Tier 0 or Tier 1 unit."},
),
BattleCard(
    name="Shard of the Deceiver",
    tier=3,
    cost=6,
    icons={"G": 1, "S": 1, "M": 2},
    primary="Play the top card from your combat deck. Do not resolve its abilities, but gain its combat icons during this combat.",
    secondary = {"requires": ["C'tan Shard", "Tomb Ship"], "effect": "Take your C'tan Shard and place it on any friendly world."},
),
],
    order_upgrades = [
        OrderUpgrade(
            name       = "Harvest Raid",
            order_type = "advance",
            tier       = 0,
            cost       = 1,
            primary   = "Orbital Strike, once per round. Gain 1 [?].",
            secondary = "You may choose 1 Tier 0 unit on the world. That unit must suffer damage first during this orbital strike.",
        ),
        OrderUpgrade(
            name       = "Eternity Gate",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            primary   = "After moving your units, you may take any of your Tier 0 or Tier 1 units from 1 friendly world containing a structure and place them on any world in the active system containing an unrouted Monolith. Once per round.",
            secondary = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Reanimation Protocols",
            order_type = "strategize",
            tier       = 1,
            cost       = 2,
            primary   = "When you reveal this order token, rally all of your units in the active system and all of your ground units in every other system. Once per round.",
            secondary = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Tomb Worlds",
            order_type = "deploy",
            tier       = 1,
            cost       = 2,
            primary   = "After you resolve this order, if you purchased at least 1 unit or structure, you may purchase 1 bastion and place it on a friendly or uncontrolled world in either the active system or an adjacent system. Once per round.",
            secondary = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Translocation Crypts",
            order_type = "deploy",
            tier       = 1,
            cost       = 2,
            primary   = "While resolving this order, you may treat all your cities in the active system as factories. Once per round.",
            secondary = "Command Level 1.",
        ),
    ],
    event_cards = [
        EventCard(name="Chronomancy",           warp_storm_move="Across",           card_type="Scheme", effect="At start of execution round of combat, you may discard this card to draw up to 2 combat cards and then discard that many combat cards from your hand."),
        EventCard(name="Deathmarks",            warp_storm_move="Across",           card_type="Scheme", effect="At start of execution round of combat, may discard this card to rout 1 enemy Tier 0 or Tier 1 unit."),
        EventCard(name="Doom Scythes",          warp_storm_move="Sideways",         card_type="Scheme", effect="At start of execution round of combat, may discard this card and rout up to 2 of your units. If you do, enemy destroys 1 (R) in this area for each unit you routed."),
        EventCard(name="Remorseless Advance",   warp_storm_move="Top Rgt/Bot Left", card_type="Scheme", effect="At start of execution round of combat, may discard this card to resolve 1 additional assess damage step during execution round."),
        EventCard(name="Resurrection Orb",      warp_storm_move="Top Rgt/Bot Left", card_type="Scheme", effect="When 1 of your Tier 0 or Tier 1 units is routed or destroyed during combat, may discard this card to take it and place it back unrouted in this area at the end of the assess damage step."),
        EventCard(name="Tomb World Awakening",  warp_storm_move="Sideways",         card_type="Tactic", effect="Purchase 1 structure and place it on a friendly world not containing a structure."),
        EventCard(name="Tomb World Archives",   warp_storm_move="Top Left/Bot Rgt", card_type="Tactic", effect="Purchase 1 combat upgrade."),
        EventCard(name="Wrath of the Void Dragon",warp_storm_move="Top Left/Bot Rgt",card_type="Scheme",effect="At start of execution round of combat, may discard this card. If you do, you and your enemy suffer an additional 3 damage during this assess damage step."),
    ],
    extra = {
        "homeworld":    "Tomb World",
        "color_scheme": "#00BCD4",
    },
)
