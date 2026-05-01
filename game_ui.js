'use strict';
// ══════════════════════════════════════════════
//  UI HELPERS  (modals, hotpass, log, card viewers, phase)
// ══════════════════════════════════════════════

// ── Card deck viewers ────────────────────────────────────────────

function _renderCardColumn(cards, title, color, renderFn) {
  let html = `<div style="flex:1;min-width:280px;max-height:600px;overflow-y:auto;padding-right:4px;">`;
  html += `<div style="font-weight:bold;color:${color};margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid ${color};">${title} (${cards.length})</div>`;
  if (cards.length === 0) {
    html += `<div style="color:var(--dim);font-style:italic;text-align:center;padding:20px 0;">Пусто</div>`;
  } else {
    cards.forEach(c => { html += renderFn(c); });
  }
  html += `</div>`;
  return html;
}

function _showCardImageOverlay(src) {
  let ov = document.getElementById('card-img-overlay');
  if (!ov) {
    ov = document.createElement('div');
    ov.id = 'card-img-overlay';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.88);display:flex;align-items:center;justify-content:center;z-index:9999;cursor:pointer;';
    ov.onclick = () => ov.remove();
    document.body.appendChild(ov);
  }
  ov.innerHTML = `<img src="${src}" style="max-width:90vw;max-height:90vh;border-radius:6px;object-fit:contain;">`;
}

function _renderBattleCard(c) {
  const name = typeof c === 'string' ? c : c.name;
  const cost = c.cost ? `<span style="color:#ff8c00;margin-left:6px;">Стоимость: ${c.cost}</span>` : '';
  const tier = c.tier != null && c.tier >= 0 ? `<span style="color:var(--dim);margin-left:6px;">Tier ${c.tier}</span>` : '';
  const e1 = c.effect_1 ? `<div style="color:#aaa;font-size:.78rem;margin-top:4px;">${c.effect_1}</div>` : '';
  const e2 = c.effect_2 ? `<div style="color:#888;font-size:.78rem;margin-top:2px;">${c.effect_2}</div>` : '';
  const nameHtml = c.image
    ? `<span onclick="_showCardImageOverlay('${c.image.replace(/ /g, '%20')}')" style="cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px;">${name}</span>`
    : name;
  return `<div style="margin-bottom:8px;padding:8px;background:rgba(0,0,0,.4);border-left:3px solid rgba(255,215,0,.4);border-radius:4px;">
    <div style="font-weight:bold;font-size:.9rem;">${nameHtml}${cost}${tier}</div>${e1}${e2}
  </div>`;
}

function _renderOrderUpgrade(c) {
  const name = typeof c === 'string' ? c : c.name;
  const type = c.order_type ? `<span style="color:#00bcd4;margin-left:6px;">[${c.order_type}]</span>` : '';
  const cost = c.cost ? `<span style="color:#ff8c00;margin-left:6px;">Стоимость: ${c.cost}</span>` : '';
  const e1 = c.effect_1 ? `<div style="color:#aaa;font-size:.78rem;margin-top:4px;">${c.effect_1}</div>` : '';
  const e2 = c.effect_2 ? `<div style="color:#888;font-size:.78rem;margin-top:2px;">${c.effect_2}</div>` : '';
  const nameHtml = c.image
    ? `<span onclick="_showCardImageOverlay('${c.image.replace(/ /g, '%20')}')" style="cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px;">${name}</span>`
    : name;
  return `<div style="margin-bottom:8px;padding:8px;background:rgba(0,0,0,.4);border-left:3px solid rgba(0,188,212,.4);border-radius:4px;">
    <div style="font-weight:bold;font-size:.9rem;">${nameHtml}${type}${cost}</div>${e1}${e2}
  </div>`;
}

function _renderEventCard(c) {
  const name = typeof c === 'string' ? c : c.name;
  const ctype = c.card_type ? `<span style="color:#ab47bc;margin-left:6px;">[${c.card_type}]</span>` : '';
  const warp = c.warp_storm_move ? `<div style="color:#ff8c00;font-size:.78rem;margin-top:4px;">Warp: ${c.warp_storm_move}</div>` : '';
  const eff = c.effect ? `<div style="color:#aaa;font-size:.78rem;margin-top:2px;">${c.effect}</div>` : '';
  const nameHtml = c.image
    ? `<span onclick="_showCardImageOverlay('${c.image.replace(/ /g, '%20')}')" style="cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px;">${name}</span>`
    : name;
  return `<div style="margin-bottom:8px;padding:8px;background:rgba(0,0,0,.4);border-left:3px solid rgba(171,71,188,.4);border-radius:4px;">
    <div style="font-weight:bold;font-size:.9rem;">${nameHtml}${ctype}</div>${warp}${eff}
  </div>`;
}

