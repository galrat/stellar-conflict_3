'use strict';
// ══════════════════════════════════════════════
//  RENDER BOARD
// ══════════════════════════════════════════════
function renderBoard() {
  const board = document.getElementById('map-board');
  board.innerHTML = '';
  const tiles = Object.values(G.map);

  const cols = tiles.map(t=>t.col);
  const rows = tiles.map(t=>t.row);
  const minC=(cols.length?Math.min(...cols):0)-1;
  const minR=(rows.length?Math.min(...rows):0)-1;
  const maxC=(cols.length?Math.max(...cols):2)+1;
  const maxR=(rows.length?Math.max(...rows):1)+1;
  const W=(maxC-minC+1)*CELL, H=(maxR-minR+1)*CELL;
  board.style.width=W+'px'; board.style.height=H+'px';

  const px = (col,row) => ({left:(col-minC)*CELL, top:(row-minR)*CELL});

  // Drop cells (tile-placement phase)
  if (G.phase==='tile-placement' && G.selHandIdx!==null) {
    getValidDrops().forEach(({col,row}) => {
      const p=px(col,row);
      const el=document.createElement('div');
      el.className='drop-cell';
      el.style.cssText=`left:${p.left}px;top:${p.top}px;width:${CELL}px;height:${CELL}px;`;
      el.innerHTML='<span style="font-size:1.4rem;color:rgba(0,200,255,.5);font-family:Orbitron">+</span>';
      el.onclick=()=>dropTile(col,row);
      board.appendChild(el);
    });
  }

  // Placed tiles
  tiles.forEach(tile => {
    const p=px(tile.col,tile.row);
    const el=document.createElement('div');
    el.className='stile';
    el.classList.add(tile.isHome?(tile.owner===0?'hp1':'hp2'):(tile.owner===0?'np1':'np2'));
    const side = tile.side || 0;
    const imgSuffix = side === 0 ? 'a' : 'b';
    el.style.cssText=`left:${p.left}px;top:${p.top}px;width:${CELL}px;height:${CELL}px;`;

    // Rotating background image
    const bgWrap = document.createElement('div'); bgWrap.className = 'stile-bg';
    const bgImg  = document.createElement('div'); bgImg.className  = 'stile-bg-img';
    bgImg.style.backgroundImage = `url('tiles/${tile.tileDefId}_${imgSuffix}.png')`;
    bgImg.style.transform       = `rotate(${tile.rotation || 0}deg)`;
    bgWrap.appendChild(bgImg); el.appendChild(bgWrap);

    if (tile.isHome) {
      const hb=document.createElement('div'); hb.className='hbadge'; hb.textContent='\u{1F3E0}'; el.appendChild(hb);
    }
    const cb=document.createElement('div'); cb.className='tcoord';
    const sideLabel = side===1?' [B]':'';
    cb.textContent=tile.key+(tile.rotation?` ${tile.rotation}\u00b0`:'')+sideLabel; el.appendChild(cb);

    const inner=document.createElement('div'); inner.className='stilei';

    const rotAreas = getRotatedAreas(tile);
    rotAreas.forEach((area, displayIdx) => {
      const realIdx = tile.areas.indexOf(area);
      const ae=document.createElement('div');
      ae.className=`tarea a${area.type}`;

      const cap = area.capacity;
      const used = area.troops.length;
      const lbl=document.createElement('div'); lbl.className='atlbl';
      if (area.type==='planet') {
        const capMark = '\u25cf'.repeat(cap);
        const incMark = area.income   > 0 ? ` <span class="inc-mark">\u25cf${area.income}</span>`   : '';
        const valMark = area.valuable > 0 ? ` <span class="val-mark">\u25c6${area.valuable}</span>` : '';
        let lblHTML = capMark + incMark + valMark;
        if (area.support)  lblHTML += ' <span class="tok-sup">\u2295</span>';
        if (area.discount) lblHTML += ' <span class="tok-dis">\u2296</span>';
        if (area.forge)    lblHTML += ' <span class="tok-frg">\u2692</span>';
        if (area.joker)    lblHTML += ' <span class="tok-jok">\u2605</span>';
        lbl.innerHTML = lblHTML;
      } else {
        lbl.textContent = '\u2736';
      }
      ae.appendChild(lbl);
      const capEl=document.createElement('div'); capEl.className='acap';
      const pendingCount = G.pending_deploy?.tile_key === tile.key
        ? (G.pending_deploy.placed||[]).filter(p => p.area_idx === realIdx).length : 0;
      const effectiveUsed = used + pendingCount;
      capEl.textContent=`${effectiveUsed}/${cap}`;
      if (effectiveUsed>=cap) capEl.style.color='var(--accent2)';
      ae.appendChild(capEl);

      // Structures
      (area.structures||[]).forEach(s => {
        const info = STRUCTURE_INFO[s.type] || { icon:'?', label:s.type };
        const tok=document.createElement('div');
        tok.className='astruc';
        const sFacColor = FACTIONS.find(f=>f.id===G.players[s.player].faction)?.color || (s.player===0?'#00c8ff':'#ff4d6d');
        tok.style.background = hexAlpha(sFacColor, 0.5);
        tok.style.borderColor = sFacColor;
        tok.style.color = getTextColor(sFacColor);
        tok.textContent=info.icon; tok.title=info.label;
        ae.appendChild(tok);
      });

      // Troops
      area.troops.forEach(u => {
        const tok=document.createElement('div');
        const uFac = FACTIONS.find(f=>f.id===G.players[u.player].faction);
        const uColor = uFac?.color || (u.player===0?'#00c8ff':'#ff4d6d');
        tok.className=`atroop ${u.unitType}`;
        tok.style.background = hexAlpha(uColor, 0.15);
        tok.style.borderColor = uColor;
        tok.style.color = uColor;
        tok.textContent=`T${u.tier??0}`;
        tok.title=getUnitName(G.players[u.player].faction, u.unitType, u.tier??0);
        ae.appendChild(tok);
      });

      // Pending deploy units (not yet committed to tile.areas)
      {
        const pd = G.pending_deploy;
        if (pd && tile.key === pd.tile_key && pd.placed) {
          const cp = G.players[G.curP];
          const facColor = FACTIONS.find(f=>f.id===cp.faction)?.color || (G.curP===0?'#00c8ff':'#ff4d6d');
          const catalog = pd.deploy_info?.unit_catalog || [];
          pd.placed.filter(p => p.area_idx === realIdx).forEach(p => {
            const uInfo = catalog.find(c => c.unit_key === p.unit_key);
            const tok = document.createElement('div');
            const uType = _DEPLOY_UT[p.unit_key] || 'ground';
            tok.className = `atroop ${uType}`;
            tok.style.background = hexAlpha(facColor, 0.25);
            tok.style.borderColor = facColor;
            tok.style.color = facColor;
            tok.style.opacity = '0.7';
            tok.style.outline = '2px dashed ' + facColor;
            tok.textContent = `T${uInfo?.tier ?? 0}`;
            tok.title = `${uInfo?.name || p.unit_key} (ожидает)`;
            ae.appendChild(tok);
          });
        }
      }

      // Ownership highlight
      const h1=area.troops.some(t=>t.player===0), h2=area.troops.some(t=>t.player===1);
      if (h1&&h2) ae.classList.add('contested');
      else if (h1) ae.classList.add('h1');
      else if (h2) ae.classList.add('h2');

      // Подсветка допустимых зон при размещении войск
      if (G.phase === 'troop-on-tile' && tile.key === G.lastKey) {
        const cp2 = G.players[G.curP];
        if (G.selUnitIdx !== null) {
          const u = cp2.pool[G.selUnitIdx];
          if (u) ae.classList.add(isCompatible(u, area.type) && area.troops.length < area.capacity ? 'aok' : 'ano');
        } else if (G.selStructIdx !== null) {
          ae.classList.add(area.type === 'planet' && (!area.structures || area.structures.length === 0) ? 'aok' : 'ano');
        } else if (tile.needsObjective && !tile.objectiveMarker) {
          // Подсветить области для метки цели
          const eligIdxs = getObjectiveEligibleDisplayIdxs(tile);
          if (eligIdxs.includes(displayIdx) && area.type === 'planet') ae.classList.add('aok-obj');
        }
      }

      // Deploy highlighting
      {
        const pd = G.pending_deploy;
        if (pd && tile.key === pd.tile_key) {
          const info = pd.deploy_info || {};
          const availIdxs = new Set((info.available_areas || []).map(a => a.idx));
          if (pd.step === 'place_units' && _deploySelectedUnit) {
            const _UT = {infantry:'ground',marines:'ground',mechanized:'ground',elite:'ground',fighter:'space',destroyer:'space'};
            const uType = _UT[_deploySelectedUnit];
            const expected = uType === 'ground' ? 'planet' : 'space';
            ae.classList.add(availIdxs.has(realIdx) && area.type === expected ? 'aok' : 'ano');
          } else if (pd.step === 'buy_building' && _deploySelectedBuilding) {
            const planets = new Set(info.available_planets || []);
            ae.classList.add(planets.has(realIdx) ? 'aok' : 'ano');
          } else if (pd.step === 'resolve_overflow') {
            // Highlight overflow areas in red
            const cnt = (area.troops || []).length + (pd.placed || []).filter(p => p.area_idx === realIdx).length;
            if (cnt > area.capacity) ae.classList.add('ano');
          }
        }
      }

      // Метка цели
      if (tile.objectiveMarker && tile.objectiveMarker.realAreaIdx === realIdx) {
        const opPlayer = tile.objectiveMarker.owner;
        const opFac = FACTIONS.find(f => f.id === G.players[opPlayer].faction);
        const opColor = opFac?.color || (opPlayer === 0 ? '#00c8ff' : '#ff4d6d');
        const opIcon = opFac?.icon || (opPlayer === 0 ? 'P1' : 'P2');
        const marker = document.createElement('div');
        marker.className = 'obj-marker';
        marker.style.background = hexAlpha(opColor, 0.25);
        marker.style.borderColor = opColor;
        marker.style.color = opColor;
        marker.textContent = opIcon;
        marker.title = `Цель: ${G.players[opPlayer].name}`;
        ae.appendChild(marker);
      }

      ae.onclick=()=>areaClick(tile.key, displayIdx);
      inner.appendChild(ae);
    });

    el.appendChild(inner);

    // Центральная зона — размещение приказов (клик отправляет на API)
    const centerZone = document.createElement('div');
    centerZone.style.cssText = `
      position: absolute;
      left: 50%;
      top: 50%;
      width: 60px;
      height: 60px;
      transform: translate(-50%, -50%);
      cursor: ${G.phase === 'order-placement' ? 'pointer' : 'default'};
      z-index: 5;
      pointer-events: ${G.phase === 'order-placement' ? 'auto' : 'none'};
    `;
    if (G.phase === 'order-placement') {
      centerZone.onclick = (e) => {
        e.stopPropagation();
        placeOrderViaAPI(tile.key);
      };
    }
    el.appendChild(centerZone);

    // Отрисовка приказов на тайле (стопка в центре, смещение вверх-вправо)
    const tilesOrders = G.orders.filter(o => o.tile === tile.key)
      .sort((a, b) => (a.position || 0) - (b.position || 0));

    // Playable order IDs from server UI hints
    const boardPlayableIds = new Set(G.ui?.playable_order_ids || []);

    tilesOrders.forEach((order, idx) => {
      const orderEl = document.createElement('div');
      const fac = FACTIONS.find(f => f.id === G.players[order.owner].faction);
      const facIcon = fac?.icon || (order.owner === 0 ? 'P1' : 'P2');
      const orderName = ORDER_TYPES[order.type]?.name || order.type;

      // Смещение для стопки: каждый выше и правее (вверх-вправо)
      const offsetY = -idx * 5;
      const offsetX = idx * 5;

      const factionColor = G.players[order.owner].faction_color || (order.owner === 0 ? '#00c8ff' : '#ff4d6d');

      // Во время execution: кликабелен если сервер пометил как playable
      const isClickable = G.phase === 'execution' && boardPlayableIds.has(order.id);
      const isSelected  = _selectedOrderForPlay?.id === order.id;

      orderEl.className = `order-fd${isSelected ? ' selected-order' : ''}`;
      orderEl.style.cssText = `
        position: absolute;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 1px;
        font-family: 'Orbitron', monospace;
        pointer-events: ${isClickable ? 'auto' : 'none'};
        cursor: ${isClickable ? 'pointer' : 'default'};
        top: calc(50% + ${offsetY}px);
        left: calc(50% + ${offsetX}px);
        transform: translate(-50%, -50%);
        box-shadow: 0 2px 10px rgba(0,0,0,.85)${isSelected ? ', 0 0 0 3px rgba(255,220,50,.8)' : ''};
        z-index: ${10 + idx};
        background: #1a1a1a;
        border: 2px solid ${isSelected ? 'rgba(255,220,50,.9)' : '#333'};
        color: ${factionColor};
        clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
      `;
      orderEl.innerHTML = `
        <div style="font-size: 2rem; font-weight: bold; line-height: 1;">${facIcon}</div>
      `;
      orderEl.title = isClickable
        ? (isSelected ? `Нажмите ещё раз для розыгрыша: ${orderName}` : `Выбрать: ${orderName}`)
        : `${orderName} (${G.players[order.owner].name})`;

      if (isClickable) {
        orderEl.addEventListener('click', (e) => {
          e.stopPropagation();
          selectOrderForPlay(order.id, order.type, tile.key);
        });
      }

      el.appendChild(orderEl);
    });

    // Варп-штормы: визуализация + кликабельные границы в фазе warp-storm
    ['top','bottom','left','right'].forEach(side => {
      const isH = side === 'top' || side === 'bottom';
      const hasWS = G.warpStorms.some(ws => ws.tileKey === tile.key && ws.side === side);
      if (hasWS) {
        const ws = document.createElement('div');
        ws.className = `warp-storm warp-storm-${side} ${isH ? 'warp-storm-h' : 'warp-storm-v'}`;
        el.appendChild(ws);
      }
      const canPlaceWS = G.phase === 'warp-storm' && !hasWS && !G.warpStorms.some(ws => ws.owner === G.curP) && !G.warpConfirmed[G.curP];
      if (canPlaceWS) {
        const border = document.createElement('div');
        border.className = `ws-border ws-border-${isH ? 'h' : 'v'} warp-storm-${side}`;
        border.onclick = (e) => { e.stopPropagation(); placeWarpStorm(tile.key, side); };
        el.appendChild(border);
      }
    });

    board.appendChild(el);
  });
}


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
    lbl.textContent=ht.isHome?`${fac?.icon} \u0414\u043e\u043c\u0430\u0448\u043d\u044f\u044f`:`\u0421\u0438\u0441\u0442\u0435\u043c\u0430 ${idx+1}`;
    el.appendChild(prev); el.appendChild(lbl);
    el.onclick=()=>selectHandTile(idx);
    el.addEventListener('mouseenter', () => _startTileHover(el, ht.tileDefId));
    el.addEventListener('mouseleave', _cancelTileHover);
    handEl.appendChild(el);
  });
}


