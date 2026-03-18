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
├── units.py            ✅ Unit, UnitCategory, GroundType, SpaceType, Structure, StructureType,
│                          ResourceToken, UNIT_STATS, STRUCTURE_STATS, make_unit(), make_structure()
├── player_hand.py      ✅ Cost, UnitSpec, StructureSpec, PlayerStartKit, UNIT_TYPE_CATALOG,
│                          STRUCTURE_CATALOG, build_start_kit() — full unit/building params + starting kit
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
    ├── chaos.py           Хаос
    ├── marine.py          Space Marine
    ├── orks.py            Орки
    ├── eldar.py           Элдары
    └── ...                (8 skeleton factions)
```

### Adding a New Faction
1. Create `faction_defs/<faction_id>.py` — define a `Faction` object using classes from `faction_base.py`
2. In `faction_defs/__init__.py`: add one import line and one entry to `_ALL_FACTIONS`
3. Nothing else needs to change — `FACTIONS` and `FACTION_CONFIGS` are built automatically

---

## Game Structure

The game has **3 stages**. Stage 1 is played once; stages 2 and 3 repeat as rounds.

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1 — PREPARATION  (played once at the start)          │
│  Map building + placement of units and structures            │
│                                                              │
│   Players alternate:                                         │
│   • Place a system tile on the board                         │
│   • Place troops and structures on that tile                 │
│   After all tiles are placed:                                │
│   • Place remaining troops and structures anywhere           │
└─────────────────────────────────────────────────────────────┘
              ↓  repeated N times (default: 2)
┌─────────────────────────────────────────────────────────────┐
│  ROUND  (stages 2 + 3 together = 1 round)                   │
│                                                              │
│  STAGE 2 — ORDER PLACEMENT                                   │
│   Each player secretly places 2 orders on the board         │
│                                                              │
│  STAGE 3 — ORDER RESOLUTION                                  │
│   Orders are revealed and resolved one by one                │
│   Each order moves troops → battles are checked              │
└─────────────────────────────────────────────────────────────┘
              ↓  after N rounds
┌─────────────────────────────────────────────────────────────┐
│  END — score by units on board, winner announced             │
└─────────────────────────────────────────────────────────────┘
```

## Game Phases (Phase enum in game_state.py)

| Phase            | Stage      | Status | Description                                              |
|------------------|------------|--------|----------------------------------------------------------|
| SETUP            | —          | ✅     | Players, hands, pools initialized in GameState.__init__ |
| TILE_PLACEMENT   | Stage 1    | ✅     | Alternating tile placement, shape validation (3×2/2×3)  |
| TROOP_ON_TILE    | Stage 1    | ✅     | Place troops + structures on just-placed tile            |
| TROOP_PLACEMENT  | Stage 1    | ✅     | Place remaining troops + structures anywhere             |
| ORDER_PLACEMENT  | Stage 2    | ✅     | Each player places 2 orders (hot-seat, sequential)       |
| EXECUTION        | Stage 3    | ✅     | Orders resolved: move troops → check battles             |
| ENDED            | —          | ✅     | Score by unit count, winner announced                    |

After EXECUTION completes: if rounds remain → back to ORDER_PLACEMENT; otherwise → ENDED.

## Core Classes

### units.py
- `UnitCategory` — GROUND / SPACE
- `GroundType` — INFANTRY, MARINES, MECHANIZED, ELITE
- `SpaceType` — FIGHTER, DESTROYER
- `StructureType` — FACTORY, CITY, BASTION
- `ResourceType` — SUPPORT, DISCOUNT, FORGE
- `Unit` — dataclass: player_id, category, unit_type: `Optional[Union[GroundType, SpaceType]]`
- `Structure` — dataclass: player_id, structure_type
- `ResourceToken` — dataclass: resource_type
- `UNIT_STATS` — dict with attack_bonus, symbol, label per unit type (combat stats only)
- `STRUCTURE_STATS`, `RESOURCE_STATS` — display symbols and labels
- `make_unit()`, `make_structure()` — factory functions

### player_hand.py
Full unit and building specifications + starting-kit factory. **Separate from combat logic.**

**Unit identifier format (formation phase):** `{faction_id}_{category}_t{tier}`
- Example: `chaos_ground_t0`, `marine_space_t2`, `eldar_ground_t1`
- `category`: `ground` or `space`
- Ground tiers: t0 (infantry), t1 (marines), t2 (mechanized), t3 (elite)
- Space tiers: **t0 (fighter) and t2 (destroyer) only — no t1**
- Stats are per unit TYPE, not per tier: marines (t1) and mechanized (t2) have different stats

