'use strict';
// ══════════════════════════════════════════════
//  RENDER SIDE — advance phases
// ══════════════════════════════════════════════

function _renderAdvanceDebugAreas(poolEl, pa) {
  poolEl.appendChild(_mkCls('rs-dbg-hdr', 'DEBUG — области с юнитами (array idx):'));

  const dispIdx = (tile, arrayIdx) =>
    RMAP[Math.floor((tile.rotation || 0) / 90) % 4][arrayIdx] ?? arrayIdx;

  const renderTile = (tileKey, label) => {
    const tile = G.map?.[tileKey];
    if (!tile) return;
    poolEl.appendChild(_mkDiv('font-size:.63rem;color:var(--gold);margin-top:4px;', `${label} [${tileKey}] rot=${tile.rotation}°:`));
    (tile.areas || []).forEach((area, idx) => {
      const ships  = (area.troops || []).filter(t => t.unitType === 'space');
      const ground = (area.troops || []).filter(t => t.unitType === 'ground');
      if (!ships.length && !ground.length) return;
      const parts = [];
      if (ships.length)  parts.push(`🚀×${ships.length} p${ships.map(t => t.player).join(',')}`);
      if (ground.length) parts.push(`⚔×${ground.length} p${ground.map(t => t.player).join(',')}`);
      poolEl.appendChild(_mkDiv('font-size:.63rem;color:#ccc;margin-left:8px;',
        `disp.${dispIdx(tile, idx)} arr.${idx} (${area.type}): ${parts.join('  ')}`));
    });
  };

  renderTile(pa.tile_key, 'Активная');
  if (pa.source_tile) renderTile(pa.source_tile, 'Source');
}

function _renderAdvanceChooseSourcePhase() {
  const poolEl = _resetPanels();
  const pa     = G.pending_advance;

  poolEl.appendChild(_mkPtitle('ADVANCE: выбор источника'));
  poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:8px;', 'Выберите соседнюю систему с вашими войсками или пропустите'));

  (pa.adjacent_tiles || []).forEach(tk => {
    const btn = document.createElement('button');
    btn.className = `abtn ${G.curP === 0 ? 'bp' : 'br'}`;
    btn.style.cssText = 'width:100%;margin-bottom:4px;';
    btn.textContent   = `📍 Система [${tk}]`;
    btn.onclick = () => _advanceChooseSource(tk);
    poolEl.appendChild(btn);
  });

  if (!(pa.adjacent_tiles || []).length)
    poolEl.appendChild(_mkCls('rs-dim-sm', 'Нет соседних систем с вашими войсками'));

  const sk = document.createElement('button');
  sk.className  = 'abtn bw';
  sk.style.cssText = 'width:100%;margin-top:4px;';
  sk.textContent   = 'Пропустить (только активная система)';
  sk.onclick = () => _advanceChooseSource(null);
  poolEl.appendChild(sk);
}

function _renderAdvanceMovement(type) {
  const isShips  = type === 'ships';
  const pa       = G.pending_advance;
  const poolEl   = _resetPanels();
  const avail    = isShips ? (G.ui?.advance_available_ships || []) : (G.ui?.advance_available_ground || []);
  const facColor = _facColor();
  const selUnit  = isShips ? _advanceSelectedShip : _advanceSelectedGround;

  poolEl.appendChild(_mkPtitle(isShips ? 'ADVANCE: корабли' : 'ADVANCE: наземные юниты'));
  poolEl.appendChild(_mkCls('rs-hint', selUnit
    ? (isShips ? '✓ Корабль выбран — кликните область в активной системе'
               : '✓ Юнит выбран — кликните планету в активной системе')
    : (isShips ? '← Выберите корабль, затем кликните область назначения'
               : '← Выберите юнита, затем кликните планету назначения')));

  if (avail.length > 0) {
    poolEl.appendChild(_mkDiv('font-size:.65rem;color:var(--dim);text-transform:uppercase;margin-bottom:4px;letter-spacing:.04em;',
      isShips ? 'Доступные корабли:' : 'Доступные юниты:'));
    avail.forEach(u => {
      const isSel = isShips
        ? (_advanceSelectedShip?.area_idx === u.area_idx && _advanceSelectedShip?.origin === u.origin)
        : (_advanceSelectedGround?.area_idx === u.area_idx && _advanceSelectedGround?.origin === u.origin);
      const tok = document.createElement('div');
      tok.className     = `ttok ${isShips ? 'space' : 'ground'}${isSel ? ' sel' : ''}`;
      tok.style.background  = hexAlpha(facColor, isSel ? 0.35 : 0.15);
      tok.style.borderColor = facColor;
      tok.style.color       = facColor;
      tok.textContent = `T${u.unit.tier ?? 0}`;
      tok.title = `${getUnitName(G.players[G.curP].faction, isShips ? 'space' : 'ground', u.unit.tier ?? 0)} (${u.origin === 'source' ? 'из источника' : 'активный'})`;
      tok.onclick = () => isShips ? _advanceSelectShip(u) : _advanceSelectGround(u);
      poolEl.appendChild(tok);
    });
  } else {
    poolEl.appendChild(_mkCls('rs-dim-sm', isShips ? 'Нет доступных кораблей' : 'Нет доступных наземных юнитов'));
  }

  if ((pa.committed_moves || []).length > 0)
    poolEl.appendChild(_mkCls('rs-moves', `Перемещений: ${pa.committed_moves.length}`));

  if (!isShips) _renderAdvanceGroundDebug(poolEl, pa);

  _renderAdvanceDebugAreas(poolEl, pa);

  const btn = document.createElement('button');
  btn.className = `abtn ${G.curP === 0 ? 'bp' : 'br'}`;
  btn.style.cssText = 'width:100%;margin-top:8px;';
  btn.textContent   = isShips ? 'Готово с кораблями →' : 'Зафиксировать перемещения →';
  btn.onclick = () => isShips ? _advanceNextStep() : _advanceCommit();
  poolEl.appendChild(btn);
}

