'use strict';
// ══════════════════════════════════════════════
//  CHAOS DOMINATE — особое свойство доминации
// ══════════════════════════════════════════════

let _chaosSelectedUnit = null;  // {area_idx, troop_idx, unitType, tier}

function chaosDominateAreaClick(tileKey, realIdx) {
  const pc = G.pending_chaos_dominate;
  if (!pc || pc.player_id !== G.curP) return;

  if (!_chaosSelectedUnit) {
    if (tileKey !== pc.source_tile_key) return;
    const unit = (pc.movable_units || []).find(u => u.area_idx === realIdx);
    if (!unit) return;
    _chaosSelectedUnit = unit;
    renderBoard();
  } else {
    const isTarget = (pc.valid_targets || []).some(
      t => t.tile_key === tileKey && t.area_idx === realIdx
    );
    if (!isTarget) {
      _chaosSelectedUnit = null;
      renderBoard();
      return;
    }
    _chaosDominateExecuteMove(
      pc.player_id,
      _chaosSelectedUnit.area_idx,
      _chaosSelectedUnit.troop_idx,
      tileKey,
      realIdx,
    );
  }
}

async function _chaosDominateExecuteMove(playerId, srcAreaIdx, srcTroopIdx, targetTileKey, targetAreaIdx) {
  _chaosSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-chaos-choose', {
      player_id:       playerId,
      src_area_idx:    srcAreaIdx,
      src_troop_idx:   srcTroopIdx,
      target_tile_key: targetTileKey,
      target_area_idx: targetAreaIdx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Хаос: культист → система ${targetTileKey}, область ${targetAreaIdx}`, playerId);
      if (res.state?.pending_chaos_retreat) {
        _showChaosRetreatModal(res.state.pending_chaos_retreat);
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

function _showChaosRetreatModal(pending) {
  const pid      = pending.player_id;
  const tileKey  = pending.tile_key;
  const areaIdx  = pending.area_idx;
  const capacity = pending.capacity;
  const units    = pending.units || [];

  const btns = units.map(u => {
    const lbl = u.player === pid
      ? `Ваш: ${u.unitType} tier${u.tier}`
      : `Соперник: ${u.unitType} tier${u.tier}`;
    return `<button class="abtn bp" onclick="_chaosRetreatChoose(${pid},'${tileKey}',${areaIdx},${u.troop_idx})"
      style="margin:4px 2px;display:block;width:100%;">${lbl}</button>`;
  }).join('');

  showMsg('⬡ Хаос: выберите юнита для удаления', `
    <div style="margin-bottom:10px;color:#aaa;">
      Область переполнена (capacity=${capacity}). Выберите юнита для удаления:
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;">${btns}</div>
  `);
}

async function _chaosRetreatChoose(playerId, tileKey, areaIdx, troopIdx) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-chaos-retreat', {
      player_id: playerId,
      tile_key:  tileKey,
      area_idx:  areaIdx,
      troop_idx: troopIdx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Хаос: юнит удалён из ${tileKey}/${areaIdx}`, playerId);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

async function chaosDominateSkip() {
  _chaosSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-chaos-skip', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      addLog('Хаос: особое свойство пропущено', G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}
