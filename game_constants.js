'use strict';
// ══════════════════════════════════════════════
//  CONSTANTS
// ══════════════════════════════════════════════
const FACTIONS = [
  { id:'chaos', name:'Хаос', icon:'⬡', color:'#FF0000', homeTileId:'home_chaos', flavor:'Особое свойство доминации:вы можете переместить культиста на свободный или дружественный мир соседней системы', troops:{ground:4,space:1}, unitTiers:{ground:[0, 0, 1, 1],space:[0]}, structures:['factory'] },
  { id:'marine', name:'Space marine', icon:'◆', color:'#1F4E9E', homeTileId:'home_marine', flavor:'Особое свойство доминации:вы можете заменить Т0 на Т1 или Т1 на Т2 за 1 материал', troops:{ground:5,space:1}, unitTiers:{ground:[0, 0, 0, 0, 1],space:[0]}, structures:['factory'] },
  { id:'orks', name:'Orks', icon:'💀', color:'#2E7D32', homeTileId:'home_orks', flavor:'Dominate: Purchase 1 unit and place it on a world in the active system', troops:{ground:5,space:0}, unitTiers:{ground:[0, 0, 0, 0, 1],space:[]}, structures:['factory'] },
  { id:'eldar', name:'Eldar', icon:'◉', color:'#F2C94C', homeTileId:'home_eldar', flavor:'По доминации вы можете переместить одного юнита из мира активной системы в дружественный мир.', troops:{ground:4,space:2}, unitTiers:{ground:[0, 0, 0, 1],space:[0, 0]}, structures:['factory'] },
  { id:'necrons', name:'Necrons', icon:'☥', color:'#00BCD4', homeTileId:'home_necrons', flavor:'Dominate: Take any of your units from 1 world and place them on a friendly world containing a structure in the active system.', troops:{ground:5,space:0}, unitTiers:{ground:[0, 0, 0, 0, 1],space:[]}, structures:['factory'] },
  { id:'tyranids', name:'Tyranids', icon:'🧬', color:'#6A1B9A', homeTileId:'home_tyranids', flavor:'Dominate: Gain 1 additional asset token of your choice. You can have up to 4 of each asset token in your play area at any time.', troops:{ground:3,space:2}, unitTiers:{ground:[0, 0, 0],space:[0, 2]}, structures:['factory', 'bastion'] },
  { id:'tau', name:'Tau', icon:'⊕', color:'#00897B', homeTileId:'home_tau', flavor:'Dominate: When you resolve a dominate order in a system containing at least 1 of your units or structures, you may draw 4 cards from the top of your event deck. Resolve the ability of 1 of those cards and discard the others.', troops:{ground:5,space:0}, unitTiers:{ground:[0, 0, 0, 1, 1],space:[]}, structures:['factory'] },
  { id:'imperial_guard', name:'Imperial Guard', icon:'⚜', color:'#795548', homeTileId:'home_imperial_guard', flavor:'Dominate: When you resolve a dominate order, you may resolve a deploy order, only to purchase 2 or more identical units and placing them on either 1 friendly world containing a structure or 1 friendly or uncontrolled void. Reduce the materiel cost of each unit by 1.', troops:{ground:5,space:1}, unitTiers:{ground:[0, 0, 0, 1, 1],space:[0]}, structures:['factory'] },
];

const STRUCTURE_INFO = {
  factory: { icon:'⚙', label:'Фабрика' },
  city:    { icon:'⬡', label:'Город'   },
  bastion: { icon:'⛉', label:'Бастион' },
};

const TILES_PP = 3;
const CELL     = 320;

// TILE_CATALOG и функция tileDefToAreas загружены из tiles.js

// Tile rotation: RMAP[rot/90][originalIdx] = displayPosition
// Layout:  0|1
//          2|3
const RMAP = [
  [0,1,2,3],  // 0°
  [1,3,0,2],  // 90° CW  (TL→TR, TR→BR, BL→TL, BR→BL)
  [3,2,1,0],  // 180°
  [2,0,3,1],  // 270° CW (TL→BL, TR→TL, BL→BR, BR→TR)
];

// Адрес сервера API
const API_URL = 'http://localhost:8000';

const ORDER_TYPES = {
  dominate:   { icon: '🎯', name: 'Dominate'   },
  deploy:     { icon: '🚀', name: 'Deploy'      },
  advance:    { icon: '⚔️', name: 'Advance'     },
  strategize: { icon: '🧠', name: 'Strategize'  },
};

// ══════════════════════════════════════════════
//  GLOBAL STATE
// ══════════════════════════════════════════════
let nextId   = 0;
let G;
let isSaving = false;  // флаг для предотвращения одновременных сохранений

function makeState() {
  return {
    version: 1,        // для миграции старых сохранений
    players: [
      { name:'Alpha', faction:null, color:'c1', pool:[], hand:[], structurePool:[], hand_orders:[] },
      { name:'Omega', faction:null, color:'c2', pool:[], hand:[], structurePool:[], hand_orders:[] },
    ],
    phase: 'setup',
    curP: 0,           // текущий игрок в этом раунде (кто сейчас ходит)
    round: 1, totalRounds: 8,
    firstPlayer: 0,    // кто ходит первым в этом раунде (не меняется в раунде)
    map: {},           // "col,row" → tile obj
    tilesPlaced: 0,
    lastKey: null,
    // ── undo state ──────────────────────────
    tileSnap: null,        // { handIdx, key } — set by dropTile, cleared by undoTile or endTurn
    unitsPlaced: [],       // [{ key, realAreaIdx, unitId }]
    structsPlaced: [],     // [{ key, realAreaIdx, structId }]
    // ── turn snapshot (for undo to start of turn) ───
    _turnSnap: null,       // deep snapshot at start of each player's turn
    // ── selection ──────────────────────────
    selHandIdx: null,
    selUnitIdx: null,
    selUnitType: null,
    selStructIdx: null,    // index in cp.structurePool
    // ── warp storms ──────────────────────────
    warpStorms: [],    // [{ tileKey: 'col,row', side: 'top'|'bottom'|'left'|'right', owner: 0|1 }]
    warpStormStep: 0,  // 0 = second player places, 1 = first player places
    warpConfirmed: [false, false],  // подтверждение варп-штормов каждым игроком
    // ── target markers ──────────────────────
    targetMarkers: [], // [{ tile: 'col,row', areaIdx: int, owner: 0|1 }]
    // ── orders (управляются Python Stage 2) ──
    orders: [],        // [{ id, type, owner, tile, position, revealed }]
    ordersPlaced: [0, 0],
    order_placed_this_turn: [false, false],
    dropped_orders: [],
    execution_order_played: [false, false],
  };
}
