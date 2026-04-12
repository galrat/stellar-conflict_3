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
            "infantry":   dict(name="Cultists",                   cost=2,               combat_strength=1, health=2, morale=2, max_count=9),
            "marines":    dict(name="Chaos Space Marines",        cost=3,               combat_strength=3, health=3, morale=2, max_count=6),
            "mechanized": dict(name="Helbrute",                   cost=4,               combat_strength=3, health=4, morale=3, max_count=3),
            "elite":      dict(name="Chaos Reaver Titan",         cost=5, cost_forge=1, combat_strength=4, health=5, morale=3, max_count=3),
            "fighter":    dict(name="Iconoclast Destroyer",       cost=2,               combat_strength=2, health=2, morale=2, max_count=3),
            "destroyer":  dict(name="Repulsive Cruiser",          cost=5, cost_forge=1, combat_strength=4, health=5, morale=4, max_count=3),
        },
        # ── Стартовая колода боевых карт ──────────────────────────────────────
        battle_card_deck = [
            "Dark Faith",
            "Foul Worship",
            "Impure Zeal",
            "Khorne's Rage",
            "Lure of Chaos",
            "Mark of Khorne",
            "Mark of Nurgle",
            "Mark of Slaanesh",
            "Mark of Tzeentch",
            "Chaos United",
            "Daemonic Resilience",
            "Inhuman Strength",
            "Chaos Victorious",
            "Death and Despair",
        ],
    ),
    battle_cards = [
        # ── Начальные (бесплатные) ──────────────────────────────────────────
        BattleCard(
            name     = "Dark Faith",
            level    = CardLevel.INITIAL,
            tier       = -1,
            cost       = 0,
            effect_1 = "Gain 1 [M]. Requires: Cultist / Iconoclast.",
            effect_2 = "If more [M] than enemy, place free Cultist on another friendly or uncontrolled world in system.",
        ),
        BattleCard(
            name     = "Foul Worship",
            level=CardLevel.INITIAL,
            tier=-1,
            cost=0,
            effect_1 = "Gain 1 [?]. Requires: Cultist / Iconoclast.",
            effect_2 = "If enemy has routed unit, gain 1 (s) per unrouted Cultist or Iconoclast.",
        ),
        BattleCard(
            name     = "Impure Zeal",
            level=CardLevel.INITIAL,
            tier=-1,
            cost=0,
            effect_1 = "If more [M] than enemy, rally 1 unit. Requires: Cultist / Iconoclast.",
            effect_2 = "Enemy routs 1 unit, or you gain 1 (g) per unrouted Cultist or Iconoclast.",
        ),
        BattleCard(
            name     = "Khorne's Rage",
            level=CardLevel.INITIAL,
            tier=-1,
            cost=0,
            effect_1 = "Spend 1 [G] to gain 3 (g). Requires: Marine / Iconoclast.",
            effect_2 = "Enemy spends 1 [S] or routs unit of his choosing.",
        ),
        BattleCard(
            name     = "Lure of Chaos",
            level=CardLevel.INITIAL,
            tier=-1,
            cost=0,
            effect_1 = "Enemy may choose a unit to rout to gain 1 [?]. Otherwise place a free Cultist or Iconoclast in the area. Requires: Cultist / Iconoclast.",
            effect_2 = "Gain 2 (g) or 2 (s).",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Mark of Khorne",
            level    = CardLevel.ZERO,
            tier = 0,
            cost = 2,
            effect_1 = "Spend 1 [G] or 1 [M] to gain 3 (g). Requires: Marine / Iconoclast.",
            effect_2 = "Enemy spends 1 [S] or destroys 1 routed unit.",
        ),
        BattleCard(
            name     = "Mark of Nurgle",
            level=CardLevel.ZERO,
            tier=0,
            cost=2,
            effect_1 = "Spend 1 [S] or 1 [M] to gain 3 (s). Requires: Marine / Iconoclast.",
            effect_2 = "Enemy destroys 1 routed unit, otherwise gain 2 (s).",
        ),
        BattleCard(
            name     = "Mark of Slaanesh",
            level=CardLevel.ZERO,
            tier=0,
            cost=2,
            effect_1 = "Gain 1 [?]. If more [M] than enemy, he routs 1 unit of his choice. Requires: Marine.",
            effect_2 = "If enemy has routed unit, place free Cultist on this world.",
        ),
        BattleCard(
            name     = "Mark of Tzeentch",
            level=CardLevel.ZERO,
            tier=0,
            cost=2,
            effect_1 = "Gain 1 [M]. If more [M] than enemy, upgrade 1 Cultist / (R) to Marine. Requires: Chaos Marine / Iconoclast.",
            effect_2 = "Convert up to 2 [M] to [G] and/or [S].",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Chaos United",
            level    = CardLevel.TWO,
            tier = 2,
            cost = 4,
            effect_1 = "Enemy may rout 1 of its units. If not, gain a die of your choice. Requires: Cultist / Marine / Helbrute.",
            effect_2 = "Take 1 unit from any world and place it on this world. Command level cannot exceed number of Cultists in this system.",
        ),
        BattleCard(
            name     = "Daemonic Resilience",
            level=CardLevel.TWO,
            tier=2,
            cost=4,
            effect_1 = "Gain 1 [M] or 1 [S]. Requires: Helbrute / Cruiser.",
            effect_2 = "Gain 4 (s) unless enemy destroys 1 unit of his choice.",
        ),
        BattleCard(
            name     = "Inhuman Strength",
            level=CardLevel.TWO,
            tier=2,
            cost=4,
            effect_1 = "Gain 1 [G] or 1 [M]. Requires: Helbrute / Cruiser.",
            effect_2 = "Destroy 1 unit to gain 4 (g).",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Chaos Victorious",
            level    = CardLevel.THREE,
            tier = 3,
            cost = 6,
            effect_1 = "Gain 2 [?]. If more [M] than enemy, rout all his Tier 0 units. Requires: Titan / Cruiser.",
            effect_2 = "Rout 1 enemy unit.",
        ),
        BattleCard(
            name     = "Death and Despair",
            level=CardLevel.THREE,
            tier=3,
            cost=6,
            effect_1 = "Gain 2 [G] or 2 [M]. Spend any [M], each destroys 1 Tier 0 unit. Requires: Titan / Cruiser.",
            effect_2 = "If more [M] than enemy, destroy 1 routed unit.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Fear from Above",
            order_type = "advance",
            tier       = 0,
            cost       = 1,
            effect_1   = "Orbital Strike, once per round. Gain [?].",
            effect_2   = "Spend 1 [M] to force any unit taking damage to rout.",
        ),
        OrderUpgrade(
            name       = "Dread Ritual",
            order_type = "deploy",
            tier       = 1,
            cost       = 2,
            effect_1   = "Purchase 1 Tier 0–2 unit; reduce cost by 1 per Cultist in active system.",
            effect_2   = "Factory not required.",
        ),
        OrderUpgrade(
            name       = "Favour of the Dark Gods",
            order_type = "strategize",
            tier       = 1,
            cost       = 2,
            effect_1   = "Place 2 order tokens from play area onto top of event deck.",
            effect_2   = "Once per round.",
        ),
        OrderUpgrade(
            name       = "From the Warp",
            order_type = "advance",
            tier       = 1,
            cost       = 2,
            effect_1   = "Ships can move through Warp Storms.",
            effect_2   = "Once per round.",
        ),
        OrderUpgrade(
            name       = "Complete Destruction",
            order_type = "advance",
            tier       = 2,
            cost       = 3,
            effect_1   = "Orbital Strike, once per round. Bastions do not prevent orbital strike.",
            effect_2   = "Spend 2 [S] to force enemy to choose unit or structure to destroy.",
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
