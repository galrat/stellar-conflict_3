"""
game_serializer.py — сохранение и загрузка состояния игры

Функции:
    generate_game_state(game_state: GameState) -> dict
    save_game_state(state: dict, filename: str) -> bool
    load_game_state(filename: str) -> Optional[dict]
"""
import json
import os
from typing import Optional, Dict, List
from pathlib import Path


def generate_game_state(game_state) -> dict:
    """
    Конвертирует GameState в JSON-совместимый словарь.

    Структура:
    {
        "turn": int,
        "round": int,
        "phase": str,
        "current_player": str,

        "players": {
            "p1": {
                "name": str,
                "faction": str,
                "money": int,
                "support": int,
                "discount": int,
                "forge": int,
                "hand_battle_cards": [str],              # начальные боевые карты (уровень -1)
                "available_battle_cards": [str],        # доступные боевые карты (уровни 0, 2, 3)
                "hand_order_upgrades": [
                    {
                        "name": str,
                        "order_upgrade_status": "active" or "used",  # статус улучшения приказа
                        ...
                    }
                ],                                      # улучшения приказов на руке
                "available_order_upgrades": [str],      # доступные улучшения приказов
                "hand_event_cards": [str],              # карты событий на руке
                "available_event_cards": [str],         # доступные карты событий
                "object_tokens": int,                   # жетоны объектов
                "battle_deck": [str],
                "order_deck": [str],
            },
            ...
        },

        "tiles": {
            "t_key": {
                "x": int,
                "y": int,
                "orientation": int (0, 90, 180, 270),
                "side": str (A or B),
                "areas": [area_id],
                "order_stack": [order_id],
            },
            ...
        },

        "areas": {
            "area_id": {
                "tile": "t_key",
                "type": "planet" or "space",
                "owner": "p1" or "p2" or "neutral",
                "units": [unit_id],
                "buildings": [building_id],
            },
            ...
        },

        "units": {
            "unit_id": {
                "type": str (infantry, marines, fighter, destroyer, etc.),
                "area": "area_id",
                "status": "active" or "routed",
            },
            ...
        },

        "buildings": {
            "building_id": {
                "type": str (factory, city, bastion),
                "area": "area_id",
            },
            ...
        },

        "orders": {
            "order_id": {
                "owner": "p1" or "p2",
                "tile": "t_key",
                "type": str,
                "revealed": bool,
            },
            ...
        },

        "warp_storms": [
            {
                "tile": "t_key",
                "side": "top|bottom|left|right",
                "owner": "p1" or "p2",  # кто разместил этот вихрь
                "status": "active" or "used"
            },
            ...
        ],

        "dropped_orders": [
            {
                "id": str,
                "type": str,
                "owner": "p1" or "p2"
            },
            ...
        ],

        "target_markers": [
            {
                "tile": "t_key",
                "area_index": int,
                "owner": "p1" or "p2"
            },
            ...
        ]
    }
    """
    state = {
        "turn": 1,
        "round": game_state.round,
        "phase": game_state.phase.value,
        "current_player": f"p{game_state.current_player_id + 1}",

        "players": {},
        "tiles": {},
        "areas": {},
        "units": {},
        "buildings": {},
        "orders": {},
        "dropped_orders": [],
        "warpStorms": [],
    }

    # ── Игроки ──────────────────────────────────────────────────────────────
    for pi, player in enumerate(game_state.players):
        player_key = f"p{pi + 1}"

        # Подсчитаны ресурсы
        resource_counts = {"reinforcement": 0, "cash": 0, "forge": 0}
        for res in player.resources:
            res_type = res.resource_type.value
            resource_counts[res_type] = resource_counts.get(res_type, 0) + 1

        # ── Информация о картах из фракции ──────────────────────────────────
        faction = player.faction
        hand_battle_cards = [c.to_dict() for c in faction.battle_cards if c.level.value == -1]
        available_battle_cards = [c.to_dict() for c in faction.battle_cards if c.level.value != -1]
        available_order_upgrades = [u.to_dict() for u in faction.order_upgrades]
        available_event_cards = [e.to_dict() for e in faction.event_cards]

        state["players"][player_key] = {
            "name": player.name,
            "faction": player.faction.id,
            "money": player.credits,
            "support": resource_counts.get("support", 0),
            "discount": resource_counts.get("discount", 0),
            "forge": resource_counts.get("forge", 0),
            "hand_battle_cards": hand_battle_cards,
            "available_battle_cards": available_battle_cards,
            "hand_order_upgrades": [],
            "available_order_upgrades": available_order_upgrades,
            "hand_event_cards": [],  # карты событий на руке (инициально пусто)
            "available_event_cards": available_event_cards,
            "boughtUpgrades": player.boughtUpgrades,  # купленные улучшения (пусто в начале)
            "object_tokens": player.object_tokens,  # жетоны объектов
            "battle_deck": [],
            "order_deck": [],
        }

    # ── Плитки и области ────────────────────────────────────────────────────
    area_id_counter = 0
    area_id_map = {}  # area object -> "a_XXX"

    for tile_key, tile in game_state.board.tiles.items():
        col, row = map(int, tile_key.split(","))

        # Плитка
        state["tiles"][tile_key] = {
            "x": col,
            "y": row,
            "orientation": tile.rotation,
            "side": tile.tile_def_id.split("_")[-1].upper() if "_" in tile.tile_def_id else "A",
            "areas": [],
            "order_stack": [],
        }

        # Области этой плитки
        for area in tile.areas:
            area_id = f"a{area_id_counter}"
            area_id_counter += 1
            area_id_map[id(area)] = area_id

            state["tiles"][tile_key]["areas"].append(area_id)

            # Определить владельца области
            owner = "neutral"
            if hasattr(tile, 'owner') and tile.owner is not None:
                owner = f"p{tile.owner + 1}"

            state["areas"][area_id] = {
                "tile": tile_key,
                "type": area.area_type.value,
                "owner": owner,
                "units": [],
                "buildings": [],
            }

    # ── Юниты ──────────────────────────────────────────────────────────────
    for tile_key, tile in game_state.board.tiles.items():
        for area_idx, area in enumerate(tile.areas):
            area_id = None
            for aid, a in area_id_map.items():
                if aid == id(area):
                    area_id = a
                    break

            if not area_id:
                continue

            for unit in area.units:
                unit_id = unit.id

                state["units"][unit_id] = {
                    "type": unit.unit_type.value if unit.unit_type else "unknown",
                    "area": area_id,
                    "status": "active",  # TODO: из game_state.py добавить поле status
                }

                state["areas"][area_id]["units"].append(unit_id)

            # Постройки
            for struct in area.structures:
                struct_id = struct.id

                state["buildings"][struct_id] = {
                    "type": struct.structure_type.value,
                    "area": area_id,
                }

                state["areas"][area_id]["buildings"].append(struct_id)

    # ── Приказы (если они размещены) ────────────────────────────────────────
    # TODO: когда будет фаза расстановки приказов

    return state


