'use strict';
// ══════════════════════════════════════════════
//  RENDER SIDE — orders phases
// ══════════════════════════════════════════════

function _renderOrderPlacementPhase() {
  const cp    = G.players[G.curP];
  const poolEl = _resetPanels();

  if (cp.hand_orders && cp.hand_orders.length > 0 && G.ui?.can_place_order) {
    cp.hand_orders.forEach((order, idx) => {
      const orderName  = ORDER_TYPES[order.type]?.name || order.type;
      const isSelected = _selectedOrderForPlacement?.id === order.id;
      const btn = document.createElement('button');
      btn.className  = `abtn ${G.curP === 0 ? 'bp' : 'br'}`;
      btn.style.cssText = 'width:100%;margin-bottom:4px;';
      btn.textContent   = `${ORDER_TYPES[order.type]?.icon || '?'} ${orderName}`;
      btn.title = `${orderName} #${idx + 1}`;
      if (isSelected) {
        btn.style.filter    = 'brightness(1.3)';
        btn.style.boxShadow = '0 0 8px currentColor';
      }
      btn.onclick = () => selectOrderForPlacement(idx, order);
      poolEl.appendChild(btn);
    });
  } else {
    const placed = G.ordersPlaced[G.curP] || 0;
    if (placed >= 4) {
      poolEl.innerHTML = '<span style="color:var(--gold);font-size:.75rem">✓ Все 4 приказа размещены</span>';
    } else if (G.ui?.order_placed_this_turn) {
      poolEl.innerHTML = '<span class="rs-dim-sm">Приказ размещён. Передайте ход.</span>';
    } else {
      poolEl.innerHTML = '<span class="rs-dim-sm">Приказы выставлены</span>';
    }
  }

  const ordersOnField = G.orders.filter(o => o.owner === G.curP);
  if (!ordersOnField.length) return;

  const divider = _mkCls('rs-divider');
  divider.appendChild(_mkPtitle('ПРИКАЗЫ НА ПОЛЕ'));

  const byTile = {};
  ordersOnField.forEach(o => { (byTile[o.tile] = byTile[o.tile] || []).push(o); });

  Object.entries(byTile).sort().forEach(([tileKey, orders]) => {
    const tileInfo = _mkCls('rs-tile-info');
    tileInfo.appendChild(_mkCls('rs-tile-label', `📍 [${tileKey}]`));
    orders.forEach((o, i) => {
      const ot     = ORDER_TYPES[o.type];
      const abbrev = (ot?.name || o.type).substring(0, 3).toUpperCase();
      tileInfo.appendChild(_mkDiv('color:var(--dim);font-size:.7rem;margin-left:4px;', `${i + 1}. ${ot?.icon || '?'} ${abbrev}`));
    });
    divider.appendChild(tileInfo);
  });

  poolEl.appendChild(divider);
}

function _renderOrdersPlacedPhase() {
  const poolEl = _resetPanels();
  poolEl.innerHTML = `
    <div style="text-align:center;padding:10px;color:var(--gold);font-weight:bold;">
      ✓ ВСЕ ПРИКАЗЫ ВЫСТАВЛЕНЫ
    </div>
    <div style="margin-top:10px;color:var(--dim);font-size:.75rem;text-align:center;">
      Ожидание второго игрока...
    </div>
  `;
}

function _renderStrategizePhase() {
  const poolEl  = _resetPanels();
  const dtf = G.pending_direct_the_faithful;

  // Direct the Faithful: два независимых действия
  if (dtf && dtf.player_id === G.curP) {
    const cardsDone = !G.pending_strategize;
    const buildDone = dtf.replacement_done;
    const credits = G.players[G.curP].credits || 0;

    let html = '<div class="ptitle">⚜ DIRECT THE FAITHFUL</div>';
    html += `<div style="font-size:.75rem;color:#aaa;margin-bottom:12px;">Кредиты: ${credits}. Выполните оба действия в любом порядке.</div>`;

    if (buildDone) {
      html += '<button class="abtn" style="width:100%;margin-bottom:6px;opacity:.5;cursor:default;background:#333;" disabled>✓ Здание заменено</button>';
    } else {
      html += '<button class="abtn bp" style="width:100%;margin-bottom:6px;" onclick="_showDirectFaithfulModal()">🏛 Заменить здание</button>';
    }

    if (cardsDone) {
      html += '<button class="abtn" style="width:100%;opacity:.5;cursor:default;background:#333;" disabled>✓ Карты куплены</button>';
    } else {
      html += '<button class="abtn bp" style="width:100%;" onclick="renderStrategize()">🎯 Купить карты</button>';
    }

    poolEl.innerHTML = html;
    return;
  }

  // Обычный Strategize (без Direct the Faithful)
  const step    = G.pending_strategize.step || 'buy_combat_card';
  const credits = G.players[G.curP].credits || 0;

  let html = '<div class="ptitle">🎯 STRATEGIZE</div>';
  if (step === 'buy_combat_card') {
    html += `<div style="font-size:.75rem;color:#aaa;margin-bottom:8px;">Обменять боевую карту (${credits} кредитов)</div>`;
    html += '<button class="abtn bp" style="width:100%;margin-top:8px;" onclick="renderStrategize()">📋 Открыть обмен</button>';
  } else if (step === 'buy_order_upgrade') {
    html += `<div style="font-size:.75rem;color:#aaa;margin-bottom:8px;">Купить улучшение приказа (${credits} кредитов)</div>`;
    html += '<button class="abtn bp" style="width:100%;margin-top:8px;" onclick="renderStrategize()">⚔ Выбрать улучшение</button>';
  }

  poolEl.innerHTML = html;
}

