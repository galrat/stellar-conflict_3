# Stellar Conflict — Game Engine
## (Inspired by Forbidden Stars / Fantasy Flight Games)

## Project Goal
A turn-based strategy game engine — a **prototype/skeleton** of a full project.
All game phases and mechanics are implemented, but the number of variants and level of detail are
intentionally reduced. The goal is a working skeleton that can be expanded into a full project.
Other players should eventually be able to play over the network.

## Original Game
Mechanics are based on **Forbidden Stars** (Fantasy Flight Games, Warhammer 40K setting).
Key mechanics: faction selection, tile-based map building with simultaneous troop placement,
order system with simultaneous placement and resolution, combat with dice and battle cards.
When in doubt about game logic or rules — refer to Forbidden Stars rules.

## Architecture

### Technology Stack
- **Language:** Python (latest stable, managed via PyCharm)
- **Paradigm:** OOP with dataclasses
- **Style:** type hints + docstrings on all classes and methods
- **Backend/Network (future):** FastAPI + WebSockets
- **Database (future):** SQLite
- **Testing:** Manual only (demo.py serves as integration test)

### Interface Roadmap
1. ✅ Console + hot-seat (Python, demo.py) — done
2. ✅ Browser hot-seat (game_engine.html, standalone) — **current phase**
3. Network play over the internet (FastAPI + WebSockets)
4. Web interface connected to Python backend
5. Mobile application

## Current File Structure
```
project/
├── CLAUDE.md
├── game_engine.html    ✅ Standalone browser frontend — full hot-seat game, no server needed
│
├── units.py            ✅ Unit, UnitCategory, GroundType, SpaceType, UNIT_STATS, make_unit()
├── tiles.py            ✅ Area, AreaType, SystemTile, TileType, AREA_LAYOUTS, rotation logic
├── board.py            ✅ Board — placement, adjacency, shape validation (3×2 or 2×3)
├── combat.py           ✅ BattleResult, resolve_battle(), apply_battle(), format_battle()
├── game_state.py       ✅ GameState, GameConfig, Phase, Order, LogEntry
├── demo.py             ✅ Console integration test — 3 scenarios
│
├── faction_base.py     ✅ Base faction dataclasses — CardLevel, BattleCard, OrderUpgrade,
│                          UnitConfig, Faction, Player
├── factions.py         ✅ Thin re-export layer — all «from factions import …» still work
└── faction_defs/       ✅ One file per faction (target: 12 total)
    ├── __init__.py        FACTIONS dict + FACTION_CONFIGS — add faction here (2 lines)
    ├── federation.py      Федерация — balanced, diplomatic
    ├── empire.py          Империя — heavy mechanized
    ├── syndicate.py       Синдикат — fast marines, hit-and-run
    └── collective.py      Коллектив — infantry swarm, hive mind
```

### Adding a New Faction
1. Create `faction_defs/<faction_id>.py` — define a `Faction` object using classes from `faction_base.py`
2. In `faction_defs/__init__.py`: add one import line and one entry to `_ALL_FACTIONS`
3. Nothing else needs to change — `FACTIONS` and `FACTION_CONFIGS` are built automatically

## Game Phases (all implemented in Phase enum)

| Phase            | Status | Description                                         |
|------------------|--------|-----------------------------------------------------|
| SETUP            | ✅     | Players and hands initialized in GameState.__init__ |
| TILE_PLACEMENT   | ✅     | Alternating tile placement, shape validation        |
| TROOP_ON_TILE    | ✅     | Place troops on just-placed tile                    |
| TROOP_PLACEMENT  | ✅     | Place remaining troops anywhere                     |
| ORDER_PLACEMENT  | ✅     | Each player places 2 orders (simultaneous)          |
| EXECUTION        | ✅     | Orders resolved: move troops → check battles        |
| ENDED            | ✅     | Score by unit count, winner announced               |

## Core Classes

### units.py
- `UnitCategory` — GROUND / SPACE
- `GroundType` — INFANTRY, MARINES, MECHANIZED, ELITE
- `SpaceType` — FIGHTER, DESTROYER
- `Unit` — dataclass: player_id, category, unit_type: `Optional[Union[GroundType, SpaceType]]`
- `UNIT_STATS` — dict with attack_bonus, symbol, label per unit type
- `make_unit(player_id, category, unit_type)` — factory function

### tiles.py
- `AreaType` — PLANET (ground units only) / SPACE (space units only)
- `TileType` — HOME (3 planets + 1 space) / NORMAL (2 planets + 2 space)
- `Area` — one zone inside a tile, holds list of units, `accepts(unit)` validation
- `SystemTile` — 4 areas in 2×2 grid, rotation 0/90/180/270°, `rotated_areas()` for display

### board.py
- `Board` — dict of tiles by key "col,row"
- `place(tile)` / `remove(col, row)` — placement with validation
- `is_valid_position(col, row)` — checks adjacency + shape constraint (3×2 or 2×3)
- `valid_positions()` — all valid positions for next tile
- `neighbors(col, row)` — adjacent tiles

### faction_base.py
- `CardLevel` — INITIAL / ZERO / TWO / THREE (4 battle card tiers)
- `BattleCard` — name, level, effect_1, effect_2
- `OrderUpgrade` — name, order_type, effect_1, effect_2
- `UnitConfig` — unit counts per type, `build_units(player_id)` factory
- `Faction` — id, name, icon, flavor, special_ability_name/desc, unit_config,
  battle_cards, order_upgrades, extra (arbitrary dict for future mechanics)
  - `cards_by_level(level)` — filter cards by tier
  - `upgrade_for(order_type)` — get upgrade for a specific order type
- `Player` — id, name, color, faction (Faction object), pool, hand, orders
  - `faction_id` — property, returns `faction.id`

