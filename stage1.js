'use strict';
// ══════════════════════════════════════════════
//  STAGE 1: Setup, Tile Placement, Troops, Warp Storms
//  Этот файл не нужно читать при работе над Stage 2+
// ══════════════════════════════════════════════

function _facResHtml(f) {
  const parts = [];
  if (f.credits)  parts.push(`💰${f.credits}`);
  if (f.tokens?.support)  parts.push(`⊕${f.tokens.support}`);
  if (f.tokens?.discount) parts.push(`⊖${f.tokens.discount}`);
  if (f.tokens?.forge)    parts.push(`⚒${f.tokens.forge}`);
  if (f.structures?.length) {
    const counts = {};
    f.structures.forEach(s => { counts[s] = (counts[s] || 0) + 1; });
    Object.entries(counts).forEach(([s, n]) => {
      const info = STRUCTURE_INFO[s] || { icon:'?' };
      parts.push(`${info.icon}${n > 1 ? n : ''}`);
    });
  }
  if (!parts.length) return '';
  return parts.map(p => `<span style="background:rgba(255,255,255,.06);padding:1px 4px;border-radius:3px;">${p}</span>`).join('');
}

function buildFactionUI() {
  [0,1].forEach(pi => {
    const cont = document.getElementById(`p${pi+1}-factions`);
    cont.innerHTML = '';
    FACTIONS.forEach(f => {
      const btn = document.createElement('div');
      btn.className = 'faction-btn';
      btn.dataset.fid = f.id;
      const resHtml = _facResHtml(f);
      btn.innerHTML = `<span class="fi">${f.icon}</span><div class="fn">${f.name}</div><div class="ff">${f.flavor}</div><div class="fres">${resHtml}</div>`;
      btn.onclick = () => pickFaction(pi, f.id);
      cont.appendChild(btn);
    });
  });
  G.players[0].faction = 'chaos';
  G.players[1].faction = 'marine';
  refreshFactionUI();
}

function pickFaction(pi, fid) {
  if (G.players[1-pi].faction === fid) return;
  G.players[pi].faction = fid;
  refreshFactionUI();
}

function refreshFactionUI() {
  [0,1].forEach(pi => {
    const other = G.players[1-pi].faction;
    document.querySelectorAll(`#p${pi+1}-factions .faction-btn`).forEach(btn => {
      btn.classList.remove('sel1','sel2','taken');
      const fac = FACTIONS.find(f => f.id === btn.dataset.fid);
      const col = fac?.color || '#888888';

      if (btn.dataset.fid === G.players[pi].faction) {
        // Выбрана: полный цвет фракции, текст инвертируется при необходимости
        btn.style.background   = col;
        btn.style.borderColor  = col;
        btn.style.color        = getTextColor(col);
        btn.classList.add(pi===0?'sel1':'sel2');
      } else if (btn.dataset.fid === other) {
        // Занята другим игроком: приглушённый цвет
        btn.style.background   = hexAlpha(col, 0.08);
        btn.style.borderColor  = hexAlpha(col, 0.25);
        btn.style.color        = '';
        btn.classList.add('taken');
      } else {
        // Обычное состояние: мягкий цветной фон + цветная рамка
        btn.style.background   = hexAlpha(col, 0.13);
        btn.style.borderColor  = hexAlpha(col, 0.55);
        btn.style.color        = col;
      }
    });
  });
}

// ══════════════════════════════════════════════
//  START
// ══════════════════════════════════════════════
function pickFirstPlayer(pi) {
  document.getElementById('fp-lbl-0').classList.toggle('active', pi === 0);
  document.getElementById('fp-lbl-1').classList.toggle('active', pi === 1);
  document.querySelector(`input[name="first-player"][value="${pi}"]`).checked = true;
}

