"""
faction_defs/marine.py — фракция «marine»

Тяжёлая бронированная держава. Опирается на механизированные войска
и эсминцы. Медленная, но сокрушительная в прямом столкновении.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

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
    ),
    battle_cards = [
        # ── Начальные (бесплатные) ──────────────────────────────────────────
        BattleCard(
            name     = "Ambush",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 2 (g). Requires: Scout / Cruiser.",
            effect_2 = "When enemy is routed this round, must spend [M] or be destroyed.",
        ),
        BattleCard(
            name     = "Blessed Power Armour",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 2 (s). Requires: Bastion / Marine / Cruiser.",
            effect_2 = "Convert up to 2 dice to [S].",
        ),
        BattleCard(
            name     = "Faith in the Emperor",
            level    = CardLevel.INITIAL,
            effect_1 = "Gain 1 [?]. Requires: Scout / Marine / Cruiser.",
            effect_2 = "Rally 1 unit or gain 1 [M].",
        ),
        BattleCard(
            name     = "Fury of the Ultramar",
            level    = CardLevel.INITIAL,
            effect_1 = "Enemy rerolls 1 [S]. You may reroll 1 [S]. Requires: Marine / Cruiser.",
            effect_2 = "Force enemy to lose 1 [S] or 2 (s).",
        ),
        BattleCard(
            name     = "Reconnaissance",
            level    = CardLevel.INITIAL,
            effect_1 = "If attacking, look at enemy card first. Requires: Scout / Cruiser.",
            effect_2 = "Spend 1 [M] to retreat 1 unit.",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Drop Pod Assault",
            level    = CardLevel.ZERO,
            effect_1 = "Gain 1 [?]. Requires: Marine.",
            effect_2 = "Spend 1 [M] to take 1 Scout or 1 Marine from any world to this world.",
        ),
        BattleCard(
            name     = "Glory and Death",
            level    = CardLevel.ZERO,
            effect_1 = "Gain 2 (g). If attacking, rally 1 unit. Requires: Marine / Cruiser.",
            effect_2 = "Force enemy to lose 1 [S] or 1 [M].",
        ),
        BattleCard(
            name     = "Hold the Line",
            level    = CardLevel.ZERO,
            effect_1 = "Gain 2 (s). If defending, rally 1 unit. Requires: Bastion / Marine / Cruiser.",
            effect_2 = "Gain 1 [S] or 1 [M].",
        ),
        BattleCard(
            name     = "Veteran Scouts",
            level    = CardLevel.ZERO,
            effect_1 = "For each morale dice, gain 1 (g) or (s). Requires: Scout / Cruiser.",
            effect_2 = "Spend any [M]; retreat 1 unit per die.",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Armoured Advance",
            level    = CardLevel.TWO,
            effect_1 = "Gain 1 [?]. Requires: Land Raider / Battle Barge.",
            effect_2 = "Resolve 1 additional assess damage step this round (including tokens etc).",
        ),
        BattleCard(
            name     = "Break the Line",
            level    = CardLevel.TWO,
            effect_1 = "Convert up to 3 [M] to [G] and/or [S]. Requires: Land Raider / Battle Barge.",
            effect_2 = "Enemy chooses 1 face up combat card to discard.",
        ),
        BattleCard(
            name     = "Show No Fear",
            level    = CardLevel.TWO,
            effect_1 = "Own units cannot become routed this round. Requires: Bastion / Marine / Cruiser.",
            effect_2 = "Spend 1 [M] to rally all units.",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Emperor's Glory",
            level    = CardLevel.THREE,
            effect_1 = "Gain 2 [?]. Requires: Titan / Battle Barge.",
            effect_2 = "Rally all units. Convert any dice to [M].",
        ),
        BattleCard(
            name     = "Emperor's Might",
            level    = CardLevel.THREE,
            effect_1 = "Gain 2 [?]. Requires: Titan / Battle Barge.",
            effect_2 = "Spend any [G]; gain 2 (g) per die.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Reign of Fire",
            order_type = "advance",
            effect_1   = "Orbital Strike, once per round. Gain [?].",
            effect_2   = "Convert 1 [M] into [G].",
        ),
        OrderUpgrade(
            name       = "Crusade",
            order_type = "advance",
            effect_1   = "If no friendly worlds in system, gain 1 (R). Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Direct the Faithful",
            order_type = "strategize",
            effect_1   = "May change 1 structure to a different structure. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Recruitment Worlds",
            order_type = "deploy",
            effect_1   = "Treat Bastions as Factories, lower deployment limit by 1 each. Once per round.",
            effect_2   = "Command Level 1.",
        ),
        OrderUpgrade(
            name       = "Drop Pods",
            order_type = "advance",
            effect_1   = "Orbital Strike, once per round. Bastions do not prevent orbital strike.",
            effect_2   = "Spend 2 [S] to place free Marine (may start combat). Command Level 2.",
        ),
    ],
    extra = {
        "homeworld":    "Трон-Прайм",
        "color_scheme": "#C0392B",
    },
)
