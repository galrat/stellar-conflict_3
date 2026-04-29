

let _advanceSelectedShip    = null;
let _advanceSelectedGround  = null;
let _advanceOrbitalShipArea = null;

function _advanceClearSelection() {
  _advanceSelectedShip    = null;
  _advanceSelectedGround  = null;
  _advanceOrbitalShipArea = null;
}

function _resetAdvanceUI() {
  _advanceClearSelection();
}

function showAdvanceUI() {
  const pa = G.pending_advance;
  if (!pa) {
    setPhase('execution');
    return;
  }
  setPhase('execution');
  if (pa.step === 'orbital_defend') {
    _showAdvanceOrbitalDefendModal();
  } else if (pa.step === 'capacity_overflow') {
    _showOverflowModal();
  } else if (pa.step === 'combat_declare') {
    _showCombatDeclareModal();
  }
}

// ── choose_source ──────────────────────────────────────────────

async function _advanceChooseSource(sourceTileKey) {
  try {
    const res = await apiCall('/api/game/advance-choose-source', {
      player_id:       G.curP,
      source_tile_key: sourceTileKey || null,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Не удалось выбрать источник');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── ships ──────────────────────────────────────────────────────

function _advanceSelectShip(ship) {
  const same = _advanceSelectedShip?.ship_id === ship.ship_id;
  _advanceSelectedShip = same ? null : ship;
  renderSide(); renderBoard();
}

async function _advanceMoveShip(shipId, toAreaIdx) {
  try {
    const res = await apiCall('/api/game/advance-move-ship', {
      player_id:   G.curP,
      ship_id:     shipId,
      to_area_idx: toAreaIdx,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      renderBoard();
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Нельзя переместить корабль');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

async function _advanceNextStep() {
  try {
    const res = await apiCall('/api/game/advance-next-step', { player_id: G.curP });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error);
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── ground ─────────────────────────────────────────────────────

function _advanceSelectGround(unit) {
  const same = _advanceSelectedGround?.ground_id === unit.ground_id;
  _advanceSelectedGround = same ? null : unit;
  renderSide(); renderBoard();
}

async function _advanceMoveGround(groundId, toAreaIdx) {
  try {
    const res = await apiCall('/api/game/advance-move-ground', {
      player_id:   G.curP,
      ground_id:   groundId,
      to_area_idx: toAreaIdx,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      renderBoard();
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Нельзя переместить юнита');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

async function _advanceNextStepUI() {
  const pa = G.pending_advance;
  if (!pa) return;

  const step = pa.step;
  if (step === 'choose_source') {
    // Skip source selection
    _advanceChooseSource(null);
  } else if (step === 'ships') {
    // Move to ground step
    _advanceNextStep();
  }
}

async function _advanceCommit() {
  try {
    const res = await apiCall('/api/game/advance-commit', { player_id: G.curP });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Нельзя зафиксировать');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── combat_declare ─────────────────────────────────────────────

function _showCombatDeclareModal() {
  const pa = G.pending_advance;
  if (!pa) return;

  const areaIdx = pa.contest_area_idx;
  const tile = G.map?.[pa.tile_key];
  if (!tile) return;
  const area = tile.areas?.[areaIdx];
  if (!area) return;

  const attackerIdx = pa.player_id;
  const defenderIdx = 1 - attackerIdx;

  const attacker = G.players[attackerIdx];
  const attackerFac = FACTIONS.find(f => f.id === attacker.faction);
  const attackerColor = attackerFac?.color || (attackerIdx === 0 ? '#00c8ff' : '#ff4d6d');

  const makeBtn = (pIdx) => {
    const p = G.players[pIdx];
    const fac = FACTIONS.find(f => f.id === p.faction);
    const col = fac?.color || (pIdx === 0 ? '#00c8ff' : '#ff4d6d');
    const units = (area.troops || []).filter(t => t.player === pIdx);
    const role = pIdx === attackerIdx ? 'Атакующий' : 'Защищающийся';
    return `<button class="abtn" style="flex:1;border-color:${col};color:${col}"
      onclick="_advanceDeclareWinner(${pIdx})">
      <strong>${p.name}</strong><br>
      <small style="opacity:.7">${role}</small><br>
      <small>${units.length} юн.</small>
    </button>`;
  };

  const html = `<div style="color:#aaa;font-size:.82rem;margin-bottom:12px;">
    Бой в области ${areaIdx} системы [${pa.tile_key}].<br>
    <span style="color:${attackerColor}">Атакует: <strong>${attacker.name}</strong></span><br>
    Выберите победителя:
  </div>
  <div style="display:flex;gap:8px;">
    ${makeBtn(attackerIdx)}
    ${makeBtn(defenderIdx)}
  </div>`;

  showMsg('⚔ Разрешение боя', html);
}

async function _advanceDeclareWinner(winnerId) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/advance-declare-winner', {
      player_id: G.curP,
      winner_id: winnerId,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      renderBoard();
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Ошибка объявления победителя');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

async function _advanceRetreat(tileKey, areaIdx) {
  try {
    const res = await apiCall('/api/game/advance-retreat', {
      player_id: G.curP,
      retreat_tile_key: tileKey,
      retreat_area_idx: areaIdx,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Нельзя выполнить отступление');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── combat (legacy, не используется в UI) ──────────────────────

async function _advanceFight() {
  try {
    const res = await apiCall('/api/game/advance-fight', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      const lastLog = res.state?.log?.slice(-1)[0]?.message || 'Бой завершён';
      if (res.state?.pending_advance) {
        showAdvanceUI();  // рендерит orbital панель
        showMsg('⚔ Результат боя', lastLog + '<br><br>Нажмите OK для продолжения.');
      } else {
        setPhase('execution');
        showMsg('⚔ Результат боя', lastLog + '<br><br>Advance завершён.');
      }
    } else {
      showMsg('Ошибка', res.error || 'Ошибка боя');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── orbital ────────────────────────────────────────────────────

async function _advanceOrbital(shipAreaIdx, targetAreaIdx) {
  try {
    const res = await apiCall('/api/game/advance-orbital', {
      player_id:       G.curP,
      ship_area_idx:   shipAreaIdx,
      target_area_idx: targetAreaIdx,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Нельзя выполнить орбитальный удар');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

async function _advanceSkipOrbital() {
  try {
    const res = await apiCall('/api/game/advance-skip-orbital', { player_id: G.curP });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      addLog('Advance завершён', G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error);
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── orbital_defend modal ───────────────────────────────────────

function _showAdvanceOrbitalDefendModal() {
  const pa = G.pending_advance;
  if (!pa) return;

  const attackerIdx   = pa.player_id;
  const defenderIdx   = 1 - attackerIdx;
  const defender      = G.players[defenderIdx];
  const tileKey       = pa.tile_key;
  const targetAreaIdx = pa.orbital_target_area;

  const tile = G.map?.[tileKey];
  if (!tile) return;
  const area = tile.areas?.[targetAreaIdx];
  if (!area) { _advanceSkipOrbital(); return; }

  const defUnits = (area.troops || [])
    .map((t, i) => ({ ...t, _i: i }))
    .filter(t => t.player === defenderIdx);

  if (defUnits.length === 0) { _advanceSkipOrbital(); return; }

  const fac = FACTIONS.find(f => f.id === defender.faction);
  const facColor = fac?.color || '#ff4d6d';

  let html = `<div style="color:#aaa;font-size:.82rem;margin-bottom:10px;">
    Передайте устройство <strong style="color:${facColor}">${defender.name}</strong>.<br>
    Выберите юнита которого потеряете с планеты [${tileKey}] обл.${targetAreaIdx}:
  </div>`;

  defUnits.forEach(t => {
    const name = getUnitName(defender.faction, t.unitType, t.tier ?? 0);
    const icon = t.unitType === 'space' ? '🚀' : '⚔';
    html += `<button class="abtn br" style="width:100%;margin-bottom:4px"
      onclick="_advanceOrbitalRemove(${defenderIdx},${targetAreaIdx},${t._i})">
      ${icon} ${name} T${t.tier ?? 0}
    </button>`;
  });

  showMsg(`🎯 Орбитальный удар — ${defender.name}`, html);
}

async function _advanceOrbitalRemove(defenderIdx, areaIdx, unitIdx) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/advance-orbital-remove', {
      player_id: defenderIdx,
      area_idx:  areaIdx,
      unit_idx:  unitIdx,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      addLog('Орбитальный удар: юнит уничтожен', G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || 'Не удалось удалить юнита');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

function _showShipSelectModal(ships) {
  let html = '<div style="display:flex;flex-direction:column;gap:8px;">';
  ships.forEach(s => {
    const name = getUnitName(G.players[G.curP].faction, 'space', s.unit.tier ?? 0);
    const shipId = s.ship_id;
    html += `<button class="abtn br" style="width:100%" onclick="window._selectShipById(${shipId});closeMsg();renderBoard();">
      🚀 ${name} T${s.unit.tier ?? 0}
    </button>`;
  });
  html += '</div>';
  showMsg('Выбрать корабль', html);
  window._shipOptions = ships;
}

function _showGroundSelectModal(units) {
  let html = '<div style="display:flex;flex-direction:column;gap:8px;">';
  units.forEach(g => {
    const name = getUnitName(G.players[G.curP].faction, 'ground', g.unit.tier ?? 0);
    const groundId = g.ground_id;
    html += `<button class="abtn bp" style="width:100%" onclick="window._selectGroundById(${groundId});closeMsg();renderBoard();">
      ⚔ ${name} T${g.unit.tier ?? 0}
    </button>`;
  });
  html += '</div>';
  showMsg('Выбрать юнита', html);
  window._groundOptions = units;
}

function _selectShipById(shipId) {
  const ship = (window._shipOptions || []).find(s => s.ship_id === shipId);
  if (ship) _advanceSelectShip(ship);
}

function _selectGroundById(groundId) {
  const unit = (window._groundOptions || []).find(g => g.ground_id === groundId);
  if (unit) _advanceSelectGround(unit);
}

function advanceAreaClick(tileKey, displayIdx) {
  const pa = G.pending_advance;
  if (!pa) return;

  const tile    = G.map[tileKey];
  if (!tile) return;
  const area    = getAreaByDisplay(tile, displayIdx);
  const realIdx = tile.areas.indexOf(area);
  const step    = pa.step;
  const activeKey = pa.tile_key;
  const sourceKey = pa.source_tile;

  // Choose source: только для выбора source тайла
  if (step === 'choose_source') {
    const adjacent = pa.adjacent_tiles || [];
    if (adjacent.includes(tileKey)) {
      _advanceChooseSource(tileKey);
    }
    return;
  }

  // Ships: только в одобренные области космоса
  if (step === 'ships') {
    if (!_advanceSelectedShip) {
      const origin = tileKey === activeKey ? 'active'
                   : tileKey === sourceKey  ? 'source' : null;
      if (!origin) return;
      const shipsInArea = (pa.available_ships || [])
        .filter(s => s.area_idx === realIdx && s.origin === origin);

      if (!shipsInArea.length) return;

      if (shipsInArea.length === 1) {
        _advanceSelectShip(shipsInArea[0]);
      } else {
        _showShipSelectModal(shipsInArea);
      }
      return;
    }
    // Клик на ту же область — снять выделение
    const selShip = _advanceSelectedShip;
    const selOrigin = selShip.origin === 'active' ? activeKey : sourceKey;
    if (tileKey === selOrigin && realIdx === selShip.area_idx) {
      _advanceSelectedShip = null;
      renderSide(); renderBoard();
      return;
    }
    if (tileKey !== activeKey) return;
    const clickable = pa.clickable_space_areas || [];
    if (clickable.includes(realIdx)) {
      _advanceMoveShip(_advanceSelectedShip.ship_id, realIdx);
    }
    return;
  }

  // На шаге ships ground юниты недоступны
  if (step === 'ships') return;

  // Ground: только в доступные планеты
  if (step === 'ground') {
    if (!_advanceSelectedGround) {
      const origin = tileKey === activeKey ? 'active'
                   : tileKey === sourceKey  ? 'source' : null;
      if (!origin) return;
      const unitsInArea = (pa.available_ground_units || [])
        .filter(g => g.area_idx === realIdx && g.origin === origin);

      if (!unitsInArea.length) return;

      if (unitsInArea.length === 1) {
        _advanceSelectGround(unitsInArea[0]);
      } else {
        _showGroundSelectModal(unitsInArea);
      }
      return;
    }
    // Клик на ту же область — снять выделение
    const selGround = _advanceSelectedGround;
    const selOriginTile = selGround.origin === 'active' ? activeKey : sourceKey;
    if (tileKey === selOriginTile && realIdx === selGround.area_idx) {
      _advanceSelectedGround = null;
      renderSide(); renderBoard();
      return;
    }
    if (tileKey !== activeKey) return;
    const gid = _advanceSelectedGround.ground_id;
    const reachableById = pa.reachable_planets_by_id || {};
    const planetList = reachableById[gid] ?? reachableById[String(gid)] ?? [];
    if (planetList.includes(realIdx)) {
      _advanceMoveGround(_advanceSelectedGround.ground_id, realIdx);
    }
    return;
  }

  // combat_retreat: клик на допустимую область для отступления (может быть в другом тайле)
  if (step === 'combat_retreat') {
    const validAreas = pa.retreat_valid_areas || [];
    const isValid = validAreas.some(([tk, ai]) => tk === tileKey && ai === realIdx);
    if (isValid) {
      _advanceRetreat(tileKey, realIdx);
    }
    return;
  }

  // Orbital: только разрешённые кораблями и вражеские планеты
  if (step === 'orbital' && tileKey === activeKey) {
    if (_advanceOrbitalShipArea === null) {
      const orbitalShips = pa.orbital_ships || [];
      if (orbitalShips.includes(realIdx)) {
        _advanceOrbitalShipArea = realIdx;
        renderSide(); renderBoard();
      }
      return;
    }
    const opp = 1 - G.curP;
    if ((area.troops || []).some(t => t.player === opp)) {
      _advanceOrbital(_advanceOrbitalShipArea, realIdx);
    }
    return;
  }
}

// ── capacity_overflow ──────────────────────────────────────────────────────

function _showOverflowModal() {
  const pa = G.pending_advance;
  if (!pa) return;

  const overflowAreas = pa.overflow_areas || [];
  if (!overflowAreas.length) return;

  const { area_idx, excess } = overflowAreas[0];
  const tile = G.map?.[pa.tile_key];
  if (!tile) return;
  const area = tile.areas?.[area_idx];
  if (!area) return;

  const overflowPIdx = pa.overflow_player ?? G.curP;
  const cp = G.players[overflowPIdx];
  const fac = FACTIONS.find(f => f.id === cp.faction);
  const facColor = fac?.color || '#00c8ff';

  const myUnits = (area.troops || [])
    .map((t, i) => ({ ...t, _i: i }))
    .filter(t => t.player === overflowPIdx);

  let html = `<div style="color:#aaa;font-size:.82rem;margin-bottom:10px;">
    Область ${area_idx} переполнена (лишних: ${excess}).<br>
    Выберите юнита для возврата в запас:
  </div>`;

  myUnits.forEach((t, idx) => {
    const name = getUnitName(cp.faction, t.unitType, t.tier ?? 0);
    const icon = t.unitType === 'space' ? '🚀' : '⚔';
    html += `<button class="abtn br" style="width:100%;margin-bottom:4px"
      onclick="_advanceRemoveOverflow(${area_idx},${idx},${overflowPIdx})">
      ${icon} ${name} T${t.tier ?? 0}
    </button>`;
  });

  showMsg(`⚠ Переполнение области ${area_idx}`, html);
}

async function _advanceRemoveOverflow(areaIdx, unitIdx, overflowPlayer) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/advance-remove-overflow', {
      player_id: overflowPlayer ?? G.curP,
      area_idx:  areaIdx,
      unit_idx:  unitIdx,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Не удалось убрать юнита');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}
