"""
faction_defs/chaos.py — фракция «Хаос»

Союз свободных миров. Сбалансированная фракция с акцентом на координацию
и адаптивность. Сильна в обороне и логистике.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

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
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=2, marines=2, mechanized=0, elite=0,
        fighters=1, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        # Характеристики построек — см. STRUCTURE_CATALOG в player_hand.py.
        factories=1, cities=1, bastions=1,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=1, discount_tokens=1, forge_tokens=1,
        # ── Характеристики юнитов (cost 2–5 + forge, strength 0–6, health 1–6, morale 0–6) ──
        unit_stats={
            "infantry":   dict(cost=2,                  combat_strength=1, health=2, morale=2),
            "marines":    dict(cost=3,                  combat_strength=3, health=3, morale=2),
            "mechanized": dict(cost=4,                  combat_strength=3, health=3, morale=2),
            "elite":      dict(cost=5, cost_forge=1,    combat_strength=4, health=3, morale=3),
            "fighter":    dict(cost=2,                  combat_strength=2, health=2, morale=2),
            "destroyer":  dict(cost=5, cost_forge=1,    combat_strength=4, health=3, morale=3),
        },
    ),
    battle_cards = [
        # ── Начальные ──────────────────────────────────────────────────────
        BattleCard(
            name     = "Тактическое отступление",
            level    = CardLevel.INITIAL,
            effect_1 = "До подсчёта потерь переместите 1 своего юнита в соседнюю дружественную зону.",
            effect_2 = "Противник получает −1 к боевому счёту в следующем бою этого раунда.",
        ),
        BattleCard(
            name     = "Организованная оборона",
            level    = CardLevel.INITIAL,
            effect_1 = "Защитник добавляет +1 за каждые 2 своих юнита в зоне (не более +3).",
            effect_2 = "Если защитник победил — один юнит атакующего переходит в его резерв.",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Залповый огонь",
            level    = CardLevel.ZERO,
            effect_1 = "Добавьте +1 к боевому счёту за каждый отряд механизированной пехоты в зоне.",
            effect_2 = "Если результат кубика ≤ 2 — перебросьте его один раз.",
        ),
        BattleCard(
            name     = "Воздушное прикрытие",
            level    = CardLevel.ZERO,
            effect_1 = "Ваши истребители добавляют +1 к наземному бою на той же планете.",
            effect_2 = "Уничтожьте 1 вражеский истребитель до начала космического боя на этом тайле.",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Координированная атака",
            level    = CardLevel.TWO,
            effect_1 = "Все ваши юниты в бою получают +1 к атаке.",
            effect_2 = "Если у вас строго больше юнитов — победитель не несёт потерь.",
        ),
        BattleCard(
            name     = "Вызов подкреплений",
            level    = CardLevel.TWO,
            effect_1 = "Немедленно переместите до 2 юнитов из резерва в текущую зону боя.",
            effect_2 = "Эти юниты участвуют в бою, но не могут быть использованы в следующем приказе.",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Стратегическая инициатива",
            level    = CardLevel.THREE,
            effect_1 = "Замените результат кубика противника на 1.",
            effect_2 = "Ваши элитные юниты в этом бою имеют attack_bonus +3 вместо обычного.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Стремительный марш",
            order_type = "move",
            effect_1   = "Войска могут перемещаться через 2 тайла за один приказ вместо 1.",
            effect_2   = "Пехота не тратит слот приказа при перемещении на планету союзного тайла.",
        ),
        OrderUpgrade(
            name       = "Массированное подкрепление",
            order_type = "reinforce",
            effect_1   = "Разместите до 3 юнитов из резерва вместо стандартных 2.",
            effect_2   = "Если на целевом тайле находится ваша домашняя система — +1 дополнительный юнит.",
        ),
    ],
    extra = {
        "homeworld":    "Терра Федерация",
        "color_scheme": "#4A90D9",
    },
)