function showBattleCards(playerIdx) {
  const p = G.players[playerIdx];
  const hand = p.hand_battle_cards || [];
  const avail = p.available_battle_cards || [];
  const html = `<div style="display:flex;gap:16px;font-size:.85rem;">
    ${_renderCardColumn(hand, 'На руке', 'rgba(76,175,80,.9)', _renderBattleCard)}
    ${_renderCardColumn(avail, 'Доступные для получения', 'rgba(255,215,0,.8)', _renderBattleCard)}
  </div>`;
  showMsg(`Боевые карты: ${p.name}`, html, true);
}

function showOrderUpgrades(playerIdx) {
  const p = G.players[playerIdx];
  const hand = p.hand_order_upgrades || [];
  const avail = p.available_order_upgrades || [];
  const html = `<div style="display:flex;gap:16px;font-size:.85rem;">
    ${_renderCardColumn(hand, 'На руке', 'rgba(76,175,80,.9)', _renderOrderUpgrade)}
    ${_renderCardColumn(avail, 'Доступные для получения', 'rgba(0,188,212,.8)', _renderOrderUpgrade)}
  </div>`;
  showMsg(`Улучшения приказов: ${p.name}`, html, true);
}

function showEventCards(playerIdx) {
  const p = G.players[playerIdx];
  const hand = p.hand_event_cards || [];
  const avail = p.available_event_cards || [];
  const dropped = (G.dropped_orders || []).filter(o => o.owner === playerIdx);

  const _renderDroppedOrder = (o) => {
    const orderType = ORDER_TYPES[o.type];
    const orderName = orderType?.name || o.type;
    return `<div style="padding:4px 6px;background:rgba(255,100,50,.1);border:1px solid rgba(255,100,50,.3);border-radius:4px;font-size:.75rem;margin-bottom:3px;">
      ${orderType?.icon || '?'} ${orderName}
    </div>`;
  };

  const droppedHtml = dropped.length === 0
    ? '<span style="color:var(--dim);font-size:.75rem">Нет сброшенных приказов</span>'
    : dropped.map(_renderDroppedOrder).join('');

  const html = `<div style="display:flex;gap:16px;font-size:.85rem;flex-wrap:wrap;">
    ${_renderCardColumn(hand, 'На руке', 'rgba(76,175,80,.9)', _renderEventCard)}
    ${_renderCardColumn(avail, 'Доступные для получения', 'rgba(171,71,188,.8)', _renderEventCard)}
    <div style="flex:1;min-width:120px;">
      <div style="font-weight:bold;margin-bottom:6px;color:rgba(255,100,50,.9);font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;">Сброшенные приказы</div>
      ${droppedHtml}
    </div>
  </div>`;
  showMsg(`Карты событий: ${p.name}`, html, true);
}

// ── Phase control ────────────────────────────────────────────────

