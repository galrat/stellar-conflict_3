'use strict';
// ══════════════════════════════════════════════
//  CONSTANTS  (declared at module scope — never inside functions)
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


// Название юнита берётся из fac.unitNames['{ground|space}_{tier}'].
// Fallback: 'T{tier}' если фракция не определена или названия нет.
function getUnitName(factionId, unitType, tier) {
  const fac = FACTIONS.find(f => f.id === factionId);
  return (fac && fac.unitNames && fac.unitNames[`${unitType}_${tier}`]) || `T${tier}`;
}

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
// 0°  → display order = original order
// 90° CW  → top-left gets original bottom-left, etc.
const RMAP = [
  [0,1,2,3],  // 0°
  [1,3,0,2],  // 90° CW  (TL→TR, TR→BR, BL→TL, BR→BL)
  [3,2,1,0],  // 180°
  [2,0,3,1],  // 270° CW (TL→BL, TR→TL, BL→BR, BR→TR)
];

// ══════════════════════════════════════════════
//  ROTATION HELPERS  (global functions, not inside setPhase)
// ══════════════════════════════════════════════
function getRotatedAreas(tile) {
  const rot = (tile.rotation || 0);
  const rmap = RMAP[rot / 90];
  const out = new Array(4);
  for (let i = 0; i < 4; i++) out[rmap[i]] = tile.areas[i];
  return out;
}

function getAreaByDisplay(tile, displayIdx) {
  return getRotatedAreas(tile)[displayIdx];
}

function getRealIdx(tile, displayIdx) {
  const area = getAreaByDisplay(tile, displayIdx);
  return tile.areas.indexOf(area);
}

// ══════════════════════════════════════════════
//  STATE
// ══════════════════════════════════════════════
let nextId = 0;
let G;
let isSaving = false;  // флаг для предотвращения одновременных сохранений

// Адрес сервера API
const API_URL = 'http://localhost:8000';

const ORDER_TYPES = {
  dominate: { icon: '🎯', name: 'Dominate' },
  deploy: { icon: '🚀', name: 'Deploy' },
  advance: { icon: '⚔️', name: 'Advance' },
  strategize: { icon: '🧠', name: 'Strategize' },
};

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

// ══════════════════════════════════════════════
//  COLOR HELPERS
// ══════════════════════════════════════════════
// Возвращает '#ffffff' или '#000000' в зависимости от яркости фона
function getTextColor(hex) {
  const r = parseInt(hex.slice(1,3),16)/255;
  const g = parseInt(hex.slice(3,5),16)/255;
  const b = parseInt(hex.slice(5,7),16)/255;
  const lum = 0.2126*r + 0.7152*g + 0.0722*b;
  return lum > 0.35 ? '#000000' : '#ffffff';
}
// hex + alpha → rgba(...)
function hexAlpha(hex, a) {
  const r=parseInt(hex.slice(1,3),16), g=parseInt(hex.slice(3,5),16), b=parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${a})`;
}

// ══════════════════════════════════════════════
//  SAVE / LOAD
// ══════════════════════════════════════════════
const SAVE_KEY = 'stellar_conflict_map';

function saveGame() {
  if (isSaving) return;

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const defaultName = `game_${timestamp}`;

  const html = `
    <div style="margin-bottom:8px;color:#aaa;">Название файла:</div>
    <input id="save-filename-input" type="text" value="${defaultName}"
      style="width:100%;box-sizing:border-box;padding:8px;background:rgba(0,200,255,.07);border:1px solid rgba(0,200,255,.3);color:#e0f0ff;border-radius:4px;font-size:.9rem;">
    <div style="margin-top:12px;display:flex;gap:8px;">
      <button class="abtn bp" style="flex:1" onclick="_doSaveGame()">💾 Сохранить</button>
      <button class="abtn bw" style="flex:0 0 auto" onclick="closeMsg()">Отмена</button>
    </div>`;
  showMsg('💾 Сохранить игру', html);
  setTimeout(() => {
    const inp = document.getElementById('save-filename-input');
    if (inp) { inp.focus(); inp.select(); }
  }, 50);
}

function _doSaveGame() {
  const inp = document.getElementById('save-filename-input');
  const filename = (inp ? inp.value.trim() : '') || `game_${Date.now()}`;
  closeMsg();

  isSaving = true;
  fetch(`${API_URL}/api/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, state: G })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      showMsg('💾 Сохранено', `Файл: <strong>${data.filename}</strong><br><br>📁 Загрузки/Stellar_Conflict_Saves/`);
    } else {
      showMsg('Ошибка сохранения', data.error || 'Неизвестная ошибка');
    }
  })
  .catch(e => {
    localStorage.setItem('game_' + filename, JSON.stringify(G));
    showMsg('💾 Сохранено (локально)', `<strong>${filename}</strong><br><br>⚠ Сервер недоступен.`);
  })
  .finally(() => { isSaving = false; });
}

function loadGame() {
  fetch(`${API_URL}/api/list`)
  .then(r => r.json())
  .then(data => {
    if (!data.success || data.games.length === 0) {
      console.warn('⚠️  Нет сохранённых игр на сервере');
      showMsg('Нет сохранений', 'Сохранённые игры находятся в:<br>Загрузки/Stellar_Conflict_Saves/<br><br>Запустите сервер: python game_server.py');
      return;
    }

    let html = '<div style="max-height:500px;overflow-y:auto;">';
    data.games.forEach(g => {
      const date = new Date(g.modified * 1000).toLocaleString();
      html += `<div style="padding:8px;background:rgba(0,200,255,.1);margin-bottom:6px;border-radius:4px;cursor:pointer;" onclick="loadGameFile('${g.filename}')">
        <div style="font-weight:bold;">${g.filename}</div>
        <div style="font-size:.75rem;color:#aaa;">${date} · ${g.size} B</div>
      </div>`;
    });
    html += '</div>';

    console.log(`✅ Получено ${data.games.length} сохранённых игр`);
    showMsg('📂 Загрузить игру', html);
  })
  .catch(e => {
    console.error('❌ Ошибка при загрузке списка игр:', e);
    showMsg('Ошибка', '⚠ Сервер недоступен.<br><br>Для загрузки из Загрузок запустите:<br><code>python game_server.py</code>');
  });
}

function validateGameState(state) {
  // Проверка обязательных полей
  const requiredFields = ['version', 'players', 'phase', 'map', 'curP'];
  for (const field of requiredFields) {
    if (!(field in state)) {
      return { valid: false, error: `Отсутствует поле: ${field}` };
    }
  }

  // Проверка версии
  if (state.version !== 1) {
    console.warn(`⚠️  Версия сохранения: ${state.version}. Текущая версия: 1. Попытаемся загрузить...`);
  }

  // Проверка типов
  if (!Array.isArray(state.players) || state.players.length !== 2) {
    return { valid: false, error: 'Некорректное количество игроков' };
  }

  if (typeof state.phase !== 'string') {
    return { valid: false, error: 'Некорректная фаза игры' };
  }

  return { valid: true };
}

function loadGameFile(filename) {
  fetch(`${API_URL}/api/load/${filename}`)
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      const validation = validateGameState(data.state);
      if (!validation.valid) {
        console.error('❌ Ошибка валидации:', validation.error);
        showMsg('Ошибка загрузки', `Файл повреждён или устарел:<br><strong>${validation.error}</strong>`);
        return;
      }

      Object.keys(G).forEach(k => delete G[k]);
      Object.assign(G, data.state);
      console.log(`✅ Игра загружена: ${filename}`);
      clearLog();  // очистить DOM-лог перед загрузкой новой игры
      showScreen('game-screen');

      const phase = G.phase;
      if (['execution', 'end-round'].includes(phase)) {
        // Восстановить state на сервере без сброса фазы
        console.log(`🔄 Восстанавливаю игру в фазе ${phase}...`);
        _restoreGame(phase);
      } else if (['order-placement', 'orders_placed', 'game-start', 'warp-storm'].includes(phase)) {
        console.log('🔄 Инициализирую Stage 2 для загруженной игры...');
        startStage2();
      } else {
        setPhase(phase);
        updateHeader();
        renderBoard();
        renderSide();
        syncLog();
      }

      addLog('Игра загружена', -1);
      closeMsg();
    } else {
      console.error('❌ Ошибка загрузки файла:', data.error);
      showMsg('Ошибка загрузки', data.error);
    }
  })
  .catch(e => {
    console.error('❌ Ошибка при загрузке:', e);
    showMsg('Ошибка', 'Не удалось загрузить: ' + e.message);
  });
}

// ══════════════════════════════════════════════
//  VIEW CARD DECKS
// ══════════════════════════════════════════════

function _renderCardColumn(cards, title, color, renderFn) {
  let html = `<div style="flex:1;min-width:280px;max-height:600px;overflow-y:auto;padding-right:4px;">`;
  html += `<div style="font-weight:bold;color:${color};margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid ${color};">${title} (${cards.length})</div>`;
  if (cards.length === 0) {
    html += `<div style="color:var(--dim);font-style:italic;text-align:center;padding:20px 0;">Пусто</div>`;
  } else {
    cards.forEach(c => { html += renderFn(c); });
  }
  html += `</div>`;
  return html;
}

function _renderBattleCard(c) {
  const name = typeof c === 'string' ? c : c.name;
  const cost = c.cost ? `<span style="color:#ff8c00;margin-left:6px;">Стоимость: ${c.cost}</span>` : '';
  const tier = c.tier != null && c.tier >= 0 ? `<span style="color:var(--dim);margin-left:6px;">Tier ${c.tier}</span>` : '';
  const e1 = c.effect_1 ? `<div style="color:#aaa;font-size:.78rem;margin-top:4px;">${c.effect_1}</div>` : '';
  const e2 = c.effect_2 ? `<div style="color:#888;font-size:.78rem;margin-top:2px;">${c.effect_2}</div>` : '';
  return `<div style="margin-bottom:8px;padding:8px;background:rgba(0,0,0,.4);border-left:3px solid rgba(255,215,0,.4);border-radius:4px;">
    <div style="font-weight:bold;font-size:.9rem;">${name}${cost}${tier}</div>${e1}${e2}
  </div>`;
}

