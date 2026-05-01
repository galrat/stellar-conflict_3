/**
 * game_strategize.js — UI для разыгрыша приказа Strategize
 *
 * Фазы:
 * 1. buy_combat_card — обмен одной боевой карты на другую
 * 2. buy_order_upgrade — покупка одного улучшения приказа
 */

function _resetStrategizeUI() {
  window._combatCardSelection = null;
  window._upgradeSelection = null;
}

function renderStrategize() {
  const ps = G.pending_strategize;
  if (!ps) return;

  const step = ps.step || 'buy_combat_card';

  if (step === 'buy_combat_card') {
    _showCombatCardExchangeModal();
  } else if (step === 'buy_order_upgrade') {
    _showOrderUpgradeModal();
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function _cardBg(isSelected, isDisabled) {
  if (isSelected) return 'rgba(76,175,80,.25)';
  if (isDisabled) return 'rgba(0,0,0,.2)';
  return 'rgba(0,0,0,.4)';
}

function _cardBorder(isSelected, isDisabled, baseColor) {
  if (isSelected) return '#4caf50';
  if (isDisabled) return baseColor.replace(/[\d.]+\)$/, '0.15)');
  return baseColor;
}

function _renderSelectableBattleCard(card, isSelected, isDisabled, onclickExpr) {
  const cost = card.cost ? `<span style="color:#ff8c00;margin-left:6px;">Стоимость: ${card.cost}</span>` : '';
  const tier = card.tier != null ? `<span style="color:var(--dim);margin-left:6px;">Tier ${card.tier}</span>` : '';
  const e1 = card.effect_1 ? `<div style="color:#aaa;font-size:.78rem;margin-top:4px;">${card.effect_1}</div>` : '';
  const e2 = card.effect_2 ? `<div style="color:#888;font-size:.78rem;margin-top:2px;">${card.effect_2}</div>` : '';
  const bg     = _cardBg(isSelected, isDisabled);
  const border = _cardBorder(isSelected, isDisabled, 'rgba(255,215,0,.4)');
  const extra  = isSelected ? 'box-shadow:0 0 0 1px #4caf50;' : '';
  const onClick = (!isDisabled && onclickExpr) ? `onclick="${onclickExpr}"` : '';
  const nameHtml = card.image
    ? `<span onclick="event.stopPropagation();_showCardImageOverlay('${card.image.replace(/ /g, '%20')}')" style="cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px;">${card.name}</span>`
    : card.name;
  return `<div ${onClick}
    style="margin-bottom:8px;padding:8px;background:${bg};border-left:3px solid ${border};
    border-radius:4px;opacity:${isDisabled ? .45 : 1};cursor:${isDisabled ? 'not-allowed' : 'pointer'};${extra}">
    <div style="font-weight:bold;font-size:.9rem;">${nameHtml}${cost}${tier}</div>${e1}${e2}
  </div>`;
}

function _renderSelectableUpgrade(upgrade, isSelected, isDisabled, onclickExpr) {
  const type = upgrade.order_type ? `<span style="color:#00bcd4;margin-left:6px;">[${upgrade.order_type}]</span>` : '';
  const cost = upgrade.cost ? `<span style="color:#ff8c00;margin-left:6px;">Стоимость: ${upgrade.cost}</span>` : '';
  const tier = upgrade.tier != null ? `<span style="color:var(--dim);margin-left:6px;">Tier ${upgrade.tier}</span>` : '';
  const e1 = upgrade.effect_1 ? `<div style="color:#aaa;font-size:.78rem;margin-top:4px;line-height:1.4;">${upgrade.effect_1}</div>` : '';
  const e2 = upgrade.effect_2 ? `<div style="color:#888;font-size:.78rem;margin-top:2px;">${upgrade.effect_2}</div>` : '';
  const bg     = _cardBg(isSelected, isDisabled);
  const border = _cardBorder(isSelected, isDisabled, 'rgba(0,188,212,.4)');
  const extra  = isSelected ? 'box-shadow:0 0 0 1px #4caf50;' : '';
  const onClick = (!isDisabled && onclickExpr) ? `onclick="${onclickExpr}"` : '';
  return `<div ${onClick}
    style="margin-bottom:8px;padding:8px;background:${bg};border-left:3px solid ${border};
    border-radius:4px;opacity:${isDisabled ? .45 : 1};cursor:${isDisabled ? 'not-allowed' : 'pointer'};${extra}">
    <div style="font-weight:bold;font-size:.9rem;">${upgrade.name}${type}${cost}${tier}</div>${e1}${e2}
  </div>`;
}

// ── Combat card exchange modal ──────────────────────────────────────────────

function _showCombatCardExchangeModal() {
  const player = G.players[G.curP];
  const handCards = player.hand_battle_cards || [];
  const availableCards = player.available_battle_cards || [];
  const playerLevel = G.pending_strategize?.player_level || 0;

  if (!window._combatCardSelection) {
    window._combatCardSelection = { fromHand: null, toBuy: null };
  }

  const credits = player.credits || 0;

  let html = `<div style="font-size:.85rem;color:#aaa;margin-bottom:12px;">`;
  html += `Кредиты: <strong style="color:#ff8c00;">${credits}</strong> &nbsp;|&nbsp; Уровень: <strong>${playerLevel}</strong>`;
  html += `</div>`;

  html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:12px;">`;

  // Карты в руке
  html += `<div>`;
  html += `<div style="font-weight:bold;color:rgba(76,175,80,.9);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid rgba(76,175,80,.4);font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;">На руке (${handCards.length})</div>`;
  if (handCards.length === 0) {
    html += `<div style="color:var(--dim);font-style:italic;font-size:.8rem;">Пусто</div>`;
  } else {
    handCards.forEach(card => {
      const isSelected = window._combatCardSelection?.fromHand?.name === card.name;
      const escaped = (card.name || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
      html += _renderSelectableBattleCard(card, isSelected, false, `window._selectFromHandCard('${escaped}')`);
    });
  }
  html += `</div>`;

  // Доступные карты для покупки
  html += `<div>`;
  html += `<div style="font-weight:bold;color:rgba(255,215,0,.8);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid rgba(255,215,0,.4);font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;">Для покупки (${availableCards.length})</div>`;
  if (availableCards.length === 0) {
    html += `<div style="color:var(--dim);font-style:italic;font-size:.8rem;">Пусто</div>`;
  } else {
    availableCards.forEach(card => {
      const canAffordCredits = credits >= (card.cost || 0);
      const canAffordLevel   = (card.tier || 0) <= playerLevel;
      const canAfford = canAffordCredits && canAffordLevel;
      const isSelected = window._combatCardSelection?.toBuy?.name === card.name;
      const escaped = (card.name || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");

      let reason = '';
      if (!canAffordCredits) reason = `<div style="color:#f88;font-size:.75rem;margin-top:3px;">Недостаточно кредитов</div>`;
      else if (!canAffordLevel) reason = `<div style="color:#f88;font-size:.75rem;margin-top:3px;">Требуется Tier ${card.tier} (у вас ${playerLevel})</div>`;

      const cardHtml = _renderSelectableBattleCard(card, isSelected, !canAfford, canAfford ? `window._selectToBuyCard('${escaped}')` : null);
      // inject reason after first closing div
      html += cardHtml.replace('</div>\n  </div>', `${reason}</div>\n  </div>`);
    });
  }
  html += `</div>`;

  html += `</div>`;

  // Action buttons
  html += `<div style="display:flex;gap:8px;margin-top:4px;">`;
  html += `<button class="abtn bp" style="flex:1;" onclick="_buyCombatCard()">✓ Купить</button>`;
  html += `<button class="abtn" style="flex:1;background:#555;" onclick="_skipCombatCardExchange()">⊘ Пропустить</button>`;
  html += `</div>`;

  showMsg('🎯 Strategize — Обмен боевой карты', html);
  document.querySelector('#msg-modal .mbtns').innerHTML = '';
}

function _selectFromHandCard(cardName) {
  window._combatCardSelection.fromHand = { name: cardName };
  _showCombatCardExchangeModal();
}

function _selectToBuyCard(cardName) {
  window._combatCardSelection.toBuy = { name: cardName };
  _showCombatCardExchangeModal();
}

function _skipCombatCardExchange() {
  closeMsg();
  apiCall('/api/game/strategize-skip-combat-card', { player_id: G.curP }).then(res => {
    if (res.success) {
      applyState(res.state);
      addLog('Strategize: пропущена покупка боевой карты', G.curP);
      if (res.state?.pending_strategize?.step === 'buy_order_upgrade') {
        renderStrategize();
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось пропустить обмен');
    }
  }).catch(e => showMsg('Ошибка сервера', e.message));
}

async function _buyCombatCard() {
  const sel = window._combatCardSelection;
  if (!sel?.fromHand?.name || !sel?.toBuy?.name) {
    showMsg('Ошибка', 'Выберите обе карты');
    return;
  }

  closeMsg();
  try {
    const res = await apiCall('/api/game/strategize-buy-combat-card', {
      player_id: G.curP,
      card_to_buy_name: sel.toBuy.name,
      card_from_hand_name: sel.fromHand.name,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Strategize: обмен карты ${sel.fromHand.name} на ${sel.toBuy.name}`, G.curP);
      if (res.state?.pending_strategize?.step === 'buy_order_upgrade') {
        renderStrategize();
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось обменять карту');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

// ── Order upgrade purchase modal ────────────────────────────────────────────

function _showOrderUpgradeModal() {
  const player = G.players[G.curP];
  const availableUpgrades = player.available_order_upgrades || [];
  const credits = player.credits || 0;
  const playerLevel = G.pending_strategize?.player_level || 0;

  if (!window._upgradeSelection) {
    window._upgradeSelection = null;
  }

  let html = `<div style="font-size:.85rem;color:#aaa;margin-bottom:12px;">`;
  html += `Кредиты: <strong style="color:#ff8c00;">${credits}</strong> &nbsp;|&nbsp; Уровень: <strong>${playerLevel}</strong>`;
  html += `</div>`;

  html += `<div style="margin-bottom:12px;">`;
  if (availableUpgrades.length === 0) {
    html += `<div style="color:var(--dim);font-style:italic;font-size:.85rem;text-align:center;padding:20px 0;">Нет доступных улучшений</div>`;
  } else {
    availableUpgrades.forEach(upgrade => {
      const canAffordCredits = credits >= (upgrade.cost || 0);
      const canAffordLevel   = (upgrade.tier || 0) <= playerLevel;
      const canAfford = canAffordCredits && canAffordLevel;
      const isSelected = window._upgradeSelection?.name === upgrade.name;
      const escaped = (upgrade.name || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");

      let reason = '';
      if (!canAffordCredits) reason = `<div style="color:#f88;font-size:.75rem;margin-top:3px;">Недостаточно кредитов</div>`;
      else if (!canAffordLevel) reason = `<div style="color:#f88;font-size:.75rem;margin-top:3px;">Требуется Tier ${upgrade.tier} (у вас ${playerLevel})</div>`;

      const cardHtml = _renderSelectableUpgrade(upgrade, isSelected, !canAfford, canAfford ? `window._selectUpgrade('${escaped}')` : null);
      html += cardHtml.replace('</div>\n  </div>', `${reason}</div>\n  </div>`);
    });
  }
  html += `</div>`;

  html += `<div style="display:flex;gap:8px;">`;
  html += `<button class="abtn bp" style="flex:1;" onclick="_buyOrderUpgrade()">✓ Купить</button>`;
  html += `<button class="abtn" style="flex:1;background:#555;" onclick="_skipOrderUpgrade()">⊘ Пропустить</button>`;
  html += `</div>`;

  showMsg('🎯 Strategize — Покупка улучшения приказа', html);
  document.querySelector('#msg-modal .mbtns').innerHTML = '';
}

function _selectUpgrade(upgradeName) {
  window._upgradeSelection = { name: upgradeName };
  _showOrderUpgradeModal();
}

function _skipOrderUpgrade() {
  closeMsg();
  apiCall('/api/game/strategize-skip-order-upgrade', { player_id: G.curP }).then(res => {
    if (res.success) {
      applyState(res.state);
      addLog('Strategize: пропущена покупка улучшения приказа', G.curP);
      if (!res.state?.pending_strategize) {
        addLog('Strategize завершён', G.curP);
        _selectedOrderForPlay = null;
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось пропустить улучшение');
    }
  }).catch(e => showMsg('Ошибка сервера', e.message));
}

async function _buyOrderUpgrade() {
  const sel = window._upgradeSelection;
  if (!sel?.name) {
    showMsg('Ошибка', 'Выберите улучшение');
    return;
  }

  closeMsg();
  try {
    const res = await apiCall('/api/game/strategize-buy-order-upgrade', {
      player_id: G.curP,
      upgrade_name: sel.name,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Strategize: покупка улучшения ${sel.name}`, G.curP);
      if (!res.state?.pending_strategize) {
        addLog('Strategize завершён', G.curP);
        _selectedOrderForPlay = null;
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось купить улучшение');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}
