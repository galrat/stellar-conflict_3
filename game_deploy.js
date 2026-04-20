'use strict';
// ══════════════════════════════════════════════
//  DEPLOY ORDER UI — тонкий клиент
// ══════════════════════════════════════════════
// Все данные (цены, доступность, лимиты) берутся с сервера.
// JS только отображает и передаёт пользовательский выбор.

let _deployBasket          = [];
let _deploySelectedUnit    = null;
let _deploySelectedBuilding = null;
let _deployBlockReasons    = [];

// ── UI State Cleanup ──────────────────────────────────
function _resetDeployUI() {
  _deployBasket = [];
  _deploySelectedUnit = null;
  _deploySelectedBuilding = null;
  _deployBlockReasons = [];
}

function showDeployUI() {
  const pd = G.pending_deploy;
  if (!pd) {
    console.log('showDeployUI: нет pending_deploy');
    return;
  }
  const step = pd.step;
  console.log('showDeployUI: step=' + step);
  if      (step === 'buy_units')        { console.log('→ открываю buy_units'); _showDeployBuyUnits(); }
  else if (step === 'place_units')      { console.log('→ открываю place_units'); _showDeployPlaceUnitsSide(); }
  else if (step === 'resolve_overflow') { console.log('→ открываю resolve_overflow'); _showDeployResolveOverflow(); }
  else if (step === 'buy_building')     { console.log('→ открываю buy_building'); _showDeployBuyBuilding(); }
  else                                   { console.warn('Unknown step: ' + step); }
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

  // DEBUG: выводим информацию о deploy
  const availableCount = catalog.filter(u => u.available).length;
  const blockedCount = catalog.filter(u => !u.available).length;
  console.log('DEPLOY_INFO - Каталог:', catalog.length, 'юнитов | Доступно:', availableCount, '| Заблокировано:', blockedCount);
  console.log('DEPLOY_INFO - Capacity:', capacity, '| Credits:', credits, '| Forge:', forge, '| Cash:', cash);
  if (availableCount === 0 && catalog.length > 0) {
    console.log('DEPLOY_INFO - ВСЕ ЮНИТЫ ЗАБЛОКИРОВАНЫ. Причины:');
    catalog.forEach(u => {
      if (!u.available) {
        console.log('  -', u.name, ':', u.reason);
      }
    });
  }

  // Подсчёт состояния корзины (используем готовые значения с сервера)
  let totalCred = 0, forgeSpent = 0, cashSpent = 0;
  const bPool = {};
  for (const item of _deployBasket) {
    const u = catalog.find(c => c.unit_key === item.unit_key);
    if (!u) continue;
    forgeSpent += u.total_forge_cost || 0;  // ← готовое значение с сервера
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

  // Ренден каталога: берем данные из deploy_info, НЕ вычисляем локально
  const catalogHtml = catalog.map(u => {
    const inBasket  = bPool[u.unit_key] || 0;
    const remaining = u.pool_available - inBasket;
    // available — флаг с сервера (уже учитывает пул и тир)
    // remaining > 0 проверяет что еще есть в пуле после добавленных в корзину
    const available = u.available && remaining > 0;
    const icon      = u.type === 'ground' ? '⚔' : '🚀';

    console.log(`Unit: ${u.name}, available=${u.available}, remaining=${remaining}, btn_available=${available}`);

    // Полная стоимость forge берется готовой с сервера
    const forgeNote = u.total_forge_cost ? ` <span style="color:#ff8a65">${u.total_forge_cost}🔨</span>` : '';

    // Если недоступен — показать причину вместо цены
    const statusHtml = available
      ? `<span style="color:#4fc3f7">${u.cost}💰${forgeNote}</span>`
      : `<span style="color:#ff8a80;font-size:.85rem">${u.lock_reason || 'недоступен'}</span>`;

    return `
      <div style="display:flex;align-items:center;gap:8px;padding:6px 8px;
                  background:rgba(255,255,255,.05);margin-bottom:3px;border-radius:4px;
                  ${!available ? 'opacity:.35;' : 'cursor:pointer;'}"
           ${available ? `onclick="_deployAddUnit('${u.unit_key}')"` : ''}>
        <span>${icon} T${u.tier}</span>
        <span style="flex:1">${u.name}</span>
        ${statusHtml}
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
    </button>
    <button class="abtn bw" style="width:100%;margin-top:4px;"
            onclick="closeMsg();undoLastOrderViaAPI()">
      ↩ Отменить deploy
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
  const map_    = info.unit_type_tier_map || {};  // {(unitType, tier): unit_key}
  const areas   = G.map[pd.tile_key]?.areas || [];
  const getName = k => catalog.find(c => c.unit_key === k)?.name || k;

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
      const key = `${t.unitType},${t.tier}`;
      const uk = map_[key] || `${t.unitType}T${t.tier}`;
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
