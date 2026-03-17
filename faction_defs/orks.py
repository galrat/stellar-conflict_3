"""
faction_defs/orks.py — фракция «Орки»

Орды зелёных варваров. Самая многочисленная фракция — много дешёвой пехоты
с высокой боевой силой, но низкой моралью. Сила в числе.
"""
from faction_base import Faction, UnitConfig, BattleCard, OrderUpgrade, CardLevel

ORKS = Faction(
    id    = "orks",
    name  = "Орки",
    icon  = "💀",
    color        = "#2E7D32",
    home_tile_id = "home_orks",
    flavor = (
        "Особое свойство фракции: "
        "вы можете купить один отряд и поместить его в дружественный мир активной системы"
    ),
    special_ability_name = "Мобилизация",
    special_ability_desc = "Вы можете купить один отряд и поместить его в дружественный мир активной системы",
    unit_config = UnitConfig(
        # ── Стартовый состав войск ──────────────────────────────────────────
        infantry=4, marines=1, mechanized=0, elite=0,
        fighters=0, destroyers=0,
        # ── Стартовые постройки ─────────────────────────────────────────────
        # Характеристики построек — см. STRUCTURE_CATALOG в player_hand.py.
        factories=1, cities=0, bastions=0,
        # ── Стартовые ресурсы ───────────────────────────────────────────────
        credits=6, support_tokens=2, discount_tokens=1, forge_tokens=0,
        # ── Характеристики юнитов (cost 2–5 + forge, strength 0–6, health 1–6, morale 0–6) ──
        # Орки: высокая боевая сила, крепкое телосложение, но слабая дисциплина.
        unit_stats={
            "infantry":   dict(cost=2,                  combat_strength=2, health=2, morale=1),
            "marines":    dict(cost=3,                  combat_strength=3, health=3, morale=2),
            "mechanized": dict(cost=4,                  combat_strength=3, health=3, morale=2),
            "elite":      dict(cost=5, cost_forge=1,    combat_strength=5, health=4, morale=2),
            "fighter":    dict(cost=2,                  combat_strength=2, health=2, morale=1),
            "destroyer":  dict(cost=4, cost_forge=1,    combat_strength=4, health=3, morale=2),
        },
    ),
    battle_cards = [
        BattleCard(
            name     = "Вааааgh!",
            level    = CardLevel.INITIAL,
            effect_1 = "Добавьте +1 к боевому счёту за каждого пехотинца в бою (не более +4).",
            effect_2 = "Если орков больше, чем противника — перебросьте кубик, используйте лучший.",
        ),
        BattleCard(
            name     = "Больше пушек",
            level    = CardLevel.ZERO,
            effect_1 = "До боя уничтожьте 1 вражеский наземный юнит залпом орочьей артиллерии.",
            effect_2 = "Ваш атакующий кубик минимум 3 в этом бою.",
        ),
        BattleCard(
            name     = "Орочий напор",
            level    = CardLevel.TWO,
            effect_1 = "Все ваши юниты в бою получают +2 к боевому счёту.",
            effect_2 = "Если вы победили — немедленно переместите 1 орка из резерва в эту зону.",
        ),
        BattleCard(
            name     = "Зелёный прилив",
            level    = CardLevel.THREE,
            effect_1 = "Замените результат своего кубика на 6.",
            effect_2 = "Проигравший теряет дополнительно 1 юнита (итого минус 2 из зоны боя).",
        ),
    ],
    order_upgrades = [
        OrderUpgrade(
            name       = "Орочий марш",
            order_type = "move",
            effect_1   = "Пехота может перемещаться через 2 тайла за один приказ.",
            effect_2   = "При перемещении в планету без противника — разместите 1 орка из резерва бесплатно.",
        ),
        OrderUpgrade(
            name       = "Безумная атака",
            order_type = "attack",
            effect_1   = "Атакующие юниты бросают 2 кубика и берут лучший результат.",
            effect_2   = "После победы в атаке — перместите всех орков-победителей в соседнюю свободную зону.",
        ),
    ],
    extra = {
        "homeworld":    "Гхазгхулл",
        "color_scheme": "#2E7D32",
    },
)
