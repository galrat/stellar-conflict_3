"""
faction_base.py — базовые типы данных для системы фракций Stellar Conflict.

Содержит: CardLevel, BattleCard, OrderUpgrade, UnitConfig, Faction, Player.

Намеренно не зависит от game_state.py — можно изменять этот файл
без затрагивания игровой логики, и наоборот.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union

from units import Unit, UnitCategory, GroundType, SpaceType, make_unit
from tiles import SystemTile, TileType


# ── Уровни боевых карт ──────────────────────────────────────────────────────

class CardLevel(Enum):
    """
    Уровень боевой карты фракции.

    INITIAL — стартовые карты, выдаются в начале игры бесплатно.
    ZERO    — нулевого уровня (базовые покупные).
    TWO     — второго уровня.
    THREE   — третьего уровня.
    """
    INITIAL = "initial"
    ZERO    = 0
    TWO     = 2
    THREE   = 3


# ── Боевая карта ─────────────────────────────────────────────────────────────

@dataclass
class BattleCard:
    """
    Боевая карта, разыгрываемая в бою для изменения его исхода.
    Каждая карта имеет два независимых свойства/эффекта.
    """
    name:     str
    level:    CardLevel
    effect_1: str   # первый эффект карты
    effect_2: str   # второй эффект карты

    def to_dict(self) -> dict:
        return {
            "name":     self.name,
            "level":    self.level.value,
            "effect_1": self.effect_1,
            "effect_2": self.effect_2,
        }


# ── Улучшение приказа ────────────────────────────────────────────────────────

@dataclass
class OrderUpgrade:
    """
    Улучшение конкретного типа приказа, уникальное для фракции.
    Изменяет правила выполнения выбранного типа приказа.
    """
    name:       str
    order_type: str   # "move" | "attack" | "reinforce" | "dominate" | "build"
    effect_1:   str   # первый эффект улучшения
    effect_2:   str   # второй эффект улучшения

    def to_dict(self) -> dict:
        return {
            "name":       self.name,
            "order_type": self.order_type,
            "effect_1":   self.effect_1,
            "effect_2":   self.effect_2,
        }


# ── Конфигурация начальных юнитов ────────────────────────────────────────────

@dataclass
class UnitConfig:
    """
    Конфигурация начального набора юнитов фракции.
    Значения — количество юнитов каждого типа у игрока в начале партии.
    """
    infantry:   int = 2
    marines:    int = 1
    mechanized: int = 1
    elite:      int = 0
    fighters:   int = 2
    destroyers: int = 1

    @property
    def total_ground(self) -> int:
        return self.infantry + self.marines + self.mechanized + self.elite

    @property
    def total_space(self) -> int:
        return self.fighters + self.destroyers

    @property
    def total(self) -> int:
        return self.total_ground + self.total_space

    def build_units(self, player_id: int) -> List[Unit]:
        """Создаёт список объектов Unit согласно конфигурации."""
        units: List[Unit] = []
        specs = [
            (UnitCategory.GROUND, GroundType.INFANTRY,   self.infantry),
            (UnitCategory.GROUND, GroundType.MARINES,    self.marines),
            (UnitCategory.GROUND, GroundType.MECHANIZED, self.mechanized),
            (UnitCategory.GROUND, GroundType.ELITE,      self.elite),
            (UnitCategory.SPACE,  SpaceType.FIGHTER,     self.fighters),
            (UnitCategory.SPACE,  SpaceType.DESTROYER,   self.destroyers),
        ]
        for category, unit_type, count in specs:
            for _ in range(count):
                units.append(make_unit(player_id, category, unit_type))
        return units

    def to_dict(self) -> dict:
        return {
            "infantry":    self.infantry,
            "marines":     self.marines,
            "mechanized":  self.mechanized,
            "elite":       self.elite,
            "fighters":    self.fighters,
            "destroyers":  self.destroyers,
            "total_ground": self.total_ground,
            "total_space":  self.total_space,
            "total":        self.total,
        }


# ── Фракция ──────────────────────────────────────────────────────────────────

@dataclass
class Faction:
    """
    Полное описание фракции.

    Поля:
        id                   — уникальный строковый идентификатор
        name                 — отображаемое название
        icon                 — символ-иконка для консольного интерфейса
        flavor               — художественное описание фракции
        special_ability_name — название фракционного особого свойства
        special_ability_desc — описание эффекта особого свойства
        unit_config          — состав и количество начальных юнитов
        battle_cards         — список боевых карт всех уровней
        order_upgrades       — список улучшений приказов
        extra                — произвольный словарь для будущих механик
                               (ресурсы, постройки, технологии и т.д.)
    """
    id:                    str
    name:                  str
    icon:                  str
    flavor:                str
    special_ability_name:  str
    special_ability_desc:  str
    unit_config:           UnitConfig         = field(default_factory=UnitConfig)
    battle_cards:          List[BattleCard]   = field(default_factory=list)
    order_upgrades:        List[OrderUpgrade] = field(default_factory=list)
    extra:                 dict               = field(default_factory=dict)

    def cards_by_level(self, level: CardLevel) -> List[BattleCard]:
        """Все боевые карты указанного уровня."""
        return [c for c in self.battle_cards if c.level == level]

    def upgrade_for(self, order_type: str) -> Optional[OrderUpgrade]:
        """Улучшение для конкретного типа приказа (None если нет)."""
        return next(
            (u for u in self.order_upgrades if u.order_type == order_type),
            None
        )

    def to_dict(self) -> dict:
        return {
            "id":                   self.id,
            "name":                 self.name,
            "icon":                 self.icon,
            "flavor":               self.flavor,
            "special_ability_name": self.special_ability_name,
            "special_ability_desc": self.special_ability_desc,
            "unit_config":          self.unit_config.to_dict(),
            "battle_cards":         [c.to_dict() for c in self.battle_cards],
            "order_upgrades":       [u.to_dict() for u in self.order_upgrades],
            "extra":                self.extra,
        }


# ── Игрок ─────────────────────────────────────────────────────────────────────

@dataclass
class Player:
    """Игрок и его текущее состояние в партии."""
    id:      int
    name:    str
    color:   str       # "p1" | "p2"
    faction: Faction   # объект фракции (не просто строка-ID)

    pool:   List[Unit]       = field(default_factory=list)  # резерв (не на поле)
    hand:   List[SystemTile] = field(default_factory=list)  # тайлы в руке
    orders: List             = field(default_factory=list)  # список Order-объектов

    @property
    def faction_id(self) -> str:
        """Строковый ID фракции (для сериализации)."""
        return self.faction.id

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "name":       self.name,
            "color":      self.color,
            "faction_id": self.faction_id,
            "faction":    self.faction.to_dict(),
            "pool_count": len(self.pool),
            "pool":       [u.to_dict() for u in self.pool],
            "hand_count": len(self.hand),
            "orders":     [
                o.to_dict() if hasattr(o, "to_dict") else o
                for o in self.orders
            ],
        }
