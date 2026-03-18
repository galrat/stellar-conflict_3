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
            "infantry":   dict(name="Аспект",        cost=2,               combat_strength=1, health=1, morale=4, max_count=9),
            "marines":    dict(name="Рейнджер",      cost=3,               combat_strength=2, health=1, morale=5, max_count=3),
            "mechanized": dict(name="Корар",         cost=3,               combat_strength=2, health=2, morale=4, max_count=3),
            "elite":      dict(name="Титан",         cost=4, cost_forge=1, combat_strength=3, health=2, morale=6, max_count=3),
            "fighter":    dict(name="Истребитель",   cost=2,               combat_strength=2, health=1, morale=4, max_count=6),
            "destroyer":  dict(name="Воидкрафт",     cost=3, cost_forge=1, combat_strength=3, health=2, morale=5, max_count=3),
        },
    ),
    battle_cards = [
        # ── Начальные ──────────────────────────────────────────────────────
        BattleCard(
            name     = "Засада",
            level    = CardLevel.INITIAL,
            effect_1 = "Сыграйте до броска кубиков: противник бросает кубик с минусом 2.",
            effect_2 = "Один ваш десантник в бою считается имеющим attack_bonus +2 вместо +1.",
        ),
        BattleCard(
            name     = "Дымовая завеса",
            level    = CardLevel.INITIAL,
            effect_1 = "Противник не может сыграть боевую карту в этом бою.",
            effect_2 = "Если вы проиграли — сохраните 1 своего юнита вместо полной потери.",
        ),
        # ── Нулевой уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Инфильтрация",
            level    = CardLevel.ZERO,
            effect_1 = "Переместите 1 вражеский юнит из текущей зоны в резерв противника до боя.",
            effect_2 = "Ваши истребители участвуют в наземном бою, добавляя +1 к счёту.",
        ),
        BattleCard(
            name     = "Чёрный рынок",
            level    = CardLevel.ZERO,
            effect_1 = "Возьмите 1 боевую карту уровня ZERO из колоды любой другой фракции.",
            effect_2 = "Если вы победили — противник не может использовать свой следующий слот приказа.",
        ),
        # ── Второй уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Клинок в темноте",
            level    = CardLevel.TWO,
            effect_1 = "Десантники добавляют +3 к боевому счёту вместо стандартного бонуса.",
            effect_2 = "После боя переместите до 2 ваших юнитов в соседний тайл без приказа.",
        ),
        BattleCard(
            name     = "Диверсия",
            level    = CardLevel.TWO,
            effect_1 = "До боя выберите 1 приказ противника — он отменяется без исполнения.",
            effect_2 = "Ваши истребители в этом бою считаются эсминцами для расчёта attack_bonus.",
        ),
        # ── Третий уровень ────────────────────────────────────────────────
        BattleCard(
            name     = "Операция «Призрак»",
            level    = CardLevel.THREE,
            effect_1 = "Замените результат своего кубика на 6.",
            effect_2 = "Ваши потери в этом бою возвращаются в резерв, а не удаляются из игры.",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Теневой бросок",
            order_type = "move",
            effect_1   = "Десантники могут перемещаться на 2 тайла и атаковать в конце движения.",
            effect_2   = "Перемещение Синдиката не видно противнику до момента исполнения приказа.",
        ),
        OrderUpgrade(
            name       = "Стремительный рейд",
            order_type = "attack",
            effect_1   = "Перед атакой переместите до 2 десантников из любого дружественного тайла.",
            effect_2   = "Если атака успешна — получите дополнительный слот приказа в этом раунде.",
        ),
    ],
    extra = {
        "homeworld":    "Umbra Station",
        "color_scheme": "#8E44AD",
    },
)