function _renderOrderUpgrade(c) {
  const name = typeof c === 'string' ? c : c.name;
  const type = c.order_type ? `<span style="color:#00bcd4;margin-left:6px;">[${c.order_type}]</span>` : '';
  const cost = c.cost ? `<span style="color:#ff8c00;margin-left:6px;">Стоимость: ${c.cost}</span>` : '';
  const e1 = c.effect_1 ? `<div style="color:#aaa;font-size:.78rem;margin-top:4px;">${c.effect_1}</div>` : '';
  const e2 = c.effect_2 ? `<div style="color:#888;font-size:.78rem;margin-top:2px;">${c.effect_2}</div>` : '';
  return `<div style="margin-bottom:8px;padding:8px;background:rgba(0,0,0,.4);border-left:3px solid rgba(0,188,212,.4);border-radius:4px;">
    <div style="font-weight:bold;font-size:.9rem;">${name}${type}${cost}</div>${e1}${e2}
  </div>`;
}

function _renderEventCard(c) {
  const name = typeof c === 'string' ? c : c.name;
  const ctype = c.card_type ? `<span style="color:#ab47bc;margin-left:6px;">[${c.card_type}]</span>` : '';
  const warp = c.warp_storm_move ? `<div style="color:#ff8c00;font-size:.78rem;margin-top:4px;">Warp: ${c.warp_storm_move}</div>` : '';
  const eff = c.effect ? `<div style="color:#aaa;font-size:.78rem;margin-top:2px;">${c.effect}</div>` : '';
  return `<div style="margin-bottom:8px;padding:8px;background:rgba(0,0,0,.4);border-left:3px solid rgba(171,71,188,.4);border-radius:4px;">
    <div style="font-weight:bold;font-size:.9rem;">${name}${ctype}</div>${warp}${eff}
  </div>`;
}

function showBattleCards(playerIdx) {
  const p = G.players[playerIdx];
  const hand = p.hand_battle_cards || [];
  const avail = p.available_battle_cards || [];
  const html = `<div style="display:flex;gap:16px;font-size:.85rem;">
    ${_renderCardColumn(hand, 'На руке', 'rgba(76,175,80,.9)', _renderBattleCard)}
    ${_renderCardColumn(avail, 'Доступные для получения', 'rgba(255,215,0,.8)', _renderBattleCard)}
  </div>`;
  showMsg(`Боевые карты: ${p.name}`, html, true);
}

function showOrderUpgrades(playerIdx) {
  const p = G.players[playerIdx];
  const hand = p.hand_order_upgrades || [];
  const avail = p.available_order_upgrades || [];
  const html = `<div style="display:flex;gap:16px;font-size:.85rem;">
    ${_renderCardColumn(hand, 'На руке', 'rgba(76,175,80,.9)', _renderOrderUpgrade)}
    ${_renderCardColumn(avail, 'Доступные для получения', 'rgba(0,188,212,.8)', _renderOrderUpgrade)}
  </div>`;
  showMsg(`Улучшения приказов: ${p.name}`, html, true);
}

function showEventCards(playerIdx) {
  const p = G.players[playerIdx];
  const hand = p.hand_event_cards || [];
  const avail = p.available_event_cards || [];
  const dropped = (G.dropped_orders || []).filter(o => o.owner === playerIdx);

  const _renderDroppedOrder = (o) => {
    const orderType = ORDER_TYPES[o.type];
    const orderName = orderType?.name || o.type;
    return `<div style="padding:4px 6px;background:rgba(255,100,50,.1);border:1px solid rgba(255,100,50,.3);border-radius:4px;font-size:.75rem;margin-bottom:3px;">
      ${orderType?.icon || '?'} ${orderName}
    </div>`;
  };

  const droppedHtml = dropped.length === 0
    ? '<span style="color:var(--dim);font-size:.75rem">Нет сброшенных приказов</span>'
    : dropped.map(_renderDroppedOrder).join('');

  const html = `<div style="display:flex;gap:16px;font-size:.85rem;flex-wrap:wrap;">
    ${_renderCardColumn(hand, 'На руке', 'rgba(76,175,80,.9)', _renderEventCard)}
    ${_renderCardColumn(avail, 'Доступные для получения', 'rgba(171,71,188,.8)', _renderEventCard)}
    <div style="flex:1;min-width:120px;">
      <div style="font-weight:bold;margin-bottom:6px;color:rgba(255,100,50,.9);font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">Сброшенные приказы</div>
      ${droppedHtml}
    </div>
  </div>`;
  showMsg(`Карты событий: ${p.name}`, html, true);
}

