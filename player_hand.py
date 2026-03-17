"""
player_hand.py — Спецификации юнитов, построек и начальный набор игрока.

Каждый юнит идентифицируется строкой вида:
    {faction_id}_{category}_t{tier}
    Примеры: chaos_ground_t0, marine_space_t2, eldar_ground_t1

Категория (category):  "ground" — наземный,  "space" — космический
Уровень (tier):
    Наземные: t0 (пехота), t1 (десант/механ.), t2 (элита), t3 (легенда)
    Космические: t0 (истребитель), t2 (эсминец) — уровня t1 нет

Характеристики задаются PER ТИП юнита, не per уровень:
    marines и mechanized — оба t1, но могут иметь разные stats.
    Каталог UNIT_TYPE_CATALOG ключован по имени типа: "infantry", "marines", etc.

Содержит:
    Cost              — стоимость (монеты + опциональные жетоны молотка)
    UnitSpec          — полные параметры типа юнита
    StructureSpec     — параметры типа постройки (бастион имеет боевые хар-ки)
    PlayerStartKit    — полный начальный набор игрока «в руке»
    UNIT_TYPE_CATALOG — базовые параметры по имени типа юнита
    STRUCTURE_CATALOG — параметры трёх типов построек
    build_start_kit() — фабрика: Faction + UnitConfig → PlayerStartKit
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Стоимость ────────────────────────────────────────────────────────────────

@dataclass
class Cost:
    """
    Стоимость покупки юнита или постройки.

    credits      — монеты (основная валюта)
    forge_tokens — жетоны молотка (ценные ресурсы; ⚒ на жетоне)
    """
    credits:      int = 0
    forge_tokens: int = 0   # жетоны молотка

    def to_dict(self) -> dict:
        return {"credits": self.credits, "forge_tokens": self.forge_tokens}

    def __str__(self) -> str:
        parts = [f"{self.credits}₡"]
        if self.forge_tokens:
            parts.append(f"{self.forge_tokens}⚒")
        return " + ".join(parts)


# ── Спецификация юнита ────────────────────────────────────────────────────────

@dataclass
class UnitSpec:
    """
    Полное описание класса юнита (не экземпляра, а типа).

    unit_id         — уникальный ID: {faction_id}_{category}_t{tier}
    display_name    — название для отображения в UI
    category        — "ground" (наземный) или "space" (космический)
    tier            — уровень: 0 = базовый, 1 = улучшенный, 2 = элитный, 3 = легендарный
                      (у космических: только 0 и 2, уровня 1 нет)
    cost            — стоимость (монеты + жетоны молотка)
    combat_strength — боевая сила: прибавка к броску кубика
    health          — здоровье: количество урона до уничтожения
    morale          — боевой дух: порог паники и отступления
    start_count     — количество, выставляемое при начальной расстановке
    total_count     — общий запас в начале игры (включает резерв)
    """
    unit_id:         str
    display_name:    str
    category:        str          # "ground" | "space"
    tier:            int
    cost:            Cost
    combat_strength: int          # бонус к кубику
    health:          int          # здоровье
    morale:          int          # боевой дух
    start_count:     int          # выставляется при старте
    total_count:     int          # всего в запасе на старте

    def to_dict(self) -> dict:
        return {
            "unit_id":         self.unit_id,
            "display_name":    self.display_name,
            "category":        self.category,
            "tier":            self.tier,
            "cost":            self.cost.to_dict(),
            "combat_strength": self.combat_strength,
            "health":          self.health,
            "morale":          self.morale,
            "start_count":     self.start_count,
            "total_count":     self.total_count,
        }


# ── Спецификация постройки ────────────────────────────────────────────────────

@dataclass
class StructureSpec:
    """
    Полное описание типа постройки (Бастион / Фабрика / Город).

    structure_id    — "bastion" | "factory" | "city"
    display_name    — название для UI
    cost            — стоимость постройки
    defense_bonus   — бонус к защите при обороне (только Бастион)
    start_count     — количество у игрока на старте
    description     — краткое описание эффекта

    Боевые характеристики (только у Бастиона, у Фабрики и Города — None):
    combat_strength — боевая сила
    health          — здоровье
    morale          — боевой дух
    """
    structure_id:    str
    display_name:    str
    cost:            Cost
    defense_bonus:   int
    start_count:     int
    description:     str
    combat_strength: Optional[int] = None   # только у Бастиона
    health:          Optional[int] = None   # только у Бастиона
    morale:          Optional[int] = None   # только у Бастиона

    @property
    def has_combat_stats(self) -> bool:
        """True если постройка участвует в бою (т.е. является Бастионом)."""
        return self.combat_strength is not None

    def to_dict(self) -> dict:
        d = {
            "structure_id":  self.structure_id,
            "display_name":  self.display_name,
            "cost":          self.cost.to_dict(),
            "defense_bonus": self.defense_bonus,
            "start_count":   self.start_count,
            "description":   self.description,
        }
        if self.has_combat_stats:
            d["combat_strength"] = self.combat_strength
            d["health"]          = self.health
            d["morale"]          = self.morale
        return d


# ── Каталог типов юнитов ──────────────────────────────────────────────────────
# Ключ: имя типа юнита ("infantry", "marines", "mechanized", "elite",
#                        "fighter", "destroyer")
# Это позволяет marines и mechanized (оба t1) иметь разные характеристики.
# Поле tier здесь — уровень для формирования unit_id.
#
# Космические юниты: ТОЛЬКО t0 (fighter) и t2 (destroyer). Уровня t1 нет.

UNIT_TYPE_CATALOG: Dict[str, dict] = {
    # ── Наземные ──────────────────────────────────────────────────────────────
    "infantry": dict(
        display_name    = "Пехота",
        category        = "ground",
        tier            = 0,
        cost            = Cost(credits=1),
        combat_strength = 0,
        health          = 1,
        morale          = 2,
    ),
    "marines": dict(
        display_name    = "Десант",
        category        = "ground",
        tier            = 1,
        cost            = Cost(credits=2),
        combat_strength = 1,
        health          = 1,
        morale          = 3,
    ),
    "mechanized": dict(
        display_name    = "Механ.",
        category        = "ground",
        tier            = 1,
        cost            = Cost(credits=2),
        combat_strength = 1,
        health          = 2,    # прочнее десанта
        morale          = 2,    # но меньший боевой дух
    ),
    "elite": dict(
        display_name    = "Элита",
        category        = "ground",
        tier            = 2,
        cost            = Cost(credits=3, forge_tokens=1),
        combat_strength = 2,
        health          = 2,
        morale          = 4,
    ),
    # ── Космические (t0 и t2, уровня t1 нет) ─────────────────────────────────
    "fighter": dict(
        display_name    = "Истребитель",
        category        = "space",
        tier            = 0,
        cost            = Cost(credits=1),
        combat_strength = 0,
        health          = 1,
        morale          = 2,
    ),
    "destroyer": dict(
        display_name    = "Эсминец",
        category        = "space",
        tier            = 2,                          # t2, не t1
        cost            = Cost(credits=3, forge_tokens=1),
        combat_strength = 2,
        health          = 2,
        morale          = 3,
    ),
}

# ── Каталог построек ─────────────────────────────────────────────────────────

STRUCTURE_CATALOG: Dict[str, StructureSpec] = {
    "factory": StructureSpec(
        structure_id  = "factory",
        display_name  = "Фабрика",
        cost          = Cost(credits=2),
        defense_bonus = 0,
        start_count   = 0,
        description   = "Производит юнитов. Позволяет построить 1 юнит дополнительно за ход.",
        # combat_strength / health / morale — нет (не участвует в бою)
    ),
    "city": StructureSpec(
        structure_id  = "city",
        display_name  = "Город",
        cost          = Cost(credits=3),
        defense_bonus = 0,
        start_count   = 0,
        description   = "Приносит победные очки. Учитывается при финальном подсчёте.",
        # combat_strength / health / morale — нет (не участвует в бою)
    ),
    "bastion": StructureSpec(
        structure_id    = "bastion",
        display_name    = "Бастион",
        cost            = Cost(credits=2, forge_tokens=1),
        defense_bonus   = 1,
        start_count     = 0,
        description     = "Укреплённая позиция. Участвует в бою на стороне защитника.",
        combat_strength = 2,   # фиксировано
        health          = 3,   # фиксировано
        morale          = 2,   # фиксировано
    ),
}


# ── Начальный набор игрока ────────────────────────────────────────────────────

@dataclass
class PlayerStartKit:
    """
    Полный начальный набор игрока — всё, что у него «в руке» перед партией.

    Включает:
      unit_specs      — список UnitSpec по одному на каждый тип юнита в запасе
      structure_specs — список StructureSpec по одному на каждый тип постройки
      credits         — начальные монеты
      support_tokens  — жетоны поддержки (⊕)
      discount_tokens — жетоны скидки (⊖)
      forge_tokens    — жетоны молотка/кузницы (⚒)
    """
    faction_id:      str
    unit_specs:      List[UnitSpec]      = field(default_factory=list)
    structure_specs: List[StructureSpec] = field(default_factory=list)
    credits:         int = 0
    support_tokens:  int = 0
    discount_tokens: int = 0
    forge_tokens:    int = 0

    @property
    def total_units(self) -> int:
        return sum(s.total_count for s in self.unit_specs)

    @property
    def total_ground(self) -> int:
        return sum(s.total_count for s in self.unit_specs if s.category == "ground")

    @property
    def total_space(self) -> int:
        return sum(s.total_count for s in self.unit_specs if s.category == "space")

    @property
    def total_structures(self) -> int:
        return sum(s.start_count for s in self.structure_specs)

    def to_dict(self) -> dict:
        return {
            "faction_id":       self.faction_id,
            "unit_specs":       [u.to_dict() for u in self.unit_specs],
            "structure_specs":  [s.to_dict() for s in self.structure_specs],
            "credits":          self.credits,
            "support_tokens":   self.support_tokens,
            "discount_tokens":  self.discount_tokens,
            "forge_tokens":     self.forge_tokens,
            "total_units":      self.total_units,
            "total_ground":     self.total_ground,
            "total_space":      self.total_space,
            "total_structures": self.total_structures,
        }


# ── Фабрика ───────────────────────────────────────────────────────────────────

def build_start_kit(faction_id: str, unit_config) -> PlayerStartKit:
    """
    Создаёт PlayerStartKit из faction_id и UnitConfig.

    unit_config — объект UnitConfig из faction_base.py.
    Маппинг: тип юнита → имя в UNIT_TYPE_CATALOG → UnitSpec.
    unit_id формируется как {faction_id}_{category}_t{tier}.
    """
    from units import GroundType, SpaceType

    # (unit_type_enum) → ключ в UNIT_TYPE_CATALOG
    _CATALOG_KEY = {
        GroundType.INFANTRY:   "infantry",
        GroundType.MARINES:    "marines",
        GroundType.MECHANIZED: "mechanized",
        GroundType.ELITE:      "elite",
        SpaceType.FIGHTER:     "fighter",
        SpaceType.DESTROYER:   "destroyer",
    }

    unit_specs: List[UnitSpec] = []
    for unit_type, count in [
        (GroundType.INFANTRY,   unit_config.infantry),
        (GroundType.MARINES,    unit_config.marines),
        (GroundType.MECHANIZED, unit_config.mechanized),
        (GroundType.ELITE,      unit_config.elite),
        (SpaceType.FIGHTER,     unit_config.fighters),
        (SpaceType.DESTROYER,   unit_config.destroyers),
    ]:
        if count <= 0:
            continue
        key  = _CATALOG_KEY[unit_type]
        base = UNIT_TYPE_CATALOG.get(key, {})
        cat  = base.get("category", "ground")
        tier = base.get("tier", 0)
        spec = UnitSpec(
            unit_id         = f"{faction_id}_{cat}_t{tier}",
            display_name    = base.get("display_name", unit_type.value),
            category        = cat,
            tier            = tier,
            cost            = base.get("cost", Cost()),
            combat_strength = base.get("combat_strength", 0),
            health          = base.get("health", 1),
            morale          = base.get("morale", 2),
            start_count     = count,
            total_count     = count,
        )
        unit_specs.append(spec)

    structure_specs: List[StructureSpec] = []
    for sid, count in [
        ("factory", unit_config.factories),
        ("city",    unit_config.cities),
        ("bastion", unit_config.bastions),
    ]:
        if count > 0:
            base_spec = STRUCTURE_CATALOG[sid]
            s = StructureSpec(
                structure_id    = base_spec.structure_id,
                display_name    = base_spec.display_name,
                cost            = base_spec.cost,
                defense_bonus   = base_spec.defense_bonus,
                start_count     = count,
                description     = base_spec.description,
                combat_strength = base_spec.combat_strength,
                health          = base_spec.health,
                morale          = base_spec.morale,
            )
            structure_specs.append(s)

    return PlayerStartKit(
        faction_id      = faction_id,
        unit_specs      = unit_specs,
        structure_specs = structure_specs,
        support_tokens  = unit_config.support_tokens,
        discount_tokens = unit_config.discount_tokens,
        forge_tokens    = unit_config.forge_tokens,
    )
