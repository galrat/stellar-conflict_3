"""
faction_defs/tyranids.py — фракция «Тираниды»

Биологический рой. Высокая мораль, уничтожают свои юниты ради выгоды в бою.
Dominance позволяет набирать дополнительные жетоны ресурсов (до 4 каждого типа).
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel, EventCard

TYRANIDS = Faction(
    id    = "tyranids",
    name  = "Tyranids",
    icon  = "🧬",
    color        = "#6A1B9A",
    home_tile_id = "home_tyranids",
    flavor = (
        "Dominate: Gain 1 additional asset token of your choice. "
        "You can have up to 4 of each asset token in your play area at any time."
    ),
    special_ability_name = "Dominate",
    special_ability_desc = (
        "Gain 1 additional asset token of your choice. "
        "You can have up to 4 of each asset token in your play area at any time."
    ),
    unit_config = UnitConfig(
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=3, marines=0, mechanized=0, elite=0,
        fighters=1, destroyers=1,
        # ── Стартовые постройки ─────────────────────────────────────────────
        factories=1, cities=0, bastions=1,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=1, discount_tokens=0, forge_tokens=0,
        # ── Характеристики юнитов ───────────────────────────────────────────
        unit_stats={
            "infantry":   dict(name="Gaunts",                   cost=2,               combat_strength=1, health=1, morale=3, max_count=6),
            "marines":    dict(name="Warriors",                 cost=3,               combat_strength=3, health=2, morale=3, max_count=6),
            "mechanized": dict(name="Carnifexes",               cost=4,               combat_strength=4, health=3, morale=3, max_count=3),
            "elite":      dict(name="Hierophant Bio-Titans",    cost=5, cost_forge=1, combat_strength=5, health=4, morale=3, max_count=3),
            "fighter":    dict(name="Devourer Bio-Ships",       cost=2,               combat_strength=1, health=2, morale=3, max_count=6),
            "destroyer":  dict(name="Leviathan Hive Ships",     cost=5, cost_forge=1, combat_strength=3, health=6, morale=4, max_count=3),
        },
        # ── Стартовая колода боевых карт ──────────────────────────────────────
        battle_card_deck = [
            "Burrowing Organisms",
            "Genestealer Hybrids",
            "Hive Tyrant",
            "Hormagaunt Brood",
            "Rain of Spores",
        ],
    ),
    battle_cards = [
        # ── Начальные (бесплатные) ──────────────────────────────────────────
        BattleCard(
            name     = "Burrowing Organisms",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "If attacking, gain 2 (g). If defending, either place 1 free (R) in this area or destroy 2 unrouted Gaunts to place 1 free bastion on this world if it does not already contain a structure.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Genestealer Hybrids",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "Requires: Gaunt / Devourer.",
            effect_2 = "Force enemy to lose 1 [G], 1 [S], or 1 [M], whichever he has most of. If tied, you choose. Then gain 1 [G], 1 [S], or 1 [M], whichever your enemy lost.",
        ),
        BattleCard(
            name     = "Hive Tyrant",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "Play 1 combat card from your hand. Do not resolve its abilities, but gain its combat icons during this combat. Requires: Warrior / Hive Ship.",
            effect_2 = "Either rally 1 of your units. Spend 1 [M] to gain either 1 [G] or 1 [S].",
        ),
        BattleCard(
            name     = "Hormagaunt Brood",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "Gain 1 (s). Requires: Gaunt / Devourer.",
            effect_2 = "Destroy 1 unrouted Gaunt or Devourer to gain 3 (g).",
        ),
        BattleCard(
            name     = "Rain of Spores",
            level    = CardLevel.INITIAL,
            tier     = -1,
            cost     = 0,
            effect_1 = "Destroy 1 unrouted Devourer in this system to place 1 free Warrior on this world.",
            effect_2 = "—",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Ripper Swarms",
            level    = CardLevel.ZERO,
            tier     = 0,
            cost     = 2,
            effect_1 = "Gain 2 (g). Requires: Gaunt / Devourer.",
            effect_2 = "At the end of this execution round, gain 1 materiel for each unit destroyed during this execution round, to a maximum of 2.",
        ),
        BattleCard(
            name     = "Termagaunt Brood",
            level    = CardLevel.ZERO,
            tier     = 0,
            cost     = 2,
            effect_1 = "Either gain 1 (g) for each unrouted Gaunt or Devourer or place 1 free reinforcement token in this area. For each Gaunt or Devourer destroyed or routed this execution round, reduce damage you suffer in the next execution round by 1.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Warrior Brood",
            level    = CardLevel.ZERO,
            tier     = 0,
            cost     = 2,
            effect_1 = "Destroy 1 of your unrouted units to gain 2 (s) and reduce the damage you suffer in the next execution round by 2. Requires: Warrior / Hive Ship.",
            effect_2 = "Reroll all of your [G], [S], or [M].",
        ),
        BattleCard(
            name     = "Winged Horror",
            level    = CardLevel.ZERO,
            tier     = 0,
            cost     = 2,
            effect_1 = "Destroy 1 of your unrouted units to gain 3 (g). Requires: Warrior / Devourer.",
            effect_2 = "Your enemy may allow you to gain 2 (s). If he does not, add 2 to your offence value in the next execution round.",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Crushing Claws",
            level    = CardLevel.TWO,
            tier     = 2,
            cost     = 4,
            effect_1 = "Destroy 1 of your unrouted units to gain 3 (g). Requires: Carnifex / Hive Ship.",
            effect_2 = "Spend either 1 [G] or 1 [M] to force your enemy to lose 2 [S].",
        ),
        BattleCard(
            name     = "Scything Talons",
            level    = CardLevel.TWO,
            tier     = 2,
            cost     = 4,
            effect_1 = "During this execution round, if enemy has to assign any damage, he assigns 3 additional damage. Requires: Carnifex / Hive Ship.",
            effect_2 = "Destroy 1 unrouted Carnifex or Hive Ship to gain 3 (g) and 2 (s).",
        ),
        BattleCard(
            name     = "Synaptic Control",
            level    = CardLevel.TWO,
            tier     = 2,
            cost     = 4,
            effect_1 = "Gain 1 [?]. Place 1 free (R) in this area. Requires: Warrior / Hive Ship.",
            effect_2 = "Rally 1 of your units. Gain either 1 (g) or 1 (s) for each of your unrouted units in excess of the number of your enemy's unrouted units.",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Glory of the Swarm",
            level    = CardLevel.THREE,
            tier     = 3,
            cost     = 6,
            effect_1 = "Spend any number of [M]. For each [M] you spend, gain either 1 [G] or 1 [S]. Requires: Bio-Titan / Hive Ship.",
            effect_2 = "Rally all of your units. During this execution round, you assign damage to your enemy's units and bastions.",
        ),
        BattleCard(
            name     = "Overwhelming Presence",
            level    = CardLevel.THREE,
            tier     = 3,
            cost     = 6,
            effect_1 = "Destroy 1 of your unrouted units to gain either 3 (g) or 3 (s). Requires: Bio-Titan / Hive Ship.",
            effect_2 = "Force your enemy to choose 3 times to either choose and rout 1 of his units or lose 1 die of his choice.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Genestealer Infiltration",
            order_type = "advance",
            tier       = 0,
            cost       = 1,
            effect_1   = "Orbital Strike, once per round. Gain 1 [?].",
            effect_2   = "May spend up to 2 [G] to gain 1 (R) for each [G] you spend.",
        ),
        OrderUpgrade(
            name       = "Breeding Chambers",
            order_type = "deploy",
            tier       = 1,
            cost       = 2,
            effect_1   = "After you resolve this order, may purchase up to 2 units for each unrouted Hive Ship in the active system and place them on any friendly or unfriendly worlds in the active system. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Capillary Towers",
            order_type = "strategize",
            tier       = 1,
            cost       = 2,
            effect_1   = "After you resolve this order, may destroy any of your units or structures on a world in the active system to temporarily gain materiel equal to their materiel cost. Use this materiel only to purchase ships in the active system. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Without Number",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            effect_1   = "While resolving this order in a system in which you have an unrouted ship, you may place 1 free (R) in the contested area at the start of a reinforce step of combat. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Mycetic Spores",
            order_type = "advance",
            tier       = 2,
            cost       = 3,
            effect_1   = "Orbital Strike, once per round. Requires Breeding Chambers. Bastions do not prevent orbital strike.",
            effect_2   = "Spend up to 2 [G] for each participating Hive Ship. For each [G] you spend, purchase 1 unit Tier 2 or less and place it on the world. Command Level 2.",
        ),
    ],
    event_cards = [
        EventCard(name="Brood Nests",            warp_storm_move="Top Rgt/Bot Left", card_type="Scheme", effect="Before revealing an order during the Operations Phase, may discard to place 1 free Gaunt on each of 2 different friendly worlds."),
        EventCard(name="Devourer of Worlds",     warp_storm_move="Across",           card_type="Tactic", effect="Choose a system. Gain materiel equal to the materiel value of friendly worlds in that system."),
        EventCard(name="Hive Mind",              warp_storm_move="Top Left/Bot Rgt", card_type="Scheme", effect="While resolving an order, may discard this card to increase your Tier by 1 for each of your Hive Ships."),
        EventCard(name="Infiltration Organisms", warp_storm_move="Top Rgt/Bot Left", card_type="Tactic", effect="Purchase 1 combat upgrade, reducing its materiel cost by 1 for each of your Hive Ships."),
        EventCard(name="Rapid Mutation",         warp_storm_move="Sideways",         card_type="Tactic", effect="Gain 2 (F)."),
        EventCard(name="Rise of the Faithful",   warp_storm_move="Across",           card_type="Scheme", effect="Instead of revealing an order during the Operations Phase, may discard this card to place 1 free bastion on a friendly world not containing a structure."),
        EventCard(name="Shadow in the Warp",     warp_storm_move="Across",           card_type="Scheme", effect="May discard this card when you start a combat. If you do, your enemy cannot use reinforcement tokens during the combat."),
        EventCard(name="Splinter Fleet",         warp_storm_move="Top Left/Bot Rgt", card_type="Tactic", effect="Place 1 free Devourer on any friendly void."),
    ],
    extra = {
        "homeworld":    "Hive Fleet",
        "color_scheme": "#6A1B9A",
    },
)