// ══════════════════════════════════════════════
//  PHASE  — only sets UI state, never touches tileSnap/unitsPlaced
// ══════════════════════════════════════════════
function setPhase(phase) {
  G.phase = phase;
  G.selHandIdx = null;
  G.selUnitIdx = null;
  G.selUnitType = null;

  // Hide all action buttons
  ['btn-ut','btn-uu','btn-fl','btn-rccw','btn-rcw','btn-et','btn-pass','btn-undo-order','btn-undo-ws','btn-confirm-ws','btn-discard-order','btn-next-round','btn-pick-event'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  _selectedOrderForPlay = null;

  const cp  = G.players[G.curP];
  const ins = document.getElementById('pinstr');

  if (phase === 'tile-placement') {
    G.tileSnap   = null;
    G.unitsPlaced = [];
    const rem = cp.hand.filter(h => !h.placed).length;
    ins.innerHTML = `<strong>РАЗМЕЩЕНИЕ СИСТЕМ</strong><br>${cp.name}: выберите систему из руки, затем кликните ячейку. Осталось: ${rem}`;
    renderSide(); renderBoard();
  }
  else if (phase === 'troop-on-tile') {
    // tileSnap + unitsPlaced уже заданы в dropTile — НЕ сбрасывать
    const tile = G.map[G.lastKey];
    const needObj = tile?.needsObjective && !tile?.objectiveMarker;
    const objHint = needObj ? `<br><small style="color:var(--gold)">★ Кликните область без выбранного войска чтобы поставить метку цели соперника</small>` : '';
    ins.innerHTML = `<strong>ВОЙСКА НА СИСТЕМУ</strong><br>${cp.name}: размещайте войска на только что поставленной системе.<br><small style="color:var(--dim)">▲ наземные → 🪐 · ◈ космические → ✦</small>${objHint}`;
    show('btn-ut'); show('btn-uu'); show('btn-fl'); show('btn-rccw'); show('btn-rcw'); show('btn-et');
    document.getElementById('btn-et').textContent = 'Готово →';
    renderSide(); renderBoard(G.lastKey);
  }
  else if (phase === 'warp-storm') {
    const myStorm = G.warpStorms.find(ws => ws.owner === G.curP);
    if (myStorm && !G.warpConfirmed[G.curP]) {
      ins.innerHTML = `<strong>ВАРП-ШТОРМ</strong><br>${cp.name}: варп-шторм размещён на [${myStorm.tileKey}] ${myStorm.side}. Подтвердите или отмените.`;
      show('btn-undo-ws');
      show('btn-confirm-ws');
    } else if (G.warpConfirmed[G.curP]) {
      ins.innerHTML = `<strong>ВАРП-ШТОРМ</strong><br>${cp.name}: размещение подтверждено. Ожидание второго игрока...`;
    } else {
      ins.innerHTML = `<strong>ВАРП-ШТОРМ</strong><br>${cp.name}: кликните на границу любой системы чтобы поставить варп-шторм`;
    }
    renderBoard();
  }
  else if (phase === 'order-placement' || phase === 'orders_placed' || phase === 'execution' || phase === 'end-round') {
    // Stage 2 phases: UI hints from server
    if (G.ui) {
      ins.innerHTML = G.ui.instruction;
      (G.ui.buttons || []).forEach(id => show(id));
    }
    renderSide(); renderBoard();

    // Конец раунда: если игрок ещё не выбрал карту — показать пикер
    if (phase === 'end-round' && G.ui?.event_cards_to_pick?.length) {
      setTimeout(showEventCardPicker, 150);
    }
  }
  updateHeader();
}

function show(id) { const el = document.getElementById(id); if (el) el.style.display = 'block'; }


// ══════════════════════════════════════════════
//  RENDER BOARD
// ══════════════════════════════════════════════
function renderBoard() {
  const board = document.getElementById('map-board');
  board.innerHTML = '';
  const tiles = Object.values(G.map);

  const cols = tiles.map(t=>t.col);
  const rows = tiles.map(t=>t.row);
  const minC=(cols.length?Math.min(...cols):0)-1;
  const minR=(rows.length?Math.min(...rows):0)-1;
  const maxC=(cols.length?Math.max(...cols):2)+1;
  const maxR=(rows.length?Math.max(...rows):1)+1;
  const W=(maxC-minC+1)*CELL, H=(maxR-minR+1)*CELL;
  board.style.width=W+'px'; board.style.height=H+'px';

  const px = (col,row) => ({left:(col-minC)*CELL, top:(row-minR)*CELL});

  // Drop cells (tile-placement phase)
  if (G.phase==='tile-placement' && G.selHandIdx!==null) {
    getValidDrops().forEach(({col,row}) => {
      const p=px(col,row);
      const el=document.createElement('div');
      el.className='drop-cell';
      el.style.cssText=`left:${p.left}px;top:${p.top}px;width:${CELL}px;height:${CELL}px;`;
      el.innerHTML='<span style="font-size:1.4rem;color:rgba(0,200,255,.5);font-family:Orbitron">+</span>';
      el.onclick=()=>dropTile(col,row);
      board.appendChild(el);
    });
  }

  // Placed tiles
  tiles.forEach(tile => {
    const p=px(tile.col,tile.row);
    const el=document.createElement('div');
    el.className='stile';
    el.classList.add(tile.isHome?(tile.owner===0?'hp1':'hp2'):(tile.owner===0?'np1':'np2'));
    const side = tile.side || 0;
    const imgSuffix = side === 0 ? 'a' : 'b';
    el.style.cssText=`left:${p.left}px;top:${p.top}px;width:${CELL}px;height:${CELL}px;`;

    // Rotating background image
    const bgWrap = document.createElement('div'); bgWrap.className = 'stile-bg';
    const bgImg  = document.createElement('div'); bgImg.className  = 'stile-bg-img';
    bgImg.style.backgroundImage = `url('tiles/${tile.tileDefId}_${imgSuffix}.png')`;
    bgImg.style.transform       = `rotate(${tile.rotation || 0}deg)`;
    bgWrap.appendChild(bgImg); el.appendChild(bgWrap);

    if (tile.isHome) {
      const hb=document.createElement('div'); hb.className='hbadge'; hb.textContent='\u{1F3E0}'; el.appendChild(hb);
    }
    const cb=document.createElement('div'); cb.className='tcoord';
    const sideLabel = side===1?' [B]':'';
    cb.textContent=tile.key+(tile.rotation?` ${tile.rotation}\u00b0`:'')+sideLabel; el.appendChild(cb);

    const inner=document.createElement('div'); inner.className='stilei';

    const rotAreas = getRotatedAreas(tile);
    rotAreas.forEach((area, displayIdx) => {
      const realIdx = tile.areas.indexOf(area);
      const ae=document.createElement('div');
      ae.className=`tarea a${area.type}`;

      const cap = area.capacity;
      const used = area.troops.length;
      const lbl=document.createElement('div'); lbl.className='atlbl';
      if (area.type==='planet') {
        const capMark = '\u25cf'.repeat(cap);
        const incMark = area.income   > 0 ? ` <span class="inc-mark">\u25cf${area.income}</span>`   : '';
        const valMark = area.valuable > 0 ? ` <span class="val-mark">\u25c6${area.valuable}</span>` : '';
        let lblHTML = capMark + incMark + valMark;
        if (area.support)  lblHTML += ' <span class="tok-sup">\u2295</span>';
        if (area.discount) lblHTML += ' <span class="tok-dis">\u2296</span>';
        if (area.forge)    lblHTML += ' <span class="tok-frg">\u2692</span>';
        if (area.joker)    lblHTML += ' <span class="tok-jok">\u2605</span>';
        lbl.innerHTML = lblHTML;
      } else {
        lbl.textContent = '\u2736';
      }
      ae.appendChild(lbl);
      const capEl=document.createElement('div'); capEl.className='acap';
      const pendingCount = G.pending_deploy?.tile_key === tile.key
        ? (G.pending_deploy.placed||[]).filter(p => p.area_idx === realIdx).length : 0;
      const effectiveUsed = used + pendingCount;
      capEl.textContent=`${effectiveUsed}/${cap}`;
      if (effectiveUsed>=cap) capEl.style.color='var(--accent2)';
      ae.appendChild(capEl);

      // Structures
      (area.structures||[]).forEach(s => {
        const info = STRUCTURE_INFO[s.type] || { icon:'?', label:s.type };
        const tok=document.createElement('div');
        tok.className='astruc';
        const sFacColor = FACTIONS.find(f=>f.id===G.players[s.player].faction)?.color || (s.player===0?'#00c8ff':'#ff4d6d');
        tok.style.background = hexAlpha(sFacColor, 0.5);
        tok.style.borderColor = sFacColor;
        tok.style.color = getTextColor(sFacColor);
        tok.textContent=info.icon; tok.title=info.label;
        ae.appendChild(tok);
      });

      // Troops
      area.troops.forEach(u => {
        const tok=document.createElement('div');
        const uFac = FACTIONS.find(f=>f.id===G.players[u.player].faction);
        const uColor = uFac?.color || (u.player===0?'#00c8ff':'#ff4d6d');
        tok.className=`atroop ${u.unitType}`;
        tok.style.background = hexAlpha(uColor, 0.15);
        tok.style.borderColor = uColor;
        tok.style.color = uColor;
        tok.textContent=`T${u.tier??0}`;
        tok.title=getUnitName(G.players[u.player].faction, u.unitType, u.tier??0);
        ae.appendChild(tok);
      });

      // Pending deploy units (not yet committed to tile.areas)
      {
        const pd = G.pending_deploy;
        if (pd && tile.key === pd.tile_key && pd.placed) {
          const cp = G.players[G.curP];
          const facColor = FACTIONS.find(f=>f.id===cp.faction)?.color || (G.curP===0?'#00c8ff':'#ff4d6d');
          const catalog = pd.deploy_info?.unit_catalog || [];
          pd.placed.filter(p => p.area_idx === realIdx).forEach(p => {
            const uInfo = catalog.find(c => c.unit_key === p.unit_key);
            const tok = document.createElement('div');
            const uType = _DEPLOY_UT[p.unit_key] || 'ground';
            tok.className = `atroop ${uType}`;
            tok.style.background = hexAlpha(facColor, 0.25);
            tok.style.borderColor = facColor;
            tok.style.color = facColor;
            tok.style.opacity = '0.7';
            tok.style.outline = '2px dashed ' + facColor;
            tok.textContent = `T${uInfo?.tier ?? 0}`;
            tok.title = `${uInfo?.name || p.unit_key} (ожидает)`;
            ae.appendChild(tok);
          });
        }
      }

      // Ownership highlight
      const h1=area.troops.some(t=>t.player===0), h2=area.troops.some(t=>t.player===1);
      if (h1&&h2) ae.classList.add('contested');
      else if (h1) ae.classList.add('h1');
      else if (h2) ae.classList.add('h2');

      // Подсветка допустимых зон при размещении войск
      if (G.phase === 'troop-on-tile' && tile.key === G.lastKey) {
        const cp2 = G.players[G.curP];
        if (G.selUnitIdx !== null) {
          const u = cp2.pool[G.selUnitIdx];
          if (u) ae.classList.add(isCompatible(u, area.type) && area.troops.length < area.capacity ? 'aok' : 'ano');
        } else if (G.selStructIdx !== null) {
          ae.classList.add(area.type === 'planet' && (!area.structures || area.structures.length === 0) ? 'aok' : 'ano');
        } else if (tile.needsObjective && !tile.objectiveMarker) {
          // Подсветить области для метки цели
          const eligIdxs = getObjectiveEligibleDisplayIdxs(tile);
          if (eligIdxs.includes(displayIdx) && area.type === 'planet') ae.classList.add('aok-obj');
        }
      }

      // Deploy highlighting
      {
        const pd = G.pending_deploy;
        if (pd && tile.key === pd.tile_key) {
          const info = pd.deploy_info || {};
          const availIdxs = new Set((info.available_areas || []).map(a => a.idx));
          if (pd.step === 'place_units' && _deploySelectedUnit) {
            const _UT = {infantry:'ground',marines:'ground',mechanized:'ground',elite:'ground',fighter:'space',destroyer:'space'};
            const uType = _UT[_deploySelectedUnit];
            const expected = uType === 'ground' ? 'planet' : 'space';
            ae.classList.add(availIdxs.has(realIdx) && area.type === expected ? 'aok' : 'ano');
          } else if (pd.step === 'buy_building' && _deploySelectedBuilding) {
            const planets = new Set(info.available_planets || []);
            ae.classList.add(planets.has(realIdx) ? 'aok' : 'ano');
          } else if (pd.step === 'resolve_overflow') {
            // Highlight overflow areas in red
            const cnt = (area.troops || []).length + (pd.placed || []).filter(p => p.area_idx === realIdx).length;
            if (cnt > area.capacity) ae.classList.add('ano');
          }
        }
      }

      // Метка цели
      if (tile.objectiveMarker && tile.objectiveMarker.realAreaIdx === realIdx) {
        const opPlayer = tile.objectiveMarker.owner;
        const opFac = FACTIONS.find(f => f.id === G.players[opPlayer].faction);
        const opColor = opFac?.color || (opPlayer === 0 ? '#00c8ff' : '#ff4d6d');
        const opIcon = opFac?.icon || (opPlayer === 0 ? 'P1' : 'P2');
        const marker = document.createElement('div');
        marker.className = 'obj-marker';
        marker.style.background = hexAlpha(opColor, 0.25);
        marker.style.borderColor = opColor;
        marker.style.color = opColor;
        marker.textContent = opIcon;
        marker.title = `Цель: ${G.players[opPlayer].name}`;
        ae.appendChild(marker);
      }

      ae.onclick=()=>areaClick(tile.key, displayIdx);
      inner.appendChild(ae);
    });

    el.appendChild(inner);

    // Центральная зона — размещение приказов (клик отправляет на API)
    const centerZone = document.createElement('div');
    centerZone.style.cssText = `
      position: absolute;
      left: 50%;
      top: 50%;
      width: 60px;
      height: 60px;
      transform: translate(-50%, -50%);
      cursor: ${G.phase === 'order-placement' ? 'pointer' : 'default'};
      z-index: 5;
      pointer-events: ${G.phase === 'order-placement' ? 'auto' : 'none'};
    `;
    if (G.phase === 'order-placement') {
      centerZone.onclick = (e) => {
        e.stopPropagation();
        placeOrderViaAPI(tile.key);
      };
    }
    el.appendChild(centerZone);

    // Отрисовка приказов на тайле (стопка в центре, смещение вверх-вправо)
    // Сортируем по позиции чтобы верхний (наибольшая position) был последним в DOM (z-index выше)
    const tilesOrders = G.orders.filter(o => o.tile === tile.key)
      .sort((a, b) => (a.position || 0) - (b.position || 0));

    // Playable order IDs from server UI hints
    const boardPlayableIds = new Set(G.ui?.playable_order_ids || []);

    tilesOrders.forEach((order, idx) => {
      const orderEl = document.createElement('div');
      const fac = FACTIONS.find(f => f.id === G.players[order.owner].faction);
      const facIcon = fac?.icon || (order.owner === 0 ? 'P1' : 'P2');
      const orderName = ORDER_TYPES[order.type]?.name || order.type;

      // Смещение для стопки: каждый выше и правее (вверх-вправо)
      const offsetY = -idx * 5;
      const offsetX = idx * 5;

      const factionColor = G.players[order.owner].faction_color || (order.owner === 0 ? '#00c8ff' : '#ff4d6d');

      // Во время execution: кликабелен если сервер пометил как playable
      const isClickable = G.phase === 'execution' && boardPlayableIds.has(order.id);
      const isSelected = _selectedOrderForPlay?.id === order.id;

      orderEl.className = `order-fd${isSelected ? ' selected-order' : ''}`;
      orderEl.style.cssText = `
        position: absolute;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 1px;
        font-family: 'Orbitron', monospace;
        pointer-events: ${isClickable ? 'auto' : 'none'};
        cursor: ${isClickable ? 'pointer' : 'default'};
        top: calc(50% + ${offsetY}px);
        left: calc(50% + ${offsetX}px);
        transform: translate(-50%, -50%);
        box-shadow: 0 2px 10px rgba(0,0,0,.85)${isSelected ? ', 0 0 0 3px rgba(255,220,50,.8)' : ''};
        z-index: ${10 + idx};
        background: #1a1a1a;
        border: 2px solid ${isSelected ? 'rgba(255,220,50,.9)' : '#333'};
        color: ${factionColor};
        clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
      `;
      orderEl.innerHTML = `
        <div style="font-size: 2rem; font-weight: bold; line-height: 1;">${facIcon}</div>
      `;
      orderEl.title = isClickable
        ? (isSelected ? `Нажмите ещё раз для розыгрыша: ${orderName}` : `Выбрать: ${orderName}`)
        : `${orderName} (${G.players[order.owner].name})`;

      if (isClickable) {
        orderEl.addEventListener('click', (e) => {
          e.stopPropagation();
          selectOrderForPlay(order.id, order.type, tile.key);
        });
      }

      el.appendChild(orderEl);
    });

    // Варп-штормы: визуализация + кликабельные границы в фазе warp-storm
    ['top','bottom','left','right'].forEach(side => {
      const isH = side === 'top' || side === 'bottom';
      const hasWS = G.warpStorms.some(ws => ws.tileKey === tile.key && ws.side === side);
      if (hasWS) {
        const ws = document.createElement('div');
        ws.className = `warp-storm warp-storm-${side} ${isH ? 'warp-storm-h' : 'warp-storm-v'}`;
        el.appendChild(ws);
      }
      const canPlaceWS = G.phase === 'warp-storm' && !hasWS && !G.warpStorms.some(ws => ws.owner === G.curP) && !G.warpConfirmed[G.curP];
      if (canPlaceWS) {
        const border = document.createElement('div');
        border.className = `ws-border ws-border-${isH ? 'h' : 'v'} warp-storm-${side}`;
        border.onclick = (e) => { e.stopPropagation(); placeWarpStorm(tile.key, side); };
        el.appendChild(border);
      }
    });

    board.appendChild(el);
  });
}

// ── Tile hover preview ────────────────────────────────────────────────────────


// ══════════════════════════════════════════════
//  RENDER SIDE PANEL
// ══════════════════════════════════════════════
function renderSide() {
  _cancelTileHover(); _cancelTileHideTimer(); _dismissTilePreview();
  const cp = G.players[G.curP];

  // В фазе размещения войск — показываем пул, скрываем руку тайлов
  const poolSection   = document.getElementById('unit-pool-section');
  const structSection = document.getElementById('struct-pool-section');
  if (G.phase === 'troop-on-tile') {
    document.getElementById('tile-hand').innerHTML = '';

    // Пул юнитов
    const poolEl = document.getElementById('unit-pool');
    poolSection.style.display = 'block';
    poolEl.innerHTML = '';
    if (cp.pool.length > 0) {
      cp.pool.forEach((u, idx) => {
        const tok = document.createElement('div');
        const fac = FACTIONS.find(f=>f.id===cp.faction);
        const facColor = fac?.color || (G.curP===0?'#00c8ff':'#ff4d6d');
        tok.className = `ttok ${u.unitType}${G.selUnitIdx===idx?' sel':''}`;
        tok.style.background = hexAlpha(facColor, 0.15);
        tok.style.borderColor = facColor;
        tok.style.color = facColor;
        tok.textContent = `T${u.tier??0}`;
        tok.title = getUnitName(cp.faction, u.unitType, u.tier??0);
        tok.onclick = () => selectUnitFromPool(idx);
        poolEl.appendChild(tok);
      });
    } else {
      poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Нет войск</span>';
    }

    // Пул построек
    const structEl = document.getElementById('struct-pool');
    if (cp.structurePool && cp.structurePool.length > 0) {
      structSection.style.display = 'block';
      structEl.innerHTML = '';
      cp.structurePool.forEach((s, idx) => {
        const info = STRUCTURE_INFO[s.type] || { icon:'?', label:s.type };
        const tok = document.createElement('div');
        tok.className = `ttok stok ${G.curP===0?'c1':'c2'}${G.selStructIdx===idx?' sel':''}`;
        tok.innerHTML = info.icon;
        tok.title = info.label;
        tok.onclick = () => selectStructFromPool(idx);
        structEl.appendChild(tok);
      });
    } else {
      structSection.style.display = 'none';
    }
    return;
  }

  // В фазе расстановки приказов — показываем приказы через API
  if (G.phase === 'order-placement') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';

    // Раздел 1: Приказы в руке (используем G.ui для логики)
    const canPlace = G.ui?.can_place_order;

    if (cp.hand_orders && cp.hand_orders.length > 0 && canPlace) {
      cp.hand_orders.forEach((order, idx) => {
        const btn = document.createElement('button');
        const orderName = ORDER_TYPES[order.type]?.name || order.type;
        const isSelected = _selectedOrderForPlacement?.id === order.id;

        btn.className = `abtn ${G.curP===0?'bp':'br'}`;
        btn.style.width = '100%';
        btn.style.marginBottom = '4px';
        btn.textContent = `${ORDER_TYPES[order.type]?.icon || '?'} ${orderName}`;
        btn.title = `${orderName} #${idx+1}`;

        if (isSelected) {
          btn.style.filter = 'brightness(1.3)';
          btn.style.boxShadow = '0 0 8px currentColor';
        }

        btn.onclick = () => selectOrderForPlacement(idx, order);
        poolEl.appendChild(btn);
      });
    } else {
      const ordersPlacedCount = G.ordersPlaced[G.curP] || 0;
      if (ordersPlacedCount >= 4) {
        poolEl.innerHTML = '<span style="color:var(--gold);font-size:.75rem">✓ Все 4 приказа размещены</span>';
      } else if (G.ui?.order_placed_this_turn) {
        poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Приказ размещён. Передайте ход.</span>';
      } else {
        poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Приказы выставлены</span>';
      }
    }

    // Раздел 2: Приказы на поле (только текущего игрока)
    const ordersOnField = G.orders.filter(o => o.owner === G.curP);
    if (ordersOnField.length > 0) {
      const divider = document.createElement('div');
      divider.style.cssText = 'margin-top:10px;padding-top:8px;border-top:1px solid var(--border);';

      const title = document.createElement('div');
      title.className = 'ptitle';
      title.textContent = 'ПРИКАЗЫ НА ПОЛЕ';
      divider.appendChild(title);

      // Группируем приказы по системам
      const ordersByTile = {};
      ordersOnField.forEach(o => {
        if (!ordersByTile[o.tile]) ordersByTile[o.tile] = [];
        ordersByTile[o.tile].push(o);
      });

      // Выводим каждую систему с приказами
      Object.entries(ordersByTile).sort().forEach(([tileKey, orders]) => {
        const tileInfo = document.createElement('div');
        tileInfo.style.cssText = 'margin-top:6px;padding:6px;background:rgba(255,255,255,.05);border-radius:4px;font-size:.75rem;';

        const tileLabel = document.createElement('div');
        tileLabel.style.cssText = 'font-weight:bold;color:var(--gold);margin-bottom:3px;';
        tileLabel.textContent = `📍 [${tileKey}]`;
        tileInfo.appendChild(tileLabel);

        // Приказы в этой системе
        orders.forEach((o, i) => {
          const orderDisplay = document.createElement('div');
          const orderType = ORDER_TYPES[o.type];
          const abbrev = (orderType?.name || o.type).substring(0, 3).toUpperCase();
          orderDisplay.style.cssText = `color:var(--dim);font-size:.7rem;margin-left:4px;`;
          orderDisplay.textContent = `${i+1}. ${orderType?.icon || '?'} ${abbrev}`;
          tileInfo.appendChild(orderDisplay);
        });

        divider.appendChild(tileInfo);
      });

      poolEl.appendChild(divider);
    }

    return;
  }

  // ── ФАЗА ОЖИДАНИЯ (ORDERS_PLACED) ──
  if (G.phase === 'orders_placed') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = `
      <div style="text-align:center;padding:10px;color:var(--gold);font-weight:bold;">
        ✓ ВСЕ ПРИКАЗЫ ВЫСТАВЛЕНЫ
      </div>
      <div style="margin-top:10px;color:var(--dim);font-size:.75rem;text-align:center;">
        Ожидание второго игрока...
      </div>
    `;

    return;
  }

  // ── DEPLOY: place_units — юниты в левой панели ──
  if (G.phase === 'execution' && G.pending_deploy?.step === 'place_units') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const pd      = G.pending_deploy;
    const hand    = pd.hand || [];
    const placed  = pd.placed || [];
    const catalog = pd.deploy_info?.unit_catalog || [];
    const getName = k => catalog.find(c => c.unit_key === k)?.name || k;
    const cp      = G.players[G.curP];
    const facColor = FACTIONS.find(f => f.id === cp.faction)?.color || (G.curP === 0 ? '#00c8ff' : '#ff4d6d');

    const handRem = [...hand];
    for (const p of placed) {
      const i = handRem.indexOf(p.unit_key);
      if (i >= 0) handRem.splice(i, 1);
    }

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';

    const title = document.createElement('div');
    title.className = 'ptitle';
    title.textContent = `DEPLOY: юниты (${placed.length}/${hand.length})`;
    poolEl.appendChild(title);

    const hint = document.createElement('div');
    hint.style.cssText = 'font-size:.68rem;color:var(--gold);margin-bottom:6px;';
    hint.textContent = _deploySelectedUnit
      ? `✓ Выбран: ${_deploySelectedUnit} — кликните область на карте`
      : '← Выберите юнит, затем кликните область на тайле';
    poolEl.appendChild(hint);

    if (handRem.length > 0) {
      handRem.forEach(uk => {
        const u   = catalog.find(c => c.unit_key === uk);
        const tok = document.createElement('div');
        tok.className = `ttok ${_DEPLOY_UT[uk] || 'ground'}${_deploySelectedUnit === uk ? ' sel' : ''}`;
        tok.style.background  = hexAlpha(facColor, 0.15);
        tok.style.borderColor = facColor;
        tok.style.color       = facColor;
        tok.textContent = `T${u?.tier ?? 0}`;
        tok.title       = u?.name || uk;
        tok.onclick     = () => { _deploySelectedUnit = uk; renderSide(); renderBoard(); };
        poolEl.appendChild(tok);
      });
    } else {
      const msg = document.createElement('span');
      msg.style.cssText = 'color:var(--dim);font-size:.75rem';
      msg.textContent = 'Все размещены';
      poolEl.appendChild(msg);
    }

    if (placed.length > 0) {
      const placed_div = document.createElement('div');
      placed_div.style.cssText = 'margin-top:8px;padding-top:6px;border-top:1px solid var(--border);font-size:.72rem;color:var(--dim);';
      placed_div.textContent = 'Размещено: ' + placed.map(p => getName(p.unit_key) + ' →area' + p.area_idx).join(', ');
      poolEl.appendChild(placed_div);
    }
    return;
  }

  // ── DEPLOY: buy_building — здания в левой панели ──
  if (G.phase === 'execution' && G.pending_deploy?.step === 'buy_building') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const pd      = G.pending_deploy;
    const info    = pd.deploy_info || {};
    const credits = info.credits - (pd.unit_costs?.credits || 0);
    const cash    = info.cash_tokens - (pd.unit_costs?.cash || 0);
    const pool    = info.structure_pool || [];

    const poolCounts = {};
    for (const s of pool) poolCounts[s.type] = (poolCounts[s.type] || 0) + 1;
    const bTypes = Object.keys(poolCounts);

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';

    const title = document.createElement('div');
    title.className = 'ptitle';
    title.textContent = 'DEPLOY: постройка';
    poolEl.appendChild(title);

    const resLine = document.createElement('div');
    resLine.style.cssText = 'font-size:.72rem;color:var(--dim);margin-bottom:6px;';
    resLine.textContent = `💰${credits}  cash:${cash}`;
    poolEl.appendChild(resLine);

    if (bTypes.length > 0) {
      bTypes.forEach(bt => {
        const cost = _DEPLOY_COSTS[bt] || 0;
        const canAfford = credits >= cost;
        const isSelected = _deploySelectedBuilding === bt;
        const btn = document.createElement('button');
        btn.className = `abtn ${isSelected ? 'bg' : 'bp'}`;
        btn.style.cssText = 'width:100%;margin-bottom:4px;';
        btn.disabled = !canAfford;
        btn.title = !canAfford ? 'Не хватает кредитов' : '';
        btn.textContent = `${_DEPLOY_ICONS[bt] || '🏠'} ${bt} (${cost}💰) ×${poolCounts[bt]}`;
        btn.onclick = () => _deploySelectBuilding(bt);
        poolEl.appendChild(btn);
      });
    } else {
      const empty = document.createElement('div');
      empty.style.cssText = 'color:var(--dim);font-size:.75rem;';
      empty.textContent = 'Резерв построек пуст';
      poolEl.appendChild(empty);
    }

    if (_deploySelectedBuilding) {
      const hint = document.createElement('div');
      hint.style.cssText = 'font-size:.68rem;color:var(--gold);margin:6px 0;';
      hint.textContent = `✓ Выбрано: ${_DEPLOY_ICONS[_deploySelectedBuilding] || ''} ${_deploySelectedBuilding} — кликните планету на карте`;
      poolEl.appendChild(hint);

      const cashLabel = document.createElement('label');
      cashLabel.style.cssText = 'font-size:.75rem;display:flex;align-items:center;gap:6px;cursor:pointer;margin-bottom:6px;';
      cashLabel.innerHTML = `<input type="checkbox" id="deploy-use-cash-panel"> Cash токен (−2💰)`;
      poolEl.appendChild(cashLabel);
    }

    const skipBtn = document.createElement('button');
    skipBtn.className = 'abtn bw';
    skipBtn.style.cssText = 'width:100%;margin-top:8px;';
    skipBtn.textContent = 'Пропустить постройку →';
    skipBtn.onclick = () => _deploySkipBuilding();
    poolEl.appendChild(skipBtn);

    return;
  }

  // ── ФАЗА РОЗЫГРЫША ПРИКАЗОВ (EXECUTION) ──
  if (G.phase === 'execution') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';

    // Показать кнопку сброса если выбран приказ
    const discardBtn = document.getElementById('btn-discard-order');
    if (discardBtn) {
      discardBtn.style.display = _selectedOrderForPlay ? 'block' : 'none';
    }

    const ordersOnField = G.orders.filter(o => o.owner === G.curP);

    if (ordersOnField.length === 0) {
      poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Нет приказов на поле. Нажмите ПЕРЕДАТЬ ХОД.</span>';
      return;
    }

    const wrap = document.createElement('div');

    const title = document.createElement('div');
    title.className = 'ptitle';
    title.textContent = 'ПРИКАЗЫ НА ПОЛЕ';
    wrap.appendChild(title);

    // Группируем по системам
    const ordersByTile = {};
    ordersOnField.forEach(o => {
      if (!ordersByTile[o.tile]) ordersByTile[o.tile] = [];
      ordersByTile[o.tile].push(o);
    });

    const playableIds = new Set(G.ui?.playable_order_ids || []);
    const blockedTiles = new Set(G.ui?.blocked_tiles || []);

    Object.entries(ordersByTile).sort().forEach(([tileKey, orders]) => {
      // Сортируем: наибольшая position = верхний = позиция 1
      orders.sort((a, b) => (b.position || 0) - (a.position || 0));

      const blockedByOpponent = blockedTiles.has(tileKey);

      const tileLabel = document.createElement('div');
      tileLabel.style.cssText = 'font-size:.65rem;margin:6px 0 2px;text-transform:uppercase;letter-spacing:.05em;display:flex;align-items:center;gap:4px;';
      tileLabel.innerHTML = `<span style="color:var(--dim)">[${tileKey}]</span>${blockedByOpponent ? '<span style="color:#ff6b6b;font-size:.6rem;">⊘ заблокирован</span>' : ''}`;
      wrap.appendChild(tileLabel);

      orders.forEach((order, stackIdx) => {
        const posNum = stackIdx + 1;  // 1 = верхний в своей стопке
        const isMyTop = stackIdx === 0;
        const isPlayable = playableIds.has(order.id);
        const isSelected = _selectedOrderForPlay?.id === order.id;
        const orderType = ORDER_TYPES[order.type];
        const orderName = orderType?.name || order.type;

        const row = document.createElement('div');
        row.style.cssText = `
          display:flex;align-items:center;gap:6px;padding:4px 6px;margin-bottom:3px;
          border-radius:5px;cursor:${isPlayable?'pointer':'default'};
          background:${isSelected ? 'rgba(255,220,50,.15)' : isMyTop && !blockedByOpponent ? 'rgba(255,255,255,.05)' : 'rgba(255,255,255,.02)'};
          border:1px solid ${isSelected ? 'rgba(255,220,50,.6)' : isMyTop && !blockedByOpponent ? 'rgba(255,255,255,.15)' : 'rgba(255,255,255,.06)'};
          opacity:${isMyTop ? '1' : '0.55'};
        `;

        const numBadge = document.createElement('span');
        numBadge.style.cssText = `
          min-width:16px;height:16px;border-radius:50%;
          background:${isPlayable ? (G.curP===0?'#00c8ff':'#ff4d6d') : '#444'};
          color:#fff;font-size:.6rem;font-weight:bold;
          display:flex;align-items:center;justify-content:center;flex-shrink:0;
        `;
        numBadge.textContent = posNum;

        const label = document.createElement('span');
        label.style.cssText = 'font-size:.72rem;flex:1;';
        label.textContent = `${orderType?.icon || '?'} ${orderName}`;

        row.appendChild(numBadge);
        row.appendChild(label);

        if (isPlayable) {
          row.onclick = () => selectOrderForPlay(order.id, order.type, tileKey);
          row.title = isSelected
            ? 'Нажмите ещё раз для розыгрыша'
            : `Выбрать: ${orderName}`;
        } else if (isMyTop && blockedByOpponent) {
          row.title = 'Заблокирован приказом соперника';
        }

        wrap.appendChild(row);
      });
    });

    poolEl.appendChild(wrap);
    return;
  }

  // ── ФАЗА КОНЦА РАУНДА (END-ROUND) ──
  if (G.phase === 'end-round') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const poolEl = document.getElementById('unit-pool');
    const roundNum = G.round || 1;
    const totalRounds = G.totalRounds || 8;
    poolEl.innerHTML = `
      <div style="text-align:center;padding:10px;color:var(--gold);font-weight:bold;">
        ✓ РАУНД ${roundNum}/${totalRounds} ЗАВЕРШЁН
      </div>
      <div style="margin-top:10px;color:var(--dim);font-size:.75rem;text-align:center;">
        Все приказы разыграны. Сброшенные приказы возвращены в руки.
      </div>
    `;

    return;
  }

  // В других фазах — скрыть пул
  if (poolSection)   poolSection.style.display   = 'none';
  if (structSection) structSection.style.display = 'none';

  // Tile hand
  const handEl = document.getElementById('tile-hand');
  handEl.innerHTML = '';
  cp.hand.forEach((ht,idx) => {
    if (ht.placed) return;
    const el=document.createElement('div');
    el.className=`htile${ht.isHome?' hthome':''}`;
    if (G.selHandIdx===idx) el.classList.add(cp.color==='c1'?'hs1':'hs2');
    const tileDef=TILE_CATALOG.find(t=>t.id===ht.tileDefId);
    const sideLayout=tileDef?tileDef.sides[0].layout.flat():[];
    const prev=document.createElement('div'); prev.className='hpreview';
    sideLayout.forEach(v=>{ const d=document.createElement('div'); d.className=`hpa ${v===1?'hpp':'hps'}`; prev.appendChild(d); });
    const lbl=document.createElement('div'); lbl.className='htlabel';
    const fac=FACTIONS.find(f=>f.id===cp.faction);
    lbl.textContent=ht.isHome?`${fac?.icon} \u0414\u043e\u043c\u0430\u0448\u043d\u044f\u044f`:`\u0421\u0438\u0441\u0442\u0435\u043c\u0430 ${idx+1}`;
    el.appendChild(prev); el.appendChild(lbl);
    el.onclick=()=>selectHandTile(idx);
    el.addEventListener('mouseenter', () => _startTileHover(el, ht.tileDefId));
    el.addEventListener('mouseleave', _cancelTileHover);
    handEl.appendChild(el);
  });
}

