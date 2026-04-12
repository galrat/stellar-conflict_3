"""
faction_defs/tau.py — фракция «Тау»

Тактическая, дальнобойная фракция. Низкое здоровье, высокая боевая мощь.
Dominance позволяет просматривать и использовать карты событий.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel, EventCard

TAU = Faction(
    id    = "tau",
    name  = "Tau",
    icon  = "⊕",
    color        = "#00897B",
    home_tile_id = "home_tau",
    flavor = (
        "Dominate: When you resolve a dominate order in a system containing at least 1 of your "
        "units or structures, you may draw 4 cards from the top of your event deck. "
        "Resolve the ability of 1 of those cards and discard the others."
    ),
    special_ability_name = "Dominate",
    special_ability_desc = (
        "When you resolve a dominate order in a system containing at least 1 of your units or structures, "
        "you may draw 4 cards from the top of your event deck. "
        "Resolve the ability of 1 of those cards and discard the others."
    ),
    unit_config = UnitConfig(
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=3, marines=2, mechanized=0, elite=0,
        fighters=0, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        factories=1, cities=0, bastions=0,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=0, discount_tokens=0, forge_tokens=0,
        # ── Характеристики юнитов ───────────────────────────────────────────
        unit_stats={
            "infantry":   dict(name="Fire Warriors",                    cost=2,               combat_strength=2, health=1, morale=2, max_count=6),
            "marines":    dict(name="XV8 Crisis Battlesuits",           cost=3,               combat_strength=3, health=3, morale=2, max_count=6),
            "mechanized": dict(name="TX7 Hammerhead Gunships",          cost=4,               combat_strength=4, health=4, morale=2, max_count=3),
            "elite":      dict(name="KX139 Supremacy Armour",           cost=5, cost_forge=1, combat_strength=4, health=5, morale=3, max_count=3),
            "fighter":    dict(name="Protector Cruisers",               cost=2,               combat_strength=3, health=1, morale=2, max_count=2),
            "destroyer":  dict(name="Custodian Carriers",               cost=5, cost_forge=1, combat_strength=5, health=4, morale=4, max_count=2),
        },
        # ── Стартовая колода боевых карт ──────────────────────────────────────
        battle_card_deck = [
            "Crossfire",
            "Kroot Hunting Packs",
            "Pathfinder Teams",
            "Stealth Teams",
            "Tactical Retreat",
        ],
    ),
    battle_cards = [
        # ── Начальные (бесплатные) ──────────────────────────────────────────
        BattleCard(
            name     = "Crossfire",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "At the start of the assess damage step of this execution round, your enemy loses 3 (g). Requires: Fire Warrior / Battlesuit / Protector.",
            effect_2 = "Gain 2 (g).",
        ),
        BattleCard(
            name     = "Kroot Hunting Packs",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "If you have fewer units than your enemy, gain 1 (s) and your enemy loses 1 [G]. Otherwise, gain 1 (g). Requires: Fire Warrior / Protector.",
            effect_2 = "Gain 1 [?].",
        ),
        BattleCard(
            name     = "Pathfinder Teams",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "Requires: Fire Warrior / Protector.",
            effect_2 = "If you are attacking, look at your enemy's facedown combat card. Play 1 combat card from your hand. Then discard this card.",
        ),
        BattleCard(
            name     = "Stealth Teams",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "Gain 1 (s). Requires: Fire Warrior / Protector.",
            effect_2 = "Your enemy may choose and rout 1 of his units. If he does not, force your enemy to lose 1 [G], 1 [S], or 1 [M].",
        ),
        BattleCard(
            name     = "Tactical Retreat",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "Retreat 1 of your units. If you do, you may spend 1 [M] to rally that unit. Requires: Fire Warrior / Protector.",
            effect_2 = "Gain 2 (s).",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Evasion",
            level    = CardLevel.ZERO,
            tier     = 0,
            cost     = 2,
            effect_1 = "Gain 1 [?]. Requires: Fire Warrior / Protector.",
            effect_2 = "During this execution round, if any of your unrouted Tier 0 units become routed or are destroyed, you may take them and place them back in this area at the end of the assess damage step.",
        ),
        BattleCard(
            name     = "Feigned Retreat",
            level    = CardLevel.ZERO,
            tier     = 0,
            cost     = 2,
            effect_1 = "Your enemy must reroll all [S]. You must reroll either 2 [S] or retreat 1 of your units. Requires: Fire Warrior / Battlesuit / Protector.",
            effect_2 = "If none of your units retreated during this execution round, gain 2 (g).",
        ),
        BattleCard(
            name     = "Kauyon",
            level    = CardLevel.ZERO,
            tier     = 0,
            cost     = 2,
            effect_1 = "Gain 1 (s). At the end of this execution round, if you are defending, you may move 1 of your units from an adjacent area to this area. Gain [?] equal to that unit's combat value.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Mont'ka",
            level    = CardLevel.ZERO,
            tier     = 0,
            cost     = 2,
            effect_1 = "Gain 2 (g). Choose 1 of your enemy's units or bastions. That unit or bastion suffers damage first during this execution round. Requires: Battlesuit / Protector.",
            effect_2 = "Spend up to 2 dice. For each dice you spend, gain 2 (g).",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Fire and Movement",
            level    = CardLevel.TWO,
            tier     = 2,
            cost     = 4,
            effect_1 = "Reroll all of your [G], [S], or [M]. Requires: Hammerhead / Custodian.",
            effect_2 = "During this execution round, when 1 of your units is destroyed during the assess damage step, you may retreat that unit instead.",
        ),
        BattleCard(
            name     = "Firefight",
            level    = CardLevel.TWO,
            tier     = 2,
            cost     = 4,
            effect_1 = "At the start of the assess damage step of this execution round, enemy loses 3 (g). Requires: Battlesuit / Hammerhead / Custodian.",
            effect_2 = "Gain 1 (s). Force your enemy to lose either 1 [G] or 1 [M].",
        ),
        BattleCard(
            name     = "Regroup",
            level    = CardLevel.TWO,
            tier     = 2,
            cost     = 4,
            effect_1 = "Spend any number of dice. For every 2 dice you spend, rally 1 of your units. Requires: Hammerhead / Custodian.",
            effect_2 = "Gain 2 [?].",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "For the Greater Good",
            level    = CardLevel.THREE,
            tier     = 3,
            cost     = 6,
            effect_1 = "Your enemy must reroll all [G]. Requires: Supremacy / Custodian.",
            effect_2 = "Force your enemy to lose 3 [M]. For each [M] your enemy cannot lose, gain 2 (g).",
        ),
        BattleCard(
            name     = "Supremacy",
            level    = CardLevel.THREE,
            tier     = 3,
            cost     = 6,
            effect_1 = "Gain 2 (g). Spend up to 2 [M]. For each [M], gain either 1 [G] or 1 [S]. Requires: Supremacy / Custodian.",
            effect_2 = "During this execution round, the health value of your enemy's units is reduced to 3.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Precision Strikes",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            effect_1   = "Orbital Strike, once per round. Gain 1 [?].",
            effect_2   = "May spend 1 die of your choice to choose 1 enemy unit on the world. That unit must suffer damage first during this orbital strike.",
        ),
        OrderUpgrade(
            name       = "Gue'vesa Allies",
            order_type = "deploy",
            tier       = 1,
            cost       = 2,
            effect_1   = "When you reveal this order in a system containing 1 of your units or structures and a friendly or uncontrolled world, you may spend 1 materiel to place 1 free Tier 0 unit on a friendly or uncontrolled area in the active system. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Mobilised Hunter Cadres",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            effect_1   = "Before you resolve this order, you may resolve an additional Advance Order using only 1 of your Tier 0 or Tier 1 units already in the active system. If combat occurs, resolve 1 execution round only. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Teachings of Tau'va",
            order_type = "strategize",
            tier       = 1,
            cost       = 2,
            effect_1   = "When you reveal this order token, you may place 3 of your order tokens from your play area onto the top of your event deck. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Targeting Array",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            effect_1   = "Orbital Strike, once per round. Enemy bastions do not prevent this orbital strike. Gain 1 [?].",
            effect_2   = "Command Level 1.",
        ),
    ],
    event_cards = [
        EventCard(name="Autonomous Drones",   warp_storm_move="Sideways",         card_type="Tactic", effect="Rout 1 enemy unit of Tier 2 or less that is in a system containing at least 1 of your units."),
        EventCard(name="Critical Strike",     warp_storm_move="Top Left/Bot Rgt", card_type="Scheme", effect="When an enemy unit suffers damage during combat, you may discard this card to destroy that unit."),
        EventCard(name="Denial of Supplies",  warp_storm_move="Across",           card_type="Scheme", effect="You may discard this card at the start of combat. If you do, your enemy cannot place (R) from his play area into the contested area during the reinforce step of combat."),
        EventCard(name="Evacuation",          warp_storm_move="Across",           card_type="Tactic", effect="Destroy 1 of your structures in any system to place 1 free structure on a different friendly world not containing a structure in the same or adjacent system."),
        EventCard(name="Philosophy of War",   warp_storm_move="Top Rgt/Bot Left", card_type="Scheme", effect="You may discard this card at the start of combat. If you do, replace any number of pairs of combat cards from your combat deck with pairs of combat cards of the same or lower Tier from your upgrade deck."),
        EventCard(name="Rapid Response",      warp_storm_move="Top Left/Bot Rgt", card_type="Tactic", effect="Choose a system. Move any of your units between friendly or uncontrolled areas in the chosen system."),
        EventCard(name="Sabotage",            warp_storm_move="Top Left/Bot Rgt", card_type="Tactic", effect="Destroy 1 of your unrouted units in any system to destroy 1 enemy structure in that system."),
        EventCard(name="War Council",         warp_storm_move="Sideways",         card_type="Scheme", effect="Before revealing an order during the Operations Phase, you may discard this card to rally all of your units in any 1 system."),
    ],
    extra = {
        "homeworld":    "T'au",
        "color_scheme": "#00897B",
    },
)