function startGame() {
  if (!G.players[0].faction || !G.players[1].faction) { showMsg('Выберите фракции','Оба игрока должны выбрать фракцию.'); return; }
  G.players[0].name = document.getElementById('p1-name').value.trim() || 'Alpha';
  G.players[1].name = document.getElementById('p2-name').value.trim() || 'Omega';

  // Первый игрок
  const fpVal = parseInt(document.querySelector('input[name="first-player"]:checked')?.value ?? '0');
  G.firstPlayer = fpVal;
  G.curP = fpVal;

  // Применяем цвета выбранных фракций как CSS-переменные игроков
  const f1 = FACTIONS.find(f => f.id === G.players[0].faction);
  const f2 = FACTIONS.find(f => f.id === G.players[1].faction);
  document.documentElement.style.setProperty('--p1', f1?.color || '#00c8ff');
  document.documentElement.style.setProperty('--p2', f2?.color || '#ff4d6d');

  // Раздаём тайлы из каталога: каждому игроку 1 домашний (свой для фракции) + (TILES_PP-1) обычных
  const normalTiles = [...TILE_CATALOG.filter(t => !t.isHome)].sort(() => Math.random()-.5);

  G.players.forEach((p, pi) => {
    const fac = FACTIONS.find(f => f.id === p.faction);
    p.pool = [];
    // Добавляем юниты с правильными уровнями из unitTiers
    if (fac.unitTiers?.ground && Array.isArray(fac.unitTiers.ground)) {
      fac.unitTiers.ground.forEach(tier => p.pool.push({ id:nextId++, player:pi, unitType:'ground', tier }));
    }
    if (fac.unitTiers?.space && Array.isArray(fac.unitTiers.space)) {
      fac.unitTiers.space.forEach(tier => p.pool.push({ id:nextId++, player:pi, unitType:'space', tier }));
    }
    // Добавляем структуры (фабрики из structures массива)
    p.structurePool = [];
    if (Array.isArray(fac.structures)) {
      fac.structures.forEach(type => p.structurePool.push({ id:nextId++, player:pi, type }));
    }
    p.credits = fac.credits ?? 6;
    p.tokens  = { ...(fac.tokens ?? {support:0,discount:0,forge:0}) };

    // Карты загрузятся с сервера асинхронно
    p.hand_battle_cards = [];
    p.available_battle_cards = [];
    p.hand_order_upgrades = [];
    p.available_order_upgrades = [];
    p.hand_event_cards = [];
    p.available_event_cards = [];
    p.boughtUpgrades = [];

    // Загрузить карты фракции с сервера
    fetch(`${API_URL}/api/faction-cards/${p.faction}`)
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          p.hand_battle_cards = data.hand_battle_cards;
          p.available_battle_cards = data.available_battle_cards;
          p.hand_order_upgrades = data.hand_order_upgrades;
          p.available_order_upgrades = data.available_order_upgrades;
          p.hand_event_cards = data.hand_event_cards;
          p.available_event_cards = data.available_event_cards;
        }
      })
      .catch(() => {});

    // Инициализируем приказы (2 dominate, 2 deploy, 2 advance, 2 strategize)
    p.hand_orders = [
      { id:`p${pi+1}_dominate_1`, type:'dominate', owner:pi },
      { id:`p${pi+1}_dominate_2`, type:'dominate', owner:pi },
      { id:`p${pi+1}_deploy_1`, type:'deploy', owner:pi },
      { id:`p${pi+1}_deploy_2`, type:'deploy', owner:pi },
      { id:`p${pi+1}_advance_1`, type:'advance', owner:pi },
      { id:`p${pi+1}_advance_2`, type:'advance', owner:pi },
      { id:`p${pi+1}_strategize_1`, type:'strategize', owner:pi },
      { id:`p${pi+1}_strategize_2`, type:'strategize', owner:pi },
    ];
    const myHome = TILE_CATALOG.find(t => t.id === fac.homeTileId)
                || TILE_CATALOG.find(t => t.isHome);
    const myNormal = normalTiles.splice(0, TILES_PP - 1);
    p.hand = [myHome, ...myNormal].map((td, t) => ({
      handIdx:   t,
      tileDefId: td.id,
      tileId:    nextId++,
      isHome:    td.isHome,
      placed:    false,
    }));
  });

  // G.firstPlayer и G.curP уже заданы выше
  showScreen('game-screen');
  updateHeader();
  renderBoard();
  showHP(G.players[G.firstPlayer].name, 'Разместите вашу первую систему', () => setPhase('tile-placement'));
}