// ══════════════════════════════════════════════
//  HEADER
// ══════════════════════════════════════════════
function updateHeader() {
  const cp=G.players[G.curP];
  [0,1].forEach(pi=>{
    const p=G.players[pi], pfx=pi===0?'p1':'p2';
    document.getElementById(`h-${pfx}-name`).textContent=p.name;
    document.getElementById(`h-${pfx}-init`).textContent=p.name.substring(0,2).toUpperCase();
    const fac=FACTIONS.find(f=>f.id===p.faction);
    document.getElementById(`h-${pfx}-fac`).textContent=fac?`${fac.icon} ${fac.name}`:'—';
    const resEl = document.getElementById(`h-${pfx}-res`);
    if (resEl) {
      const parts = [];
      if (p.credits != null) parts.push(`💰${p.credits}`);
      if (p.tokens?.support)  parts.push(`⊕${p.tokens.support}`);
      if (p.tokens?.discount) parts.push(`⊖${p.tokens.discount}`);
      if (p.tokens?.forge)    parts.push(`⚒${p.tokens.forge}`);
      resEl.textContent = parts.join('  ') || '';
    }
  });
  const hRound = document.getElementById('h-round');
  if (hRound) hRound.textContent = G.round ? `Раунд ${G.round}` : 'Раунд —';

  const hObj0 = document.getElementById('h-obj-p1');
  const hObj1 = document.getElementById('h-obj-p2');
  if (hObj0) hObj0.textContent = `🎯 ${G.players[0]?.collected_objectives ?? 0}`;
  if (hObj1) hObj1.textContent = `🎯 ${G.players[1]?.collected_objectives ?? 0}`;

  const edsp = document.getElementById('event-stack-disp');
  if (edsp) edsp.style.display='none';
}

