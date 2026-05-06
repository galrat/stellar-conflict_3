'use strict';
// ══════════════════════════════════════════════
//  RENDER SIDE PANEL — dispatcher + helpers + troop/tile-hand/end-round
// ══════════════════════════════════════════════

function _facColor(pIdx) {
  pIdx = pIdx ?? G.curP;
  return FACTIONS.find(f => f.id === G.players[pIdx].faction)?.color
    || (pIdx === 0 ? '#00c8ff' : '#ff4d6d');
}

function _resetPanels() {
  document.getElementById('tile-hand').innerHTML = '';
  document.getElementById('unit-pool-section').style.display = 'block';
  document.getElementById('struct-pool-section').style.display = 'none';
  const poolEl = document.getElementById('unit-pool');
  poolEl.innerHTML = '';
  return poolEl;
}

function _mkDiv(cssText, text) {
  const d = document.createElement('div');
  if (cssText) d.style.cssText = cssText;
  if (text !== undefined) d.textContent = text;
  return d;
}

function _mkCls(className, text) {
  const d = document.createElement('div');
  d.className = className;
  if (text !== undefined) d.textContent = text;
  return d;
}

function _mkPtitle(text) {
  return _mkCls('ptitle', text);
}

function renderSide() {
  _cancelTileHover(); _cancelTileHideTimer(); _dismissTilePreview();

  if (G.phase === 'troop-on-tile')   return _renderTroopPhase();
  if (G.phase === 'order-placement') return _renderOrderPlacementPhase();
  if (G.phase === 'orders_placed')   return _renderOrdersPlacedPhase();
  if (G.phase === 'end-round')       return _renderEndRoundPhase();

  if (G.phase === 'execution') {
    if (G.pending_eldar_dominate)                                 return _renderEldarDominatePhase();
    if (G.pending_chaos_dominate)                                 return _renderChaosDominatePhase();
    if (G.pending_marine_dominate)                                return _renderMarineDominatePhase();
    if (G.pending_deploy?.step === 'place_units')                 return _renderDeployPlaceUnitsPhase();
    if (G.pending_deploy?.step === 'buy_building')                return _renderDeployBuyBuildingPhase();
    if (G.pending_advance?.step === 'choose_source')              return _renderAdvanceChooseSourcePhase();
    if (G.pending_advance?.step === 'ships')                      return _renderAdvanceMovement('ships');
    if (G.pending_advance?.step === 'ground')                     return _renderAdvanceMovement('ground');
    if (G.pending_advance?.step === 'combat')                     return _renderAdvanceCombatPhase();
    if (G.pending_advance?.step === 'combat_retreat')             return _renderAdvanceCombatRetreatPhase();
    if (G.pending_advance?.step === 'orbital')                    return _renderAdvanceOrbitalPhase();
    if (G.pending_advance?.step === 'orbital_defend')             return _renderAdvanceOrbitalDefendPhase();
    if (G.pending_strategize)                                     return _renderStrategizePhase();
    return _renderExecutionPhase();
  }

  // Default — hide pools, show tile hand
  document.getElementById('unit-pool-section').style.display   = 'none';
  document.getElementById('struct-pool-section').style.display = 'none';

  const cp = G.players[G.curP];
  const handEl = document.getElementById('tile-hand');
  handEl.innerHTML = '';
  cp.hand.forEach((ht, idx) => {
    if (ht.placed) return;
    const el = document.createElement('div');
    el.className = `htile${ht.isHome ? ' hthome' : ''}`;
    if (G.selHandIdx === idx) el.classList.add(cp.color === 'c1' ? 'hs1' : 'hs2');
    const tileDef = TILE_CATALOG.find(t => t.id === ht.tileDefId);
    const sideLayout = tileDef ? tileDef.sides[0].layout.flat() : [];
    const prev = document.createElement('div'); prev.className = 'hpreview';
    sideLayout.forEach(v => {
      const d = document.createElement('div');
      d.className = `hpa ${v === 1 ? 'hpp' : 'hps'}`;
      prev.appendChild(d);
    });
    const lbl = document.createElement('div'); lbl.className = 'htlabel';
    lbl.textContent = ht.isHome
      ? `${FACTIONS.find(f => f.id === cp.faction)?.icon} Домашняя`
      : `Система ${idx + 1}`;
    el.appendChild(prev); el.appendChild(lbl);
    el.onclick = () => selectHandTile(idx);
    el.addEventListener('mouseenter', () => _startTileHover(el, ht.tileDefId));
    el.addEventListener('mouseleave', _cancelTileHover);
    handEl.appendChild(el);
  });
}