// ══════════════════════════════════════════════
//  TILE PLACEMENT
// ══════════════════════════════════════════════
function selectHandTile(idx) {
  if (G.phase !== 'tile-placement') return;
  if (G.players[G.curP].hand[idx].placed) return;
  G.selHandIdx = idx;
  _cancelTileHover(); _cancelTileHideTimer(); _dismissTilePreview();
  renderSide(); renderBoard();
}

function getValidDrops() {
  const placed = Object.values(G.map);
  if (!placed.length) return [{col:0,row:0}];
  const cands = new Set();
  placed.forEach(({col,row}) => {
    [[0,1],[0,-1],[1,0],[-1,0]].forEach(([dc,dr]) => {
      const k = `${col+dc},${row+dr}`;
      if (!G.map[k]) cands.add(k);
    });
  });
  const valid = [];
  cands.forEach(k => {
    const [nc,nr] = k.split(',').map(Number);
    const cols = placed.map(t=>t.col).concat([nc]);
    const rows = placed.map(t=>t.row).concat([nr]);
    const w = Math.max(...cols)-Math.min(...cols)+1;
    const h = Math.max(...rows)-Math.min(...rows)+1;
    if ((w<=3&&h<=2)||(w<=2&&h<=3)) valid.push({col:nc,row:nr});
  });
  return valid;
}

function dropTile(col, row) {
  if (G.selHandIdx === null) { showMsg('Выберите систему','Сначала выберите систему из руки.'); return; }
  const cp = G.players[G.curP];
  const ht = cp.hand[G.selHandIdx];
  if (!ht || ht.placed) return;

  const key = `${col},${row}`;
  const tileDef  = TILE_CATALOG.find(t => t.id === ht.tileDefId) || TILE_CATALOG[0];
  const sideData = tileDef.sides[0];

  ht.placed = true;
  G.tilesPlaced++;

  // Build tile object — areas with capacity, income, tokens, troops
  G.map[key] = {
    key, col, row,
    owner:     G.curP,
    isHome:    ht.isHome,
    tileId:    ht.tileId,
    tileDefId: ht.tileDefId,
    rotation:  0,
    side:      0,
    areas:     tileDefToAreas(sideData).map(a => ({ ...a, structures:[] })),
    needsObjective: Object.values(G.map).filter(t => t.owner === G.curP).length < 2,  // первые два тайла игрока получают метку цели
    objectiveMarker: null,               // { owner: playerIdx, realAreaIdx: N }
  };
  G.lastKey     = key;

  // Set undo snapshot BEFORE calling setPhase
  G.tileSnap      = { handIdx: G.selHandIdx, key };
  G.unitsPlaced   = [];
  G.structsPlaced = [];
  G.selHandIdx  = null;

  addLog(`${cp.name} разместил${ht.isHome?' домашнюю':''} систему [${key}]`, G.curP);

  _afterTilePlaced();
}

// ══════════════════════════════════════════════
//  UNDO TILE  — fully self-contained, no setPhase call for cleanup
// ══════════════════════════════════════════════
function undoTile() {
  if (G.phase !== 'tile-placement' && G.phase !== 'troop-on-tile') return;
  if (!G.tileSnap) { showMsg('Нечего отменять','Нет активного тайла для возврата.'); return; }

  const cp   = G.players[G.curP];
  const snap = G.tileSnap;  // local copy before we clear state

  // 1. Return all units placed this turn to pool
  for (const rec of G.unitsPlaced) {
    const tile = G.map[rec.key];
    if (!tile) continue;
    const area = tile.areas[rec.realAreaIdx];
    if (!area) continue;
    const idx = area.troops.findIndex(t => t.id === rec.unitId);
    if (idx >= 0) { cp.pool.push(area.troops.splice(idx, 1)[0]); }
  }
  // Return all structures placed this turn to pool
  for (const rec of G.structsPlaced) {
    const tile = G.map[rec.key];
    if (!tile) continue;
    const area = tile.areas[rec.realAreaIdx];
    if (!area) continue;
    if (!area.structures) area.structures = [];
    const idx = area.structures.findIndex(s => s.id === rec.structId);
    if (idx >= 0) { cp.structurePool.push(area.structures.splice(idx, 1)[0]); }
  }

  // 2. Remove tile from map, restore to hand
  delete G.map[snap.key];
  cp.hand[snap.handIdx].placed = false;
  G.tilesPlaced--;

  // 3. Clear undo state
  G.tileSnap      = null;
  G.unitsPlaced   = [];
  G.structsPlaced = [];
  G.lastKey     = null;

  addLog(`${cp.name} вернул систему [${snap.key}] в руку`, G.curP);

  // 4. Go back to tile-placement (this WILL clear snap/unitsPlaced again — harmless)
  setPhase('tile-placement');
}

