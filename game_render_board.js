'use strict';
// ══════════════════════════════════════════════
//  RENDER BOARD
// ══════════════════════════════════════════════

function _mkTroop(unitType, tier, color, opts = {}) {
  const tok = document.createElement('div');
  tok.className = `atroop ${unitType}`;
  if (opts.routed)    tok.classList.add('routed');
  tok.style.background  = hexAlpha(color, opts.bgAlpha ?? 0.15);
  tok.style.borderColor = color;
  tok.style.color       = color;
  if (opts.opacity)   tok.style.opacity   = opts.opacity;
  if (opts.outline)   tok.style.outline   = opts.outline;
  if (opts.cursor)    tok.style.cursor    = opts.cursor;
  if (opts.boxShadow) tok.style.boxShadow = opts.boxShadow;
  tok.textContent = `T${tier}`;
  tok.title = opts.title || '';
  if (opts.onclick) tok.onclick = opts.onclick;
  return tok;
}

function _drawDropCells(board, px) {
  getValidDrops().forEach(({ col, row }) => {
    const p  = px(col, row);
    const el = document.createElement('div');
    el.className     = 'drop-cell';
    el.style.cssText = `left:${p.left}px;top:${p.top}px;width:${CELL}px;height:${CELL}px;`;
    el.innerHTML     = '<span style="font-size:1.4rem;color:rgba(0,200,255,.5);font-family:Orbitron">+</span>';
    el.onclick = () => dropTile(col, row);
    board.appendChild(el);
  });
}

function _drawAreaTroops(ae, tile, area, realIdx) {
  const paAdv       = G.pending_advance;
  const advCommits  = paAdv?.committed_moves || [];
  const advStep     = paAdv?.step;
  const isAdvActive = tile.key === paAdv?.tile_key;
  const isAdvSource = tile.key === paAdv?.source_tile;

  // Build skip-counts for units committed away from this area
  const movedOut = {};
  advCommits.forEach(m => {
    const fromHere =
      (m.origin === 'active' && isAdvActive && m.from_area_idx === realIdx) ||
      (m.origin === 'source' && isAdvSource && m.from_area_idx === realIdx);
    if (fromHere) {
      const k = `${m.unit.unitType}${m.unit.tier ?? 0}`;
      movedOut[k] = (movedOut[k] || 0) + 1;
    }
  });
  const skip = { ...movedOut };

  // Real troops
  area.troops.forEach((u, troopIdx) => {
    const k = `${u.unitType}${u.tier ?? 0}`;
    if (u.player === G.curP && skip[k] > 0) { skip[k]--; return; }

    const color = _facColor(u.player);
    const opts  = {
      routed: u.unit_status === 'routed',
      title:  getUnitName(G.players[u.player].faction, u.unitType, u.tier ?? 0),
    };

    if (u.ready_to_move) {
      const show = !paAdv ||
        (advStep === 'ships'  && u.unitType === 'space') ||
        (advStep === 'ground' && u.unitType === 'ground');
      if (show) { opts.outline = `2px dashed ${color}`; opts.opacity = '0.9'; }
    }

    const ped = G.pending_eldar_dominate;
    if (ped && ped.player_id === G.curP && tile.key === ped.source_tile_key
        && u.player === G.curP && u.unitType === 'ground') {
      const movable = (ped.movable_units || []).find(
        m => m.area_idx === realIdx && m.troop_idx === troopIdx
      );
      if (movable) {
        const isSel = _eldarSelectedUnit?.area_idx === realIdx && _eldarSelectedUnit?.troop_idx === troopIdx;
        opts.cursor = 'pointer';
        opts.boxShadow = `0 0 6px ${color}`;
        if (isSel) opts.outline = `2px solid ${color}`;
      }
    }

    if (paAdv && u.player === G.curP && (isAdvActive || isAdvSource)) {
      const origin = isAdvActive ? 'active' : 'source';
      if (advStep === 'ships' && u.unitType === 'space') {
        const sd = (G.ui?.advance_available_ships || [])
          .find(s => s.area_idx === realIdx && s.origin === origin);
        if (sd) {
          opts.cursor = 'pointer'; opts.boxShadow = `0 0 4px ${color}`;
          if (_advanceSelectedShip?.area_idx === realIdx && _advanceSelectedShip?.origin === origin)
            opts.outline = `2px solid ${color}`;
          opts.onclick = (e) => { e.stopPropagation(); _advanceSelectShip(sd); };
        }
      } else if (advStep === 'ground' && u.unitType === 'ground') {
        const gd = (G.ui?.advance_available_ground || [])
          .find(g => g.area_idx === realIdx && g.origin === origin);
        if (gd) {
          opts.cursor = 'pointer'; opts.boxShadow = `0 0 4px ${color}`;
          if (_advanceSelectedGround?.area_idx === realIdx && _advanceSelectedGround?.origin === origin)
            opts.outline = `2px solid ${color}`;
          opts.onclick = (e) => { e.stopPropagation(); _advanceSelectGround(gd); };
        }
      }
    }

    ae.appendChild(_mkTroop(u.unitType, u.tier ?? 0, color, opts));
  });

  // Ghost units: committed moves landing in this area
  if (paAdv && isAdvActive) {
    const color = _facColor();
    advCommits.forEach(m => {
      if (m.to_area_idx !== realIdx) return;
      ae.appendChild(_mkTroop(m.unit.unitType, m.unit.tier ?? 0, color, {
        bgAlpha: 0.2, opacity: '0.75', outline: `2px dashed ${color}`,
        title: `${getUnitName(G.players[G.curP].faction, m.unit.unitType, m.unit.tier ?? 0)} (перемещается)`,
      }));
    });
  }

  // Pending deploy units (not yet in tile.areas)
  const pd = G.pending_deploy;
  if (pd && tile.key === pd.tile_key && pd.placed) {
    const color   = _facColor();
    const catalog = pd.deploy_info?.unit_catalog || [];
    pd.placed.filter(p => p.area_idx === realIdx).forEach(p => {
      const u = catalog.find(c => c.unit_key === p.unit_key);
      ae.appendChild(_mkTroop(u?.unitType || 'ground', u?.tier ?? 0, color, {
        bgAlpha: 0.25, opacity: '0.7', outline: `2px dashed ${color}`,
        title: `${u?.name || p.unit_key} (ожидает)`,
      }));
    });
  }
}