function _renderTroopPhase() {
  const cp = G.players[G.curP];
  const facColor = _facColor();
  document.getElementById('tile-hand').innerHTML = '';
  document.getElementById('unit-pool-section').style.display = 'block';

  const poolEl = document.getElementById('unit-pool');
  poolEl.innerHTML = '';
  if (cp.pool.length > 0) {
    cp.pool.forEach((u, idx) => {
      const tok = document.createElement('div');
      tok.className = `ttok ${u.unitType}${G.selUnitIdx === idx ? ' sel' : ''}`;
      tok.style.background  = hexAlpha(facColor, 0.15);
      tok.style.borderColor = facColor;
      tok.style.color       = facColor;
      tok.textContent = `T${u.tier ?? 0}`;
      tok.title   = getUnitName(cp.faction, u.unitType, u.tier ?? 0);
      tok.onclick = () => selectUnitFromPool(idx);
      poolEl.appendChild(tok);
    });
  } else {
    poolEl.innerHTML = '<span style="color:var(--dim);font-size:.75rem">Нет войск</span>';
  }

  const structSection = document.getElementById('struct-pool-section');
  const structEl      = document.getElementById('struct-pool');
  if (cp.structurePool && cp.structurePool.length > 0) {
    structSection.style.display = 'block';
    structEl.innerHTML = '';
    cp.structurePool.forEach((s, idx) => {
      const info = STRUCTURE_INFO[s.type] || { icon: '?', label: s.type };
      const tok = document.createElement('div');
      tok.className = `ttok stok ${G.curP === 0 ? 'c1' : 'c2'}${G.selStructIdx === idx ? ' sel' : ''}`;
      tok.innerHTML = info.icon;
      tok.title     = info.label;
      tok.onclick   = () => selectStructFromPool(idx);
      structEl.appendChild(tok);
    });
  } else {
    structSection.style.display = 'none';
  }
}

function _renderEldarDominatePhase() {
  const poolEl = _resetPanels();
  const pe = G.pending_eldar_dominate;

  poolEl.appendChild(_mkPtitle('ELDAR: особое свойство доминации'));

  if (!_eldarSelectedUnit) {
    poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:12px;',
      'Кликните на наземного юнита в активной системе для перемещения'));
  } else {
    poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:12px;',
      `Юнит выбран (область ${_eldarSelectedUnit.area_idx}). Кликните на дружественную планету`));
  }

  const skipBtn = document.createElement('button');
  skipBtn.className = 'abtn';
  skipBtn.style.cssText = 'width:100%;padding:8px;margin-top:8px;';
  skipBtn.textContent = 'Пропустить';
  skipBtn.onclick = eldarDominateSkip;
  poolEl.appendChild(skipBtn);
}

function _renderChaosDominatePhase() {
  const poolEl = _resetPanels();
  poolEl.appendChild(_mkPtitle('ХАОС: особое свойство доминации'));

  if (!_chaosSelectedUnit) {
    poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:12px;',
      'Кликните на культиста в активной системе для перемещения'));
  } else {
    poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:12px;',
      `Культист выбран (область ${_chaosSelectedUnit.area_idx}). Кликните на планету соседней системы`));
  }

  const skipBtn = document.createElement('button');
  skipBtn.className = 'abtn';
  skipBtn.style.cssText = 'width:100%;padding:8px;margin-top:8px;';
  skipBtn.textContent = 'Пропустить';
  skipBtn.onclick = chaosDominateSkip;
  poolEl.appendChild(skipBtn);
}

function _renderMarineDominatePhase() {
  const poolEl = _resetPanels();
  poolEl.appendChild(_mkPtitle('MARINE: особое свойство доминации'));

  if (!_marineSelectedUnit) {
    poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:12px;',
      'Кликните на юнита tier0/tier1 в активной системе для улучшения'));
  } else {
    poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:12px;',
      `Юнит выбран (область ${_marineSelectedUnit.area_idx}, tier${_marineSelectedUnit.tier})`));
  }

  const skipBtn = document.createElement('button');
  skipBtn.className = 'abtn';
  skipBtn.style.cssText = 'width:100%;padding:8px;margin-top:8px;';
  skipBtn.textContent = 'Пропустить';
  skipBtn.onclick = marineDominateSkip;
  poolEl.appendChild(skipBtn);
}

function _renderEndRoundPhase() {
  const poolEl = _resetPanels();
  const roundNum    = G.round || 1;
  const totalRounds = G.totalRounds || 8;
  poolEl.innerHTML = `
    <div style="text-align:center;padding:10px;color:var(--gold);font-weight:bold;">
      ✓ РАУНД ${roundNum}/${totalRounds} ЗАВЕРШЁН
    </div>
    <div style="margin-top:10px;color:var(--dim);font-size:.75rem;text-align:center;">
      Все приказы разыграны. Сброшенные приказы возвращены в руки.
    </div>
  `;
}
