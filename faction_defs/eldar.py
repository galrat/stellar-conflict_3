"""
faction_defs/eldar.py — фракция «Эльдары»

Хитрые и маневренные.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

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
        credits=6, support_tokens=0, discount_tokens=0, forge_tokens=1,
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
    ),
    battle_cards = [
        # ── Начальные (бесплатные) ──────────────────────────────────────────
        BattleCard(
            name     = "Command of the Autarch",
            level    = CardLevel.INITIAL,
            effect_1 = "Either rally 1 unit or gain 1 [M]. Play 1 card from your hand — gain its combat icons but not its abilities.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Hit and Run",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 2 (g). Requires: Aspect / Frigate.",
            effect_2 = "Spend 1 [M] to move 1 unit to adjacent friendly or uncontrolled area.",
        ),
        BattleCard(
            name     = "Howling Banshees",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 1 [?]. Requires: Aspect / Frigate.",
            effect_2 = "Spend 1 [M] to force enemy to rout a unit of his choice.",
        ),
        BattleCard(
            name     = "Ranger Support",
            level    = CardLevel.INITIAL,
            effect_1 = "If attacking, gain 1 (g) and 1 (s). If defending, you may retreat 1 unit.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Striking Scorpions",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 1 [?]. Requires: Aspect / Frigate.",
            effect_2 = "Enemy loses 1 die of his choice.",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Fire Dragon's Vengeance",
            level    = CardLevel.ZERO,
            effect_1 = "If you are attacking, enemy cannot gain (s) this execution round. Requires: Aspect / Frigate.",
            effect_2 = "Gain 2 (s).",
        ),
        BattleCard(
            name     = "Swooping Hawks",
            level    = CardLevel.ZERO,
            effect_1 = "If you are defending, enemy loses 3 (g). Requires: Aspect / Frigate.",
            effect_2 = "Spend 1 [M] to gain 2 (g).",
        ),
        BattleCard(
            name     = "Wraithguard Advance",
            level    = CardLevel.ZERO,
            effect_1 = "Gain 1 [?] or 1 [M]. Convert up to 2 [S] into [G]. Requires: Wraithguard / Frigate / Stalker.",
            effect_2 = "Enemy spends 1 [M] or routs unit of his choosing.",
        ),
        BattleCard(
            name     = "Wraithguard Support",
            level    = CardLevel.ZERO,
            effect_1 = "Gain 1 [?] or 1 [M]. Convert up to 2 [G] into [S]. Requires: Wraithguard / Frigate / Stalker.",
            effect_2 = "Spend 1 [M] to rally 1 unit.",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Fire Prism",
            level    = CardLevel.TWO,
            effect_1 = "Convert any [M] into [G]. Requires: Falcon / Stalker.",
            effect_2 = "If attacking, gain 2 (g). If defending, force enemy to lose 5 (s).",
        ),
        BattleCard(
            name     = "Spiritseer's Guidance",
            level    = CardLevel.TWO,
            effect_1 = "Gain 1 [M]. Rout 1 unit; units cannot suffer any damage this execution round.",
            effect_2 = "—",
        ),
        BattleCard(
            name     = "Wave Serpent",
            level    = CardLevel.TWO,
            effect_1 = "Gain 1 [?]. Gain 3 (s) unless enemy spends 1 [M]. Requires: Falcon / Stalker.",
            effect_2 = "Spend 1 [M] to move any number of Tier 0 and Tier 1 units to an adjacent area — may start a new combat.",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Holofield Emitter",
            level    = CardLevel.THREE,
            effect_1 = "Gain 1 [?]. Draw 1 combat card. Requires: Titan / Stalker.",
            effect_2 = "Play 1 card from your hand — gain its combat icons but not its abilities.",
        ),
        BattleCard(
            name     = "Psychic Lance",
            level    = CardLevel.THREE,
            effect_1 = "Gain 1 [?]. Enemy discards 1 random combat card from his hand. Requires: Titan / Stalker.",
            effect_2 = "Gain 4 (g) unless enemy discards 1 face up card of your choice.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Tactical Strikes",
            order_type = "advance",
            effect_1   = "Orbital Strike, once per round. Gain 1 [?].",
            effect_2   = "Spend 1 [M] to choose enemy unit on the world — this must suffer damage first.",
        ),
        OrderUpgrade(
            name       = "Wraithbone Singers",
            order_type = "deploy",
            effect_1   = "When purchasing structure, may place it on world containing exactly 1 different structure. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Farseer",
            order_type = "strategize",
            effect_1   = "This order can be resolved even if there are no units in the active system. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Corsair Raid",
            order_type = "advance",
            effect_1   = "After resolving a combat with this order, you may perform 1 orbital strike in the active system. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Strafing Run",
            order_type = "advance",
            effect_1   = "Orbital Strike, once per round. Bastions do not prevent orbital strike.",
            effect_2   = "Spend 1 [S] to move any ships in active system to friendly or empty voids in adjacent system. Command Level 2.",
        ),
    ],
    extra = {
        "homeworld":    "Umbra Station",
        "color_scheme": "#8E44AD",
    },
)