// ══════════════════════════════════════════════
//  HEADER
// ══════════════════════════════════════════════
function updateHeader() {
  const cp=G.players[G.curP];
  // Если идёт deploy — вычитаем зарезервированные ресурсы за юнитов из отображения
  const pd = G.pending_deploy;
  const unitCosts = (pd && pd.unit_costs) ? pd.unit_costs : null;
  const deployPlayer = pd ? pd.player_id : null;

  [0,1].forEach(pi=>{
    const p=G.players[pi], pfx=pi===0?'p1':'p2';
    document.getElementById(`h-${pfx}-name`).textContent=p.name;
    document.getElementById(`h-${pfx}-init`).textContent=p.name.substring(0,2).toUpperCase();
    const fac=FACTIONS.find(f=>f.id===p.faction);
    document.getElementById(`h-${pfx}-fac`).textContent=fac?`${fac.icon} ${fac.name}`:'—';
    const resEl = document.getElementById(`h-${pfx}-res`);
    if (resEl) {
      // Для игрока, выполняющего deploy, показываем скорректированные ресурсы
      const uc = (unitCosts && pi === deployPlayer) ? unitCosts : null;
      const credits  = (p.credits  ?? 0) - (uc?.credits ?? 0);
      const support  = (p.tokens?.support  ?? 0);
      const discount = (p.tokens?.discount ?? 0) - (uc?.cash    ?? 0);
      const forge    = (p.tokens?.forge    ?? 0) - (uc?.forge   ?? 0);
      const parts = [];
      if (p.credits != null) parts.push(`💰${credits}`);
      if (support)  parts.push(`⊕${support}`);
      if (discount) parts.push(`⊖${discount}`);
      if (forge)    parts.push(`⚒${forge}`);
      resEl.textContent = parts.join('  ') || '';
    }
  });
  const hRound = document.getElementById('h-round');
  if (hRound) hRound.textContent = G.round ? `Раунд ${G.round}` : 'Раунд —';

  const hObj0 = document.getElementById('h-obj-p1');
  const hObj1 = document.getElementById('h-obj-p2');
  if (hObj0) hObj0.textContent = `🎯 ${G.players[0]?.collected_objectives ?? 0}`;
  if (hObj1) hObj1.textContent = `🎯 ${G.players[1]?.collected_objectives ?? 0}`;

  const edsp = document.getElementById('event-stack-disp');
  if (edsp) edsp.style.display='none';
}