function _renderDirectFaithfulPhase() {
  const poolEl = _resetPanels();
  const dtf = G.pending_direct_the_faithful;

  let html = '<div class="ptitle">⚜ DIRECT THE FAITHFUL</div>';
  html += `<div style="font-size:.75rem;color:#aaa;margin-bottom:12px;">Карты куплены. Система [${dtf.order_tile}].</div>`;

  if (dtf.replacement_done) {
    html += '<button class="abtn" style="width:100%;opacity:.5;cursor:default;background:#333;" disabled>✓ Здание заменено</button>';
    html += '<button class="abtn bp" style="width:100%;margin-top:8px;" onclick="directFaithfulSkipBuilding()">✓ Завершить ход</button>';
  } else {
    html += '<button class="abtn bp" style="width:100%;margin-bottom:6px;" onclick="_showDirectFaithfulModal()">🏛 Заменить здание</button>';
    html += '<button class="abtn" style="width:100%;background:#555;" onclick="directFaithfulSkipBuilding()">⊘ Пропустить замену</button>';
  }

  poolEl.innerHTML = html;
}

function _renderGreenTidePhase() {
  const poolEl = _resetPanels();
  const clsBtn = 'abtn ' + (G.curP === 0 ? 'bp' : 'br');
  const tileKey = G.pending_green_tide?.order_tile || '';

  let html = '<div class="ptitle">THE GREEN TIDE</div>';
  html += `<div style="font-size:.75rem;color:#aaa;margin-bottom:12px;">Тайл [${tileKey}]. Выберите тип приказа:</div>`;
  poolEl.innerHTML = html;

  const choices = [
    { type: 'dominate',   icon: ORDER_TYPES['dominate']?.icon   || '★', name: 'Dominate'   },
    { type: 'deploy',     icon: ORDER_TYPES['deploy']?.icon     || '★', name: 'Deploy'     },
    { type: 'advance',    icon: ORDER_TYPES['advance']?.icon    || '★', name: 'Advance'    },
    { type: 'strategize', icon: ORDER_TYPES['strategize']?.icon || '★', name: 'Strategize' },
  ];

  choices.forEach(c => {
    const btn = document.createElement('button');
    btn.className = clsBtn;
    btn.style.cssText = 'width:100%;margin-bottom:6px;';
    btn.textContent = `${c.icon} ${c.name}`;
    btn.onclick = () => chooseGreenTideOrder(c.type);
    poolEl.appendChild(btn);
  });
}