// ══════════════════════════════════════════════
//  HOTPASS / UTILS
// ══════════════════════════════════════════════
let _hpCb=null;
function showHP(name,action,cb) {
  _hpCb=cb;
  document.getElementById('hp-name').textContent=name;
  document.getElementById('hp-action').textContent=action;
  const btn=document.getElementById('hp-btn');
  const isP2=G.players[1]?.name===name;
  btn.style.borderColor=isP2?'var(--p2)':'var(--p1)';
  btn.style.color      =isP2?'var(--p2)':'var(--p1)';
  btn.style.background =isP2?'rgba(255,77,109,.1)':'rgba(0,200,255,.1)';
  document.getElementById('hpov').classList.add('active');
}
function closeHP() {
  document.getElementById('hpov').classList.remove('active');
  if(_hpCb){_hpCb();_hpCb=null;}
}
let _msgCb = null;
function showMsg(t,b,cb){
  _msgCb = cb || null;
  document.getElementById('msg-title').textContent=t;
  document.getElementById('msg-body').innerHTML=b;
  // Always restore standard OK button
  document.querySelector('#msg-modal .mbtns').innerHTML='<button class="abtn bp" onclick="closeMsg()">OK</button>';
  document.getElementById('msg-modal').classList.add('active');
}
function closeMsg(){
  document.getElementById('msg-modal').classList.remove('active');
  if(_msgCb){const f=_msgCb;_msgCb=null;f();}
}
function showScreen(id){
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}
let _renderedLogCount = 0;

