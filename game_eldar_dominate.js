'use strict';
// ══════════════════════════════════════════════
//  ELDAR DOMINATE — особое свойство доминации
// ══════════════════════════════════════════════

let _eldarSelectedUnit = null;  // {area_idx, troop_idx, unitType, tier}

function eldarDominateAreaClick(tileKey, realIdx) {
  const pe = G.pending_eldar_dominate;
  if (!pe || pe.player_id !== G.curP) return;

  if (!_eldarSelectedUnit) {
    if (tileKey !== pe.source_tile_key) return;
    const unit = (pe.movable_units || []).find(u => u.area_idx === realIdx);
    if (!unit) return;
    _eldarSelectedUnit = unit;
    renderBoard();
  } else {
    const isTarget = (pe.valid_targets || []).some(
      t => t.tile_key === tileKey && t.area_idx === realIdx
    );
    if (!isTarget) {
      _eldarSelectedUnit = null;
      renderBoard();
      return;
    }
    _eldarDominateExecuteMove(
      pe.player_id,
      _eldarSelectedUnit.area_idx,
      _eldarSelectedUnit.troop_idx,
      tileKey,
      realIdx,
    );
  }
}

async function _eldarDominateExecuteMove(playerId, srcAreaIdx, srcTroopIdx, targetTileKey, targetAreaIdx) {
  _eldarSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-eldar-choose', {
      player_id:       playerId,
      src_area_idx:    srcAreaIdx,
      src_troop_idx:   srcTroopIdx,
      target_tile_key: targetTileKey,
      target_area_idx: targetAreaIdx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Eldar: юнит → система ${targetTileKey}, область ${targetAreaIdx}`, playerId);
      if (res.state?.pending_eldar_retreat) {
        _showEldarRetreatModal(res.state.pending_eldar_retreat);
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

function _showEldarRetreatModal(pending) {
  const pid      = pending.player_id;
  const tileKey  = pending.tile_key;
  const areaIdx  = pending.area_idx;
  const capacity = pending.capacity;
  const units    = pending.units || [];

  const btns = units.map(u => {
    const lbl = u.player === pid
      ? `Ваш: ${u.unitType} tier${u.tier}`
      : `Соперник: ${u.unitType} tier${u.tier}`;
    return `<button class="abtn bp" onclick="_eldarRetreatChoose(${pid},'${tileKey}',${areaIdx},${u.troop_idx})"
      style="margin:4px 2px;display:block;width:100%;">${lbl}</button>`;
  }).join('');

  showMsg('⬡ Eldar: выберите юнита для удаления', `
    <div style="margin-bottom:10px;color:#aaa;">
      Область переполнена (capacity=${capacity}). Выберите юнита для удаления:
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;">${btns}</div>
  `);
}

async function _eldarRetreatChoose(playerId, tileKey, areaIdx, troopIdx) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-eldar-retreat', {
      player_id: playerId,
      tile_key:  tileKey,
      area_idx:  areaIdx,
      troop_idx: troopIdx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Eldar: юнит удалён из ${tileKey}/${areaIdx}`, playerId);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

async function eldarDominateSkip() {
  _eldarSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-eldar-skip', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      addLog('Eldar: особое свойство пропущено', G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}
