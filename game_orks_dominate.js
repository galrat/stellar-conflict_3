'use strict';
// ══════════════════════════════════════════════
//  ORKS DOMINATE — особое свойство доминации
// ══════════════════════════════════════════════

let _orksBasket       = [];
let _orksSelectedUnit = null;

function showOrksDominateUI() {
  const po = G.pending_orks_dominate;
  if (!po) return;
  const step = po.step;
  if      (step === 'ask')              _showOrksDominateAsk();
  else if (step === 'buy_unit')         _showOrksBuyUnit();
  else if (step === 'place_unit')       _showOrksPlaceUnitSide();
  else if (step === 'resolve_overflow') _showOrksResolveOverflow();
}

// ── Step: ask ─────────────────────────────────────────────────────

function _showOrksDominateAsk() {
  showMsg('\uD83E\uDAAB Orks: особое свойство доминации', `
    <div style="margin-bottom:14px;color:#aaa;">
      В активной системе есть дружественные планеты.<br>
      Хотите купить одного юнита и разместить его?
    </div>
    <div style="display:flex;gap:8px;">
      <button class="abtn bp" style="flex:1;padding:10px;"
              onclick="_orksAskYes()">✓ Да</button>
      <button class="abtn bw" style="flex:1;padding:10px;"
              onclick="orksDominateSkip()">✕ Нет</button>
    </div>
  `);
}