### factions.py
Re-exports everything from `faction_base` and `faction_defs`.
Keeps all existing imports (`from factions import ...`) working without changes.

### faction_defs/
- `__init__.py` — builds `FACTIONS: Dict[str, Faction]` and `FACTION_CONFIGS: Dict[str, UnitConfig]`
- Each faction file exports one `Faction` instance with full data:
  special ability, unit config, 6–7 battle cards across all 4 levels, 2 order upgrades, extra dict

### game_engine.html — Browser Frontend
Standalone file, opens directly in browser. Pure HTML + JavaScript, no server or build step needed.
Two implementations exist in parallel: Python backend (authoritative data model) and this JS frontend (simplified, playable prototype).

**JS data model (simplified vs Python):**
- Units: only two types — `ground` (▲/▼) and `space` (◈/◆), no subtypes (infantry/mechanized etc.)
- Factions: 4 factions, all with identical troops 3 ground + 3 space, no special abilities or battle cards wired in
- Tiles: HOME = 3 planets + 1 space; NORMAL = 2 planets + 2 space; 3 tiles per player
- Rounds: 2 by default
- Rotation: RMAP lookup table maps original area index → display position for 0/90/180/270°

**Implemented in JS frontend:**
- Setup screen: player names + faction selection (mutual exclusion)
- Hot-pass overlay between players (blocks screen, shows whose turn it is)
- All game phases: tile placement → troops on tile → troop placement → order placement → execution → end screen
- Tile placement: valid drop cells highlighted, shape validation (3×2 or 2×3 bounding box)
- Tile rotation (CW/CCW) during troop-on-tile phase
- Undo: undo last unit, undo entire tile
- Order placement: 2 orders per player, click slot then click target area; orders shown as pips on board
- Execution: move all friendly units from adjacent tiles into target area (compatible type only)
- Battle: d6 + unit count, loser loses all units; battle modal with dice display
- Scoring: total units on board, winner announced on end screen

**NOT in JS frontend (future):**
- [ ] Unit subtypes with different attack bonuses
- [ ] Battle cards played during combat
- [ ] Multiple order types (only "move" exists)
- [ ] Faction special abilities
- [ ] Only one battle per execution step (first contested area found); others skipped
- [ ] Save/load
- [ ] Network connection to Python backend

### combat.py
- `BattleResult` — participants, dice rolls, scores, winner (actual player_id), loser_units
- `resolve_battle(tile_key, area_index, area_type, p1_units, p2_units)` — roll d6 + unit count
  + max attack_bonus; loser loses ALL units; winner/loser stored as actual player_id from units
- `apply_battle(area, battle)` — removes loser's units from area
- `format_battle(battle, p1_name, p2_name)` — text log string

### game_state.py
- `GameConfig` — player names/factions, total_rounds, tiles_per_player, optional unit overrides
- `Order` — player_id, order_slot (0/1), tile_key, area_index, order_type
- `LogEntry` — message + player_id (-1 = system)
- `GameState` — master game controller
  - `place_tile()`, `rotate_tile()`, `undo_tile()` — tile placement phase
  - `place_unit()`, `undo_last_unit()`, `end_troop_on_tile()` — troop placement
  - `place_order()`, `cancel_order()`, `confirm_orders()` — order phase
  - `execute_next_order()` → returns `(bool, str, List[BattleResult])`
  - `to_dict()` / `to_json()` — full state serialization

## What's NOT Yet Implemented (next steps)

### Python backend
- [ ] Battle cards actually played during combat (data structure exists, game logic not wired in)
- [ ] 4 order types — currently only "move" exists; need: attack, reinforce, dominate, build
- [ ] 12 factions — currently 4 implemented (federation, empire, syndicate, collective)
- [ ] Faction special abilities wired into game logic (data exists, effect not applied)
- [ ] Order upgrades wired into game logic (data exists, effect not applied)
- [ ] Save/load game to SQLite
- [ ] Network layer (FastAPI + WebSockets)
- [ ] Faction selection phase (currently hardcoded in GameConfig)

### JS frontend (game_engine.html)
- [ ] Unit subtypes with different attack bonuses (currently all units are equal)
- [ ] Battle cards during combat
- [ ] Multiple order types (only "move" / troop relocation implemented)
- [ ] Faction special abilities
- [ ] Multiple battles per execution step (currently only first contested area resolved)
- [ ] Connect to Python backend via API

## Code Conventions
- All methods return `(bool, str)` or `(bool, str, optional_data)` tuples — never raise exceptions for game logic errors
- Game logic is completely separated from I/O (no print() in game_state.py)
- Use `dataclass` for data containers, regular class for logic controllers
- `to_dict()` on every class for JSON serialization
- Type hints on all function signatures
- Docstrings on all classes and non-trivial methods
- All enums use `enum.Enum`: `Phase`, `CardLevel`, `AreaType`, `TileType`, `UnitCategory`, `GroundType`, `SpaceType`

## Important Design Decisions
- Tile rotation is visual only — `rotated_areas()` remaps display positions, underlying `areas[]` list stays unchanged
- `area_display_index` in place_unit/place_order refers to visual position after rotation (what the player sees)
- At equal combat score — defender (p1, who placed first) wins
- Board shape constraint: bounding box must fit in 3×2 OR 2×3 (either orientation)
- `player.pool` = units NOT on the board (reserve); units on board live inside `Area.units`
- `Player` stores the full `Faction` object (not just faction_id); `player.faction_id` is a derived property
- `execute_next_order()` returns `List[BattleResult]` — all battles in all zones of the target tile
- `combat.py` is stateless — winner/loser are derived from actual unit.player_id values, not hardcoded indices
- `faction_base.py` has no dependency on `game_state.py` — faction data can be edited independently
