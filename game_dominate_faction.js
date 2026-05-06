'use strict';
// ══════════════════════════════════════════════
//  FACTION DOMINATE — универсальное особое свойство доминации
// ══════════════════════════════════════════════

let _factionSelectedUnit = null;  // {area_idx, troop_idx, unitType, tier}

function factionDominateAreaClick(tileKey, realIdx) {
  const pf = G.pending_faction_dominate;
  if (!pf || pf.player_id !== G.curP) return;

  if (!_factionSelectedUnit) {
    if (tileKey !== pf.source_tile_key) return;
    const unit = (pf.movable_units || []).find(u => u.area_idx === realIdx);
    if (!unit) return;
    _factionSelectedUnit = unit;
    renderBoard();
  } else {
    const isTarget = (pf.valid_targets || []).some(
      t => t.tile_key === tileKey && t.area_idx === realIdx
    );
    if (!isTarget) {
      _factionSelectedUnit = null;
      renderBoard();
      return;
    }
    _factionDominateExecuteAction(
      pf.player_id,
      _factionSelectedUnit.area_idx,
      _factionSelectedUnit.troop_idx,
      tileKey,
      realIdx,
    );
  }
}

async function _factionDominateExecuteAction(playerId, srcAreaIdx, srcTroopIdx, targetTileKey, targetAreaIdx) {
  _factionSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-faction-action', {
      player_id:       playerId,
      src_area_idx:    srcAreaIdx,
      src_troop_idx:   srcTroopIdx,
      target_tile_key: targetTileKey,
      target_area_idx: targetAreaIdx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Особое свойство: юнит → система ${targetTileKey}, область ${targetAreaIdx}`, playerId);
      if (res.state?.pending_faction_retreat) {
        _showFactionRetreatModal(res.state.pending_faction_retreat);
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

function _showFactionRetreatModal(pending) {
  const pid      = pending.player_id;
  const tileKey  = pending.tile_key;
  const areaIdx  = pending.area_idx;
  const capacity = pending.capacity;
  const title    = pending.title || '⬡ Выберите юнита для удаления';
  const units    = pending.units || [];

  const btns = units.map(u => {
    const lbl = u.player === pid
      ? `Ваш: ${u.unitType} tier${u.tier}`
      : `Соперник: ${u.unitType} tier${u.tier}`;
    return `<button class="abtn bp" onclick="_factionRetreatChoose(${pid},'${tileKey}',${areaIdx},${u.troop_idx})"
      style="margin:4px 2px;display:block;width:100%;">${lbl}</button>`;
  }).join('');

  showMsg(title, `
    <div style="margin-bottom:10px;color:#aaa;">
      Область переполнена (capacity=${capacity}). Выберите юнита для удаления:
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;">${btns}</div>
  `);
}

async function _factionRetreatChoose(playerId, tileKey, areaIdx, troopIdx) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-faction-retreat', {
      player_id: playerId,
      tile_key:  tileKey,
      area_idx:  areaIdx,
      troop_idx: troopIdx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Особое свойство: юнит удалён из ${tileKey}/${areaIdx}`, playerId);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

async function factionDominateSkip() {
  _factionSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-faction-skip', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      addLog('Особое свойство доминации пропущено', G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}