**Classes:**
- `Cost` — credits (₡) + optional forge_tokens (⚒ hammer tokens)
- `UnitSpec` — full unit-type params: unit_id, display_name, category, tier, cost,
  combat_strength, health, morale, start_count (deployed at setup), total_count (total in reserve)
- `StructureSpec` — structure-type params: structure_id, display_name, cost, defense_bonus,
  start_count, description + optional combat stats (combat_strength, health, morale).
  **Bastion**: combat_strength=2, health=3, morale=2 (fixed, participates in combat).
  **Factory / City**: no combat stats (None).
- `PlayerStartKit` — everything a player holds at game start: unit_specs, structure_specs,
  credits, support_tokens, discount_tokens, forge_tokens
- `UNIT_TYPE_CATALOG` — dict keyed by unit type name (`"infantry"`, `"marines"`, `"mechanized"`,
  `"elite"`, `"fighter"`, `"destroyer"`) → base stats. Allows different stats per type within same tier.
- `STRUCTURE_CATALOG` — dict keyed `"bastion"|"factory"|"city"` → StructureSpec with shared stats
- `build_start_kit(faction_id, unit_config)` — builds PlayerStartKit from a UnitConfig

### tiles.py
- `AreaType` — PLANET (ground units + structures) / SPACE (space units only)
- `TileType` — HOME (3 planets + 1 space) / NORMAL (2 planets + 2 space)
- `Area` — one zone inside a tile; holds `units: List[Unit]` and `structures: List[Structure]`;
  `accepts(unit)` validation; max 1 structure per planet area
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
- `UnitConfig` — unit counts, structure counts, starting resources (credits + 3 token types),
  and `unit_stats` dict (per-faction stat overrides keyed by unit type name).
  Methods: `build_units(player_id)`, `build_structures(player_id)`, `build_resources()`
- `Faction` — id, name, icon, flavor, special_ability_name/desc, unit_config,
  battle_cards, order_upgrades, extra (arbitrary dict for future mechanics)
  - `cards_by_level(level)` — filter cards by tier
  - `upgrade_for(order_type)` — get upgrade for a specific order type
- `Player` — id, name, color, faction (Faction object), pool, structures, resources, credits,
  hand, orders
  - `faction_id` — property, returns `faction.id`

### faction_defs/
- `__init__.py` — builds `FACTIONS: Dict[str, Faction]` and `FACTION_CONFIGS: Dict[str, UnitConfig]`
- Each faction file is the **single source of truth** for that faction. Contains:
  - Starting troop counts per type (infantry, marines, mechanized, elite, fighters, destroyers)
  - Starting structure counts (factories, cities, bastions)
  - Starting resources: credits=6, support_tokens, discount_tokens, forge_tokens
  - `unit_stats` — per-type stats: cost (2–5₡ + optional forge), combat_strength (0–6),
    health (1–6), morale (0–6). Structure stats are shared → defined once in `STRUCTURE_CATALOG`.
  - 6–7 battle cards across all 4 levels, 2 order upgrades, special ability, extra dict

**To change anything about a faction — edit only its `faction_defs/<id>.py` file.**

### factions.py
Re-exports everything from `faction_base` and `faction_defs`.
Keeps all existing imports (`from factions import ...`) working without changes.

### game_state.py
- `GameConfig` — player names/factions, total_rounds, tiles_per_player, optional unit overrides
- `Order` — player_id, order_slot (0/1), tile_key, area_index, order_type
- `LogEntry` — message + player_id (-1 = system)
- `GameState` — master game controller
  - Stage 1: `place_tile()`, `rotate_tile()`, `undo_tile()` — tile placement
  - Stage 1: `place_unit()`, `undo_last_unit()`, `end_troop_on_tile()` — troop placement
  - Stage 1: `place_structure()`, `undo_last_structure()` — structure placement (planets only, 1 per zone)
  - Stage 2: `place_order()`, `cancel_order()`, `confirm_orders()` — order placement
  - Stage 3: `execute_next_order()` → returns `(bool, str, List[BattleResult])`
  - `to_dict()` / `to_json()` — full state serialization

### game_engine.html — Browser Frontend
Standalone file, opens directly in browser. Pure HTML + JavaScript, no server or build step needed.
Two implementations exist in parallel: Python backend (authoritative data model) and this JS frontend (simplified, playable prototype).