function _getAreaClass(tile, area, realIdx, displayIdx) {
  if (G.phase === 'troop-on-tile' && tile.key === G.lastKey) {
    const cp = G.players[G.curP];
    if (G.selUnitIdx !== null) {
      const u = cp.pool[G.selUnitIdx];
      return u ? (isCompatible(u, area.type) && area.troops.length < area.capacity ? 'aok' : 'ano') : null;
    }
    if (G.selStructIdx !== null)
      return area.type === 'planet' && !(area.structures?.length) ? 'aok' : 'ano';
    if (tile.needsObjective && !tile.objectiveMarker) {
      if (getObjectiveEligibleDisplayIdxs(tile).includes(displayIdx) && area.type === 'planet')
        return 'aok-obj';
    }
    return null;
  }

  const pd = G.pending_deploy;
  if (pd && tile.key === pd.tile_key) {
    const info      = pd.deploy_info || {};
    const availIdxs = new Set((info.available_areas || []).map(a => a.idx));
    if (pd.step === 'place_units' && _deploySelectedUnit) {
      const _UT     = { infantry:'ground', marines:'ground', mechanized:'ground', elite:'ground', fighter:'space', destroyer:'space' };
      const expected = _UT[_deploySelectedUnit] === 'ground' ? 'planet' : 'space';
      return availIdxs.has(realIdx) && area.type === expected ? 'aok' : 'ano';
    }
    if (pd.step === 'buy_building' && _deploySelectedBuilding)
      return new Set(info.available_planets || []).has(realIdx) ? 'aok' : 'ano';
    if (pd.step === 'resolve_overflow') {
      const cnt = (area.troops || []).length + (pd.placed || []).filter(p => p.area_idx === realIdx).length;
      if (cnt > area.capacity) return 'ano';
    }
    return null;
  }

  const ped = G.pending_eldar_dominate;
  if (ped && ped.player_id === G.curP) {
    if (!_eldarSelectedUnit) {
      if (tile.key === ped.source_tile_key) {
        const hasMovable = (ped.movable_units || []).some(m => m.area_idx === realIdx);
        return hasMovable ? 'aok' : null;
      }
      return null;
    } else {
      if (tile.key === ped.source_tile_key
          && _eldarSelectedUnit.area_idx === realIdx) return 'aok';
      const isTarget = (ped.valid_targets || []).some(
        t => t.tile_key === tile.key && t.area_idx === realIdx
      );
      return isTarget ? 'aok' : 'ano';
    }
  }

  const pa = G.pending_advance;
  if (!pa) return null;

  const step     = pa.step;
  const isActive = tile.key === pa.tile_key;
  const isSource = pa.source_tile && tile.key === pa.source_tile;

  if (step === 'ships' && (isActive || isSource)) {
    const origin  = isActive ? 'active' : 'source';
    const avail   = G.ui?.advance_available_ships || [];
    const hasUnit = avail.some(s => s.area_idx === realIdx && s.origin === origin);
    const isSel   = _advanceSelectedShip?.area_idx === realIdx && _advanceSelectedShip?.origin === origin;
    if (isSel || hasUnit)                                           return 'aok';
    if (isActive && _advanceSelectedShip && area.type === 'space') return 'aok';
    if (isActive && _advanceSelectedShip)                          return 'ano';
    return null;
  }

  if (step === 'ground' && (isActive || isSource)) {
    const origin  = isActive ? 'active' : 'source';
    const avail   = G.ui?.advance_available_ground || [];
    const hasUnit = avail.some(g => g.area_idx === realIdx && g.origin === origin);
    const isSel   = _advanceSelectedGround?.area_idx === realIdx && _advanceSelectedGround?.origin === origin;
    if (isSel || hasUnit) return 'aok';
    if (isActive && _advanceSelectedGround) {
      const gid  = _advanceSelectedGround.ground_id;
      const rById = pa.reachable_planets_by_id || {};
      const list  = rById[gid] ?? rById[String(gid)] ?? [];
      return area.type === 'planet' && list.includes(realIdx) ? 'aok' : 'ano';
    }
    return null;
  }

  if (step === 'orbital' && isActive) {
    if (_advanceOrbitalShipArea === null)
      return area.type === 'space' && (area.troops || []).some(t => t.player === G.curP && t.unitType === 'space')
        ? 'aok' : null;
    if (realIdx === _advanceOrbitalShipArea) return 'aok';
    const hasEnemy = (area.troops || []).some(t => t.player === 1 - G.curP);
    return area.type === 'planet' && hasEnemy ? 'aok' : 'ano';
  }

  if (step === 'combat_retreat') {
    return (pa.retreat_valid_areas || []).some(([tk, ai]) => tk === tile.key && ai === realIdx)
      ? 'adv-retreat' : 'ano';
  }

  return null;
}

