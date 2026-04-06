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

from units import (Unit, UnitCategory, GroundType, SpaceType, make_unit,
                   Structure, StructureType, make_structure,
                   ResourceToken, ResourceType)
from tiles import SystemTile, TileType


# ── Уровни боевых карт ──────────────────────────────────────────────────────

class CardLevel(Enum):
    """
    Уровень боевой карты фракции.

    INITIAL — стартовые карты, выдаются в начале игры бесплатно (уровень -1).
    ZERO    — нулевого уровня (базовые покупные).
    TWO     — второго уровня.
    THREE   — третьего уровня.
    """
    INITIAL = -1
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
    tier:     int = 0  # уровень карты для совместимости (дублирует level.value)
    cost:     int = 0  # стоимость карты в условных единицах (0, 2, 4, 6)

    def to_dict(self) -> dict:
        return {
            "name":     self.name,
            "level":    self.level.value,
            "tier":     self.tier,
            "cost":     self.cost,
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
    id:         str = ""  # уникальный идентификатор улучшения (опционально)
    tier:       int = 0   # уровень улучшения (опционально)
    cost:       int = 0   # стоимость улучшения (опционально)

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "name":       self.name,
            "order_type": self.order_type,
            "tier":       self.tier,
            "cost":       self.cost,
            "effect_1":   self.effect_1,
            "effect_2":   self.effect_2,
        }


# ── Карта событий ──────────────────────────────────────────────────────────

@dataclass
class EventCard:
    """
    Карта события, используемая в расширенной механике игры.
    Содержит информацию о движении вихря деформации и эффектах карты.
    """
    name:             str
    warp_storm_move:  str   # направление движения вихря деформации
    card_type:        str   # "Scheme" | "Tactic"
    effect:           str   # описание эффекта карты

    def to_dict(self) -> dict:
        return {
            "name":             self.name,
            "warp_storm_move":  self.warp_storm_move,
            "card_type":        self.card_type,
            "effect":           self.effect,
        }


# ── Конфигурация начальных юнитов ────────────────────────────────────────────