function _renderExecutionPhase() {
  const poolEl = _resetPanels();

  const discardBtn = document.getElementById('btn-discard-order');
  if (discardBtn) discardBtn.style.display = _selectedOrderForPlay ? 'block' : 'none';

  const ordersOnField = G.orders.filter(o => o.owner === G.curP);
  if (ordersOnField.length === 0) {
    poolEl.innerHTML = '<span class="rs-dim-sm">Нет приказов на поле. Нажмите ПЕРЕДАТЬ ХОД.</span>';
    return;
  }

  // Блок улучшений — вверху, сразу после выбора приказа
  if (_selectedOrderForPlay) {
    const usedKeys = new Set((G.upgrade_used_this_turn || [[], []])[G.curP] || []);
    const matchingUpgrades = (G.players[G.curP].hand_order_upgrades || [])
      .filter(u => u.order_type === _selectedOrderForPlay.type && !usedKeys.has(u.name || u.id));
    if (matchingUpgrades.length > 0) {
      const upgradeSection = document.createElement('div');
      upgradeSection.style.cssText = 'margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,.1);';
      upgradeSection.appendChild(_mkPtitle('УЛУЧШЕНИЯ'));
      matchingUpgrades.forEach(u => {
        const btn = document.createElement('button');
        btn.className = 'abtn ' + (G.curP === 0 ? 'bp' : 'br');
        btn.style.cssText = 'width:100%;margin-bottom:4px;font-size:.8rem;text-align:left;';
        btn.textContent = `⭐ ${u.name}`;
        btn.title = u.primary || '';
        btn.onclick = () => playOrderUpgradeViaAPI(_selectedOrderForPlay.id, [u.id]);
        upgradeSection.appendChild(btn);
      });
      if (matchingUpgrades.length >= 2) {
        const btnBoth = document.createElement('button');
        btnBoth.className = 'abtn ' + (G.curP === 0 ? 'bp' : 'br');
        btnBoth.style.cssText = 'width:100%;margin-bottom:4px;font-size:.7rem;';
        btnBoth.textContent = '⭐⭐ Сыграть оба улучшения';
        btnBoth.onclick = () => playOrderUpgradeViaAPI(
          _selectedOrderForPlay.id,
          matchingUpgrades.map(u => u.id)
        );
        upgradeSection.appendChild(btnBoth);
      }
      poolEl.appendChild(upgradeSection);
    }
  }

  const wrap = document.createElement('div');
  wrap.appendChild(_mkPtitle('ПРИКАЗЫ НА ПОЛЕ'));

  const byTile       = {};
  const playableIds  = new Set(G.ui?.playable_order_ids || []);
  const blockedTiles = new Set(G.ui?.blocked_tiles || []);

  ordersOnField.forEach(o => { (byTile[o.tile] = byTile[o.tile] || []).push(o); });

  Object.entries(byTile).sort().forEach(([tileKey, orders]) => {
    orders.sort((a, b) => (b.position || 0) - (a.position || 0));
    const blocked = blockedTiles.has(tileKey);

    const tileLabel = _mkDiv('font-size:.65rem;margin:6px 0 2px;text-transform:uppercase;letter-spacing:.05em;display:flex;align-items:center;gap:4px;');
    tileLabel.innerHTML = `<span style="color:var(--dim)">[${tileKey}]</span>${blocked ? '<span style="color:#ff6b6b;font-size:.6rem;">⊘ заблокирован</span>' : ''}`;
    wrap.appendChild(tileLabel);

    orders.forEach((order, stackIdx) => {
      const posNum     = stackIdx + 1;
      const isMyTop    = stackIdx === 0;
      const isPlayable = playableIds.has(order.id);
      const isSelected = _selectedOrderForPlay?.id === order.id;
      const ot         = ORDER_TYPES[order.type];
      const orderName  = ot?.name || order.type;

      const row = _mkDiv(`
        display:flex;align-items:center;gap:6px;padding:4px 6px;margin-bottom:3px;
        border-radius:5px;cursor:${isPlayable ? 'pointer' : 'default'};
        background:${isSelected ? 'rgba(255,220,50,.15)' : isMyTop && !blocked ? 'rgba(255,255,255,.05)' : 'rgba(255,255,255,.02)'};
        border:1px solid ${isSelected ? 'rgba(255,220,50,.6)' : isMyTop && !blocked ? 'rgba(255,255,255,.15)' : 'rgba(255,255,255,.06)'};
        opacity:${isMyTop ? '1' : '0.55'};
      `);

      const badge = _mkDiv(`
        min-width:16px;height:16px;border-radius:50%;
        background:${isPlayable ? (G.curP === 0 ? '#00c8ff' : '#ff4d6d') : '#444'};
        color:#fff;font-size:.6rem;font-weight:bold;
        display:flex;align-items:center;justify-content:center;flex-shrink:0;
      `, String(posNum));

      row.appendChild(badge);
      row.appendChild(_mkDiv('font-size:.72rem;flex:1;', `${ot?.icon || '?'} ${orderName}`));

      if (isPlayable) {
        row.onclick = () => selectOrderForPlay(order.id, order.type, tileKey);
        row.title = isSelected ? 'Нажмите ещё раз для розыгрыша' : `Выбрать: ${orderName}`;
      } else if (isMyTop && blocked) {
        row.title = 'Заблокирован приказом соперника';
      }

      wrap.appendChild(row);
    });
  });

  poolEl.appendChild(wrap);

  if (_selectedOrderForPlay) {
  }
}