function addLog(msg, player) {
  // Пишем в DOM и в G.log
  const el = document.getElementById('alog');
  const e = document.createElement('div');
  e.className = `le ${player===0?'le1':player===1?'le2':'les'}`;
  e.textContent = msg;
  el.prepend(e);
  if (!G.log) G.log = [];
  G.log.push({ message: msg, player_id: player });
  _renderedLogCount = G.log.length;
}

function _renderLogEntry(msg, player) {
  const el = document.getElementById('alog');
  const e = document.createElement('div');
  e.className = `le ${player===0?'le1':player===1?'le2':'les'}`;
  e.textContent = msg;
  el.prepend(e);
}

function clearLog() {
  document.getElementById('alog').innerHTML = '';
  _renderedLogCount = 0;
}

function syncLog() {
  // Отрендерить записи из G.log которые ещё не показаны в DOM
  const log = G.log || [];
  if (log.length > _renderedLogCount) {
    // Новые записи идут с конца — добавляем в обратном порядке чтобы prepend дал правильный порядок
    const newEntries = log.slice(_renderedLogCount);
    for (let i = newEntries.length - 1; i >= 0; i--) {
      _renderLogEntry(newEntries[i].message, newEntries[i].player_id);
    }
    _renderedLogCount = log.length;
  }
}

// ══════════════════════════════════════════════
//  ORDER PLACEMENT VIA API (Stage 2)
// ══════════════════════════════════════════════

let _selectedOrderForPlacement = null;  // { idx, id, type, owner }
let _selectedOrderForPlay = null;      // { id, type, tile } — выбранный приказ для розыгрыша/сброса

