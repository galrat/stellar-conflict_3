'use strict';
// ══════════════════════════════════════════════
//  ORDER PLACEMENT + PLAY  (Stage 2)
// ══════════════════════════════════════════════

console.log('game_orders.js загружается');

let _selectedOrderForPlacement = null;  // { idx, id, type, owner }
let _selectedOrderForPlay      = null;  // { id, type, tile } — выбранный приказ для розыгрыша/сброса

// ── Order placement ──────────────────────────────────────────────

async function undoLastOrderViaAPI() {
  try {
    const res = await apiCall('/api/game/undo', { player_id: G.curP });
    if (res.success) {
      closeMsg();  // закрыть deploy/advance modal если открыт

      // Очищаем ВСЕ временные переменные UI в одном месте
      _resetDeployUI();
      _resetAdvanceUI();
      _selectedOrderForPlacement = null;
      _selectedOrderForPlay = null;

      const prevPhase = G.phase;
      applyState(res.state);
      // applyState может уже вызвать setPhase если фаза изменилась
      // Если фаза не изменилась, вызвать setPhase без render чтобы очистить состояние
      if (G.phase === prevPhase) {
        setPhase(G.phase, false);
      }

      addLog(`${G.players[G.curP].name} отменил действие`, G.curP);
    } else {
      showMsg('Ошибка отмены', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function passOrderTurnViaAPI() {
  try {
    const res = await apiCall('/api/game/pass-turn', { player_id: G.curP });
    if (res.success) {
      _lastCleanState = JSON.parse(JSON.stringify(res.state));
      applyState(res.state);
      // applyState вызовет setPhase если фаза изменилась
      _selectedOrderForPlacement = null;

      // Визуализируем смену игрока или фазы через showHP
      const nextPlayer = G.players[G.curP];
      const actionLabels = {
        'order-placement': 'Выставьте приказы',
        'orders_placed': 'Ожидание розыгрыша',
        'execution': 'Розыгрыш приказов',
      };
      const action = actionLabels[G.phase] || 'Ход';
      addLog(`${nextPlayer.name}: ${action}`, -1);
      showHP(nextPlayer.name, action, () => closeHP());
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function selectOrderForPlacement(idx, order) {
  _selectedOrderForPlacement = { idx, id: order.id, type: order.type, owner: G.curP };
  renderSide();
}

async function placeOrderViaAPI(tileKey) {
  if (!_selectedOrderForPlacement) return;

  const orderData = _selectedOrderForPlacement;
  try {
    const res = await apiCall('/api/game/place-order', {
      player_id: G.curP,
      order_id:  orderData.id,
      tile_key:  tileKey
    });
    if (res.success) {
      applyState(res.state);
      _selectedOrderForPlacement = null;
      addLog(`${G.players[G.curP].name} выставил ${ORDER_TYPES[orderData.type]?.name || 'приказ'}`, G.curP);
      setPhase(G.phase);
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

// ── General pass ─────────────────────────────────────────────────

function passOrderTurn() {
  if (G.phase === 'order-placement' || G.phase === 'orders_placed') {
    passOrderTurnViaAPI();
  } else if (G.phase === 'execution') {
    passOrderPlayTurnViaAPI();
  }
}

// ── Order play ────────────────────────────────────────────────────

function selectOrderForPlay(orderId, orderType, tileKey) {
  console.log('selectOrderForPlay: orderId=' + orderId + ', selected=' + _selectedOrderForPlay?.id);
  if (_selectedOrderForPlay?.id === orderId) {
    // Второй клик — розыгрыш
    console.log('→ ВТОРОЙ КЛИК - розыгрыш приказа');
    playOrderViaAPI(orderId);
  } else {
    // Первый клик — выделение
    console.log('→ ПЕРВЫЙ КЛИК - выделение. Кликни еще раз чтобы разыграть');
    _selectedOrderForPlay = { id: orderId, type: orderType, tile: tileKey };
    renderSide();
    renderBoard();
  }
}

async function playOrderViaAPI(orderId) {
  const ordersBefore = G.orders.filter(o => o.owner === G.curP);
  const order        = ordersBefore.find(o => o.id === orderId);
  const orderType    = ORDER_TYPES[order?.type];
  const orderName    = orderType?.name || order?.type || orderId;

  try {
    const res = await apiCall('/api/game/play-order', {
      player_id: G.curP,
      order_id:  orderId
    });
    if (res.success) {
      _selectedOrderForPlay = null;
      console.log('playOrderViaAPI: ответ получен, type=' + orderType?.id);
      applyState(res.state);
      console.log('applyState выполнена, G.pending_deploy=' + !!G.pending_deploy);
      addLog(`${G.players[G.curP]?.name || 'Игрок'}: приказ "${orderName}" разыгран`, G.curP);
      // Check if dominate produced a joker choice
      if (res.state?.pending_joker_choice) {
        console.log('→ Joker choice');
        _showJokerChoiceUI(res.state.pending_joker_choice);
      } else if (res.state?.pending_deploy) {
        console.log('→ Deploy UI (pending_deploy есть)');
        setPhase('execution');
        showDeployUI();
      } else if (res.state?.pending_advance) {
        console.log('→ Advance UI');
        showAdvanceUI();
      } else {
        console.log('→ Ничего нет, только execution');
        setPhase('execution');
      }
    } else {
      console.log('playOrderViaAPI: ошибка - ' + res.error);
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function _showJokerChoiceUI(pending) {
  const TOKEN_LABELS = { support: '🛡 Support', discount: '💰 Discount', forge: '🔨 Forge' };
  const count = pending.joker_count || 1;
  const pid   = pending.player_id;

  const html = `
    <div style="margin-bottom:10px;color:#aaa;">Выберите тип токена для джокера (${count} шт.):</div>
    <div style="display:flex;gap:10px;justify-content:center;">
      ${['support','discount','forge'].map(t => `
        <button class="abtn bp" onclick="_resolveJoker(${pid},'${t}')"
          style="padding:12px 20px;font-size:1rem;">${TOKEN_LABELS[t]}</button>
      `).join('')}
    </div>`;
  showMsg('🎲 Выбор джокера', html);
}

async function _resolveJoker(playerId, choiceType) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-joker', {
      player_id: playerId,
      choice:    choiceType
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Джокер → ${choiceType}`, playerId);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || 'Не удалось разрешить джокер');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function discardOrderViaAPI() {
  if (!_selectedOrderForPlay) return;

  const orderId   = _selectedOrderForPlay.id;
  const orderType = ORDER_TYPES[_selectedOrderForPlay.type];
  const orderName = orderType?.name || _selectedOrderForPlay.type;

  try {
    const res = await apiCall('/api/game/discard-order', {
      player_id: G.curP,
      order_id:  orderId
    });
    if (res.success) {
      _selectedOrderForPlay = null;
      applyState(res.state);
      addLog(`${G.players[G.curP]?.name || 'Игрок'}: приказ "${orderName}" сброшен`, G.curP);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function passOrderPlayTurnViaAPI() {
  try {
    const res = await apiCall('/api/game/pass-turn-order-play', {
      player_id: G.curP
    });
    if (res.success) {
      _lastCleanState = JSON.parse(JSON.stringify(res.state));
      _selectedOrderForPlay = null;
      applyState(res.state);

      // applyState автоматически вызовет setPhase если фаза изменилась
      // Здесь только логируем и показываем UI для смены игрока
      if (G.phase === 'end-round') {
        addLog('✅ Все приказы разыграны! Конец раунда.', -1);
      } else if (G.phase === 'execution') {
        const nextPlayer = G.players[G.curP];
        addLog(`${nextPlayer.name} ходит в фазе розыгрыша`, -1);
        showHP(nextPlayer.name, 'Розыгрыш приказов', () => closeHP());
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function nextRoundViaAPI() {
  try {
    const res = await apiCall('/api/game/next-round', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      // applyState автоматически вызовет setPhase('order-placement')
      addLog(`Раунд ${G.round}. Первый ход: ${G.players[G.curP].name}`, -1);
      showHP(G.players[G.curP].name, 'Расстановка приказов', () => closeHP());
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}
