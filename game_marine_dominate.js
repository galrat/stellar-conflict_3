'use strict';
// ══════════════════════════════════════════════
//  MARINE DOMINATE — особое свойство доминации
// ══════════════════════════════════════════════

let _marineSelectedUnit = null; // {area_idx, troop_idx, unitType, tier}

function marineDominateAreaClick(tileKey, realIdx) {
  const pm = G.pending_marine_dominate;
  if (!pm || pm.player_id !== G.curP) return;
  if (tileKey !== pm.source_tile_key) return;

  const unitsInArea = (pm.movable_units || []).filter(u => u.area_idx === realIdx);
  if (!unitsInArea.length) return;

  const credits = G.players?.[G.curP]?.credits ?? 0;
  if (credits < 1) {
    showMsg('◈ Marine: особое свойство', `
      <div style="margin-bottom:14px;">Не хватает денег на улучшение.</div>
      <button class="abtn bp" onclick="closeMsg();marineDominateSkip();" style="width:100%;">Продолжить</button>
    `);
    return;
  }

  if (unitsInArea.length === 1) {
    _marineSelectedUnit = unitsInArea[0];
    renderSide();
    _showMarineUpgradeModal();
  } else {
    _showMarineUnitPickModal(unitsInArea);
  }
}

function _showMarineUnitPickModal(units) {
  const btns = units.map(u =>
    `<button class="abtn bp" onclick="_marinePickUnit(${u.area_idx},${u.troop_idx},'${u.unitType}',${u.tier})"
      style="margin:4px 2px;display:block;width:100%;">${u.unitType} tier${u.tier}</button>`
  ).join('');
  showMsg('◈ Marine: выберите юнита для улучшения', `
    <div style="margin-bottom:10px;color:#aaa;">В области несколько юнитов. Выберите, кого улучшить:</div>
    <div style="display:flex;flex-direction:column;gap:4px;">${btns}</div>
  `);
}

function _marinePickUnit(areaIdx, troopIdx, unitType, tier) {
  closeMsg();
  _marineSelectedUnit = { area_idx: areaIdx, troop_idx: troopIdx, unitType, tier };
  renderSide();
  _showMarineUpgradeModal();
}

function _showMarineUpgradeModal() {
  const u = _marineSelectedUnit;
  showMsg('◈ Marine: улучшение юнита', `
    <div style="margin-bottom:10px;color:#aaa;">${u.unitType} tier${u.tier} → tier${u.tier + 1}</div>
    <div>Хотите улучшить юнита на один уровень за 1 монету?</div>
    <div style="display:flex;gap:8px;margin-top:14px;">
      <button class="abtn bp" onclick="_marineConfirmUpgrade()" style="flex:1;">Да</button>
      <button class="abtn" onclick="_marineCancelUpgrade()" style="flex:1;">Нет</button>
    </div>
  `);
}

async function _marineConfirmUpgrade() {
  closeMsg();
  const pm = G.pending_marine_dominate;
  const u  = _marineSelectedUnit;
  _marineSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-marine-choose', {
      player_id: pm.player_id,
      area_idx:  u.area_idx,
      troop_idx: u.troop_idx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Marine: юнит tier${u.tier} → tier${u.tier + 1}`, pm.player_id);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

async function _marineCancelUpgrade() {
  closeMsg();
  _marineSelectedUnit = null;
  marineDominateSkip();
}

async function marineDominateSkip() {
  _marineSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-marine-skip', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      addLog('Marine: особое свойство пропущено', G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}