function _drawOrders(el, tile, playableIds) {
  G.orders
    .filter(o => o.tile === tile.key)
    .sort((a, b) => (a.position || 0) - (b.position || 0))
    .forEach((order, idx) => {
      const fac        = FACTIONS.find(f => f.id === G.players[order.owner].faction);
      const facIcon    = fac?.icon || (order.owner === 0 ? 'P1' : 'P2');
      const orderName  = ORDER_TYPES[order.type]?.name || order.type;
      const facColor   = G.players[order.owner].faction_color || (order.owner === 0 ? '#00c8ff' : '#ff4d6d');
      const isClickable = G.phase === 'execution' && playableIds.has(order.id);
      const isSelected  = _selectedOrderForPlay?.id === order.id;

      const orderEl = document.createElement('div');
      orderEl.className = `order-fd${isSelected ? ' selected-order' : ''}`;
      orderEl.style.cssText = `
        top:calc(50% + ${-idx * 5}px);left:calc(50% + ${idx * 5}px);
        z-index:${10 + idx};color:${facColor};
        pointer-events:${isClickable ? 'auto' : 'none'};cursor:${isClickable ? 'pointer' : 'default'};
        border-color:${isSelected ? 'rgba(255,220,50,.9)' : '#333'};
        ${isSelected ? 'box-shadow:0 2px 10px rgba(0,0,0,.85),0 0 0 3px rgba(255,220,50,.8);' : ''}
      `;
      orderEl.innerHTML = `<div style="font-size:2rem;font-weight:bold;line-height:1">${facIcon}</div>`;
      orderEl.title = isClickable
        ? (isSelected ? `Нажмите ещё раз для розыгрыша: ${orderName}` : `Выбрать: ${orderName}`)
        : `${orderName} (${G.players[order.owner].name})`;

      if (isClickable)
        orderEl.addEventListener('click', (e) => { e.stopPropagation(); selectOrderForPlay(order.id, order.type, tile.key); });

      el.appendChild(orderEl);
    });
}