// ══════════════════════════════════════════════
//  TILE ROTATION
// ══════════════════════════════════════════════
function rotateTile(cw) {
  if (!G.lastKey) return;
  const tile = G.map[G.lastKey];
  if (!tile) return;
  tile.rotation = cw ? (tile.rotation + 90) % 360 : (tile.rotation + 270) % 360;
  addLog(`Поворот [${tile.key}] ${cw?'по ч.':'пр. ч.'} → ${tile.rotation}°`, G.curP);
  renderBoard();
}

function flipTile() {
  if (!G.lastKey) return;
  const tile = G.map[G.lastKey];
  if (!tile) return;
  if (G.unitsPlaced.length > 0 || G.structsPlaced.length > 0) {
    showMsg('Нельзя перевернуть', 'Сначала верните все размещённые войска и постройки.');
    return;
  }
  const tileDef = TILE_CATALOG.find(t => t.id === tile.tileDefId);
  if (!tileDef || tileDef.sides.length < 2) {
    showMsg('Нельзя перевернуть', 'У этого тайла нет оборотной стороны.');
    return;
  }
  tile.side = 1 - (tile.side || 0);
  const sideData = tileDef.sides[tile.side];
  tile.areas    = tileDefToAreas(sideData).map(a => ({...a, structures: []}));
  tile.rotation = 0;
  tile.objectiveMarker = null; // сбрасываем метку при перевороте (areas полностью пересоздаются)
  G.selStructIdx = null; G.selUnitIdx = null; G.selUnitType = null;
  addLog(`${G.players[G.curP].name} перевернул тайл [${tile.key}] → сторона ${tile.side===0?'A':'B'}`, G.curP);
  renderBoard();
  renderSide();
}