def ensure_saves_dir(saves_dir: str = "saves") -> str:
    """Убеждается, что папка для сохранений существует."""
    path = Path(saves_dir)
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def save_game_state(state: dict, filename: str, saves_dir: str = "saves") -> bool:
    """
    Сохраняет состояние игры в JSON файл.

    Args:
        state: словарь состояния (от generate_game_state)
        filename: имя файла (например "game_001.json")
        saves_dir: папка для сохранений (по умолчанию "saves")

    Returns:
        True если успешно, False иначе
    """
    try:
        saves_path = ensure_saves_dir(saves_dir)
        filepath = Path(saves_path) / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"Ошибка при сохранении игры: {e}")
        return False


def load_game_state(filename: str, saves_dir: str = "saves") -> Optional[dict]:
    """
    Загружает состояние игры из JSON файла.

    Args:
        filename: имя файла (например "game_001.json")
        saves_dir: папка для сохранений (по умолчанию "saves")

    Returns:
        словарь состояния или None если ошибка
    """
    try:
        filepath = Path(saves_dir) / filename

        if not filepath.exists():
            print(f"Файл не найден: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)

        return state
    except Exception as e:
        print(f"Ошибка при загрузке игры: {e}")
        return None


def list_saved_games(saves_dir: str = "saves") -> List[str]:
    """
    Возвращает список сохранённых игр в папке.

    Returns:
        список имён файлов (например ["game_001.json", "game_002.json"])
    """
    saves_path = Path(saves_dir)
    if not saves_path.exists():
        return []

    return sorted([f.name for f in saves_path.glob("*.json")])