function _drawWarpStorms(el, tile) {
  ['top', 'bottom', 'left', 'right'].forEach(side => {
    const isH   = side === 'top' || side === 'bottom';
    const wsIdx = G.warpStorms.findIndex(ws => ws && ws.tileKey === tile.key && ws.side === side);
    const hasWS = wsIdx !== -1;

    if (hasWS) {
      const ws = document.createElement('div');
      ws.className = `warp-storm warp-storm-${side} ${isH ? 'warp-storm-h' : 'warp-storm-v'}`;
      if (_warpMoveState?.step === 'select_storm' && _warpMoveState.moves.some(m => m.storm_idx === wsIdx)) {
        ws.classList.add('ws-selectable');
        ws.onclick = (e) => { e.stopPropagation(); _warpSelectStorm(wsIdx); };
      } else if (_warpMoveState?.step === 'select_dest' && _warpMoveState.storm_idx === wsIdx) {
        ws.classList.add('ws-selected');
        ws.onclick = (e) => { e.stopPropagation(); _warpSelectStorm(wsIdx); };
      }
      el.appendChild(ws);
    }

    if (G.phase === 'warp-storm' && !hasWS && !G.warpStorms[G.curP] && !G.warpConfirmed[G.curP]) {
      const b = document.createElement('div');
      b.className = `ws-border ws-border-${isH ? 'h' : 'v'} warp-storm-${side}`;
      b.onclick   = (e) => { e.stopPropagation(); placeWarpStorm(tile.key, side); };
      el.appendChild(b);
    }

    if (_warpMoveState?.step === 'select_dest' && !hasWS &&
        _warpMoveState.validDests.some(d => d.tileKey === tile.key && d.side === side)) {
      const b = document.createElement('div');
      b.className = `ws-border ws-border-${isH ? 'h' : 'v'} warp-storm-${side} ws-dest`;
      b.onclick   = (e) => { e.stopPropagation(); doMoveWarpStorm(_warpMoveState.storm_idx, tile.key, side); };
      el.appendChild(b);
    }
  });
}

function _drawAdvanceOutline(el, tile, pa) {
  if (!pa) return;
  if (pa.step === 'choose_source' && (pa.adjacent_tiles || []).includes(tile.key)) {
    el.style.outline = '3px solid rgba(100,255,100,.7)';
    el.style.cursor  = 'pointer';
    el.title = `Выбрать [${tile.key}] как источник`;
    el.addEventListener('click', (e) => {
      if (!e.target.closest('.tarea') && !e.target.closest('.order-fd'))
        _advanceChooseSource(tile.key);
    });
  }
  if (pa.tile_key === tile.key && pa.step && pa.step !== 'choose_source')
    el.style.outline = '3px solid rgba(0,200,255,.45)';
  if (pa.source_tile === tile.key && pa.step !== 'choose_source')
    el.style.outline = '3px solid rgba(100,255,100,.4)';
}