async function _orksAskYes() {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-orks-ask-yes', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      showOrksDominateUI();
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── Step: buy_unit ────────────────────────────────────────────────

function _showOrksBuyUnit() {
  _orksBasket = [];
  _renderOrksBuyUnitModal();
}

function _renderOrksBuyUnitModal() {
  const po      = G.pending_orks_dominate;
  const info    = po.deploy_info || {};
  const catalog = info.unit_catalog || [];
  const capacity = info.capacity || 1;
  const credits  = info.credits;
  const forge    = info.forge_tokens;
  const cash     = info.cash_tokens;

  let totalCred = 0, forgeSpent = 0, cashSpent = 0;
  const bPool = {};
  for (const item of _orksBasket) {
    const u = catalog.find(c => c.unit_key === item.unit_key);
    if (!u) continue;
    forgeSpent += u.total_forge_cost || 0;
    cashSpent  += item.use_cash ? 1 : 0;
    totalCred  += u.cost - (item.use_cash ? 2 : 0);
    bPool[item.unit_key] = (bPool[item.unit_key] || 0) + 1;
  }
  totalCred = Math.max(0, totalCred);

  const credLeft  = credits - totalCred;
  const forgeLeft = forge - forgeSpent;
  const cashLeft  = cash - cashSpent;
  const canConfirm = credLeft >= 0 && forgeLeft >= 0 && cashLeft >= 0;

  const catalogHtml = catalog.map(u => {
    const inBasket  = bPool[u.unit_key] || 0;
    const remaining = u.pool_available - inBasket;
    const available = u.available && remaining > 0 && _orksBasket.length < capacity;
    const icon      = u.unitType === 'ground' ? '⚔' : '🚀';
    const forgeNote = u.total_forge_cost ? ` <span style="color:#ff8a65">${u.total_forge_cost}🔨</span>` : '';
    const statusHtml = available
      ? `<span style="color:#4fc3f7">${u.cost}💰${forgeNote}</span>`
      : `<span style="color:#ff8a80;font-size:.85rem">${u.lock_reason || 'недоступен'}</span>`;
    return `
      <div style="display:flex;align-items:center;gap:8px;padding:6px 8px;
                  background:rgba(255,255,255,.05);margin-bottom:3px;border-radius:4px;
                  ${!available ? 'opacity:.35;' : 'cursor:pointer;'}"
           ${available ? `onclick="_orksAddUnit('${u.unit_key}')"` : ''}>
        <span>${icon} T${u.tier}</span>
        <span style="flex:1">${u.name}</span>
        ${statusHtml}
        <span style="color:#888;font-size:.8rem">пул:${remaining}</span>
      </div>`;
  }).join('');

  const basketHtml = _orksBasket.length
    ? _orksBasket.map((item, i) => {
        const u = catalog.find(c => c.unit_key === item.unit_key);
        return `
          <div style="display:flex;align-items:center;gap:6px;padding:4px 8px;
                      background:rgba(0,200,255,.1);margin-bottom:2px;border-radius:4px;">
            <span style="flex:1;font-size:.9rem">${u?.name || item.unit_key}</span>
            <label style="font-size:.8rem;display:flex;align-items:center;gap:4px;cursor:pointer;">
              <input type="checkbox" ${item.use_cash ? 'checked' : ''}
                     onchange="_orksToggleCash(${i},this.checked)"> cash −2
            </label>
            <button class="abtn bw" style="padding:1px 7px;font-size:.7rem"
                    onclick="_orksRemoveBasket(${i})">✕</button>
          </div>`;
      }).join('')
    : '<div style="color:#555;text-align:center;padding:6px;font-size:.85rem">Выберите юнита</div>';

  const html = `
    <div style="font-size:.8rem;color:#888;margin-bottom:8px;">
      Можно купить: 1 юнит | 💰${credits} 🔨${forge} cash:${cash}
    </div>
    <div style="max-height:190px;overflow-y:auto;margin-bottom:8px;">${catalogHtml}</div>
    <div style="font-weight:bold;font-size:.85rem;margin-bottom:4px;color:#4fc3f7">
      Корзина (${_orksBasket.length}/${capacity}):
    </div>
    <div style="margin-bottom:8px;">${basketHtml}</div>
    <div style="font-size:.85rem;margin-bottom:10px;">
      Итого: <span style="color:${credLeft<0?'#ff6b6b':'#69f0ae'}">${totalCred}💰</span>
      ${forgeSpent ? `<span style="color:${forgeLeft<0?'#ff6b6b':'#aaa'}"> ${forgeSpent}🔨</span>` : ''}
      ${cashSpent  ? `<span style="color:${cashLeft<0?'#ff6b6b':'#aaa'}"> ${cashSpent} cash</span>` : ''}
      &nbsp; Остаток: <span style="color:${credLeft<0?'#ff6b6b':'#aaa'}">${credLeft}💰</span>
      <span style="color:${forgeLeft<0?'#ff6b6b':'#aaa'}"> ${forgeLeft}🔨</span>
    </div>
    <button class="abtn bp" style="width:100%;${!canConfirm && _orksBasket.length ? 'opacity:.5;' : ''}"
            onclick="_orksConfirmBasket()">
      ${_orksBasket.length ? '✓ Купить юнита' : '→ Пропустить покупку'}
    </button>
    <button class="abtn bw" style="width:100%;margin-top:4px;"
            onclick="orksDominateSkip()">
      ↩ Пропустить способность
    </button>`;

  showMsg('\uD83E\uDAAB Orks: покупка юнита', html);
}

function _orksAddUnit(unitKey) {
  _orksBasket.push({ unit_key: unitKey, use_cash: false });
  _renderOrksBuyUnitModal();
}
function _orksRemoveBasket(idx) {
  _orksBasket.splice(idx, 1);
  _renderOrksBuyUnitModal();
}
function _orksToggleCash(idx, val) {
  if (_orksBasket[idx]) { _orksBasket[idx].use_cash = val; _renderOrksBuyUnitModal(); }
}

async function _orksConfirmBasket() {
  if (_orksBasket.length > 0) {
    const po      = G.pending_orks_dominate;
    const info    = po?.deploy_info || {};
    const credits = info.credits || 0;
    const forge   = info.forge_tokens || 0;
    const catalog = info.unit_catalog || [];
    let totalCred = 0, forgeSpent = 0, cashSpent = 0;
    for (const item of _orksBasket) {
      const u = catalog.find(c => c.unit_key === item.unit_key);
      if (!u) continue;
      forgeSpent += u.total_forge_cost || 0;
      cashSpent  += item.use_cash ? 1 : 0;
      totalCred  += u.cost - (item.use_cash ? 2 : 0);
    }
    totalCred = Math.max(0, totalCred);
    if (totalCred > credits || forgeSpent > forge) {
      showMsg('Нельзя купить', 'Недостаточно ресурсов');
      return;
    }
  }
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-orks-confirm-basket', {
      player_id: G.curP,
      basket:    _orksBasket,
    });
    if (res.success) {
      _orksBasket = [];
      applyState(res.state);
      if (G.pending_orks_dominate) {
        showOrksDominateUI();
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── Step: place_unit ──────────────────────────────────────────────

function _showOrksPlaceUnitSide() {
  closeMsg();
  _orksSelectedUnit = null;
  setPhase('execution');
}

async function _orksUndoPlace() {
  const po = G.pending_orks_dominate;
  if (!po || !po.placed?.length) return;
  try {
    const res = await apiCall('/api/game/dominate-orks-undo-place', { player_id: G.curP });
    if (res.success) {
      _orksSelectedUnit = null;
      applyState(res.state);
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── Step: resolve_overflow ────────────────────────────────────────

function _showOrksResolveOverflow() {
  const po      = G.pending_orks_dominate;
  const placed  = po.placed || [];
  const info    = po.deploy_info || {};
  const catalog = info.unit_catalog || [];
  const map_    = info.unit_type_tier_map || {};
  const areas   = G.map[po.tile_key]?.areas || [];
  const getName = k => catalog.find(c => c.unit_key === k)?.name || k;

  const counts = {};
  areas.forEach((a, i) => { counts[i] = (a.troops || []).length; });
  placed.forEach(p => { counts[p.area_idx] = (counts[p.area_idx] || 0) + 1; });
  const overflows = Object.entries(counts)
    .filter(([i, c]) => c > (areas[+i]?.capacity || 0))
    .map(([i]) => +i);

  let html = `<div style="color:#ff6b6b;margin-bottom:8px;">⚠ Переполнено: area[${overflows.join('], area[')}]</div>`;
  for (const aIdx of overflows) {
    const a   = areas[aIdx];
    const cap = a?.capacity || 0;
    const cnt = counts[aIdx];
    html += `<div style="margin-bottom:10px;"><strong>area[${aIdx}] ${a?.type} (${cnt}/${cap})</strong><br>`;

    (a?.troops || []).filter(t => t.player === G.curP).forEach(t => {
      const key = `${t.unitType},${t.tier}`;
      const uk  = map_[key] || `${t.unitType}T${t.tier}`;
      html += `<button class="abtn bw" style="margin:2px;"
                       onclick="_orksRemoveOverflow(${aIdx},'${uk}')">
                 ✕ ${getName(uk)} <span style="font-size:.75rem;color:#888">(карта)</span>
               </button>`;
    });
    placed.filter(p => p.area_idx === aIdx).forEach(p => {
      html += `<button class="abtn bw" style="margin:2px;"
                       onclick="_orksRemoveOverflow(${aIdx},'${p.unit_key}')">
                 ✕ ${getName(p.unit_key)} <span style="font-size:.75rem;color:#888">(новый)</span>
               </button>`;
    });
    html += '</div>';
  }

  showMsg('\uD83E\uDAAB Orks: разрешение переполнения', html);
}

async function _orksRemoveOverflow(areaIdx, unitKey) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-orks-resolve-overflow', {
      player_id:       G.curP,
      remove_area_idx: areaIdx,
      remove_unit_key: unitKey,
    });
    if (res.success) {
      applyState(res.state);
      if (G.pending_orks_dominate) {
        showOrksDominateUI();
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── Map click handler ─────────────────────────────────────────────

async function orksAreaClick(tileKey, realIdx) {
  const po = G.pending_orks_dominate;
  if (!po || po.player_id !== G.curP) return;
  if (po.step !== 'place_unit') return;
  if (tileKey !== po.tile_key) return;

  if (!_orksSelectedUnit) {
    showMsg('Orks', 'Сначала выберите юнит в левой панели, затем кликните область.');
    return;
  }
  try {
    const res = await apiCall('/api/game/dominate-orks-place-unit', {
      player_id: G.curP,
      unit_key:  _orksSelectedUnit,
      area_idx:  realIdx,
    });
    if (res.success) {
      _orksSelectedUnit = null;
      applyState(res.state);
      if (G.pending_orks_dominate) {
        showOrksDominateUI();
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}

// ── Skip ──────────────────────────────────────────────────────────

async function orksDominateSkip() {
  closeMsg();
  _orksBasket       = [];
  _orksSelectedUnit = null;
  try {
    const res = await apiCall('/api/game/dominate-orks-skip', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      addLog('Orks: особое свойство доминации пропущено', G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) { showMsg('Ошибка сервера', e.message); }
}