// PHASE — sets UI state, never touches tileSnap/unitsPlaced
// forceRender: если false и фаза не изменилась, только очистить UI-состояние без render
function setPhase(phase, forceRender = true) {
  const phaseChanged = G.phase !== phase;
  G.phase = phase;

  // Всегда очищаем UI-состояние при любом вызове setPhase
  G.selHandIdx = null;
  G.selUnitIdx = null;
  G.selUnitType = null;

  // Hide all action buttons
  ['btn-ut','btn-uu','btn-fl','btn-rccw','btn-rcw','btn-et','btn-pass','btn-undo-order','btn-undo-ws','btn-confirm-ws','btn-discard-order','btn-next-round','btn-pick-event'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  _selectedOrderForPlay = null;

  // Если фаза не изменилась и forceRender=false, только очистили состояние, выход
  if (!phaseChanged && !forceRender) return;

  const cp  = G.players[G.curP];
  const ins = document.getElementById('pinstr');

  if (phase === 'tile-placement') {
    G.tileSnap   = null;
    G.unitsPlaced = [];
    const rem = cp.hand.filter(h => !h.placed).length;
    ins.innerHTML = `<strong>РАЗМЕЩЕНИЕ СИСТЕМ<\/strong><br>${cp.name}: выберите систему из руки, затем кликните ячейку. Осталось: ${rem}`;
    renderSide(); renderBoard();
  }
  else if (phase === 'troop-on-tile') {
    // tileSnap + unitsPlaced уже заданы в dropTile — НЕ сбрасывать
    const tile = G.map[G.lastKey];
    const needObj = tile?.needsObjective && !tile?.objectiveMarker;
    const objHint = needObj ? `<br><small style="color:var(--gold)">★ Кликните область без выбранного войска чтобы поставить метку цели соперника</small>` : '';
    ins.innerHTML = `<strong>ВОЙСКА НА СИСТЕМУ<\/strong><br>${cp.name}: размещайте войска на только что поставленной системе.<br><small style="color:var(--dim)">▲ наземные → 🪐 · ◈ космические → ✦</small>${objHint}`;
    show('btn-ut'); show('btn-uu'); show('btn-fl'); show('btn-rccw'); show('btn-rcw'); show('btn-et');
    document.getElementById('btn-et').textContent = 'Готово →';
    renderSide(); renderBoard(G.lastKey);
  }
  else if (phase === 'warp-storm') {
    const myStorm = G.warpStorms[G.curP];
    if (myStorm && !G.warpConfirmed[G.curP]) {
      ins.innerHTML = `<strong>ВАРП-ШТОРМ</strong><br>${cp.name}: варп-шторм размещён на [${myStorm.tileKey}] ${myStorm.side}. Подтвердите или отмените.`;
      show('btn-undo-ws');
      show('btn-confirm-ws');
    } else if (G.warpConfirmed[G.curP]) {
      ins.innerHTML = `<strong>ВАРП-ШТОРМ</strong><br>${cp.name}: размещение подтверждено. Ожидание второго игрока...`;
    } else {
      ins.innerHTML = `<strong>ВАРП-ШТОРМ</strong><br>${cp.name}: кликните на границу любой системы чтобы поставить варп-шторм`;
    }
    renderBoard();
  }
  else if (phase === 'order-placement' || phase === 'orders_placed' || phase === 'execution' || phase === 'end-round') {
    // Stage 2 phases: UI hints from server
    if (G.ui) {
      ins.innerHTML = G.ui.instruction;
      (G.ui.buttons || []).forEach(id => show(id));
    }
    renderSide(); renderBoard();

    // Конец раунда: если игрок ещё не выбрал карту — показать пикер
    if (phase === 'end-round' && G.ui?.event_cards_to_pick?.length) {
      setTimeout(showEventCardPicker, 150);
    }
  }
  updateHeader();
}

function show(id) { const el = document.getElementById(id); if (el) el.style.display = 'block'; }

// ── Hotpass overlay ──────────────────────────────────────────────

let _hpCb = null;
function showHP(name, action, cb) {
  _hpCb = cb;
  document.getElementById('hp-name').textContent   = name;
  document.getElementById('hp-action').textContent = action;
  const btn  = document.getElementById('hp-btn');
  const isP2 = G.players[1]?.name === name;
  btn.style.borderColor = isP2 ? 'var(--p2)' : 'var(--p1)';
  btn.style.color       = isP2 ? 'var(--p2)' : 'var(--p1)';
  btn.style.background  = isP2 ? 'rgba(255,77,109,.1)' : 'rgba(0,200,255,.1)';
  document.getElementById('hpov').classList.add('active');
}
function closeHP() {
  document.getElementById('hpov').classList.remove('active');
  if (_hpCb) { _hpCb(); _hpCb = null; }
}

// ── Message modal ────────────────────────────────────────────────

let _msgCb = null;
function showMsg(t, b, cb) {
  _msgCb = cb || null;
  document.getElementById('msg-title').textContent = t;
  document.getElementById('msg-body').innerHTML    = b;
  // Always restore standard OK button
  document.querySelector('#msg-modal .mbtns').innerHTML = '<button class="abtn bp" onclick="closeMsg()">OK</button>';
  const modal = document.getElementById('msg-modal');
  console.log('showMsg: добавляю класс active к модалю', modal);
  modal.classList.add('active');
  console.log('showMsg: модаль после добавления класса:', modal.classList.contains('active'));
}
function closeMsg() {
  console.log('closeMsg: вызвана');
  document.getElementById('msg-modal').classList.remove('active');
  if (_msgCb) { const f = _msgCb; _msgCb = null; f(); }
}

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

// ── Event log ────────────────────────────────────────────────────

let _renderedLogCount = 0;

function addLog(msg, player) {
  // Пишем в DOM и в G.log
  const el = document.getElementById('alog');
  const e  = document.createElement('div');
  e.className  = `le ${player===0?'le1':player===1?'le2':'les'}`;
  e.textContent = msg;
  el.prepend(e);
  if (!G.log) G.log = [];
  G.log.push({ message: msg, player_id: player });
  _renderedLogCount = G.log.length;
}

function _renderLogEntry(msg, player) {
  const el = document.getElementById('alog');
  const e  = document.createElement('div');
  e.className  = `le ${player===0?'le1':player===1?'le2':'les'}`;
  e.textContent = msg;
  el.prepend(e);
}

function clearLog() {
  document.getElementById('alog').innerHTML = '';
  _renderedLogCount = 0;
}

function syncLog() {
  // Отрендерить записи из G.log которые ещё не показаны в DOM
  const log = G.log || [];
  if (log.length > _renderedLogCount) {
    // Новые записи идут с конца — добавляем в обратном порядке чтобы prepend дал правильный порядок
    const newEntries = log.slice(_renderedLogCount);
    for (let i = newEntries.length - 1; i >= 0; i--) {
      _renderLogEntry(newEntries[i].message, newEntries[i].player_id);
    }
    _renderedLogCount = log.length;
  }
}