async function undoLastOrderViaAPI() {
  const isPlacement = G.phase === 'order-placement';
  const isExecution = G.phase === 'execution';
  if (!isPlacement && !isExecution) return;

  if (isPlacement && !G.ui?.order_placed_this_turn) {
    showMsg('Нет приказов', 'В этом ходу приказ не выставлялся');
    return;
  }
  if (isExecution && !G.ui?.order_played_this_turn && !G.pending_deploy) {
    showMsg('Нет действий', 'В этом ходу приказ не разыгрывался');
    return;
  }

  try {
    const res = await apiCall('/api/game/undo', { player_id: G.curP });
    if (res.success) {
      closeMsg();  // закрыть deploy modal если открыт
      _deployBasket = [];
      _deploySelectedUnit = null;
      _deploySelectedBuilding = null;
      applyState(res.state);
      _selectedOrderForPlacement = null;
      _selectedOrderForPlay = null;
      addLog(`${G.players[G.curP].name} отменил действие`, G.curP);
      setPhase(G.phase);
    } else {
      showMsg('Ошибка отмены', res.error || 'Не удалось отменить');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function passOrderTurnViaAPI() {
  if (G.phase !== 'order-placement' && G.phase !== 'orders_placed') return;

  try {
    const res = await apiCall('/api/game/pass-turn', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      _selectedOrderForPlacement = null;

      // Проверяем в какую фазу перешли
      if (G.phase === 'orders_placed') {
        addLog('✅ Ожидание начала розыгрыша приказов...', -1);
        const nextPlayer = G.players[G.curP];
        showHP(nextPlayer.name, 'Ожидание розыгрыша', () => setPhase('orders_placed'));
      } else if (G.phase === 'execution') {
        addLog('🎮 Начало розыгрыша приказов!', -1);
        const nextPlayer = G.players[G.curP];
        showHP(nextPlayer.name, 'Розыгрыш приказов', () => setPhase('execution'));
      } else {
        // Остаемся в order-placement, смена игрока
        const nextPlayer = G.players[G.curP];
        showHP(nextPlayer.name, 'Выставьте приказы', () => setPhase('order-placement'));
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось передать ход');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function selectOrderForPlacement(idx, order) {
  if (G.phase !== 'order-placement') return;
  if (!G.ui?.can_place_order) return;
  _selectedOrderForPlacement = { idx, id: order.id, type: order.type, owner: G.curP };
  renderSide();
}

async function placeOrderViaAPI(tileKey) {
  if (G.phase !== 'order-placement') {
    if (G.phase === 'orders_placed') {
      showMsg('Запрещено', 'Размещение приказов завершено. Нажмите ПЕРЕДАТЬ ХОД.');
    }
    return;
  }

  if (!G.ui?.can_place_order) {
    showMsg('Лимит достигнут', 'Вы уже разместили приказ в этом ходу или достигнут лимит');
    return;
  }

  if (!_selectedOrderForPlacement) {
    showMsg('Выберите приказ', 'Сначала выберите приказ слева');
    return;
  }

  // Отправить на сервер (валидация на стороне Python)
  const orderData = _selectedOrderForPlacement;
  try {
    const res = await apiCall('/api/game/place-order', {
      player_id: G.curP,
      order_id: orderData.id,
      tile_key: tileKey
    });
    if (res.success) {
      applyState(res.state);
      _selectedOrderForPlacement = null;
      addLog(`${G.players[G.curP].name} выставил ${ORDER_TYPES[orderData.type]?.name || 'приказ'}`, G.curP);
      setPhase('order-placement');
    } else {
      showMsg('Ошибка', res.error || 'Не удалось разместить приказ');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

// ── ОБЩАЯ ФУНКЦИЯ ПЕРЕДАЧИ ХОДА ──

function passOrderTurn() {
  if (G.phase === 'order-placement' || G.phase === 'orders_placed') {
    passOrderTurnViaAPI();
  } else if (G.phase === 'execution') {
    passOrderPlayTurnViaAPI();
  }
}

// ── РОЗЫГРЫШ ПРИКАЗОВ ──

// hasPlayableOrders и updateExecutionPassButton перенесены в Python (compute_ui_hints)

function selectOrderForPlay(orderId, orderType, tileKey) {
  if (G.phase !== 'execution') return;
  if (_selectedOrderForPlay?.id === orderId) {
    // Второй клик — розыгрыш
    playOrderViaAPI(orderId);
  } else {
    // Первый клик — выделение
    _selectedOrderForPlay = { id: orderId, type: orderType, tile: tileKey };
    renderSide();
    renderBoard();
  }
}

async function playOrderViaAPI(orderId) {
  if (G.phase !== 'execution') return;

  const ordersBefore = G.orders.filter(o => o.owner === G.curP);
  const order = ordersBefore.find(o => o.id === orderId);
  const orderType = ORDER_TYPES[order?.type];
  const orderName = orderType?.name || order?.type || orderId;

  try {
    const res = await apiCall('/api/game/play-order', {
      player_id: G.curP,
      order_id: orderId
    });
    if (res.success) {
      _selectedOrderForPlay = null;
      applyState(res.state);
      addLog(`${G.players[G.curP]?.name || 'Игрок'}: приказ "${orderName}" разыгран`, G.curP);
      // Check if dominate produced a joker choice
      if (res.state?.pending_joker_choice) {
        _showJokerChoiceUI(res.state.pending_joker_choice);
      } else if (res.state?.pending_deploy) {
        setPhase('execution');  // обновит инструкцию, затем показываем UI
        showDeployUI();
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось разыграть приказ');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function _showJokerChoiceUI(pending) {
  const TOKEN_LABELS = { support: '🛡 Support', discount: '💰 Discount', forge: '🔨 Forge' };
  const count = pending.joker_count || 1;
  const pid = pending.player_id;

  const html = `
    <div style="margin-bottom:10px;color:#aaa;">Выберите тип токена для джокера (${count} шт.):</div>
    <div style="display:flex;gap:10px;justify-content:center;">
      ${['support','discount','forge'].map(t => `
        <button class="abtn bp" onclick="_resolveJoker(${pid},'${t}')"
          style="padding:12px 20px;font-size:1rem;">${TOKEN_LABELS[t]}</button>
      `).join('')}
    </div>`;
  showMsg('🎲 Выбор джокера', html);
}

async function _resolveJoker(playerId, choiceType) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-joker', {
      player_id: playerId,
      choice: choiceType
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Джокер → ${choiceType}`, playerId);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || 'Не удалось разрешить джокер');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function discardOrderViaAPI() {
  if (G.phase !== 'execution') return;
  if (!_selectedOrderForPlay) return;

  const orderId = _selectedOrderForPlay.id;
  const orderType = ORDER_TYPES[_selectedOrderForPlay.type];
  const orderName = orderType?.name || _selectedOrderForPlay.type;

  try {
    const res = await apiCall('/api/game/discard-order', {
      player_id: G.curP,
      order_id: orderId
    });
    if (res.success) {
      _selectedOrderForPlay = null;
      applyState(res.state);
      addLog(`${G.players[G.curP]?.name || 'Игрок'}: приказ "${orderName}" сброшен`, G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || 'Не удалось сбросить приказ');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function passOrderPlayTurnViaAPI() {
  if (G.phase !== 'execution') return;

  try {
    const res = await apiCall('/api/game/pass-turn-order-play', {
      player_id: G.curP
    });
    if (res.success) {
      _selectedOrderForPlay = null;
      applyState(res.state);

      // Проверить какая фаза дальше
      if (G.phase === 'end-round') {
        addLog('✅ Все приказы разыграны! Конец раунда.', -1);
        setPhase('end-round');  // сам вызовет showEventCardPicker через setTimeout
      } else if (G.phase === 'execution') {
        const nextPlayer = G.players[G.curP];
        addLog(`${nextPlayer.name} ходит в фазе розыгрыша`, -1);
        showHP(nextPlayer.name, 'Розыгрыш приказов', () => setPhase('execution'));
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось передать ход');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function nextRoundViaAPI() {
  if (G.phase !== 'end-round') return;

  try {
    const res = await apiCall('/api/game/next-round', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      addLog(`Раунд ${G.round}. Первый ход: ${G.players[G.curP].name}`, -1);
      showHP(G.players[G.curP].name, 'Расстановка приказов', () => setPhase('order-placement'));
    } else {
      showMsg('Ошибка', res.error || 'Не удалось перейти к следующему раунду');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

// ══════════════════════════════════════════════
//  EVENT CARD PICKER
// ══════════════════════════════════════════════

function showEventCardPicker() {
  if (G.phase !== 'end-round') return;
  const selectionDone = G.event_selection_done || [false, false];
  if (selectionDone[G.curP]) return;

  const offered = (G.event_cards_offered || [[], []])[G.curP] || [];
  const playerName = G.players[G.curP].name;

  if (!offered.length) {
    // Нет карт — сразу отмечаем как готово (сервер обработает)
    return;
  }

  let cardsHtml = offered.map(card => `
    <div class="event-card-choice" onclick="selectEventCard('${card.name.replace(/'/g, "\\'")}')"
         style="padding:10px;background:rgba(0,200,255,.1);margin-bottom:8px;border-radius:6px;cursor:pointer;border:1px solid rgba(0,200,255,.2);">
      <div style="font-weight:bold;margin-bottom:4px;">${card.name}</div>
      <div style="font-size:.75rem;color:#aaa;margin-bottom:4px;">${card.card_type || ''}</div>
      <div style="font-size:.8rem;">${card.effect || ''}</div>
    </div>
  `).join('');

  const html = `
    <div style="margin-bottom:10px;color:#aaa;">Выберите одну карту для руки:</div>
    <div style="max-height:400px;overflow-y:auto;">${cardsHtml}</div>
  `;
  showMsg(`🃏 Карты событий — ${playerName}`, html);
}

async function selectEventCard(cardName) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/select-event-card', {
      player_id: G.curP,
      card_name: cardName
    });
    if (res.success) {
      const prevPlayer = G.curP;
      applyState(res.state);
      addLog(`${G.players[prevPlayer].name} взял карту событий`, prevPlayer);

      const selectionDone = G.event_selection_done || [false, false];
      if (!selectionDone.every(Boolean)) {
        // Второй игрок ещё не выбирал — hotpass, setPhase внутри колбека покажет пикер
        showHP(G.players[G.curP].name, 'Выбор карты события', () => setPhase('end-round'));
      } else {
        setPhase('end-round');  // Оба выбрали — покажет кнопку "Следующий раунд"
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось выбрать карту');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

// ══════════════════════════════════════════════
//  API BRIDGE (Python handles game logic)
// ══════════════════════════════════════════════

async function apiCall(endpoint, body = {}) {
  const r = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text();
    console.error(`API ${endpoint} → ${r.status}:`, text);
    return { success: false, error: `Сервер вернул ошибку ${r.status}` };
  }
  return r.json();
}

function applyState(newState) {
  // Сохраняем UI-only поля которые Python не знает
  const uiFields = ['selHandIdx', 'selUnitIdx', 'selUnitType', 'selStructIdx'];
  const saved = {};
  uiFields.forEach(k => { saved[k] = G[k]; });
  const prevPlayer = G.curP;
  Object.assign(G, newState);
  uiFields.forEach(k => { G[k] = saved[k]; });
  // Сбросить выбранный приказ при смене игрока
  if (G.curP !== prevPlayer) _selectedOrderForPlay = null;
  syncLog();
  renderBoard();
  renderSide();
  updateHeader();
}

async function _restoreGame(phase) {
  try {
    await apiCall('/api/game/clear-temp', {});
    const data = await apiCall('/api/game/restore', { state: G });
    if (data.success) {
      applyState(data.state);
      syncLog();
      if (phase === 'execution') {
        const player = G.players[G.curP];
        showHP(player.name, 'Розыгрыш приказов', () => setPhase('execution'));
      } else if (phase === 'end-round') {
        setPhase('end-round');
      }
    } else {
      showMsg('Ошибка восстановления', data.error || 'Не удалось восстановить игру');
    }
  } catch(e) {
    showMsg('Сервер недоступен', 'Запустите: uvicorn game_server:app --reload --port 8000');
  }
}

async function startStage2() {
  clearLog();
  addLog('Карта готова. Инициализация Stage 2...', -1);
  try {
    G.phase = 'order-placement';  // Установить фазу ДО отправки на сервер
    // Очистить старые snapshots перед новой игрой
    await apiCall('/api/game/clear-temp', {});
    const data = await apiCall('/api/game/init', { state: G });
    if (data.success) {
      applyState(data.state);
      addLog(`Stage 2 начат. Ход: ${G.players[G.curP].name}`, -1);
      setPhase('order-placement');

      // Автосохранение карты после инициализации (state уже обогащён Python)
      fetch(`${API_URL}/api/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: 'map_autosave', state: G })
      }).catch(() => {});
    } else {
      showMsg('Ошибка Stage 2', data.error || 'Неизвестная ошибка');
    }
  } catch(e) {
    showMsg('Сервер недоступен', 'Запустите: uvicorn game_server:app --reload --port 8000');
  }
}

// Init вызывается из game_engine.html после загрузки всех скриптов


// ══════════════════════════════════════════════
//  DEPLOY UI
// ══════════════════════════════════════════════

let _deployBasket = [];
let _deploySelectedUnit = null;
let _deploySelectedBuilding = null;

const _DEPLOY_UT = {
  infantry:'ground', marines:'ground', mechanized:'ground', elite:'ground',
  fighter:'space', destroyer:'space',
};
const _DEPLOY_COSTS = { factory: 2, bastion: 2, city: 3 };
const _DEPLOY_ICONS = { factory: '🏭', bastion: '🏯', city: '🏙' };

function showDeployUI() {
  const pd = G.pending_deploy;
  if (!pd) return;
  const step = pd.step;
  if      (step === 'buy_units')        _showDeployBuyUnits();
  else if (step === 'place_units')      _showDeployPlaceUnitsSide();
  else if (step === 'resolve_overflow') _showDeployResolveOverflow();
  else if (step === 'buy_building')     _showDeployBuyBuilding();
}

// ── Step: buy_units ────────────────────────────────────────────

function _showDeployBuyUnits() {
  _deployBasket = [];
  _renderDeployBuyUnitsModal();
}

function _renderDeployBuyUnitsModal() {
  const pd   = G.pending_deploy;
  const info = pd.deploy_info || {};
  const catalog  = info.unit_catalog || [];
  const capacity = info.capacity;
  const credits  = info.credits;
  const forge    = info.forge_tokens;
  const cash     = info.cash_tokens;

  // Compute basket totals
  let totalCred = 0, forgeSpent = 0, cashSpent = 0;
  const bPool = {};
  for (const item of _deployBasket) {
    const u = catalog.find(c => c.unit_key === item.unit_key);
    if (!u) continue;
    forgeSpent += (u.needs_tier_forge ? 1 : 0) + (u.cost_forge || 0);
    cashSpent  += item.use_cash ? 1 : 0;
    totalCred  += u.cost - (item.use_cash ? 2 : 0);
    bPool[item.unit_key] = (bPool[item.unit_key] || 0) + 1;
  }
  totalCred = Math.max(0, totalCred);

  const credLeft  = credits - totalCred;
  const forgeLeft = forge - forgeSpent;
  const cashLeft  = cash - cashSpent;
  const canConfirm = credLeft >= 0 && forgeLeft >= 0 && cashLeft >= 0 && _deployBasket.length <= capacity;

  const catalogHtml = catalog.map(u => {
    const inBasket  = bPool[u.unit_key] || 0;
    const remaining = u.pool_available - inBasket;
    const disabled  = !u.can_buy || remaining <= 0;
    const icon      = u.unitType === 'ground' ? '⚔' : '🚀';
    const tNote     = u.needs_tier_forge ? ' <span style="color:#ffb74d">[+1🔨]</span>' : '';
    const fNote     = u.cost_forge ? ` <span style="color:#ff8a65">+${u.cost_forge}🔨</span>` : '';
    return `
      <div style="display:flex;align-items:center;gap:8px;padding:6px 8px;
                  background:rgba(255,255,255,.05);margin-bottom:3px;border-radius:4px;
                  ${disabled ? 'opacity:.35;' : 'cursor:pointer;'}"
           ${disabled ? '' : `onclick="_deployAddUnit('${u.unit_key}')"`}>
        <span>${icon} T${u.tier}</span>
        <span style="flex:1">${u.name}</span>
        <span style="color:#4fc3f7">${u.cost}💰${fNote}${tNote}</span>
        <span style="color:#888;font-size:.8rem">пул:${remaining}</span>
      </div>`;
  }).join('');

  const basketHtml = _deployBasket.length
    ? _deployBasket.map((item, i) => {
        const u    = catalog.find(c => c.unit_key === item.unit_key);
        const name = u?.name || item.unit_key;
        return `
          <div style="display:flex;align-items:center;gap:6px;padding:4px 8px;
                      background:rgba(0,200,255,.1);margin-bottom:2px;border-radius:4px;">
            <span style="flex:1;font-size:.9rem">${name}</span>
            <label style="font-size:.8rem;display:flex;align-items:center;gap:4px;cursor:pointer;">
              <input type="checkbox" ${item.use_cash ? 'checked' : ''}
                     onchange="_deployToggleCash(${i},this.checked)"> cash −2
            </label>
            <button class="abtn bw" style="padding:1px 7px;font-size:.7rem"
                    onclick="_deployRemoveBasket(${i})">✕</button>
          </div>`;
      }).join('')
    : '<div style="color:#555;text-align:center;padding:6px;font-size:.85rem">Корзина пуста</div>';

  const html = `
    <div style="font-size:.8rem;color:#888;margin-bottom:8px;">
      Тайл: ${pd.tile_key} | capacity: ${capacity} | 💰${credits} 🔨${forge} cash:${cash}
    </div>
    <div style="max-height:190px;overflow-y:auto;margin-bottom:8px;">${catalogHtml}</div>
    <div style="font-weight:bold;font-size:.85rem;margin-bottom:4px;color:#4fc3f7">
      Корзина (${_deployBasket.length}/${capacity}):
    </div>
    <div style="margin-bottom:8px;">${basketHtml}</div>
    <div style="font-size:.85rem;margin-bottom:10px;">
      Итого: <span style="color:${credLeft<0?'#ff6b6b':'#69f0ae'}">${totalCred}💰</span>
      ${forgeSpent ? `<span style="color:${forgeLeft<0?'#ff6b6b':'#aaa'}"> ${forgeSpent}🔨</span>` : ''}
      ${cashSpent  ? `<span style="color:${cashLeft<0?'#ff6b6b':'#aaa'}"> ${cashSpent} cash</span>` : ''}
      &nbsp; Остаток: <span style="color:${credLeft<0?'#ff6b6b':'#aaa'}">${credLeft}💰</span>
      <span style="color:${forgeLeft<0?'#ff6b6b':'#aaa'}"> ${forgeLeft}🔨</span>
      <span style="color:${cashLeft<0?'#ff6b6b':'#aaa'}"> ${cashLeft} cash</span>
    </div>
    <button class="abtn bp" style="width:100%"
            ${canConfirm ? '' : 'disabled'}
            onclick="_deployConfirmBasket()">
      ${_deployBasket.length ? '✓ Купить юнитов' : '→ Пропустить юнитов'}
    </button>`;

  showMsg('🏗 Deploy — Покупка юнитов', html);
}

function _deployAddUnit(unitKey) {
  _deployBasket.push({ unit_key: unitKey, use_cash: false });
  _renderDeployBuyUnitsModal();
}
function _deployRemoveBasket(idx) {
  _deployBasket.splice(idx, 1);
  _renderDeployBuyUnitsModal();
}
function _deployToggleCash(idx, val) {
  if (_deployBasket[idx]) {
    _deployBasket[idx].use_cash = val;
    _renderDeployBuyUnitsModal();  // обновить итоги
  }
}

async function _deployConfirmBasket() {
  closeMsg();
  // Собрать актуальные значения use_cash из чекбоксов (на случай если не успело сработать onchange)
  try {
    const res = await apiCall('/api/game/deploy-confirm-basket', {
      player_id: G.curP,
      basket:    _deployBasket,
    });
    if (res.success) {
      _deployBasket = [];
      applyState(res.state);
      showDeployUI();
    } else {
      showMsg('Ошибка', res.error);
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

// ── Step: place_units — левая панель (без модала) ────────────

function _showDeployPlaceUnitsSide() {
  closeMsg();                // закрыть buy_units модал если открыт
  _deploySelectedUnit = null;
  setPhase('execution');     // обновит инструкцию и кнопки (btn-uu, btn-undo-order)
  // renderSide/renderBoard уже вызваны внутри setPhase
}

async function _deployUndoPlace() {
  const pd = G.pending_deploy;
  if (!pd || !pd.placed?.length) return;
  try {
    const res = await apiCall('/api/game/deploy-undo-place', { player_id: G.curP });
    if (res.success) {
      _deploySelectedUnit = null;
      applyState(res.state);
      // остаёмся в place_units — renderSide покажет обновлённую панель
    } else {
      showMsg('Ошибка', res.error);
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── Step: resolve_overflow ────────────────────────────────────

function _showDeployResolveOverflow() {
  const pd      = G.pending_deploy;
  const placed  = pd.placed || [];
  const info    = pd.deploy_info || {};
  const catalog = info.unit_catalog || [];
  const areas   = G.map[pd.tile_key]?.areas || [];
  const getName = k => catalog.find(c => c.unit_key === k)?.name || k;
  const UTR = {ground:{0:'infantry',1:'marines',2:'mechanized',3:'elite'},space:{0:'fighter',2:'destroyer'}};

  // compute counts
  const counts = {};
  areas.forEach((a, i) => { counts[i] = (a.troops || []).length; });
  placed.forEach(p => { counts[p.area_idx] = (counts[p.area_idx] || 0) + 1; });
  const overflows = Object.entries(counts).filter(([i, c]) => c > (areas[+i]?.capacity || 0)).map(([i]) => +i);

  let html = `<div style="color:#ff6b6b;margin-bottom:8px;">⚠ Переполнено: area[${overflows.join('], area[')}]</div>`;
  for (const aIdx of overflows) {
    const a   = areas[aIdx];
    const cap = a?.capacity || 0;
    const cnt = counts[aIdx];
    html += `<div style="margin-bottom:10px;"><strong>area[${aIdx}] ${a?.type} (${cnt}/${cap})</strong><br>`;

    // Map troops belonging to current player
    (a?.troops || []).filter(t => t.player === G.curP).forEach(t => {
      const uk = UTR[t.unitType]?.[t.tier] || `${t.unitType}T${t.tier}`;
      html += `<button class="abtn bw" style="margin:2px;"
                       onclick="_deployRemoveOverflow(${aIdx},'${uk}')">
                 ✕ ${getName(uk)} <span style="font-size:.75rem;color:#888">(карта)</span>
               </button>`;
    });
    // Placed units in this area
    placed.filter(p => p.area_idx === aIdx).forEach(p => {
      html += `<button class="abtn bw" style="margin:2px;"
                       onclick="_deployRemoveOverflow(${aIdx},'${p.unit_key}')">
                 ✕ ${getName(p.unit_key)} <span style="font-size:.75rem;color:#888">(новый)</span>
               </button>`;
    });
    html += '</div>';
  }
  showMsg('🏗 Deploy — Разрешение переполнения', html);
}

async function _deployRemoveOverflow(areaIdx, unitKey) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/deploy-resolve-overflow', {
      player_id:        G.curP,
      remove_area_idx:  areaIdx,
      remove_unit_key:  unitKey,
    });
    if (res.success) {
      applyState(res.state);
      showDeployUI();
    } else {
      showMsg('Ошибка', res.error);
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

// ── Step: buy_building — левая панель (без модала) ───────────

function _showDeployBuyBuilding() {
  closeMsg();
  _deploySelectedBuilding = null;
  setPhase('execution');  // renderSide/renderBoard вызовутся внутри
}

function _deploySelectBuilding(btype) {
  _deploySelectedBuilding = btype;
  renderSide();
  renderBoard();
}

async function _deploySkipBuilding() {
  closeMsg();
  try {
    const res = await apiCall('/api/game/deploy-skip-building', { player_id: G.curP });
    if (res.success) {
      _deploySelectedBuilding = null;
      applyState(res.state);
      addLog(`${G.players[G.curP]?.name}: Deploy завершён`, G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error);
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

// ── Map click handler for deploy ──────────────────────────────

async function deployAreaClick(key, displayIdx) {
  const pd = G.pending_deploy;
  if (!pd || pd.tile_key !== key) return;  // только тайл с приказом

  const tile = G.map[key];
  if (!tile) return;
  const area    = getAreaByDisplay(tile, displayIdx);
  const realIdx = tile.areas.indexOf(area);
  const step    = pd.step;

  if (step === 'place_units') {
    if (!_deploySelectedUnit) {
      showMsg('Deploy', 'Сначала выберите юнит в левой панели, затем кликните область.');
      return;
    }
    try {
      const res = await apiCall('/api/game/deploy-place-unit', {
        player_id: G.curP,
        unit_key:  _deploySelectedUnit,
        area_idx:  realIdx,
      });
      if (res.success) {
        _deploySelectedUnit = null;
        applyState(res.state);
        showDeployUI();
      } else {
        showMsg('Ошибка', res.error);
      }
    } catch(e) { showMsg('Ошибка сервера', e.message); }
    return;
  }

  if (step === 'buy_building') {
    if (!_deploySelectedBuilding) {
      showMsg('Deploy', 'Сначала выберите здание в левой панели, затем кликните планету.');
      return;
    }
    const useCash = document.getElementById('deploy-use-cash-panel')?.checked || false;
    try {
      const res = await apiCall('/api/game/deploy-buy-building', {
        player_id:     G.curP,
        building_type: _deploySelectedBuilding,
        area_idx:      realIdx,
        use_cash:      useCash,
      });
      if (res.success) {
        const bname = _deploySelectedBuilding;
        _deploySelectedBuilding = null;
        applyState(res.state);
        addLog(`${G.players[G.curP]?.name}: Deploy — ${bname} построена`, G.curP);
        setPhase('execution');
      } else {
        showMsg('Ошибка', res.error);
      }
    } catch(e) { showMsg('Ошибка сервера', e.message); }
  }
}

