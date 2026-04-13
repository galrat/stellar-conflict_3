'use strict';
// ══════════════════════════════════════════════
//  DEPLOY ORDER UI
// ══════════════════════════════════════════════

let _deployBasket          = [];
let _deploySelectedUnit    = null;
let _deploySelectedBuilding = null;
let _deployBlockReasons    = [];

const _DEPLOY_UT    = { infantry:'ground', marines:'ground', mechanized:'ground', elite:'ground', fighter:'space', destroyer:'space' };
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

// ── Step: buy_units ──────────────────────────────────────────────

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

  _deployBlockReasons = [];
  if (_deployBasket.length > capacity) _deployBlockReasons.push(`превышена вместимость (${_deployBasket.length}/${capacity})`);
  if (credLeft  < 0) _deployBlockReasons.push(`не хватает ${-credLeft}💰`);
  if (forgeLeft < 0) _deployBlockReasons.push(`не хватает ${-forgeLeft}🔨`);
  if (cashLeft  < 0) _deployBlockReasons.push(`не хватает ${-cashLeft} cash`);

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
    <button class="abtn bp" style="width:100%;${!canConfirm && _deployBasket.length ? 'opacity:.5;' : ''}"
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
    _renderDeployBuyUnitsModal();
  }
}

async function _deployConfirmBasket() {
  if (_deployBasket.length > 0 && _deployBlockReasons.length > 0) {
    showMsg('Нельзя купить', _deployBlockReasons.join('<br>'));
    return;
  }
  closeMsg();
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

// ── Step: place_units — левая панель (без модала) ────────────────

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

// ── Step: resolve_overflow ───────────────────────────────────────

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

// ── Step: buy_building — левая панель (без модала) ───────────────

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

// ── Map click handler for deploy ─────────────────────────────────

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
