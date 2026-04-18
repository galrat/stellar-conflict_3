'use strict';
// ══════════════════════════════════════════════
//  RENDER SIDE PANEL
// ══════════════════════════════════════════════
function renderSide() {
  _cancelTileHover(); _cancelTileHideTimer(); _dismissTilePreview();
  const cp = G.players[G.curP];

  // В фазе размещения войск — показываем пул, скрываем руку тайлов
  const poolSection   = document.getElementById('unit-pool-section');
  const structSection = document.getElementById('struct-pool-section');
  if (G.phase === 'troop-on-tile') {
    document.getElementById('tile-hand').innerHTML = '';

    // Пул юнитов
    const poolEl = document.getElementById('unit-pool');
    poolSection.style.display = 'block';
    poolEl.innerHTML = '';
    if (cp.pool.length > 0) {
      cp.pool.forEach((u, idx) => {
        const tok = document.createElement('div');
        const fac = FACTIONS.find(f=>f.id===cp.faction);
        const facColor = fac?.color || (G.curP===0?'#00c8ff':'#ff4d6d');
        tok.className = `ttok ${u.unitType}${G.selUnitIdx===idx?' sel':''}`;
        tok.style.background = hexAlpha(facColor, 0.15);
        tok.style.borderColor = facColor;
        tok.style.color = facColor;
        tok.textContent = `T${u.tier??0}`;
        tok.title = getUnitName(cp.faction, u.unitType, u.tier??0);
        tok.onclick = () => selectUnitFromPool(idx);
        poolEl.appendChild(tok);
      });
    } else {
      poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Нет войск</span>';
    }

    // Пул построек
    const structEl = document.getElementById('struct-pool');
    if (cp.structurePool && cp.structurePool.length > 0) {
      structSection.style.display = 'block';
      structEl.innerHTML = '';
      cp.structurePool.forEach((s, idx) => {
        const info = STRUCTURE_INFO[s.type] || { icon:'?', label:s.type };
        const tok = document.createElement('div');
        tok.className = `ttok stok ${G.curP===0?'c1':'c2'}${G.selStructIdx===idx?' sel':''}`;
        tok.innerHTML = info.icon;
        tok.title = info.label;
        tok.onclick = () => selectStructFromPool(idx);
        structEl.appendChild(tok);
      });
    } else {
      structSection.style.display = 'none';
    }
    return;
  }

  // В фазе расстановки приказов — показываем приказы через API
  if (G.phase === 'order-placement') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';

    // Раздел 1: Приказы в руке (используем G.ui для логики)
    const canPlace = G.ui?.can_place_order;

    if (cp.hand_orders && cp.hand_orders.length > 0 && canPlace) {
      cp.hand_orders.forEach((order, idx) => {
        const btn = document.createElement('button');
        const orderName = ORDER_TYPES[order.type]?.name || order.type;
        const isSelected = _selectedOrderForPlacement?.id === order.id;

        btn.className = `abtn ${G.curP===0?'bp':'br'}`;
        btn.style.width = '100%';
        btn.style.marginBottom = '4px';
        btn.textContent = `${ORDER_TYPES[order.type]?.icon || '?'} ${orderName}`;
        btn.title = `${orderName} #${idx+1}`;

        if (isSelected) {
          btn.style.filter = 'brightness(1.3)';
          btn.style.boxShadow = '0 0 8px currentColor';
        }

        btn.onclick = () => selectOrderForPlacement(idx, order);
        poolEl.appendChild(btn);
      });
    } else {
      const ordersPlacedCount = G.ordersPlaced[G.curP] || 0;
      if (ordersPlacedCount >= 4) {
        poolEl.innerHTML = '<span style="color:var(--gold);font-size:.75rem">✓ Все 4 приказа размещены</span>';
      } else if (G.ui?.order_placed_this_turn) {
        poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Приказ размещён. Передайте ход.</span>';
      } else {
        poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Приказы выставлены</span>';
      }
    }

    // Раздел 2: Приказы на поле (только текущего игрока)
    const ordersOnField = G.orders.filter(o => o.owner === G.curP);
    if (ordersOnField.length > 0) {
      const divider = document.createElement('div');
      divider.style.cssText = 'margin-top:10px;padding-top:8px;border-top:1px solid var(--border);';

      const title = document.createElement('div');
      title.className = 'ptitle';
      title.textContent = 'ПРИКАЗЫ НА ПОЛЕ';
      divider.appendChild(title);

      // Группируем приказы по системам
      const ordersByTile = {};
      ordersOnField.forEach(o => {
        if (!ordersByTile[o.tile]) ordersByTile[o.tile] = [];
        ordersByTile[o.tile].push(o);
      });

      // Выводим каждую систему с приказами
      Object.entries(ordersByTile).sort().forEach(([tileKey, orders]) => {
        const tileInfo = document.createElement('div');
        tileInfo.style.cssText = 'margin-top:6px;padding:6px;background:rgba(255,255,255,.05);border-radius:4px;font-size:.75rem;';

        const tileLabel = document.createElement('div');
        tileLabel.style.cssText = 'font-weight:bold;color:var(--gold);margin-bottom:3px;';
        tileLabel.textContent = `📍 [${tileKey}]`;
        tileInfo.appendChild(tileLabel);

        // Приказы в этой системе
        orders.forEach((o, i) => {
          const orderDisplay = document.createElement('div');
          const orderType = ORDER_TYPES[o.type];
          const abbrev = (orderType?.name || o.type).substring(0, 3).toUpperCase();
          orderDisplay.style.cssText = `color:var(--dim);font-size:.7rem;margin-left:4px;`;
          orderDisplay.textContent = `${i+1}. ${orderType?.icon || '?'} ${abbrev}`;
          tileInfo.appendChild(orderDisplay);
        });

        divider.appendChild(tileInfo);
      });

      poolEl.appendChild(divider);
    }

    return;
  }

  // ── ФАЗА ОЖИДАНИЯ (ORDERS_PLACED) ──
  if (G.phase === 'orders_placed') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = `
      <div style="text-align:center;padding:10px;color:var(--gold);font-weight:bold;">
        ✓ ВСЕ ПРИКАЗЫ ВЫСТАВЛЕНЫ
      </div>
      <div style="margin-top:10px;color:var(--dim);font-size:.75rem;text-align:center;">
        Ожидание второго игрока...
      </div>
    `;

    return;
  }

  // ── DEPLOY: place_units — юниты в левой панели ──
  if (G.phase === 'execution' && G.pending_deploy?.step === 'place_units') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const pd      = G.pending_deploy;
    const hand    = pd.hand || [];
    const placed  = pd.placed || [];
    const catalog = pd.deploy_info?.unit_catalog || [];

    const cp2 = G.players[G.curP];
    const facColor = FACTIONS.find(f=>f.id===cp2.faction)?.color || (G.curP===0?'#00c8ff':'#ff4d6d');

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';

    const title = document.createElement('div');
    title.className = 'ptitle';
    title.textContent = 'DEPLOY: размещение войск';
    poolEl.appendChild(title);

    const hint = document.createElement('div');
    hint.style.cssText = 'font-size:.68rem;color:var(--gold);margin-bottom:6px;';
    hint.textContent = _deploySelectedUnit
      ? `✓ Выбран: ${_deploySelectedUnit} — кликните область на карте`
      : '← Выберите юнит, затем кликните область на тайле';
    poolEl.appendChild(hint);

    // Сколько ещё нужно разместить (с учётом дублей)
    const handRem = [...hand];
    for (const p of placed) {
      const i = handRem.indexOf(p.unit_key);
      if (i >= 0) handRem.splice(i, 1);
    }
    const toPlace = handRem;
    // Группируем для отображения
    const ukCounts = {};
    toPlace.forEach(uk => { ukCounts[uk] = (ukCounts[uk] || 0) + 1; });

    if (Object.keys(ukCounts).length === 0) {
      const empty = document.createElement('div');
      empty.style.cssText = 'color:var(--gold);font-size:.75rem;';
      empty.textContent = '✓ Все войска размещены';
      poolEl.appendChild(empty);
    } else {
      Object.entries(ukCounts).forEach(([uk, cnt]) => {
        const u = catalog.find(c => c.unit_key === uk);
        const isSelected = _deploySelectedUnit === uk;
        const tok = document.createElement('div');
        tok.className = `ttok ${_DEPLOY_UT[uk] || 'ground'}${isSelected ? ' sel' : ''}`;
        tok.style.background   = hexAlpha(facColor, isSelected ? 0.35 : 0.15);
        tok.style.borderColor  = facColor;
        tok.style.color        = facColor;
        tok.textContent = `T${u?.tier ?? 0}${cnt > 1 ? ' ×' + cnt : ''}`;
        tok.title       = u?.name || uk;
        tok.onclick     = () => { _deploySelectedUnit = uk; renderSide(); renderBoard(); };
        poolEl.appendChild(tok);
      });
    }

    return;
  }

  // ── DEPLOY: buy_building — здания в левой панели ──
  if (G.phase === 'execution' && G.pending_deploy?.step === 'buy_building') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const pd      = G.pending_deploy;
    const info    = pd.deploy_info || {};
    const credits = info.credits - (pd.unit_costs?.credits || 0);
    const cash    = info.cash_tokens - (pd.unit_costs?.cash || 0);
    const pool    = info.structure_pool || [];

    const poolCounts = {};
    for (const s of pool) poolCounts[s.type] = (poolCounts[s.type] || 0) + 1;
    const bTypes = Object.keys(poolCounts);

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';

    const title = document.createElement('div');
    title.className = 'ptitle';
    title.textContent = 'DEPLOY: постройка';
    poolEl.appendChild(title);

    const resLine = document.createElement('div');
    resLine.style.cssText = 'font-size:.72rem;color:var(--dim);margin-bottom:6px;';
    resLine.textContent = `💰${credits}  cash:${cash}`;
    poolEl.appendChild(resLine);

    if (bTypes.length > 0) {
      bTypes.forEach(bt => {
        const cost = _DEPLOY_COSTS[bt] || 0;
        const cashDiscount = cash > 0 ? 2 : 0;
        const canAfford = credits >= cost || (cash > 0 && credits >= Math.max(0, cost - cashDiscount));
        const isSelected = _deploySelectedBuilding === bt;
        const btn = document.createElement('button');
        btn.className = `abtn ${isSelected ? 'bg' : 'bp'}`;
        btn.style.cssText = 'width:100%;margin-bottom:4px;';
        btn.disabled = !canAfford;
        btn.title = !canAfford ? 'Не хватает кредитов' : '';
        btn.textContent = `${_DEPLOY_ICONS[bt] || '🏠'} ${bt} (${cost}💰) ×${poolCounts[bt]}`;
        btn.onclick = () => _deploySelectBuilding(bt);
        poolEl.appendChild(btn);
      });
    } else {
      const empty = document.createElement('div');
      empty.style.cssText = 'color:var(--dim);font-size:.75rem;';
      empty.textContent = 'Резерв построек пуст';
      poolEl.appendChild(empty);
    }

    if (_deploySelectedBuilding) {
      const hint = document.createElement('div');
      hint.style.cssText = 'font-size:.68rem;color:var(--gold);margin:6px 0;';
      hint.textContent = `✓ Выбрано: ${_DEPLOY_ICONS[_deploySelectedBuilding] || ''} ${_deploySelectedBuilding} — кликните планету на карте`;
      poolEl.appendChild(hint);

      if (cash > 0) {
        const cashLabel = document.createElement('label');
        cashLabel.style.cssText = 'font-size:.75rem;display:flex;align-items:center;gap:6px;cursor:pointer;margin-bottom:6px;';
        cashLabel.innerHTML = `<input type="checkbox" id="deploy-use-cash-panel"> Cash токен (−2💰)`;
        poolEl.appendChild(cashLabel);
      }
    }

    const skipBtn = document.createElement('button');
    skipBtn.className = 'abtn bw';
    skipBtn.style.cssText = 'width:100%;margin-top:8px;';
    skipBtn.textContent = 'Пропустить постройку →';
    skipBtn.onclick = () => _deploySkipBuilding();
    poolEl.appendChild(skipBtn);

    return;
  }

  // ── ADVANCE: choose_source ──
  if (G.phase === 'execution' && G.pending_advance?.step === 'choose_source') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block'; structSection.style.display = 'none';
    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';
    const pa = G.pending_advance;
    const t0 = document.createElement('div'); t0.className = 'ptitle'; t0.textContent = 'ADVANCE: выбор источника'; poolEl.appendChild(t0);
    const h0 = document.createElement('div'); h0.style.cssText = 'font-size:.72rem;color:var(--dim);margin-bottom:8px;'; h0.textContent = 'Выберите соседнюю систему с вашими войсками или пропустите'; poolEl.appendChild(h0);
    (pa.adjacent_tiles || []).forEach(tk => {
      const btn = document.createElement('button');
      btn.className = `abtn ${G.curP===0?'bp':'br'}`; btn.style.cssText = 'width:100%;margin-bottom:4px;';
      btn.textContent = `📍 Система [${tk}]`; btn.onclick = () => _advanceChooseSource(tk); poolEl.appendChild(btn);
    });
    if (!(pa.adjacent_tiles || []).length) {
      const em = document.createElement('div'); em.style.cssText = 'color:var(--dim);font-size:.75rem;margin-bottom:8px;'; em.textContent = 'Нет соседних систем с вашими войсками'; poolEl.appendChild(em);
    }
    const sk = document.createElement('button'); sk.className = 'abtn bw'; sk.style.cssText = 'width:100%;margin-top:4px;';
    sk.textContent = 'Пропустить (только активная система)'; sk.onclick = () => _advanceChooseSource(null); poolEl.appendChild(sk);
    return;
  }

  // ── ADVANCE: ships ──
  if (G.phase === 'execution' && G.pending_advance?.step === 'ships') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block'; structSection.style.display = 'none';
    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';
    const pa = G.pending_advance;
    const avail = G.ui?.advance_available_ships || [];
    const facColor = FACTIONS.find(f=>f.id===cp.faction)?.color || (G.curP===0?'#00c8ff':'#ff4d6d');
    const t1 = document.createElement('div'); t1.className = 'ptitle'; t1.textContent = 'ADVANCE: корабли'; poolEl.appendChild(t1);
    const h1 = document.createElement('div'); h1.style.cssText = 'font-size:.68rem;color:var(--gold);margin-bottom:6px;';
    h1.textContent = _advanceSelectedShip ? '✓ Корабль выбран — кликните область в активной системе' : '← Выберите корабль, затем кликните область назначения';
    poolEl.appendChild(h1);
    if (avail.length > 0) {
      const sub = document.createElement('div'); sub.style.cssText = 'font-size:.65rem;color:var(--dim);text-transform:uppercase;margin-bottom:4px;letter-spacing:.04em;'; sub.textContent = 'Доступные корабли:'; poolEl.appendChild(sub);
      avail.forEach(s => {
        const isSel = _advanceSelectedShip?.area_idx === s.area_idx && _advanceSelectedShip?.origin === s.origin;
        const tok = document.createElement('div');
        tok.className = `ttok space${isSel?' sel':''}`;
        tok.style.background = hexAlpha(facColor, isSel?0.35:0.15); tok.style.borderColor = facColor; tok.style.color = facColor;
        tok.textContent = `T${s.unit.tier??0}`;
        tok.title = `${getUnitName(cp.faction,'space',s.unit.tier??0)} (${s.origin==='source'?'из источника':'активный'})`;
        tok.onclick = () => _advanceSelectShip(s); poolEl.appendChild(tok);
      });
    } else {
      const em = document.createElement('div'); em.style.cssText = 'color:var(--dim);font-size:.75rem;margin-bottom:6px;'; em.textContent = 'Нет доступных кораблей'; poolEl.appendChild(em);
    }
    if ((pa.committed_moves||[]).length > 0) {
      const mv = document.createElement('div'); mv.style.cssText = 'margin-top:6px;font-size:.65rem;color:var(--dim);'; mv.textContent = `Перемещений: ${pa.committed_moves.length}`; poolEl.appendChild(mv);
    }
    const nxt = document.createElement('button'); nxt.className = `abtn ${G.curP===0?'bp':'br'}`; nxt.style.cssText = 'width:100%;margin-top:8px;';
    nxt.textContent = 'Готово с кораблями →'; nxt.onclick = () => _advanceNextStep(); poolEl.appendChild(nxt);
    return;
  }

  // ── ADVANCE: ground ──
  if (G.phase === 'execution' && G.pending_advance?.step === 'ground') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block'; structSection.style.display = 'none';
    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';
    const pa = G.pending_advance;
    const avail = G.ui?.advance_available_ground || [];
    const facColor = FACTIONS.find(f=>f.id===cp.faction)?.color || (G.curP===0?'#00c8ff':'#ff4d6d');
    const t2 = document.createElement('div'); t2.className = 'ptitle'; t2.textContent = 'ADVANCE: наземные юниты'; poolEl.appendChild(t2);
    const h2 = document.createElement('div'); h2.style.cssText = 'font-size:.68rem;color:var(--gold);margin-bottom:6px;';
    h2.textContent = _advanceSelectedGround ? '✓ Юнит выбран — кликните планету в активной системе' : '← Выберите юнита, затем кликните планету назначения';
    poolEl.appendChild(h2);
    if (avail.length > 0) {
      const sub = document.createElement('div'); sub.style.cssText = 'font-size:.65rem;color:var(--dim);text-transform:uppercase;margin-bottom:4px;letter-spacing:.04em;'; sub.textContent = 'Доступные юниты:'; poolEl.appendChild(sub);
      avail.forEach(g => {
        const isSel = _advanceSelectedGround?.area_idx === g.area_idx && _advanceSelectedGround?.origin === g.origin;
        const tok = document.createElement('div');
        tok.className = `ttok ground${isSel?' sel':''}`;
        tok.style.background = hexAlpha(facColor, isSel?0.35:0.15); tok.style.borderColor = facColor; tok.style.color = facColor;
        tok.textContent = `T${g.unit.tier??0}`;
        tok.title = `${getUnitName(cp.faction,'ground',g.unit.tier??0)} (${g.origin==='source'?'из источника':'активный'})`;
        tok.onclick = () => _advanceSelectGround(g); poolEl.appendChild(tok);
      });
    } else {
      const em = document.createElement('div'); em.style.cssText = 'color:var(--dim);font-size:.75rem;margin-bottom:6px;'; em.textContent = 'Нет доступных наземных юнитов'; poolEl.appendChild(em);
    }
    if ((pa.committed_moves||[]).length > 0) {
      const mv = document.createElement('div'); mv.style.cssText = 'margin-top:6px;font-size:.65rem;color:var(--dim);'; mv.textContent = `Перемещений: ${pa.committed_moves.length}`; poolEl.appendChild(mv);
    }
    const cmt = document.createElement('button'); cmt.className = `abtn ${G.curP===0?'bp':'br'}`; cmt.style.cssText = 'width:100%;margin-top:8px;';
    cmt.textContent = 'Зафиксировать перемещения →'; cmt.onclick = () => _advanceCommit(); poolEl.appendChild(cmt);
    return;
  }

  // ── ADVANCE: combat ──
  if (G.phase === 'execution' && G.pending_advance?.step === 'combat') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block'; structSection.style.display = 'none';
    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';
    const pa = G.pending_advance;
    const t3 = document.createElement('div'); t3.className = 'ptitle'; t3.textContent = 'ADVANCE: бой'; poolEl.appendChild(t3);
    const info = document.createElement('div'); info.style.cssText = 'font-size:.8rem;color:#ff6b6b;margin-bottom:8px;';
    info.textContent = `⚔ Спорная область [${pa.tile_key}] #${pa.contest_area_idx}`; poolEl.appendChild(info);
    const h3 = document.createElement('div'); h3.style.cssText = 'font-size:.72rem;color:var(--dim);margin-bottom:10px;';
    h3.textContent = 'Оба игрока имеют войска в одной области.'; poolEl.appendChild(h3);
    const fightBtn = document.createElement('button'); fightBtn.style.cssText = 'width:100%;background:rgba(255,77,109,.15);border-color:rgba(255,77,109,.5);';
    fightBtn.className = 'abtn bp'; fightBtn.textContent = '⚔ Начать бой!'; fightBtn.onclick = () => _advanceFight(); poolEl.appendChild(fightBtn);
    return;
  }

  // ── ADVANCE: orbital ──
  if (G.phase === 'execution' && G.pending_advance?.step === 'orbital') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block'; structSection.style.display = 'none';
    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';
    const t4 = document.createElement('div'); t4.className = 'ptitle'; t4.textContent = 'ADVANCE: орбитальный удар'; poolEl.appendChild(t4);
    const h4 = document.createElement('div'); h4.style.cssText = 'font-size:.72rem;color:var(--gold);margin-bottom:8px;';
    h4.textContent = _advanceOrbitalShipArea === null
      ? '1. Кликните область с вашим кораблём на карте'
      : `2. Кликните планету противника для удара (корабль: обл.${_advanceOrbitalShipArea})`;
    poolEl.appendChild(h4);
    const sk2 = document.createElement('button'); sk2.className = 'abtn bw'; sk2.style.cssText = 'width:100%;margin-top:4px;';
    sk2.textContent = 'Пропустить орбитальный удар'; sk2.onclick = () => _advanceSkipOrbital(); poolEl.appendChild(sk2);
    return;
  }

  // ── ADVANCE: orbital_defend ──
  if (G.phase === 'execution' && G.pending_advance?.step === 'orbital_defend') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block'; structSection.style.display = 'none';
    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';
    const pa = G.pending_advance;
    const defIdx = 1 - pa.player_id;
    const t5 = document.createElement('div'); t5.className = 'ptitle'; t5.textContent = 'ADVANCE: защита'; poolEl.appendChild(t5);
    const h5 = document.createElement('div'); h5.style.cssText = 'font-size:.75rem;color:#ff6b6b;margin-bottom:8px;';
    h5.textContent = `⏳ ${G.players[defIdx].name} выбирает юнита...`; poolEl.appendChild(h5);
    return;
  }

  // ── ФАЗА РОЗЫГРЫША ПРИКАЗОВ (EXECUTION) ──
  if (G.phase === 'execution') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const poolEl = document.getElementById('unit-pool');
    poolEl.innerHTML = '';

    // Показать кнопку сброса если выбран приказ
    const discardBtn = document.getElementById('btn-discard-order');
    if (discardBtn) {
      discardBtn.style.display = _selectedOrderForPlay ? 'block' : 'none';
    }

    const ordersOnField = G.orders.filter(o => o.owner === G.curP);

    if (ordersOnField.length === 0) {
      poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Нет приказов на поле. Нажмите ПЕРЕДАТЬ ХОД.</span>';
      return;
    }

    const wrap = document.createElement('div');

    const title = document.createElement('div');
    title.className = 'ptitle';
    title.textContent = 'ПРИКАЗЫ НА ПОЛЕ';
    wrap.appendChild(title);

    // Группируем по системам
    const ordersByTile = {};
    ordersOnField.forEach(o => {
      if (!ordersByTile[o.tile]) ordersByTile[o.tile] = [];
      ordersByTile[o.tile].push(o);
    });

    const playableIds  = new Set(G.ui?.playable_order_ids || []);
    const blockedTiles = new Set(G.ui?.blocked_tiles || []);

    Object.entries(ordersByTile).sort().forEach(([tileKey, orders]) => {
      // Сортируем: наибольшая position = верхний = позиция 1
      orders.sort((a, b) => (b.position || 0) - (a.position || 0));

      const blockedByOpponent = blockedTiles.has(tileKey);

      const tileLabel = document.createElement('div');
      tileLabel.style.cssText = 'font-size:.65rem;margin:6px 0 2px;text-transform:uppercase;letter-spacing:.05em;display:flex;align-items:center;gap:4px;';
      tileLabel.innerHTML = `<span style="color:var(--dim)">[${tileKey}]</span>${blockedByOpponent ? '<span style="color:#ff6b6b;font-size:.6rem;">⊘ заблокирован</span>' : ''}`;
      wrap.appendChild(tileLabel);

      orders.forEach((order, stackIdx) => {
        const posNum = stackIdx + 1;  // 1 = верхний в своей стопке
        const isMyTop    = stackIdx === 0;
        const isPlayable = playableIds.has(order.id);
        const isSelected = _selectedOrderForPlay?.id === order.id;
        const orderType  = ORDER_TYPES[order.type];
        const orderName  = orderType?.name || order.type;

        const row = document.createElement('div');
        row.style.cssText = `
          display:flex;align-items:center;gap:6px;padding:4px 6px;margin-bottom:3px;
          border-radius:5px;cursor:${isPlayable?'pointer':'default'};
          background:${isSelected ? 'rgba(255,220,50,.15)' : isMyTop && !blockedByOpponent ? 'rgba(255,255,255,.05)' : 'rgba(255,255,255,.02)'};
          border:1px solid ${isSelected ? 'rgba(255,220,50,.6)' : isMyTop && !blockedByOpponent ? 'rgba(255,255,255,.15)' : 'rgba(255,255,255,.06)'};
          opacity:${isMyTop ? '1' : '0.55'};
        `;

        const numBadge = document.createElement('span');
        numBadge.style.cssText = `
          min-width:16px;height:16px;border-radius:50%;
          background:${isPlayable ? (G.curP===0?'#00c8ff':'#ff4d6d') : '#444'};
          color:#fff;font-size:.6rem;font-weight:bold;
          display:flex;align-items:center;justify-content:center;flex-shrink:0;
        `;
        numBadge.textContent = posNum;

        const label = document.createElement('span');
        label.style.cssText = 'font-size:.72rem;flex:1;';
        label.textContent = `${orderType?.icon || '?'} ${orderName}`;

        row.appendChild(numBadge);
        row.appendChild(label);

        if (isPlayable) {
          row.onclick = () => selectOrderForPlay(order.id, order.type, tileKey);
          row.title = isSelected
            ? 'Нажмите ещё раз для розыгрыша'
            : `Выбрать: ${orderName}`;
        } else if (isMyTop && blockedByOpponent) {
          row.title = 'Заблокирован приказом соперника';
        }

        wrap.appendChild(row);
      });
    });

    poolEl.appendChild(wrap);
    return;
  }

  // ── ФАЗА КОНЦА РАУНДА (END-ROUND) ──
  if (G.phase === 'end-round') {
    document.getElementById('tile-hand').innerHTML = '';
    poolSection.style.display = 'block';
    structSection.style.display = 'none';

    const poolEl = document.getElementById('unit-pool');
    const roundNum = G.round || 1;
    const totalRounds = G.totalRounds || 8;
    poolEl.innerHTML = `
      <div style="text-align:center;padding:10px;color:var(--gold);font-weight:bold;">
        ✓ РАУНД ${roundNum}/${totalRounds} ЗАВЕРШЁН
      </div>
      <div style="margin-top:10px;color:var(--dim);font-size:.75rem;text-align:center;">
        Все приказы разыграны. Сброшенные приказы возвращены в руки.
      </div>
    `;

    return;
  }

  // В других фазах — скрыть пул
  if (poolSection)   poolSection.style.display   = 'none';
  if (structSection) structSection.style.display = 'none';

  // Tile hand
  const handEl = document.getElementById('tile-hand');
  handEl.innerHTML = '';
  cp.hand.forEach((ht, idx) => {
    if (ht.placed) return;
    const el=document.createElement('div');
    el.className=`htile${ht.isHome?' hthome':''}`;
    if (G.selHandIdx===idx) el.classList.add(cp.color==='c1'?'hs1':'hs2');
    const tileDef=TILE_CATALOG.find(t=>t.id===ht.tileDefId);
    const sideLayout=tileDef?tileDef.sides[0].layout.flat():[];
    const prev=document.createElement('div'); prev.className='hpreview';
    sideLayout.forEach(v=>{ const d=document.createElement('div'); d.className=`hpa ${v===1?'hpp':'hps'}`; prev.appendChild(d); });
    const lbl=document.createElement('div'); lbl.className='htlabel';
    const fac=FACTIONS.find(f=>f.id===cp.faction);
    lbl.textContent=ht.isHome?`${fac?.icon} Домашняя`:`Система ${idx+1}`;
    el.appendChild(prev); el.appendChild(lbl);
    el.onclick=()=>selectHandTile(idx);
    el.addEventListener('mouseenter', () => _startTileHover(el, ht.tileDefId));
    el.addEventListener('mouseleave', _cancelTileHover);
    handEl.appendChild(el);
  });
}