@dataclass
class UnitConfig:
    """
    Конфигурация начального набора юнитов, построек и ресурсов фракции.
    Все значения — количество соответствующих объектов у игрока в начале партии.

    unit_stats — характеристики юнитов, специфичные для данной фракции.
        Ключ: имя типа ("infantry", "marines", "mechanized", "elite",
                        "fighter", "destroyer").
        Значение: dict с полями:
            name            — отображаемое название юнита (уникально для фракции)
            cost            — стоимость покупки в монетах (2–5)
            cost_forge      — стоимость в жетонах молотка (опционально, по умолчанию 0)
            combat_strength — боевая сила (0–6)
            health          — здоровье (1–6)
            morale          — мораль (0–6)
            max_count       — максимальное количество юнитов данного типа в игре
                              (стартовые + докупаемые через приказы). Отображается
                              как пул доступных к покупке единиц (max_count − на поле).
        Если тип не указан — используются значения из UNIT_TYPE_CATALOG (player_hand.py).

    battle_card_deck — стартовая колода боевых карт фракции.
        Список кортежей (card_name, level, cost), где:
            card_name — название карты (строка)
            level     — числовой уровень карты (-1 для INITIAL, 0, 2, 3)
            cost      — стоимость карты в условных единицах (0 для INITIAL, 2 для уровня 0, 4 для уровня 2, 6 для уровня 3)
    """
    # ── Боевые юниты ─────────────────────────────────────────────────────────
    infantry:   int = 2
    marines:    int = 1
    mechanized: int = 1
    elite:      int = 0
    fighters:   int = 2
    destroyers: int = 1
    # ── Постройки ─────────────────────────────────────────────────────────────
    # Размещаются на планетах, по одной на зону; не участвуют в бою.
    # Характеристики построек едины для всех фракций — см. STRUCTURE_CATALOG (player_hand.py).
    factories:  int = 0   # Фабрика  — производство юнитов
    cities:     int = 0   # Город    — победные очки
    bastions:   int = 0   # Бастион  — оборонительный бонус
    # ── Стартовые ресурсы ─────────────────────────────────────────────────────
    # Хранятся в инвентаре игрока, не размещаются на поле.
    credits:         int = 6   # Монеты — основная валюта
    reinforcement_tokens:  int = 0   # Жетон поддержки (⊕)
    cash_tokens: int = 0   # Жетон скидки (⊖)
    forge_tokens:    int = 0   # Жетон кузницы/молотка (⚒)
    # ── Характеристики юнитов (per-faction) ───────────────────────────────────
    unit_stats:      Dict[str, dict] = field(default_factory=dict)
    # ── Стартовая колода боевых карт ──────────────────────────────────────────
    # Список кортежей: (card_name, level, cost)
    battle_card_deck: List[tuple]    = field(default_factory=list)

    @property
    def total_ground(self) -> int:
        return self.infantry + self.marines + self.mechanized + self.elite

    @property
    def total_space(self) -> int:
        return self.fighters + self.destroyers

    @property
    def total_structures(self) -> int:
        return self.factories + self.cities + self.bastions

    @property
    def total_resources(self) -> int:
        return self.reinforcement_tokens + self.cash_tokens + self.forge_tokens

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

    def build_structures(self, player_id: int) -> List[Structure]:
        """Создаёт список объектов Structure согласно конфигурации."""
        structures: List[Structure] = []
        specs = [
            (StructureType.FACTORY, self.factories),
            (StructureType.CITY,    self.cities),
            (StructureType.BASTION, self.bastions),
        ]
        for structure_type, count in specs:
            for _ in range(count):
                structures.append(make_structure(player_id, structure_type))
        return structures

    def build_resources(self) -> List[ResourceToken]:
        """Создаёт список ResourceToken согласно конфигурации."""
        resources: List[ResourceToken] = []
        specs = [
            (ResourceType.REINFORCEMENT, self.reinforcement_tokens),
            (ResourceType.CASH,          self.cash_tokens),
            (ResourceType.FORGE,         self.forge_tokens),
        ]
        for resource_type, count in specs:
            for _ in range(count):
                resources.append(ResourceToken(resource_type=resource_type))
        return resources

    def to_dict(self) -> dict:
        return {
            "infantry":        self.infantry,
            "marines":         self.marines,
            "mechanized":      self.mechanized,
            "elite":           self.elite,
            "fighters":        self.fighters,
            "destroyers":      self.destroyers,
            "factories":       self.factories,
            "cities":          self.cities,
            "bastions":        self.bastions,
            "credits":         self.credits,
            "reinforcement_tokens":  self.reinforcement_tokens,
            "cash_tokens": self.cash_tokens,
            "forge_tokens":    self.forge_tokens,
            "unit_stats":      self.unit_stats,
            "battle_card_deck": self.battle_card_deck,
            "total_ground":    self.total_ground,
            "total_space":     self.total_space,
            "total_structures": self.total_structures,
            "total_resources": self.total_resources,
            "total":           self.total,
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
    color:                 str                # hex-цвет фракции для UI, например "#4A90D9"
    home_tile_id:          str                # ID домашнего тайла в TILE_CATALOG, например "home_chaos"
    flavor:                str
    special_ability_name:  str
    special_ability_desc:  str
    unit_config:           UnitConfig         = field(default_factory=UnitConfig)
    battle_cards:          List[BattleCard]   = field(default_factory=list)
    order_upgrades:        List[OrderUpgrade] = field(default_factory=list)
    event_cards:           List[EventCard]    = field(default_factory=list)
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
            "color":                self.color,
            "home_tile_id":         self.home_tile_id,
            "flavor":               self.flavor,
            "special_ability_name": self.special_ability_name,
            "special_ability_desc": self.special_ability_desc,
            "unit_config":          self.unit_config.to_dict(),
            "battle_cards":         [c.to_dict() for c in self.battle_cards],
            "order_upgrades":       [u.to_dict() for u in self.order_upgrades],
            "event_cards":          [e.to_dict() for e in self.event_cards],
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

    pool:       List[Unit]          = field(default_factory=list)  # резерв юнитов (не на поле)
    structures: List[Structure]     = field(default_factory=list)  # резерв построек
    resources:  List[ResourceToken] = field(default_factory=list)  # жетоны ресурсов
    credits:    int                 = 0                            # монеты
    hand:       List[SystemTile]    = field(default_factory=list)  # тайлы в руке
    orders:     List                = field(default_factory=list)  # список Order-объектов
    boughtUpgrades: List[str]       = field(default_factory=list)  # ID купленных улучшений приказов
    object_tokens: int              = 0                            # количество жетонов объектов

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
            "credits":          self.credits,
            "resources":        [r.to_dict() for r in self.resources],
            "pool_count":       len(self.pool),
            "pool":             [u.to_dict() for u in self.pool],
            "structures_count": len(self.structures),
            "structures":       [s.to_dict() for s in self.structures],
            "hand_count":       len(self.hand),
            "orders":     [
                o.to_dict() if hasattr(o, "to_dict") else o
                for o in self.orders
            ],
            "boughtUpgrades":   self.boughtUpgrades,
        }
