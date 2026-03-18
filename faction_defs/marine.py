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
            "infantry":   dict(name="Боевой брат",  cost=2,               combat_strength=1, health=3, morale=4, max_count=9),
            "marines":    dict(name="Десантник",    cost=3,               combat_strength=2, health=3, morale=5, max_count=6),
            "mechanized": dict(name="Дредноут",     cost=3,               combat_strength=2, health=4, morale=4, max_count=6),
            "elite":      dict(name="Терминатор",   cost=5, cost_forge=1, combat_strength=4, health=4, morale=6, max_count=3),
            "fighter":    dict(name="Перехватчик",  cost=2,               combat_strength=1, health=2, morale=4, max_count=3),
            "destroyer":  dict(name="Крейсер",      cost=4, cost_forge=1, combat_strength=3, health=4, morale=5, max_count=3),
        },
    ),
    battle_cards = [
        # ── Начальные ──────────────────────────────────────────────────────
        BattleCard(
            name     = "Бронированный удар",
            level    = CardLevel.INITIAL,
            effect_1 = "Механизированные юниты добавляют +2 к боевому счёту вместо обычного бонуса.",
            effect_2 = "Противник не может сыграть карту отступления в этом бою.",
        ),
        BattleCard(
            name     = "Железная дисциплина",
            level    = CardLevel.INITIAL,
            effect_1 = "Перебросьте свой кубик. Используйте лучший результат из двух.",
            effect_2 = "Ваши юниты не получают штраф от карт противника в этом бою.",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Орбитальная бомбардировка",
            level    = CardLevel.ZERO,
            effect_1 = "До боя уничтожьте 1 вражеский наземный юнит на целевой планете.",
            effect_2 = "Эсминцы добавляют +1 к наземному бою на той же планете.",
        ),
        BattleCard(
            name     = "Подавляющий огонь",
            level    = CardLevel.ZERO,
            effect_1 = "Противник получает −1 к боевому счёту за каждый уничтоженный юнит в этом бою.",
            effect_2 = "Если вы победили с разрывом ≥ 4 — сохраните один трофейный юнит противника.",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Блицкриг",
            level    = CardLevel.TWO,
            effect_1 = "Сыграйте эту карту перед ходом: выполните один приказ атаки без траты слота.",
            effect_2 = "Механизированные юниты после победы могут немедленно переместиться в соседнюю зону.",
        ),
        BattleCard(
            name     = "Несокрушимый строй",
            level    = CardLevel.TWO,
            effect_1 = "Если у вас ≥ 3 юнитов в зоне — ваш кубик считается минимум 4.",
            effect_2 = "Проигравший теряет вдвое больше юнитов (округление вверх).",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Кулак Императора",
            level    = CardLevel.THREE,
            effect_1 = "Добавьте +5 к боевому счёту. Не суммируется с другими бонусами атаки.",
            effect_2 = "Победитель этого боя немедленно ставит приказ на соседний тайл без траты хода.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Молниеносная атака",
            order_type = "attack",
            effect_1   = "Атакующие механизированные юниты бросают 2 кубика и берут лучший.",
            effect_2   = "После победы в атаке — переместите 1 дополнительный юнит из резерва в зону.",
        ),
        OrderUpgrade(
            name       = "Укреплённые позиции",
            order_type = "reinforce",
            effect_1   = "Разместите механизированный юнит в любой зоне, игнорируя соседство.",
            effect_2   = "Юниты, размещённые этим приказом, получают +1 к обороне до следующего раунда.",
        ),
    ],
    extra = {
        "homeworld":    "Трон-Прайм",
        "color_scheme": "#C0392B",
    },
)