// ── СОХРАНЕНИЕ КАРТЫ ─────────────────────────────────────────────────────────
function exportMap() {
  const mapData = {
    saved_at:     new Date().toISOString(),
    round:        G.round,
    total_rounds: G.totalRounds,
    players:      G.players.map((p,pi) => ({
      id: pi, name: p.name, faction: p.faction,
    })),
    tiles: Object.values(G.map).map(tile => ({
      key:       tile.key,
      col:       tile.col,
      row:       tile.row,
      tileDefId: tile.tileDefId,
      isHome:    tile.isHome,
      owner:     tile.owner,
      rotation:  tile.rotation,
      side:      tile.side || 0,
      areas:     tile.areas.map((a, ai) => ({
        index:    ai,
        type:     a.type,
        capacity: a.capacity,
        income:   a.income,
        valuable: a.valuable,
        support:  a.support,
        discount: a.discount,
        forge:    a.forge,
        joker:    a.joker,
        troops:   a.troops.map(u => ({ player:u.player, unitType:u.unitType })),
      })),
    })),
  };
  const blob = new Blob([JSON.stringify(mapData, null, 2)], { type:'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `stellar_conflict_map_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  addLog('Карта сохранена в файл.', -1);
}

// ══════════════════════════════════════════════
//  AFTER TILE PLACED
// ══════════════════════════════════════════════
function _afterTilePlaced() {
  // Always go to troop-on-tile first — endTurn() handles the next step
  setPhase('troop-on-tile');
}

// ══════════════════════════════════════════════
//  AREA CLICK (stub — no unit placement)
// ══════════════════════════════════════════════
function areaClick(key, displayIdx) {
  // Делегировать в advance если активен
  if (G.pending_advance && typeof advanceAreaClick === 'function') {
    advanceAreaClick(key, displayIdx);
    return;
  }
  // Делегировать в deploy если активен
  if (G.pending_deploy && typeof deployAreaClick === 'function') {
    deployAreaClick(key, displayIdx);
    return;
  }
  if (G.phase !== 'troop-on-tile') return;
  if (key !== G.lastKey) { showMsg('Другой тайл', 'Размещайте войска только на только что поставленной системе.'); return; }

  const cp = G.players[G.curP];
  const tile = G.map[key];
  if (!tile) return;
  const area = getAreaByDisplay(tile, displayIdx);
  const realIdx = tile.areas.indexOf(area);

  // Разместить / переместить метку цели (если ничего не выбрано)
  if (tile.needsObjective && G.selUnitIdx === null && G.selStructIdx === null) {
    const eligibleIdxs = getObjectiveEligibleDisplayIdxs(tile);
    if (eligibleIdxs.includes(displayIdx)) {
      if (area.type !== 'planet') return; // только планеты
      tile.objectiveMarker = { owner: 1 - G.curP, realAreaIdx: realIdx };
      addLog(`${cp.name} разместил метку цели на [${key}] зона ${displayIdx+1}`, G.curP);
      setPhase('troop-on-tile'); // обновить подсказку
      return;
    }
  }

  // Разместить постройку
  if (G.selStructIdx !== null) {
    const struct = cp.structurePool[G.selStructIdx];
    if (!struct) return;
    if (area.type !== 'planet') { showMsg('Только планеты', 'Постройки размещаются только на планетах (🪐).'); return; }
    if (!area.structures) area.structures = [];
    if (area.structures.length > 0) { showMsg('Занято', 'На этой планете уже есть постройка.'); return; }
    area.structures.push(struct);
    cp.structurePool.splice(G.selStructIdx, 1);
    G.structsPlaced.push({ key, realAreaIdx: realIdx, structId: struct.id, _seq: nextId++ });
    const info = STRUCTURE_INFO[struct.type] || { icon:'?', label:struct.type };
    addLog(`${cp.name} → [${key}] зона ${displayIdx+1} (${info.icon} ${info.label})`, G.curP);
    G.selStructIdx = null;
    renderSide(); renderBoard(G.lastKey);
    return;
  }

  // Разместить юнита
  if (G.selUnitIdx === null) return;
  const unit = cp.pool[G.selUnitIdx];
  if (!unit) return;
  if (!isCompatible(unit, area.type)) {
    showMsg('Несовместимо', unit.unitType === 'ground' ? 'Наземные войска — только на планеты 🪐.' : 'Космические войска — только в космос ✦.');
    return;
  }
  if (area.troops.length >= area.capacity) { showMsg('Переполнено', `Максимальная вместимость: ${area.capacity}.`); return; }
  area.troops.push(unit);
  cp.pool.splice(G.selUnitIdx, 1);
  G.unitsPlaced.push({ key, realAreaIdx: realIdx, unitId: unit.id, _seq: nextId++ });
  addLog(`${cp.name} → [${key}] зона ${displayIdx+1} (${unit.unitType === 'ground' ? '▲' : '◈'} T${unit.tier ?? 0})`, G.curP);
  G.selUnitIdx = null; G.selUnitType = null;
  renderSide(); renderBoard(G.lastKey);
}

// ══════════════════════════════════════════════
//  TURN TRANSITIONS
// ══════════════════════════════════════════════
function endTurn() {
  if (G.phase !== 'troop-on-tile') return;
  const cp = G.players[G.curP];

  // На последнем тайле — обязательно разместить все войска, которые туда помещаются
  const myTilesPlaced = Object.values(G.map).filter(t => t.owner === G.curP).length;
  if (myTilesPlaced >= TILES_PP && cp.pool.length > 0) {
    const tile = G.map[G.lastKey];
    const canPlace = tile && cp.pool.some(u =>
      getRotatedAreas(tile).some(a => isCompatible(u, a.type) && a.troops.length < a.capacity)
    );
    if (canPlace) {
      showMsg('Разместите войска', 'Это ваш последний тайл — разместите все войска, которые сюда помещаются.');
      return;
    }
  }

  // Метка цели обязательна на первых двух тайлах
  const tileForObj = G.map[G.lastKey];
  if (tileForObj?.needsObjective && !tileForObj.objectiveMarker) {
    showMsg('Разместите метку цели', 'Поставьте метку цели соперника — кликните на область тайла без выбранного войска.');
    return;
  }

  G.tileSnap = null; G.unitsPlaced = []; G.structsPlaced = [];
  G.selUnitIdx = null; G.selUnitType = null; G.selStructIdx = null;

  if (G.tilesPlaced < TILES_PP * 2) {
    G.curP = 1 - G.curP;
    showHP(G.players[G.curP].name, 'Разместите систему', () => setPhase('tile-placement'));
  } else {
    startWarpStormPlacement();
  }
}

// ORDER PLACEMENT — логика перенесена в Python (Stage 2)
// Функции apiCall / applyState / startStage2 находятся ниже перед INIT

// ══════════════════════════════════════════════
//  UNIT PLACEMENT
// ══════════════════════════════════════════════
function selectUnitFromPool(idx) {
  if (G.phase !== 'troop-on-tile') return;
  G.selUnitIdx  = idx;
  G.selUnitType = G.players[G.curP].pool[idx]?.unitType || null;
  G.selStructIdx = null;
  renderSide(); renderBoard(G.lastKey);
}

function selectStructFromPool(idx) {
  if (G.phase !== 'troop-on-tile') return;
  G.selStructIdx = idx;
  G.selUnitIdx   = null;
  G.selUnitType  = null;
  renderSide(); renderBoard(G.lastKey);
}

function undoLastUnit() {
  if (G.pending_deploy?.step === 'place_units' && typeof _deployUndoPlace === 'function') {
    _deployUndoPlace();
    return;
  }
  if (G.phase !== 'troop-on-tile') return;
  const cp = G.players[G.curP];
  const lastUnitSeq   = G.unitsPlaced.length  > 0 ? (G.unitsPlaced[G.unitsPlaced.length-1]._seq   ?? -1) : -1;
  const lastStructSeq = G.structsPlaced.length > 0 ? (G.structsPlaced[G.structsPlaced.length-1]._seq ?? -1) : -1;

  if (G.structsPlaced.length > 0 && lastStructSeq > lastUnitSeq) {
    const rec  = G.structsPlaced.pop();
    const tile = G.map[rec.key];
    if (tile) {
      const area = tile.areas[rec.realAreaIdx];
      if (!area.structures) area.structures = [];
      const idx = area.structures.findIndex(s => s.id === rec.structId);
      if (idx >= 0) {
        const s = area.structures.splice(idx, 1)[0];
        cp.structurePool.push(s);
        const info = STRUCTURE_INFO[s.type] || { icon:'?', label:s.type };
        addLog(`${cp.name} вернул ${info.icon}${info.label}`, G.curP);
      }
    }
  } else if (G.unitsPlaced.length > 0) {
    const rec  = G.unitsPlaced.pop();
    const tile = G.map[rec.key];
    if (tile) {
      const area = tile.areas[rec.realAreaIdx];
      const idx  = area.troops.findIndex(t => t.id === rec.unitId);
      if (idx >= 0) {
        cp.pool.push(area.troops.splice(idx, 1)[0]);
        addLog(`${cp.name} вернул юнита`, G.curP);
      }
    }
  } else {
    showMsg('Нечего отменять', 'Нет размещённых войск для возврата.');
    return;
  }
  G.selUnitIdx = null; G.selUnitType = null; G.selStructIdx = null;
  renderSide(); renderBoard(G.lastKey);
}

// ══════════════════════════════════════════════
//  ISCOMPATIBLE (kept for undoTile internal use)
// ══════════════════════════════════════════════
function isCompatible(unit, areaType) {
  return (unit.unitType==='ground' && areaType==='planet') ||
         (unit.unitType==='space'  && areaType==='space');
}

// ══════════════════════════════════════════════
//  OBJECTIVE MARKER HELPERS
// ══════════════════════════════════════════════
// Возвращает displayIdx областей тайла, на которые можно ставить метку цели.
// Нормальный тайл (2 планеты): обе планеты.
// Домашний тайл (3 планеты + 1 космос): планеты, соседствующие с космосом по горизонтали/вертикали.
function getObjectiveEligibleDisplayIdxs(tile) {
  const areas = getRotatedAreas(tile);
  const planetIdxs = areas.map((a,i) => ({a,i})).filter(x => x.a.type === 'planet').map(x => x.i);
  if (planetIdxs.length <= 2) return planetIdxs;
  // 3 планеты + 1 космос: исключить планету, диагональную к космосу
  const spaceIdx = areas.findIndex(a => a.type === 'space');
  const diagonal = { 0:3, 1:2, 2:1, 3:0 };
  const diagOfSpace = diagonal[spaceIdx];
  return planetIdxs.filter(i => i !== diagOfSpace);
}

// ══════════════════════════════════════════════
//  WARP STORM PLACEMENT
// ══════════════════════════════════════════════
function startWarpStormPlacement() {
  G.warpStorms = [];
  G.warpStormStep = 0;
  G.warpConfirmed = [false, false];
  // Второй игрок (не первый) ставит варп-шторм первым
  G.curP = 1 - G.firstPlayer;
  renderBoard(); updateHeader();
  showHP(G.players[G.curP].name, 'Разместите варп-шторм', () => setPhase('warp-storm'));
}

function placeWarpStorm(tileKey, side) {
  if (G.phase !== 'warp-storm') return;
  // Нельзя ставить туда, где уже стоит варп-шторм
  if (G.warpStorms.some(ws => ws.tileKey === tileKey && ws.side === side)) return;
  // Нельзя ставить если уже разместил свой
  if (G.warpStorms.some(ws => ws.owner === G.curP)) return;
  // Нельзя ставить если уже подтвердил
  if (G.warpConfirmed[G.curP]) return;

  G.warpStorms.push({ tileKey, side, owner: G.curP });
  addLog(`${G.players[G.curP].name} поставил варп-шторм: [${tileKey}] ${side}`, G.curP);
  setPhase('warp-storm');
}

function undoWarpStorm() {
  if (G.phase !== 'warp-storm') return;
  const idx = G.warpStorms.findIndex(ws => ws.owner === G.curP);
  if (idx === -1) return;
  G.warpStorms.splice(idx, 1);
  G.warpConfirmed[G.curP] = false;
  addLog(`${G.players[G.curP].name} отменил варп-шторм`, G.curP);
  setPhase('warp-storm');
}

function confirmWarpStorm() {
  if (G.phase !== 'warp-storm') return;
  if (!G.warpStorms.some(ws => ws.owner === G.curP)) return;
  G.warpConfirmed[G.curP] = true;
  addLog(`${G.players[G.curP].name} подтвердил варп-шторм`, G.curP);

  // Проверяем: оба подтвердили?
  if (G.warpConfirmed[0] && G.warpConfirmed[1]) {
    // Оба подтвердили — автосохранение карты + переход к приказам
    addLog('Варп-штормы установлены. Переход к приказам...', -1);
    G.curP = G.firstPlayer;
    G.ordersPlaced = [0, 0];
    G.orders = [];
    renderBoard(); updateHeader();

    startStage2();
  } else {
    // Передаём ход второму игроку
    G.curP = 1 - G.curP;
    updateHeader();
    const myStorm = G.warpStorms.find(ws => ws.owner === G.curP);
    if (myStorm && G.warpConfirmed[G.curP]) {
      // Второй уже подтвердил (не должно случиться, но на всякий)
    } else if (myStorm) {
      // Уже разместил, но не подтвердил
      showHP(G.players[G.curP].name, 'Подтвердите варп-шторм', () => setPhase('warp-storm'));
    } else {
      // Ещё не разместил
      showHP(G.players[G.curP].name, 'Разместите варп-шторм', () => setPhase('warp-storm'));
    }
  }
}

// ══════════════════════════════════════════════
//  END MAP DIALOG
// ══════════════════════════════════════════════
function showEndMapDialog() {
  const modal = document.getElementById('msg-modal');
  modal.querySelector('#msg-title').textContent = 'Карта сформирована';
  modal.querySelector('#msg-body').innerHTML = 'Все системы расставлены.<br><br>Завершить игру?';
  const btns = modal.querySelector('.mbtns');
  btns.innerHTML = `
    <button class="abtn br" onclick="closeMsgAndRestart()">Да — начать заново</button>
    <button class="abtn bp" onclick="closeMsgModal()">Нет — остаться на карте</button>
  `;
  modal.classList.add('active');
}
function closeMsgModal() {
  document.getElementById('msg-modal').classList.remove('active');
  renderBoard(); updateHeader();
}
function closeMsgAndRestart() {
  document.getElementById('msg-modal').classList.remove('active');
  restartGame();
}

// ══════════════════════════════════════════════
//  RESTART
// ══════════════════════════════════════════════
function restartGame() {
  document.documentElement.style.setProperty('--p1', '#00c8ff');
  document.documentElement.style.setProperty('--p2', '#ff4d6d');
  nextId=0; G=makeState(); buildFactionUI(); showScreen('setup-screen');
}

let _tileHoverTimer = null;
let _tileHideTimer = null;
function _startTileHover(el, tileDefId) {
  _cancelTileHideTimer();
  _tileHoverTimer = setTimeout(() => { _showTilePreviewPopup(el, tileDefId); _tileHoverTimer = null; }, 1000);
}
function _cancelTileHover() {
  if (_tileHoverTimer) { clearTimeout(_tileHoverTimer); _tileHoverTimer = null; }
  _scheduleTileHide();
}
function _cancelTileHideTimer() {
  if (_tileHideTimer) { clearTimeout(_tileHideTimer); _tileHideTimer = null; }
}
function _scheduleTileHide() {
  _cancelTileHideTimer();
  _tileHideTimer = setTimeout(() => { _dismissTilePreview(); _tileHideTimer = null; }, 1000);
}
function _dismissTilePreview() {
  const old = document.getElementById('tile-peek-popup'); if (old) old.remove();
}
function _showTilePreviewPopup(anchorEl, tileDefId) {
  const old = document.getElementById('tile-peek-popup'); if (old) old.remove();
  const tileDef = TILE_CATALOG.find(t => t.id === tileDefId); if (!tileDef) return;
  const areas = tileDefToAreas(tileDef.sides[0]);
  const pop = document.createElement('div');
  pop.id = 'tile-peek-popup';
  pop.style.cssText = 'position:fixed;z-index:900;background:var(--panel);border:2px solid var(--gold);border-radius:12px;padding:14px;box-shadow:0 0 28px rgba(255,215,0,.3);';
  const ttl = document.createElement('div');
  ttl.style.cssText = "font-family:'Orbitron',monospace;font-size:.6rem;color:var(--gold);letter-spacing:.2em;margin-bottom:8px;text-align:center;";
  ttl.textContent = tileDef.isHome ? 'ДОМАШНИЙ МИР' : 'СИСТЕМА';
  pop.appendChild(ttl);
  const grid = document.createElement('div'); grid.className = 'tile-peek-grid';
  areas.forEach(a => {
    const c = document.createElement('div');
    c.className = 'tile-peek-cell ' + a.type;
    if (a.type === 'planet') {
      let html = `<div>🪐</div><div>${'●'.repeat(a.capacity||2)}</div>`;
      if (a.income>0) html += `<div class="inc-mark">+${a.income}</div>`;
      if (a.support) html += `<div class="tok-sup">П</div>`;
      if (a.discount) html += `<div class="tok-dis">С</div>`;
      if (a.forge) html += `<div class="tok-frg">М</div>`;
      if (a.joker) html += `<div class="tok-jok">Д</div>`;
      c.innerHTML = html;
    } else { c.innerHTML = '<div style="font-size:1.2rem;color:var(--dim)">✦</div>'; }
    grid.appendChild(c);
  });
  pop.appendChild(grid);
  const hint = document.createElement('div');
  hint.style.cssText = 'color:var(--dim);font-size:.6rem;text-align:center;margin-top:6px;';
  hint.textContent = 'Нажмите для закрытия';
  pop.appendChild(hint);
  pop.onclick = () => { _cancelTileHideTimer(); pop.remove(); };
  pop.addEventListener('mouseenter', _cancelTileHideTimer);
  pop.addEventListener('mouseleave', _scheduleTileHide);
  document.body.appendChild(pop);
  const rect = anchorEl.getBoundingClientRect();
  let lft = rect.right + 8, top = rect.top;
  if (lft + 250 > window.innerWidth) lft = rect.left - 250;
  if (top + 270 > window.innerHeight) top = window.innerHeight - 275;
  pop.style.left = Math.max(0, lft) + 'px';
  pop.style.top = Math.max(0, top) + 'px';
}
