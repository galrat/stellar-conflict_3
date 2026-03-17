"""
units.py — определения юнитов игры Stellar Conflict
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union
import uuid


class UnitCategory(Enum):
    """Категория юнита — определяет, куда он может быть размещён."""
    GROUND = "ground"   # наземные — только планеты
    SPACE  = "space"    # космические — только космос


class GroundType(Enum):
    """Типы наземной пехоты."""
    INFANTRY    = "infantry"     # Пехота          — дёшево, много
    MARINES     = "marines"      # Десантники       — атака + планеты
    MECHANIZED  = "mechanized"   # Механизированные — бронетехника
    ELITE       = "elite"        # Элитные          — лучший бонус атаки


class SpaceType(Enum):
    """Типы космических кораблей."""
    FIGHTER     = "fighter"      # Истребитель — быстрый, слабый
    DESTROYER   = "destroyer"    # Эсминец     — сбалансированный


class StructureType(Enum):
    """Тип постройки — размещается на планете, не участвует в бою."""
    FACTORY = "factory"   # Фабрика  — производство юнитов
    CITY    = "city"      # Город    — технологический уровень / контроль
    BASTION = "bastion"   # Бастион  — оборонительный бонус


class ResourceType(Enum):
    """Тип жетона ресурса — хранится в инвентаре игрока."""
    SUPPORT  = "support"   # Жетон поддержки в бою - юнит нулевого уровня
    DISCOUNT = "discount"  # Жетон скидки в 2 материала
    FORGE    = "forge"     # Жетон кузницы для постройки юнитов и компенсации городов


STRUCTURE_STATS = {
    StructureType.FACTORY: {"symbol": "⚙", "label": "Фабрика"},
    StructureType.CITY:    {"symbol": "⬡", "label": "Город"},
    StructureType.BASTION: {"symbol": "⛉", "label": "Бастион"},
}

RESOURCE_STATS = {
    ResourceType.SUPPORT:  {"symbol": "⊕", "label": "Поддержка"},
    ResourceType.DISCOUNT: {"symbol": "⊖", "label": "Скидка"},
    ResourceType.FORGE:    {"symbol": "⊗", "label": "Кузница"},
}


# Боевые характеристики каждого типа юнита
# attack_bonus добавляется к броску кубика в бою
UNIT_STATS = {
    GroundType.INFANTRY:   {"attack_bonus": 0, "symbol": "☰", "label": "Пехота"},
    GroundType.MARINES:    {"attack_bonus": 1, "symbol": "⚔", "label": "Десант"},
    GroundType.MECHANIZED: {"attack_bonus": 1, "symbol": "⊞", "label": "Механ."},
    GroundType.ELITE:      {"attack_bonus": 2, "symbol": "★", "label": "Элита"},
    SpaceType.FIGHTER:     {"attack_bonus": 0, "symbol": "◁", "label": "Истреб."},
    SpaceType.DESTROYER:   {"attack_bonus": 1, "symbol": "◈", "label": "Эсминец"},
}


@dataclass
class Unit:
    """Один юнит на поле."""
    id:           str           = field(default_factory=lambda: str(uuid.uuid4())[:8])
    player_id:    int           = 0            # 0 или 1
    category:     UnitCategory  = UnitCategory.GROUND
    unit_type:    Optional[Union[GroundType, SpaceType]] = None

    @property
    def attack_bonus(self) -> int:
        return UNIT_STATS.get(self.unit_type, {}).get("attack_bonus", 0)

    @property
    def symbol(self) -> str:
        return UNIT_STATS.get(self.unit_type, {}).get("symbol", "?")

    @property
    def label(self) -> str:
        return UNIT_STATS.get(self.unit_type, {}).get("label", "?")

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "player_id": self.player_id,
            "category":  self.category.value,
            "unit_type": self.unit_type.value if self.unit_type else None,
            "attack_bonus": self.attack_bonus,
            "symbol":    self.symbol,
            "label":     self.label,
        }


def make_unit(player_id: int, category: UnitCategory, unit_type) -> Unit:
    """Фабрика юнитов."""
    return Unit(player_id=player_id, category=category, unit_type=unit_type)


@dataclass
class Structure:
    """Постройка на планете. Не участвует в бою, занимает место на поле."""
    id:             str           = field(default_factory=lambda: str(uuid.uuid4())[:8])
    player_id:      int           = 0
    structure_type: StructureType = StructureType.FACTORY

    @property
    def symbol(self) -> str:
        return STRUCTURE_STATS.get(self.structure_type, {}).get("symbol", "?")

    @property
    def label(self) -> str:
        return STRUCTURE_STATS.get(self.structure_type, {}).get("label", "?")

    def to_dict(self) -> dict:
        return {
            "id":             self.id,
            "player_id":      self.player_id,
            "structure_type": self.structure_type.value,
            "symbol":         self.symbol,
            "label":          self.label,
        }


@dataclass
class ResourceToken:
    """Жетон ресурса — хранится в инвентаре игрока, не размещается на поле."""
    resource_type: ResourceType = ResourceType.SUPPORT

    @property
    def symbol(self) -> str:
        return RESOURCE_STATS.get(self.resource_type, {}).get("symbol", "?")

    @property
    def label(self) -> str:
        return RESOURCE_STATS.get(self.resource_type, {}).get("label", "?")

    def to_dict(self) -> dict:
        return {
            "resource_type": self.resource_type.value,
            "symbol":        self.symbol,
            "label":         self.label,
        }


def make_structure(player_id: int, structure_type: StructureType) -> Structure:
    """Фабрика построек."""
    return Structure(player_id=player_id, structure_type=structure_type)
