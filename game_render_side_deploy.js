'use strict';
// ══════════════════════════════════════════════
//  RENDER SIDE — deploy phases
// ══════════════════════════════════════════════

function _renderDeployPlaceUnitsPhase() {
  const poolEl   = _resetPanels();
  const pd       = G.pending_deploy;
  const hand     = pd.hand || [];
  const placed   = pd.placed || [];
  const catalog  = pd.deploy_info?.unit_catalog || [];
  const facColor = _facColor();

  poolEl.appendChild(_mkPtitle('DEPLOY: размещение войск'));
  poolEl.appendChild(_mkCls('rs-hint', _deploySelectedUnit
    ? `✓ Выбран: ${_deploySelectedUnit} — кликните область на карте`
    : '← Выберите юнит, затем кликните область на тайле'));

  const handRem = [...hand];
  for (const p of placed) {
    const i = handRem.indexOf(p.unit_key);
    if (i >= 0) handRem.splice(i, 1);
  }

  const ukCounts = {};
  handRem.forEach(uk => { ukCounts[uk] = (ukCounts[uk] || 0) + 1; });

  if (Object.keys(ukCounts).length === 0) {
    poolEl.appendChild(_mkDiv('color:var(--gold);font-size:.75rem;', '✓ Все войска размещены'));
  } else {
    Object.entries(ukCounts).forEach(([uk, cnt]) => {
      const u          = catalog.find(c => c.unit_key === uk);
      const isSelected = _deploySelectedUnit === uk;
      const tok = document.createElement('div');
      tok.className     = `ttok ${u?.unitType || 'ground'}${isSelected ? ' sel' : ''}`;
      tok.style.background  = hexAlpha(facColor, isSelected ? 0.35 : 0.15);
      tok.style.borderColor = facColor;
      tok.style.color       = facColor;
      tok.textContent = `T${u?.tier ?? 0}${cnt > 1 ? ' ×' + cnt : ''}`;
      tok.title   = u?.name || uk;
      tok.onclick = () => { _deploySelectedUnit = uk; renderSide(); renderBoard(); };
      poolEl.appendChild(tok);
    });
  }
}

function _renderDeployBuyBuildingPhase() {
  const poolEl  = _resetPanels();
  const pd      = G.pending_deploy;
  const info    = pd.deploy_info || {};
  const credits = info.credits - (pd.unit_costs?.credits || 0);
  const cash    = info.cash_tokens - (pd.unit_costs?.cash || 0);
  const catalog = info.building_catalog || [];

  poolEl.appendChild(_mkPtitle('DEPLOY: постройка'));
  poolEl.appendChild(_mkDiv('font-size:.72rem;color:var(--dim);margin-bottom:6px;', `💰${credits}  cash:${cash}`));

  if (catalog.length > 0) {
    catalog.forEach(({ type: bt, icon = '🏠', cost, count }) => {
      const cashDiscount = cash > 0 ? 2 : 0;
      const canAfford    = credits >= cost || (cash > 0 && credits >= Math.max(0, cost - cashDiscount));
      const isSelected   = _deploySelectedBuilding === bt;
      const btn = document.createElement('button');
      btn.className = `abtn ${isSelected ? 'bg' : 'bp'}`;
      btn.style.cssText = 'width:100%;margin-bottom:4px;';
      btn.disabled  = !canAfford;
      btn.title     = !canAfford ? 'Не хватает кредитов' : '';
      btn.textContent = `${icon} ${bt} (${cost}💰) ×${count}`;
      btn.onclick = () => _deploySelectBuilding(bt);
      poolEl.appendChild(btn);
    });
  } else {
    poolEl.appendChild(_mkCls('rs-dim-sm', 'Резерв построек пуст'));
  }

  if (_deploySelectedBuilding) {
    const sel = catalog.find(b => b.type === _deploySelectedBuilding);
    poolEl.appendChild(_mkCls('rs-hint', `✓ Выбрано: ${sel?.icon || ''} ${_deploySelectedBuilding} — кликните планету на карте`));
    if (cash > 0) {
      const label = document.createElement('label');
      label.style.cssText = 'font-size:.75rem;display:flex;align-items:center;gap:6px;cursor:pointer;margin-bottom:6px;';
      label.innerHTML = `<input type="checkbox" id="deploy-use-cash-panel"> Cash токен (−2💰)`;
      poolEl.appendChild(label);
    }
  }

  const skipBtn = document.createElement('button');
  skipBtn.className = 'abtn bw';
  skipBtn.style.cssText = 'width:100%;margin-top:8px;';
  skipBtn.textContent = 'Пропустить постройку →';
  skipBtn.onclick = () => _deploySkipBuilding();
  poolEl.appendChild(skipBtn);
}
