"""
game_state.py — главный движок игры Stellar Conflict

Использование:
    from game_state import GameState, GameConfig

    cfg = GameConfig(
        p1_name="Alpha", p1_faction="orks",
        p2_name="Omega",  p2_faction="marine",
        total_rounds=2,
        # Переопределить начальные юниты (опционально):
        p1_unit_config=UnitConfig(infantry=3, marines=1, fighters=2, destroyers=1),
    )
    game = GameState(cfg)

    # Разместить тайл
    ok = game.place_tile(player_id=0, hand_index=0, col=0, row=0)

    # Повернуть тайл
    game.rotate_tile(col=0, row=0, clockwise=True)

    # Вернуть тайл
    game.undo_tile(player_id=0)

    # Разместить юнит
    ok = game.place_unit(player_id=0, unit_index=0, tile_key="0,0", area_index=1)

    # Вернуть последний юнит
    game.undo_last_unit(player_id=0)
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import random

from units import Unit, UnitCategory, GroundType, SpaceType
from tiles import SystemTile, TileType, AreaType, AREA_LAYOUTS, TILE_CATALOG
from board import Board
from faction_base import Player, Faction, UnitConfig
from faction_defs import FACTIONS, FACTION_CONFIGS
from game_serializer import generate_game_state, save_game_state


# ── Stub для боевой системы (combat.py) ────────────────────────────────────

@dataclass
class BattleResult:
    """Результат боевого столкновения."""
    winner_id: int
    damage_p0: int
    damage_p1: int

    def to_dict(self) -> dict:
        return {
            "winner_id": self.winner_id,
            "damage_p0": self.damage_p0,
            "damage_p1": self.damage_p1,
        }

def resolve_battle(tile_key: str, area_idx: int, area_type: str, p0_units: List[Unit], p1_units: List[Unit]) -> BattleResult:
    """Разрешить боевое столкновение и вернуть результат."""
    p0_str = sum(u.combat_strength for u in p0_units)
    p1_str = sum(u.combat_strength for u in p1_units)

    winner_id = 0 if p0_str >= p1_str else 1
    damage_p0 = max(1, len(p1_units) // 2)
    damage_p1 = max(1, len(p0_units) // 2)

    return BattleResult(winner_id, damage_p0, damage_p1)

def apply_battle(area, result: BattleResult) -> None:
    """Применить результаты боя к зоне."""
    # Удалить юниты
    units_to_remove = []
    for unit in area.units[:result.damage_p0 + result.damage_p1]:
        units_to_remove.append(unit)
    for unit in units_to_remove:
        area.units.remove(unit)

def format_battle(result: BattleResult, p0_name: str, p1_name: str) -> str:
    """Форматировать результат боя в текст."""
    winner = p0_name if result.winner_id == 0 else p1_name
    return f"БОЙ: Победитель {winner} (урон: P0={result.damage_p0}, P1={result.damage_p1})"


# ── Фазы игры ──────────────────────────────────────────────────────────────

class Phase(Enum):
    SETUP           = "setup"
    TILE_PLACEMENT  = "tile_placement"     # размещение тайла + войска на него
    TROOP_ON_TILE   = "troop_on_tile"      # размещение войск на только что поставленный тайл
    TROOP_PLACEMENT = "troop_placement"    # общая расстановка оставшихся войск
    ORDER_PLACEMENT = "order_placement"    # расстановка приказов
    EXECUTION       = "execution"          # исполнение приказов
    ENDED           = "ended"


# ── Приказ ─────────────────────────────────────────────────────────────────

@dataclass
class Order:
    player_id:  int
    order_slot: int          # 0 или 1
    tile_key:   str          # куда переместить войска
    area_index: int          # в какую зону
    order_type: str = "move"

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id, "order_slot": self.order_slot,
            "tile_key": self.tile_key, "area_index": self.area_index,
            "order_type": self.order_type,
        }


# ── Конфигурация игры ──────────────────────────────────────────────────────

@dataclass
class GameConfig:
    p1_name:        str = "Alpha"
    p1_faction:     str = "orks"
    p2_name:        str = "Omega"
    p2_faction:     str = "marine"
    total_rounds:   int = 2
    tiles_per_player: int = 3

    # Опциональные переопределения юнитов (если None — берётся дефолт фракции)
    p1_unit_config: Optional[UnitConfig] = None
    p2_unit_config: Optional[UnitConfig] = None

    def unit_config(self, player_id: int) -> UnitConfig:
        if player_id == 0:
            return self.p1_unit_config or FACTION_CONFIGS[self.p1_faction]
        return self.p2_unit_config or FACTION_CONFIGS[self.p2_faction]


# ── Запись журнала ─────────────────────────────────────────────────────────

@dataclass
class LogEntry:
    message:   str
    player_id: int = -1   # -1 = системное сообщение

    def to_dict(self) -> dict:
        return {"message": self.message, "player_id": self.player_id}


# ══════════════════════════════════════════════════════════════════════════
#  ГЛАВНЫЙ ДВИЖОК
# ══════════════════════════════════════════════════════════════════════════

class GameState:
    """
    Полное состояние игры. Все действия возвращают (success: bool, message: str).
    После каждого успешного действия состояние можно сериализовать в JSON.
    """

    def __init__(self, config: GameConfig):
        self.config = config
        self.board  = Board()
        self.phase  = Phase.SETUP
        self.current_player_id = 0
        self.round  = 1
        self.log: List[LogEntry] = []

        # Построить игроков
        self.players: List[Player] = []
        for pi, (name, fid) in enumerate([
            (config.p1_name, config.p1_faction),
            (config.p2_name, config.p2_faction),
        ]):
            p = Player(id=pi, name=name, color=f"p{pi+1}", faction=FACTIONS[fid])
            uc = config.unit_config(pi)
            p.pool       = uc.build_units(pi)
            p.structures = uc.build_structures(pi)
            p.resources  = uc.build_resources()
            p.credits    = uc.credits
            p.orders     = [None, None]
            self.players.append(p)

        # Сформировать пул обычных тайлов и перемешать
        normal_ids = [tid for tid, td in TILE_CATALOG.items() if not td.is_home]
        random.shuffle(normal_ids)
        normal_pool = iter(normal_ids)

        # Раздать тайлы каждому игроку
        for pi, p in enumerate(self.players):
            fid = p.faction.id
            home_tile_id = p.faction.home_tile_id

            # Домашний тайл — специфичный для фракции
            home_tile = SystemTile(
                tile_type=TileType.HOME,
                tile_def_id=home_tile_id,
                owner=pi,
            )
            p.hand.append(home_tile)

            # Обычные тайлы — рандомно из пула
            for _ in range(config.tiles_per_player - 1):
                normal_id = next(normal_pool, None)
                tile = SystemTile(
                    tile_type=TileType.NORMAL,
                    tile_def_id=normal_id or "",
                    owner=pi,
                )
                p.hand.append(tile)

        # Внутреннее состояние для отмены
        self._last_placed: Optional[dict] = None   # {"player_id", "tile_key", "hand_idx"}
        self._units_placed_this_turn: List[dict] = []   # [{"player_id","tile_key","area_idx","unit_id"}]
        self._structs_placed_this_turn: List[dict] = [] # [{"player_id","tile_key","area_idx","struct_id"}]

        # Очередь исполнения приказов
        self._exec_queue: List[Order] = []
        self._exec_pos:   int = 0

        self._add_log("Игра начата", -1)
        self.phase = Phase.TILE_PLACEMENT
        self._add_log(f"Ход {self.players[0].name}: разместите систему", 0)

    # ── Вспомогательные ────────────────────────────────────────────────────

    def _add_log(self, msg: str, player_id: int = -1):
        self.log.append(LogEntry(msg, player_id))

    def _cp(self) -> Player:
        """Текущий игрок."""
        return self.players[self.current_player_id]

    def _ok(self, msg: str = "OK") -> Tuple[bool, str]:
        return True, msg

    def _err(self, msg: str) -> Tuple[bool, str]:
        return False, msg

    # ── TILE PLACEMENT ──────────────────────────────────────────────────────

    def place_tile(self, player_id: int, hand_index: int,
                   col: int, row: int) -> Tuple[bool, str]:
        """Разместить тайл с позиции hand_index из руки игрока на поле."""
        if self.phase != Phase.TILE_PLACEMENT:
            return self._err("Сейчас не фаза размещения тайлов.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")

        p = self.players[player_id]
        if hand_index < 0 or hand_index >= len(p.hand):
            return self._err(f"Нет тайла с индексом {hand_index}.")
        tile = p.hand[hand_index]
        if tile is None:
            return self._err("Тайл уже размещён.")

        tile.col = col; tile.row = row
        if not self.board.place(tile):
            return self._err(f"Позиция ({col},{row}) недопустима.")

        # Сохранить для возможной отмены
        self._last_placed = {"player_id": player_id, "tile_key": tile.key,
                              "hand_idx": hand_index}
        self._units_placed_this_turn   = []
        self._structs_placed_this_turn = []
        p.hand[hand_index] = None  # помечаем как выбывший из руки

        self._add_log(
            f"{p.name} разместил {'домашнюю' if tile.is_home else ''} систему [{tile.key}]",
            player_id)
        self.phase = Phase.TROOP_ON_TILE
        return self._ok(f"Тайл размещён на [{tile.key}]. Разместите войска.")

    def rotate_tile(self, col: int, row: int,
                    clockwise: bool = True) -> Tuple[bool, str]:
        """
        Повернуть тайл на 90°. Доступно в фазах TILE_PLACEMENT и TROOP_ON_TILE
        для только что поставленного тайла, но разрешено также до передачи хода.
        """
        if self.phase not in (Phase.TILE_PLACEMENT, Phase.TROOP_ON_TILE):
            return self._err("Сейчас нельзя вращать тайлы.")
        # Если есть только что поставленный тайл — только его можно вращать
        if self._last_placed and self._last_placed["tile_key"] != f"{col},{row}":
            return self._err("Можно вращать только только что поставленный тайл.")
        if clockwise:
            ok = self.board.rotate_tile_cw(col, row)
        else:
            ok = self.board.rotate_tile_ccw(col, row)
        if not ok:
            return self._err(f"Тайл в ({col},{row}) не найден.")
        direction = "по часовой" if clockwise else "против часовой"
        self._add_log(f"Поворот тайла [{col},{row}] {direction}", self.current_player_id)
        return self._ok(f"Тайл повёрнут {direction}.")

    def undo_tile(self, player_id: int) -> Tuple[bool, str]:
        """
        Вернуть только что поставленный тайл обратно в руку игрока
        (вместе со всеми размещёнными на нём войсками этого хода).
        """
        if self.phase != Phase.TROOP_ON_TILE:
            return self._err("Отменить размещение тайла можно только сразу после его постановки.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")
        if not self._last_placed or self._last_placed["player_id"] != player_id:
            return self._err("Нет тайла для отмены.")

        snap = self._last_placed
        p = self.players[player_id]

        # Вернуть все войска этого хода обратно в резерв
        self._undo_all_troops_on_tile(player_id)

        # Убрать тайл с доски и вернуть в руку
        col, row = map(int, snap["tile_key"].split(","))
        tile = self.board.remove(col, row)
        if tile:
            tile.col = 0; tile.row = 0; tile.rotation = 0
            p.hand[snap["hand_idx"]] = tile
            self._add_log(f"{p.name} вернул систему [{snap['tile_key']}] в руку", player_id)

        self._last_placed = None
        self._units_placed_this_turn   = []
        self._structs_placed_this_turn = []
        self.phase = Phase.TILE_PLACEMENT
        return self._ok("Тайл возвращён в руку.")

    def _undo_all_troops_on_tile(self, player_id: int):
        """Вернуть все войска и постройки текущего хода из тайла в резерв."""
        p = self.players[player_id]
        for record in list(self._units_placed_this_turn):
            tile = self.board.tiles.get(record["tile_key"])
            if tile:
                area = tile.areas[record["area_idx"]]
                idx = next((i for i, u in enumerate(area.units) if u.id == record["unit_id"]), None)
                if idx is not None:
                    unit = area.units.pop(idx)
                    p.pool.append(unit)
        self._units_placed_this_turn = []
        for record in list(self._structs_placed_this_turn):
            tile = self.board.tiles.get(record["tile_key"])
            if tile:
                area = tile.areas[record["area_idx"]]
                idx = next((i for i, s in enumerate(area.structures) if s.id == record["struct_id"]), None)
                if idx is not None:
                    struct = area.structures.pop(idx)
                    p.structures.append(struct)
        self._structs_placed_this_turn = []

    # ── UNIT PLACEMENT ──────────────────────────────────────────────────────

    def place_unit(self, player_id: int, unit_index: int,
                   tile_key: str, area_display_index: int) -> Tuple[bool, str]:
        """
        Разместить юнит из резерва (pool[unit_index]) в зону area_display_index
        тайла tile_key. area_display_index — визуальная позиция (с учётом поворота).
        """
        if self.phase not in (Phase.TROOP_ON_TILE, Phase.TROOP_PLACEMENT):
            return self._err("Сейчас не фаза расстановки войск.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")

        p = self.players[player_id]
        if unit_index < 0 or unit_index >= len(p.pool):
            return self._err(f"Нет юнита с индексом {unit_index}.")

        tile = self.board.tiles.get(tile_key)
        if not tile:
            return self._err(f"Тайл [{tile_key}] не найден на поле.")

        # В фазе TROOP_ON_TILE — только на только что поставленный тайл
        if self.phase == Phase.TROOP_ON_TILE:
            if not self._last_placed or self._last_placed["tile_key"] != tile_key:
                return self._err("В эту фазу — только на только что поставленную систему.")

        # Получить область по визуальной позиции (с учётом поворота)
        areas_display = tile.rotated_areas()
        if area_display_index < 0 or area_display_index >= len(areas_display):
            return self._err("Неверный индекс зоны.")
        area = areas_display[area_display_index]
        # Найти реальный индекс зоны в tile.areas
        real_area_idx = tile.areas.index(area)

        unit = p.pool[unit_index]
        if not area.accepts(unit):
            type_label = "планету" if unit.category == UnitCategory.GROUND else "космос"
            return self._err(
                f"{unit.label} ({unit.category.value}) размещается только на {type_label}. "
                f"Эта зона — {area.area_type.value}.")

        area.units.append(unit)
        p.pool.pop(unit_index)
        self._units_placed_this_turn.append({
            "player_id": player_id, "tile_key": tile_key,
            "area_idx": real_area_idx, "unit_id": unit.id,
        })
        self._add_log(
            f"{p.name} → [{tile_key}] зона {area_display_index+1} ({unit.label})", player_id)
        return self._ok(f"Юнит '{unit.label}' размещён.")

    def undo_last_unit(self, player_id: int) -> Tuple[bool, str]:
        """Вернуть последний поставленный юнит обратно в резерв."""
        if self.phase not in (Phase.TROOP_ON_TILE, Phase.TROOP_PLACEMENT):
            return self._err("Сейчас нельзя отменить размещение юнита.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")
        if not self._units_placed_this_turn:
            return self._err("Нечего отменять — в этот ход юниты ещё не размещались.")

        record = self._units_placed_this_turn.pop()
        tile = self.board.tiles.get(record["tile_key"])
        p = self.players[player_id]
        if tile:
            area = tile.areas[record["area_idx"]]
            idx = next((i for i, u in enumerate(area.units) if u.id == record["unit_id"]), None)
            if idx is not None:
                unit = area.units.pop(idx)
                p.pool.append(unit)
                self._add_log(f"{p.name} вернул {unit.label} из [{record['tile_key']}]", player_id)
                return self._ok(f"Юнит '{unit.label}' возвращён в резерв.")
        return self._err("Не удалось найти юнит для отмены.")

    # ── STRUCTURE PLACEMENT ─────────────────────────────────────────────────

    def place_structure(self, player_id: int, struct_index: int,
                        tile_key: str, area_display_index: int) -> Tuple[bool, str]:
        """
        Разместить постройку из резерва (structures[struct_index]) на планету.
        Постройки размещаются только на PLANET-зонах, не более одной на зону.
        area_display_index — визуальная позиция (с учётом поворота тайла).
        """
        if self.phase not in (Phase.TROOP_ON_TILE, Phase.TROOP_PLACEMENT):
            return self._err("Сейчас не фаза расстановки войск и построек.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")

        p = self.players[player_id]
        if struct_index < 0 or struct_index >= len(p.structures):
            return self._err(f"Нет постройки с индексом {struct_index}.")

        tile = self.board.tiles.get(tile_key)
        if not tile:
            return self._err(f"Тайл [{tile_key}] не найден на поле.")

        if self.phase == Phase.TROOP_ON_TILE:
            if not self._last_placed or self._last_placed["tile_key"] != tile_key:
                return self._err("В эту фазу — только на только что поставленную систему.")

        areas_display = tile.rotated_areas()
        if area_display_index < 0 or area_display_index >= len(areas_display):
            return self._err("Неверный индекс зоны.")
        area = areas_display[area_display_index]
        real_area_idx = tile.areas.index(area)

        if area.area_type != AreaType.PLANET:
            return self._err("Постройки можно размещать только на планетах.")
        if area.structures:
            return self._err("На этой планете уже есть постройка.")

        struct = p.structures[struct_index]
        area.structures.append(struct)
        p.structures.pop(struct_index)
        self._structs_placed_this_turn.append({
            "player_id": player_id, "tile_key": tile_key,
            "area_idx": real_area_idx, "struct_id": struct.id,
        })
        self._add_log(
            f"{p.name} → [{tile_key}] зона {area_display_index+1} ({struct.label})", player_id)
        return self._ok(f"Постройка '{struct.label}' размещена.")

    def undo_last_structure(self, player_id: int) -> Tuple[bool, str]:
        """Вернуть последнюю поставленную постройку обратно в резерв."""
        if self.phase not in (Phase.TROOP_ON_TILE, Phase.TROOP_PLACEMENT):
            return self._err("Сейчас нельзя отменить размещение постройки.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")
        if not self._structs_placed_this_turn:
            return self._err("Нечего отменять — в этот ход постройки ещё не размещались.")

        record = self._structs_placed_this_turn.pop()
        tile = self.board.tiles.get(record["tile_key"])
        p = self.players[player_id]
        if tile:
            area = tile.areas[record["area_idx"]]
            idx = next((i for i, s in enumerate(area.structures) if s.id == record["struct_id"]), None)
            if idx is not None:
                struct = area.structures.pop(idx)
                p.structures.append(struct)
                self._add_log(f"{p.name} вернул {struct.label} из [{record['tile_key']}]", player_id)
                return self._ok(f"Постройка '{struct.label}' возвращена в резерв.")
        return self._err("Не удалось найти постройку для отмены.")

    # ── TURN TRANSITIONS ────────────────────────────────────────────────────

    def end_troop_on_tile(self, player_id: int) -> Tuple[bool, str]:
        """Завершить размещение войск на тайл, передать ход."""
        if self.phase != Phase.TROOP_ON_TILE:
            return self._err("Сейчас не та фаза.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")

        self._last_placed = None
        self._units_placed_this_turn   = []
        self._structs_placed_this_turn = []
        total_needed = self.config.tiles_per_player * 2

        if len(self.board.tiles) < total_needed:
            # Передать ход другому игроку для размещения тайла
            self.current_player_id = 1 - self.current_player_id
            self.phase = Phase.TILE_PLACEMENT
            cp = self._cp()
            self._add_log(f"Ход {cp.name}: разместите систему", cp.id)
            return self._ok(f"Ход передан {cp.name}.")
        else:
            # Все тайлы расставлены
            any_pool = any(len(p.pool) > 0 for p in self.players)
            if any_pool:
                self.current_player_id = 0
                self.phase = Phase.TROOP_PLACEMENT
                cp = self._cp()
                self._add_log(f"Ход {cp.name}: расставьте оставшиеся войска", cp.id)
                return self._ok("Переход к расстановке оставшихся войск.")
            else:
                return self._start_order_phase()

    def end_troop_placement(self, player_id: int) -> Tuple[bool, str]:
        """Завершить общую расстановку войск."""
        if self.phase != Phase.TROOP_PLACEMENT:
            return self._err("Сейчас не фаза расстановки войск.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")

        self._units_placed_this_turn   = []
        self._structs_placed_this_turn = []
        other = self.players[1 - player_id]
        if len(other.pool) > 0:
            self.current_player_id = 1 - player_id
            self._add_log(f"Ход {other.name}: расставьте оставшиеся войска", other.id)
            return self._ok(f"Ход передан {other.name}.")
        else:
            return self._start_order_phase()

    # ── ORDER PLACEMENT ─────────────────────────────────────────────────────

    def _start_order_phase(self) -> Tuple[bool, str]:
        for p in self.players:
            p.orders = [None, None]
        self.current_player_id = 0
        self.phase = Phase.ORDER_PLACEMENT
        cp = self._cp()
        self._add_log(f"Фаза приказов. Ход {cp.name}", cp.id)
        return self._ok("Начинается фаза приказов.")

    def place_order(self, player_id: int, order_slot: int,
                    tile_key: str, area_index: int) -> Tuple[bool, str]:
        """Разместить приказ."""
        if self.phase != Phase.ORDER_PLACEMENT:
            return self._err("Сейчас не фаза приказов.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")
        if order_slot not in (0, 1):
            return self._err("Слот приказа: 0 или 1.")
        if not self.board.tiles.get(tile_key):
            return self._err(f"Тайл [{tile_key}] не найден.")

        p = self.players[player_id]
        p.orders[order_slot] = Order(player_id, order_slot, tile_key, area_index)
        self._add_log(f"{p.name}: приказ {order_slot+1} → [{tile_key}] зона {area_index+1}", player_id)
        return self._ok("Приказ размещён.")

    def cancel_order(self, player_id: int, order_slot: int) -> Tuple[bool, str]:
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")
        self.players[player_id].orders[order_slot] = None
        return self._ok("Приказ отменён.")

    def confirm_orders(self, player_id: int) -> Tuple[bool, str]:
        """Подтвердить приказы и передать ход / начать исполнение."""
        if self.phase != Phase.ORDER_PLACEMENT:
            return self._err("Сейчас не фаза приказов.")
        if player_id != self.current_player_id:
            return self._err("Сейчас не ваш ход.")

        p = self.players[player_id]
        if p.orders.count(None) > 0:
            return self._err("Нужно разместить 2 приказа.")

        other_id = 1 - player_id
        other = self.players[other_id]
        if other.orders[0] is None or other.orders[1] is None:
            self.current_player_id = other_id
            self._add_log(f"Ход {other.name}: расставьте приказы", other_id)
            return self._ok(f"Ход передан {other.name}.")
        else:
            return self._start_execution()

    # ── EXECUTION ───────────────────────────────────────────────────────────

    def _start_execution(self) -> Tuple[bool, str]:
        self._exec_queue = []
        self._exec_pos   = 0
        for oi in range(2):
            for pi in range(2):
                ord_ = self.players[pi].orders[oi]
                if ord_:
                    self._exec_queue.append(ord_)
        self.phase = Phase.EXECUTION
        self.current_player_id = 0
        self._add_log("=== ПРИКАЗЫ РАСКРЫТЫ ===", -1)
        return self._ok("Начинается исполнение приказов.")

    def execute_next_order(self) -> Tuple[bool, str, List[BattleResult]]:
        """
        Выполнить следующий приказ из очереди.
        Возвращает (success, message, список_результатов_боёв).
        Список пуст если боёв не было.
        """
        if self.phase != Phase.EXECUTION:
            return False, "Сейчас не фаза исполнения.", []
        if self._exec_pos >= len(self._exec_queue):
            ok, msg = self._end_round()
            return ok, msg, []

        order = self._exec_queue[self._exec_pos]
        self._exec_pos += 1

        target = self.board.tiles.get(order.tile_key)
        if not target:
            return True, "Тайл не найден, приказ пропущен.", None

        # Переместить войска из соседних тайлов
        neighbors = self.board.neighbor_keys(order.tile_key)
        moved = 0
        p_name = self.players[order.player_id].name
        for nk in neighbors:
            nt = self.board.tiles.get(nk)
            if not nt:
                continue
            for na in nt.areas:
                to_move = [u for u in na.units if u.player_id == order.player_id]
                for unit in to_move:
                    # Найти совместимую зону в целевом тайле
                    dest_area = self._find_compatible_area(target, unit, order.area_index)
                    if dest_area is not None:
                        na.units.remove(unit)
                        dest_area.units.append(unit)
                        moved += 1

        self._add_log(
            f"{p_name} приказ {order.order_slot+1}: → [{order.tile_key}] зона {order.area_index+1} ({moved} войск)",
            order.player_id)

        # Проверить бои во всех зонах целевого тайла
        battles = self._check_battles(target)
        return True, f"Приказ выполнен. Перемещено: {moved}.", battles

    def _find_compatible_area(self, tile: SystemTile, unit: Unit,
                               preferred_display_idx: int) -> Optional[object]:
        """Найти зону в тайле, совместимую с типом юнита. Предпочтительно — preferred."""
        areas_display = tile.rotated_areas()
        preferred = areas_display[preferred_display_idx]
        if preferred.accepts(unit):
            return preferred
        # Найти любую совместимую
        for area in tile.areas:
            if area.accepts(unit):
                return area
        return None

    def _check_battles(self, tile: SystemTile) -> List[BattleResult]:
        """Проверить все зоны тайла на конфликт и разыграть каждый бой."""
        results: List[BattleResult] = []
        for ai, area in enumerate(tile.areas):
            p0 = [u for u in area.units if u.player_id == 0]
            p1 = [u for u in area.units if u.player_id == 1]
            if p0 and p1:
                result = resolve_battle(tile.key, ai, area.area_type.value, p0, p1)
                apply_battle(area, result)
                self._add_log(
                    format_battle(result, self.players[0].name, self.players[1].name), -1)
                results.append(result)
        return results

    def _end_round(self) -> Tuple[bool, str]:
        if self.round >= self.config.total_rounds:
            return self._end_game()
        self.round += 1
        self._add_log(f"=== РАУНД {self.round} НАЧАЛСЯ ===", -1)
        ok, msg = self._start_order_phase()
        return ok, msg

    def _end_game(self) -> Tuple[bool, str]:
        self.phase = Phase.ENDED
        scores = [self.board.count_units(pi) for pi in range(2)]
        winner = 0 if scores[0] >= scores[1] else 1
        self._add_log(
            f"=== ИГРА ОКОНЧЕНА === Победил {self.players[winner].name} "
            f"({scores[winner]} войск против {scores[1-winner]})", -1)
        return True, f"Игра окончена. Победитель: {self.players[winner].name}"

    # ── SERIALIZATION ───────────────────────────────────────────────────────

    def score(self) -> dict:
        return {
            f"p{pi}_{self.players[pi].name}": self.board.count_units(pi) + len(self.players[pi].pool)
            for pi in range(2)
        }

    def to_dict(self) -> dict:
        return {
            "phase":             self.phase.value,
            "round":             self.round,
            "total_rounds":      self.config.total_rounds,
            "current_player_id": self.current_player_id,
            "players":           [p.to_dict() for p in self.players],
            "board":             self.board.to_dict(),
            "log":               [e.to_dict() for e in self.log[-20:]],
            "score":             self.score(),
            "exec_queue_len":    len(self._exec_queue),
            "exec_pos":          self._exec_pos,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def save_game(self, filename: str = None) -> Tuple[bool, str]:
        """
        Сохраняет текущее состояние игры в файл.

        Args:
            filename: имя файла (например "game_001.json").
                     Если None, генерируется автоматически.

        Returns:
            (True, filepath) если успешно, (False, error_msg) иначе
        """
        if filename is None:
            # Генерируем имя файла автоматически
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_{timestamp}.json"

        state = generate_game_state(self)
        if save_game_state(state, filename):
            return True, f"Игра сохранена в {filename}"
        else:
            return False, f"Ошибка при сохранении игры"
