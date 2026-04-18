'use strict';
// ══════════════════════════════════════════════
//  ADVANCE ORDER UI
// ══════════════════════════════════════════════

let _advanceSelectedShip    = null;  // {area_idx, unit, origin}
let _advanceSelectedGround  = null;  // {area_idx, unit, origin}
let _advanceOrbitalShipArea = null;  // int: realIdx в активном тайле

function _advanceClearSelection() {
  _advanceSelectedShip    = null;
  _advanceSelectedGround  = null;
  _advanceOrbitalShipArea = null;
}

function showAdvanceUI() {
  const pa = G.pending_advance;
  if (!pa) { setPhase('execution'); return; }
  setPhase('execution');  // renderSide + renderBoard через setPhase
  if (pa.step === 'orbital_defend') {
    _showAdvanceOrbitalDefendModal();
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
  const same = _advanceSelectedShip?.area_idx === ship.area_idx
            && _advanceSelectedShip?.origin   === ship.origin;
  _advanceSelectedShip = same ? null : ship;
  renderSide(); renderBoard();
}

async function _advanceMoveShip(fromAreaIdx, toAreaIdx) {
  try {
    const res = await apiCall('/api/game/advance-move-ship', {
      player_id:     G.curP,
      from_area_idx: fromAreaIdx,
      to_area_idx:   toAreaIdx,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
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
  const same = _advanceSelectedGround?.area_idx === unit.area_idx
            && _advanceSelectedGround?.origin   === unit.origin;
  _advanceSelectedGround = same ? null : unit;
  renderSide(); renderBoard();
}

async function _advanceMoveGround(fromAreaIdx, toAreaIdx) {
  try {
    const res = await apiCall('/api/game/advance-move-ground', {
      player_id:     G.curP,
      from_area_idx: fromAreaIdx,
      to_area_idx:   toAreaIdx,
    });
    if (res.success) {
      _advanceClearSelection();
      applyState(res.state);
      showAdvanceUI();
    } else {
      showMsg('Ошибка', res.error || 'Нельзя переместить юнита');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
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

// ── combat ─────────────────────────────────────────────────────

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

// ── Map area click handler ─────────────────────────────────────

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

  if (step === 'ships') {
    if (!_advanceSelectedShip) {
      const origin = tileKey === activeKey ? 'active'
                   : tileKey === sourceKey  ? 'source' : null;
      if (!origin) return;
      const ship = (G.ui?.advance_available_ships || [])
        .find(s => s.area_idx === realIdx && s.origin === origin);
      if (ship) _advanceSelectShip(ship);
      return;
    }
    if (tileKey !== activeKey) {
      showMsg('Неверная цель', 'Корабли перемещаются только в активную систему');
      return;
    }
    if (area.type !== 'space') {
      showMsg('Неверная цель', 'Корабли могут стоять только в космосе');
      return;
    }
    _advanceMoveShip(_advanceSelectedShip.area_idx, realIdx);
    return;
  }

  if (step === 'ground') {
    if (!_advanceSelectedGround) {
      const origin = tileKey === activeKey ? 'active'
                   : tileKey === sourceKey  ? 'source' : null;
      if (!origin) return;
      const unit = (G.ui?.advance_available_ground || [])
        .find(g => g.area_idx === realIdx && g.origin === origin);
      if (unit) _advanceSelectGround(unit);
      return;
    }
    if (tileKey !== activeKey) {
      showMsg('Неверная цель', 'Наземные юниты перемещаются только в активную систему');
      return;
    }
    if (area.type !== 'planet') {
      showMsg('Неверная цель', 'Наземные юниты могут стоять только на планетах');
      return;
    }
    _advanceMoveGround(_advanceSelectedGround.area_idx, realIdx);
    return;
  }

  if (step === 'orbital' && tileKey === activeKey) {
    if (_advanceOrbitalShipArea === null) {
      if (area.type !== 'space') {
        showMsg('Орбитальный удар', 'Выберите область с вашим кораблём');
        return;
      }
      const hasShip = (area.troops || []).some(t => t.player === G.curP && t.unitType === 'space');
      if (!hasShip) {
        showMsg('Орбитальный удар', 'В этой области нет вашего корабля');
        return;
      }
      _advanceOrbitalShipArea = realIdx;
      renderSide(); renderBoard();
      return;
    }
    // Корабль выбран → выбрать целевую планету
    if (area.type !== 'planet') {
      showMsg('Орбитальный удар', 'Выберите планету для удара');
      return;
    }
    const opp = 1 - G.curP;
    if (!(area.troops || []).some(t => t.player === opp)) {
      showMsg('Орбитальный удар', 'На планете нет вражеских юнитов');
      return;
    }
    _advanceOrbital(_advanceOrbitalShipArea, realIdx);
    return;
  }
}