function _drawTile(tile, px) {
  const p  = px(tile.col, tile.row);
  const el = document.createElement('div');
  el.className = 'stile';
  el.classList.add(tile.isHome ? (tile.player === 0 ? 'hp1' : 'hp2') : (tile.player === 0 ? 'np1' : 'np2'));
  el.style.cssText = `left:${p.left}px;top:${p.top}px;width:${CELL}px;height:${CELL}px;`;

  const imgSuffix = (tile.side || 0) === 0 ? 'a' : 'b';
  el.innerHTML = `
    <div class="stile-bg"><div class="stile-bg-img" style="background-image:url('tiles/${tile.tileDefId}_${imgSuffix}.png');transform:rotate(${tile.rotation || 0}deg)"></div></div>
    ${tile.isHome ? '<div class="hbadge">\u{1F3E0}</div>' : ''}
    <div class="tcoord">${tile.key}${tile.rotation ? ` ${tile.rotation}°` : ''}${tile.side === 1 ? ' [B]' : ''}</div>
  `;

  const inner = document.createElement('div'); inner.className = 'stilei';

  getRotatedAreas(tile).forEach((area, displayIdx) => {
    const realIdx = tile.areas.indexOf(area);
    const ae      = document.createElement('div');
    ae.className       = `tarea a${area.type}`;
    ae.dataset.areaIdx = realIdx;

    // Label
    const lbl = document.createElement('div'); lbl.className = 'atlbl';
    if (area.type === 'planet') {
      const capMark = '●'.repeat(area.capacity);
      const incMark = area.income   > 0 ? ` <span class="inc-mark">●${area.income}</span>`   : '';
      const valMark = area.valuable > 0 ? ` <span class="val-mark">◆${area.valuable}</span>` : '';
      let h = capMark + incMark + valMark;
      if (area.support)  h += ' <span class="tok-sup">⊕</span>';
      if (area.discount) h += ' <span class="tok-dis">⊖</span>';
      if (area.forge)    h += ' <span class="tok-frg">⚒</span>';
      if (area.joker)    h += ' <span class="tok-jok">★</span>';
      lbl.innerHTML = h;
    } else {
      lbl.textContent = '✶';
    }
    ae.appendChild(lbl);

    // Capacity counter
    const pendingCount  = G.pending_deploy?.tile_key === tile.key
      ? (G.pending_deploy.placed || []).filter(p => p.area_idx === realIdx).length : 0;
    const effectiveUsed = area.troops.length + pendingCount;
    const capEl = document.createElement('div'); capEl.className = 'acap';
    capEl.textContent = `${effectiveUsed}/${area.capacity}`;
    if (effectiveUsed >= area.capacity) capEl.style.color = 'var(--accent2)';
    ae.appendChild(capEl);

    // Structures
    (area.structures || []).forEach(s => {
      const info = STRUCTURE_INFO[s.type] || { icon: '?', label: s.type };
      const col  = _facColor(s.player);
      const tok  = document.createElement('div'); tok.className = 'astruc';
      tok.style.background  = hexAlpha(col, 0.5);
      tok.style.borderColor = col;
      tok.style.color       = getTextColor(col);
      tok.textContent = info.icon; tok.title = info.label;
      ae.appendChild(tok);
    });

    _drawAreaTroops(ae, tile, area, realIdx);

    // Ownership highlight
    const h1 = area.troops.some(t => t.player === 0);
    const h2 = area.troops.some(t => t.player === 1);
    if (h1 && h2) ae.classList.add('contested');
    else if (h1)  ae.classList.add('h1');
    else if (h2)  ae.classList.add('h2');

    const cls = _getAreaClass(tile, area, realIdx, displayIdx);
    if (cls) ae.classList.add(cls);

    // Objective marker
    if (tile.objectiveMarker && tile.objectiveMarker.area_place === area.area_place) {
      const op  = tile.objectiveMarker.owner;
      const col = _facColor(op);
      const fac = FACTIONS.find(f => f.id === G.players[op].faction);
      const m   = document.createElement('div'); m.className = 'obj-marker';
      m.style.background  = hexAlpha(col, 0.25);
      m.style.borderColor = col;
      m.style.color       = col;
      m.textContent = fac?.icon || (op === 0 ? 'P1' : 'P2');
      m.title = `Цель: ${G.players[op].name}`;
      ae.appendChild(m);
    }

    ae.onclick = () => {
      if (G.pending_eldar_dominate) { eldarDominateAreaClick(tile.key, realIdx); return; }
      areaClick(tile.key, displayIdx);
    };
    inner.appendChild(ae);
  });

  el.appendChild(inner);

  // Center zone for order placement
  const cz = document.createElement('div'); cz.className = 'center-zone';
  cz.style.cssText = `cursor:${G.phase === 'order-placement' ? 'pointer' : 'default'};pointer-events:${G.phase === 'order-placement' ? 'auto' : 'none'};`;
  if (G.phase === 'order-placement')
    cz.onclick = (e) => { e.stopPropagation(); placeOrderViaAPI(tile.key); };
  el.appendChild(cz);

  _drawOrders(el, tile, new Set(G.ui?.playable_order_ids || []));
  _drawWarpStorms(el, tile);
  _drawAdvanceOutline(el, tile, G.pending_advance);

  return el;
}

function renderBoard() {
  const board = document.getElementById('map-board');
  board.innerHTML = '';
  const tiles = Object.values(G.map);

  const cols = tiles.map(t => t.col);
  const rows = tiles.map(t => t.row);
  const minC = (cols.length ? Math.min(...cols) : 0) - 1;
  const minR = (rows.length ? Math.min(...rows) : 0) - 1;
  const maxC = (cols.length ? Math.max(...cols) : 2) + 1;
  const maxR = (rows.length ? Math.max(...rows) : 1) + 1;

  board.style.width  = (maxC - minC + 1) * CELL + 'px';
  board.style.height = (maxR - minR + 1) * CELL + 'px';

  const px = (col, row) => ({ left: (col - minC) * CELL, top: (row - minR) * CELL });

  if (G.phase === 'tile-placement' && G.selHandIdx !== null) _drawDropCells(board, px);
  tiles.forEach(tile => board.appendChild(_drawTile(tile, px)));
}