**JS data model (simplified vs Python):**
- Units: ground/space with tier (0–2); names from UNIT_NAMES keyed `{faction}_{type}_{tier}`
- Factions: 12 factions defined; 4 main factions have `unitTiers`, `structures`, `credits`, `tokens`
- Unit tokens: `.ttok` pool 39×39 px; `.atroop` board 33×33 px
- Structure tokens: `.ttok.stok` pool; `.astruc` board (icon only, 22×22 px)
- Tiles: HOME = 3 planets + 1 space; NORMAL = 2 planets + 2 space; 3 tiles per player
- Rounds: 2 by default
- Rotation: RMAP lookup table maps original area index → display position for 0/90/180/270°

**Implemented in JS frontend:**
- Setup screen: player names + faction selection (mutual exclusion)
- Hot-pass overlay between players (blocks screen, shows whose turn it is)
- All game stages: tile placement → troops+structures on tile → troop+structure placement → order placement → execution → end screen
- Tile placement: valid drop cells highlighted, shape validation (3×2 or 2×3 bounding box)
- Tile rotation (CW/CCW) and flip (side A/B) during troop-on-tile phase
- Structure placement: pool shown in side panel, click structure → click planet area; 1 per planet; shown as icon on area
- Undo: undo last unit or structure (shared button), undo entire tile
- Starting credits and tokens displayed in header for each player (💰 ⊕ ⊖ ⚒)
- Order placement: 2 orders per player, click slot then click target area; orders shown as pips on board
- Execution: move all friendly units from adjacent tiles into target area (compatible type only)
- Battle: d6 + unit count, loser loses all units; battle modal with dice display
- Scoring: total units on board, winner announced on end screen

**NOT in JS frontend (future):**
- [ ] Unit subtypes with different attack bonuses (currently all units equal within same tier)
- [ ] Battle cards played during combat
- [ ] Multiple order types (only "move" / troop relocation implemented)
- [ ] Faction special abilities
- [ ] Multiple battles per execution step (currently only first contested area resolved)
- [ ] Save/load
- [ ] Network connection to Python backend

### combat.py
- `BattleResult` — participants, dice rolls, scores, winner (actual player_id), loser_units
- `resolve_battle(tile_key, area_index, area_type, p1_units, p2_units)` — roll d6 + unit count
  + max attack_bonus; loser loses ALL units; winner/loser stored as actual player_id from units
- `apply_battle(area, battle)` — removes loser's units from area
- `format_battle(battle, p1_name, p2_name)` — text log string

---

## What's NOT Yet Implemented (next steps)

### Python backend
- [ ] Battle cards actually played during combat (data structure exists, game logic not wired in)
- [ ] 4 order types — currently only "move" exists; need: attack, reinforce, dominate, build
- [ ] 12 factions — 4 fully implemented (chaos, marine, orks, eldar); 8 are skeletons
- [ ] Faction special abilities wired into game logic (data exists, effect not applied)
- [ ] Order upgrades wired into game logic (data exists, effect not applied)
- [ ] `build_start_kit()` (player_hand.py) not yet called in GameState — `build_units/structures/resources()` are called directly instead
- [ ] UnitSpec health/morale not yet used in combat resolution (only combat_strength matters currently)
- [ ] Save/load game to SQLite
- [ ] Network layer (FastAPI + WebSockets)
- [ ] Faction selection phase (currently hardcoded in GameConfig)

### JS frontend (game_engine.html)
- [ ] Unit subtypes with different attack bonuses (currently all units are equal within tier)
- [ ] Battle cards during combat
- [ ] Multiple order types (only "move" / troop relocation implemented)
- [ ] Faction special abilities
- [ ] Multiple battles per execution step (currently only first contested area resolved)
- [ ] Connect to Python backend via API

---

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
- `area_display_index` in place_unit/place_order/place_structure refers to visual position after rotation (what the player sees)
- At equal combat score — defender (p1, who placed first) wins
- Board shape constraint: bounding box must fit in 3×2 OR 2×3 (either orientation)
- `player.pool` = units NOT on the board (reserve); units on board live inside `Area.units`
- `player.structures` = structures NOT yet placed; placed structures live inside `Area.structures`
- Structure stats (cost, defense_bonus, combat stats for Bastion) are **shared across all factions** — defined once in `STRUCTURE_CATALOG` (player_hand.py). Faction files only specify how many of each type they start with.
- Unit stats (cost, combat_strength, health, morale) are **per-faction** — defined in `unit_stats` dict inside each faction's `UnitConfig`. Falls back to `UNIT_TYPE_CATALOG` globals if not overridden.
- `Player` stores the full `Faction` object (not just faction_id); `player.faction_id` is a derived property
- `execute_next_order()` returns `List[BattleResult]` — all battles in all zones of the target tile
- `combat.py` is stateless — winner/loser are derived from actual unit.player_id values, not hardcoded indices
- `faction_base.py` has no dependency on `game_state.py` — faction data can be edited independently
