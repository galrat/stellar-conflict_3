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
      ae.dataset.areaIdx=realIdx; # добавил, чтобы было ясно где область находится без обращения к вращению тайла

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
      {
        // Advance: compute how many units were moved away from this area
        const paAdv = G.pending_advance;
        const advCommits = paAdv?.committed_moves || [];
        const advActiveTile = paAdv?.tile_key;
        const advSourceTile = paAdv?.source_tile;
        const advStep = paAdv?.step;
        const isAdvActiveTile = tile.key === advActiveTile;
        const isAdvSourceTile = tile.key === advSourceTile;

        const movedOut = {}; // `${unitType}${tier}` => count of moved-away units
        advCommits.forEach(m => {
          const isFromHere = (
            (m.origin === 'active' && isAdvActiveTile && m.from_area_idx === realIdx) ||
            (m.origin === 'source' && isAdvSourceTile && m.from_area_idx === realIdx)
          );
          if (isFromHere) {
            const k = `${m.unit.unitType}${m.unit.tier ?? 0}`;
            movedOut[k] = (movedOut[k] || 0) + 1;
          }
        });
        const skipCounts = { ...movedOut };

        area.troops.forEach(u => {
          // Bug 3: skip units committed away from this area
          const k = `${u.unitType}${u.tier ?? 0}`;
          if (u.player === G.curP && skipCounts[k] > 0) {
            skipCounts[k]--;
            return;
          }

          const tok=document.createElement('div');
          const uFac = FACTIONS.find(f=>f.id===G.players[u.player].faction);
          const uColor = uFac?.color || (u.player===0?'#00c8ff':'#ff4d6d');
          tok.className=`atroop ${u.unitType}`;
          tok.style.background = hexAlpha(uColor, 0.15);
          tok.style.borderColor = uColor;
          tok.style.color = uColor;
          tok.textContent=`T${u.tier??0}`;
          tok.title=getUnitName(G.players[u.player].faction, u.unitType, u.tier??0);

          // Bug 2: clickable token on map for advance unit selection
          if (paAdv && u.player === G.curP && (isAdvActiveTile || isAdvSourceTile)) {
            const origin = isAdvActiveTile ? 'active' : 'source';
            if (advStep === 'ships' && u.unitType === 'space') {
              const shipData = (G.ui?.advance_available_ships || [])
                .find(s => s.area_idx === realIdx && s.origin === origin);
              if (shipData) {
                tok.style.cursor = 'pointer';
                tok.style.boxShadow = `0 0 4px ${uColor}`;
                const isSel = _advanceSelectedShip?.area_idx === realIdx && _advanceSelectedShip?.origin === origin;
                if (isSel) tok.style.outline = `2px solid ${uColor}`;
                tok.onclick = (e) => { e.stopPropagation(); _advanceSelectShip(shipData); };
              }
            } else if (advStep === 'ground' && u.unitType === 'ground') {
              const unitData = (G.ui?.advance_available_ground || [])
                .find(g => g.area_idx === realIdx && g.origin === origin);
              if (unitData) {
                tok.style.cursor = 'pointer';
                tok.style.boxShadow = `0 0 4px ${uColor}`;
                const isSel = _advanceSelectedGround?.area_idx === realIdx && _advanceSelectedGround?.origin === origin;
                if (isSel) tok.style.outline = `2px solid ${uColor}`;
                tok.onclick = (e) => { e.stopPropagation(); _advanceSelectGround(unitData); };
              }
            }
          }

          ae.appendChild(tok);
        });

        // Bug 3: ghost units at destination areas (committed_moves TO this area)
        if (paAdv && isAdvActiveTile) {
          const cp = G.players[G.curP];
          const facColor = FACTIONS.find(f=>f.id===cp.faction)?.color || (G.curP===0?'#00c8ff':'#ff4d6d');
          advCommits.forEach(m => {
            if (m.to_area_idx !== realIdx) return;
            const tok = document.createElement('div');
            tok.className = `atroop ${m.unit.unitType}`;
            tok.style.background = hexAlpha(facColor, 0.2);
            tok.style.borderColor = facColor;
            tok.style.color = facColor;
            tok.style.opacity = '0.75';
            tok.style.outline = '2px dashed ' + facColor;
            tok.textContent = `T${m.unit.tier ?? 0}`;
            tok.title = `${getUnitName(cp.faction, m.unit.unitType, m.unit.tier ?? 0)} (перемещается)`;
            ae.appendChild(tok);
          });
        }
      }

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

      // Advance highlighting
      {
        const pa = G.pending_advance;
        if (pa) {
          const step = pa.step;
          const isActive = tile.key === pa.tile_key;
          const isSource = pa.source_tile && tile.key === pa.source_tile;

          if ((step === 'ships') && (isActive || isSource)) {
            const origin = isActive ? 'active' : 'source';
            const avail  = G.ui?.advance_available_ships || [];
            const hasUnit = avail.some(s => s.area_idx === realIdx && s.origin === origin);
            const isSel   = _advanceSelectedShip?.area_idx === realIdx && _advanceSelectedShip?.origin === origin;
            if (isSel)      ae.classList.add('aok');
            else if (hasUnit) ae.classList.add('aok');
            else if (isActive && _advanceSelectedShip && area.type === 'space')  ae.classList.add('aok');
            else if (isActive && _advanceSelectedShip && area.type !== 'space')  ae.classList.add('ano');
          }

          if ((step === 'ground') && (isActive || isSource)) {
            const origin = isActive ? 'active' : 'source';
            const avail  = G.ui?.advance_available_ground || [];
            const hasUnit = avail.some(g => g.area_idx === realIdx && g.origin === origin);
            const isSel   = _advanceSelectedGround?.area_idx === realIdx && _advanceSelectedGround?.origin === origin;
            if (isSel)      ae.classList.add('aok');
            else if (hasUnit) ae.classList.add('aok');
            else if (isActive && _advanceSelectedGround && area.type === 'planet') ae.classList.add('aok');
            else if (isActive && _advanceSelectedGround && area.type !== 'planet') ae.classList.add('ano');
          }

          if (step === 'orbital' && isActive) {
            if (_advanceOrbitalShipArea === null) {
              const hasShip = (area.troops||[]).some(t => t.player === G.curP && t.unitType === 'space');
              if (area.type === 'space' && hasShip) ae.classList.add('aok');
            } else {
              if (realIdx === _advanceOrbitalShipArea) {
                ae.classList.add('aok');
              } else {
                const opp = 1 - G.curP;
                const hasEnemy = (area.troops||[]).some(t => t.player === opp);
                ae.classList.add(area.type === 'planet' && hasEnemy ? 'aok' : 'ano');
              }
            }
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

      #ae.onclick=()=>areaClick(tile.key, displayIdx);
      ae.onclick = () => areaClick(tile.key, realIdx);
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

    // Advance: outline тайла
    {
      const pa = G.pending_advance;
      if (pa) {
        if (pa.step === 'choose_source' && (pa.adjacent_tiles||[]).includes(tile.key)) {
          el.style.outline = '3px solid rgba(100,255,100,.7)';
          el.style.cursor  = 'pointer';
          el.title = `Выбрать [${tile.key}] как источник`;
          el.addEventListener('click', (e) => {
            if (!e.target.closest('.tarea') && !e.target.closest('.order-fd')) {
              _advanceChooseSource(tile.key);
            }
          });
        }
        if (pa.tile_key === tile.key && pa.step && pa.step !== 'choose_source') {
          el.style.outline = '3px solid rgba(0,200,255,.45)';
        }
        if (pa.source_tile && pa.source_tile === tile.key && pa.step !== 'choose_source') {
          el.style.outline = '3px solid rgba(100,255,100,.4)';
        }
      }
    }

    board.appendChild(el);
  });
}
