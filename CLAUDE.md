# Stellar Conflict — Game Engine
## (Inspired by Forbidden Stars / Fantasy Flight Games)

## Project Goal
A turn-based strategy game engine — a **prototype/skeleton** of a full project.
The goal is a working skeleton that can be expanded into a full project.
Other players should eventually be able to play over the network.

## Original Game
Mechanics are based on **Forbidden Stars** (Fantasy Flight Games, Warhammer 40K setting).
Key mechanics: faction selection, tile-based map building, order system, combat with dice and battle cards.
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
2. 🔧 Browser hot-seat (game_engine.html, standalone) — **current phase** — tile placement only
3. Network play over the internet (FastAPI + WebSockets)
4. Web interface connected to Python backend
5. Mobile application

## Current File Structure
```
project/
├── CLAUDE.md
├── game_engine.html         🔧 Standalone browser frontend — tile placement phase only
├── forbidden_stars_data.py  ✅ Reference database — canonical unit/card/order stats from original game
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

### forbidden_stars_data.py — Reference Database

Canonical game data from the original Forbidden Stars board game. **Use this as the authoritative
source when implementing or expanding factions.** Contains 8 factions:
`Space Marines`, `Chaos Space Marines`, `Orks`, `Eldar`, `Necrons`, `Tyranids`, `Tau`, `Imperial Guard`.

**Top-level structure:**
```python
STRUCTURES  # shared: Factory (cost 2, capacity 1), City (cost 3), Bastion (cost 2, dice 2, health 3, morale 2)
FACTIONS    # dict: faction_name → { dominate_action, units, combat_cards, enhanced_orders, event_cards, warp_storm_moves }
```

**Canonical unit name → project tier mapping** (for reference when implementing faction_defs/):

| Tier | Ground units | Space units |
|------|-------------|-------------|
| t0   | Scout, Cultist, Ork Boyz, Aspect Warriors, Warriors (Necron), Gaunts, Fire Warriors, Guardsmen | Strike Cruiser, Iconoclast, Onslaught Attack Ships, Hellebore Frigates, Scythe Harvest Ships, Devourer Bio-Ships, Custodian Carriers, Lunar-Class Cruisers |
| t1   | Space Marine, Chaos Marine, Nobz, Wraithguard, Immortals, Tyranid Warriors, XV8 Crisis Battlesuits, Ogryns | — |
| t2   | Land Raider, Helbrute, Battlewagons, Falcons, Monoliths, Carnifexes, TX7 Hammerhead, Leman Russ | Battle Barge, Repulsive Cruiser, Kill Kroozers, Void Stalkers, Cairn Tomb Ships, Leviathan Hive Ships, KX139 Supremacy, Emperor Battleships |
| t3   | Warlord Titan, Chaos Reaver Titan, Gargants, Warlock Titans, C'tan Star God Shard, Hierophant Bio-Titan, KX139 Supremacy (alt), Warhound Titan | — |

### Adding a New Faction
1. Create `faction_defs/<faction_id>.py` — define a `Faction` object using classes from `faction_base.py`
2. In `faction_defs/__init__.py`: add one import line and one entry to `_ALL_FACTIONS`
3. Nothing else needs to change — `FACTIONS` and `FACTION_CONFIGS` are built automatically

---

## Current Game Flow (game_engine.html)

Only the tile placement stage is implemented in the browser frontend.

```
┌─────────────────────────────────────────────────────────────┐
│  SETUP                                                       │
│   Players enter names and choose factions                    │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  TILE PLACEMENT  (only implemented phase)                    │
│                                                              │
│   Players alternate:                                         │
│   • Select a system tile from their hand (left panel)        │
│   • Click a valid cell on the map to place it                │
│   • Optionally rotate (↺/↻) or flip (⇄) the tile            │
│   • Undo tile placement with ↩                               │
│                                                              │
│   After all tiles placed:                                    │
│   • Dialog: "Карта сформирована — Завершить игру?"           │
│     - Да → restart (back to setup)                           │
│     - Нет → stay on the map view                             │
└─────────────────────────────────────────────────────────────┘
```

## Game Phases (JS frontend — tile-placement only)

| Phase           | Status | Description                                          |
|-----------------|--------|------------------------------------------------------|
| setup           | ✅     | Player names + faction selection                     |
| tile-placement  | ✅     | Alternating tile placement, shape validation (3×2/2×3) |
| (end dialog)    | ✅     | "Завершить игру?" modal after all tiles placed        |

**All other phases** (troop placement, orders, execution, combat, scoring) are **not implemented**
in the browser frontend. They exist in the Python backend files (game_state.py etc.) as reference.

## game_engine.html — Browser Frontend

Standalone file (~1476 lines), opens directly in browser. Pure HTML + JavaScript, no server needed.

**JS data model:**
- Factions: 12 factions defined; displayed with icon + name
- Tiles: HOME = 3 planets + 1 space; NORMAL = 2 planets + 2 space; 3 tiles per player
- Rotation: RMAP lookup table maps original area index → display position for 0/90/180/270°
- `tileDefToAreas(sideData)` — creates area objects from tile definition (in tiles.js)
- `getAreaByDisplay(tile, displayIdx)` — maps visual click position to actual area using RMAP

**Implemented:**
- Setup screen: player names + faction selection (mutual exclusion)
- Hot-pass overlay between players (blocks screen, shows whose turn it is)
- Tile placement: valid drop cells highlighted, shape validation (3×2 or 2×3 bounding box)
- Tile rotation (CW/CCW) and flip (side A/B)
- Undo tile placement
- Tile hover preview (1-second hover → full-size preview popup)
- End-of-placement dialog: "Завершить игру?" with restart option
- Activity log

**Functions:**
- `startGame()` — reads setup form, initializes G state, calls setPhase('tile-placement')
- `setPhase(phase)` — handles only 'tile-placement'; updates instruction and buttons
- `dropTile(col, row)` — places selected tile, calls `_afterTilePlaced()`
- `_afterTilePlaced()` — if all tiles placed → `showEndMapDialog()`; else → next player
- `undoTile()` — removes last placed tile, returns to tile-placement
- `rotateTile(cw)` — rotates tile CW or CCW
- `flipTile()` — flips tile to side B/A
- `showEndMapDialog()` — shows "Завершить игру?" modal
- `renderBoard()` — renders the map grid with placed tiles and valid drop cells
- `renderSide()` — renders the hand tiles in the left panel
- `updateHeader()` — updates player turn indicator

**NOT implemented in JS frontend (next steps):**
- [ ] Troop and structure placement on tiles
- [ ] Warp storm placement
- [ ] Order placement (4 orders per player)
- [ ] Order execution (advance, deploy, dominate, strategize)
- [ ] Combat (dice + battle cards)
- [ ] Faction special abilities
- [ ] Scoring and win condition
- [ ] Save/load
- [ ] Network connection to Python backend

---

## Core Classes (Python backend — reference)

### tiles.py
- `AreaType` — PLANET (ground units + structures) / SPACE (space units only)
- `TileType` — HOME (3 planets + 1 space) / NORMAL (2 planets + 2 space)
- `Area` — one zone inside a tile; `accepts(unit)` validation; max 1 structure per planet area
- `SystemTile` — 4 areas in 2×2 grid, rotation 0/90/180/270°, `rotated_areas()` for display

### board.py
- `Board` — dict of tiles by key "col,row"
- `is_valid_position(col, row)` — adjacency + shape constraint (3×2 or 2×3)
- `valid_positions()` — all valid positions for next tile

### faction_base.py
- `UnitConfig` — unit counts, structure counts, starting resources
- `Faction` — id, name, icon, flavor, special_ability_name/desc, unit_config, battle_cards, order_upgrades
- `Player` — id, name, color, faction, pool, structures, resources, credits, hand, orders

---

## Code Conventions
- All methods return `(bool, str)` or `(bool, str, optional_data)` tuples — never raise exceptions for game logic errors
- Game logic is completely separated from I/O (no print() in game_state.py)
- Use `dataclass` for data containers, regular class for logic controllers
- Type hints on all function signatures
- Docstrings on all classes and non-trivial methods

## Important Design Decisions
- Tile rotation is visual only — `rotated_areas()` remaps display positions, underlying `areas[]` list stays unchanged
- `area_display_index` refers to visual position after rotation (what the player sees)
- Board shape constraint: bounding box must fit in 3×2 OR 2×3 (either orientation)
- `tileDefToAreas()` always includes `structures: []` on each area (critical — missing this caused recurring bugs)
- RMAP[rot/90][originalIdx] = displayPosition — used for all area index mapping