function _renderAdvanceGroundDebug(poolEl, pa) {
  const reachById = pa.reachable_planets_by_id || {};
  const allUnits  = pa.available_ground_units   || [];
  if (!allUnits.length) return;

  poolEl.appendChild(_mkCls('rs-dbg-hdr', 'Легальные маршруты:'));

  const areaMap = new Map();
  allUnits.forEach(g => {
    const key = `${g.origin}:${g.area_idx}`;
    if (!areaMap.has(key)) areaMap.set(key, { origin: g.origin, area_idx: g.area_idx, reachable: new Set() });
    const r = reachById[g.ground_id] ?? reachById[String(g.ground_id)] ?? [];
    r.forEach(x => areaMap.get(key).reachable.add(x));
  });

  const activeTile = G.map?.[pa.tile_key];
  const srcTile    = pa.source_tile ? G.map?.[pa.source_tile] : null;
  const dispIdxFor = (tile, ai) => tile ? (RMAP[Math.floor((tile.rotation || 0) / 90) % 4][ai] ?? ai) : ai;

  areaMap.forEach(({ origin, area_idx, reachable }) => {
    const fromTile  = origin === 'source' ? srcTile : activeTile;
    const fromDisp  = dispIdxFor(fromTile, area_idx);
    const targets   = reachable.size > 0
      ? [...reachable].sort((a, b) => a - b)
          .map(ai => `disp.${dispIdxFor(activeTile, ai)}(arr.${ai})`).join(', ')
      : '—';
    poolEl.appendChild(_mkDiv('font-size:.65rem;color:#ccc;margin-top:3px;line-height:1.4;',
      `[${origin}] disp.${fromDisp}(arr.${area_idx}) → ${targets}`));
  });
}

function _renderAdvanceCombatPhase() {
  const poolEl = _resetPanels();
  const pa     = G.pending_advance;

  poolEl.appendChild(_mkPtitle('ADVANCE: бой'));
  poolEl.appendChild(_mkDiv('font-size:.8rem;color:#ff6b6b;margin-bottom:8px;',
    `⚔ Спорная область [${pa.tile_key}] #${pa.contest_area_idx}`));
  poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:10px;', 'Оба игрока имеют войска в одной области.'));

  const btn = document.createElement('button');
  btn.style.cssText = 'width:100%;background:rgba(255,77,109,.15);border-color:rgba(255,77,109,.5);';
  btn.className     = 'abtn bp';
  btn.textContent   = '⚔ Начать бой!';
  btn.onclick = () => _advanceFight();
  poolEl.appendChild(btn);
}

function _renderAdvanceCombatRetreatPhase() {
  const poolEl   = _resetPanels();
  const pa       = G.pending_advance;
  const loserIdx = pa.combat_loser;
  const loser    = G.players[loserIdx];
  const col      = FACTIONS.find(f => f.id === loser?.faction)?.color || (loserIdx === 0 ? '#00c8ff' : '#ff4d6d');

  poolEl.appendChild(_mkPtitle('ADVANCE: отступление'));

  const info = _mkDiv('font-size:.8rem;margin-bottom:10px;');
  info.innerHTML = `<span style="color:${col}">${loser?.name || 'Игрок'}</span> выбирает область для отступления:`;
  poolEl.appendChild(info);

  const validAreas = pa.retreat_valid_areas || [];
  if (!validAreas.length) {
    poolEl.appendChild(_mkDiv('font-size:.78rem;color:#ff4d6d;', 'Нет допустимых областей — юниты уничтожены.'));
    return;
  }

  const byTile = {};
  validAreas.forEach(([tk, ai]) => { (byTile[tk] = byTile[tk] || []).push(ai); });

  Object.entries(byTile).forEach(([tk, areaIdxs]) => {
    poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin:6px 0 3px;', `Система [${tk}]:`));
    areaIdxs.forEach(ai => {
      const area  = G.map?.[tk]?.areas?.[ai];
      const atype = area?.type === 'planet' ? '🌍' : '🌌';
      const btn   = document.createElement('button');
      btn.className = 'abtn';
      btn.style.cssText = `width:100%;margin-bottom:4px;border-color:${col};`;
      btn.textContent   = `${atype} Область ${ai}`;
      btn.onclick = () => _advanceRetreat(tk, ai);
      poolEl.appendChild(btn);
    });
  });
}

function _renderAdvanceOrbitalPhase() {
  const poolEl = _resetPanels();

  poolEl.appendChild(_mkPtitle('ADVANCE: орбитальный удар'));
  poolEl.appendChild(_mkCls('rs-hint', _advanceOrbitalShipArea === null
    ? '1. Кликните область с вашим кораблём на карте'
    : `2. Кликните планету противника для удара (корабль: обл.${_advanceOrbitalShipArea})`));

  const sk = document.createElement('button');
  sk.className  = 'abtn bw';
  sk.style.cssText = 'width:100%;margin-top:4px;';
  sk.textContent   = 'Пропустить орбитальный удар';
  sk.onclick = () => _advanceSkipOrbital();
  poolEl.appendChild(sk);
}

function _renderAdvanceOrbitalDefendPhase() {
  const poolEl = _resetPanels();
  const pa     = G.pending_advance;
  const defIdx = 1 - pa.player_id;

  poolEl.appendChild(_mkPtitle('ADVANCE: защита'));
  poolEl.appendChild(_mkDiv('font-size:.75rem;color:#ff6b6b;margin-bottom:8px;',
    `⏳ ${G.players[defIdx].name} выбирает юнита...`));
}
