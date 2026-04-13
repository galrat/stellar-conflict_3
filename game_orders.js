'use strict';
// ══════════════════════════════════════════════
//  ORDER PLACEMENT + PLAY  (Stage 2)
// ══════════════════════════════════════════════

let _selectedOrderForPlacement = null;  // { idx, id, type, owner }
let _selectedOrderForPlay      = null;  // { id, type, tile } — выбранный приказ для розыгрыша/сброса

// ── Order placement ──────────────────────────────────────────────

async function undoLastOrderViaAPI() {
  const isPlacement = G.phase === 'order-placement';
  const isExecution = G.phase === 'execution';
  if (!isPlacement && !isExecution) return;

  if (isPlacement && !G.ui?.order_placed_this_turn) {
    showMsg('Нет приказов', 'В этом ходу приказ не выставлялся');
    return;
  }
  if (isExecution && !G.ui?.order_played_this_turn && !G.pending_deploy) {
    showMsg('Нет действий', 'В этом ходу приказ не разыгрывался');
    return;
  }

  try {
    const res = await apiCall('/api/game/undo', { player_id: G.curP });
    if (res.success) {
      closeMsg();  // закрыть deploy modal если открыт
      _deployBasket = [];
      _deploySelectedUnit = null;
      _deploySelectedBuilding = null;
      applyState(res.state);
      _selectedOrderForPlacement = null;
      _selectedOrderForPlay = null;
      addLog(`${G.players[G.curP].name} отменил действие`, G.curP);
      setPhase(G.phase);
    } else {
      showMsg('Ошибка отмены', res.error || 'Не удалось отменить');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function passOrderTurnViaAPI() {
  if (G.phase !== 'order-placement' && G.phase !== 'orders_placed') return;

  try {
    const res = await apiCall('/api/game/pass-turn', { player_id: G.curP });
    if (res.success) {
      _lastCleanState = JSON.parse(JSON.stringify(res.state));
      applyState(res.state);
      _selectedOrderForPlacement = null;

      // Проверяем в какую фазу перешли
      if (G.phase === 'orders_placed') {
        addLog('✅ Ожидание начала розыгрыша приказов...', -1);
        const nextPlayer = G.players[G.curP];
        showHP(nextPlayer.name, 'Ожидание розыгрыша', () => setPhase('orders_placed'));
      } else if (G.phase === 'execution') {
        addLog('🎮 Начало розыгрыша приказов!', -1);
        const nextPlayer = G.players[G.curP];
        showHP(nextPlayer.name, 'Розыгрыш приказов', () => setPhase('execution'));
      } else {
        // Остаемся в order-placement, смена игрока
        const nextPlayer = G.players[G.curP];
        showHP(nextPlayer.name, 'Выставьте приказы', () => setPhase('order-placement'));
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось передать ход');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function selectOrderForPlacement(idx, order) {
  if (G.phase !== 'order-placement') return;
  if (!G.ui?.can_place_order) return;
  _selectedOrderForPlacement = { idx, id: order.id, type: order.type, owner: G.curP };
  renderSide();
}

async function placeOrderViaAPI(tileKey) {
  if (G.phase !== 'order-placement') {
    if (G.phase === 'orders_placed') {
      showMsg('Запрещено', 'Размещение приказов завершено. Нажмите ПЕРЕДАТЬ ХОД.');
    }
    return;
  }

  if (!G.ui?.can_place_order) {
    showMsg('Лимит достигнут', 'Вы уже разместили приказ в этом ходу или достигнут лимит');
    return;
  }

  if (!_selectedOrderForPlacement) {
    showMsg('Выберите приказ', 'Сначала выберите приказ слева');
    return;
  }

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
      setPhase('order-placement');
    } else {
      showMsg('Ошибка', res.error || 'Не удалось разместить приказ');
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
  if (G.phase !== 'execution') return;
  if (_selectedOrderForPlay?.id === orderId) {
    // Второй клик — розыгрыш
    playOrderViaAPI(orderId);
  } else {
    // Первый клик — выделение
    _selectedOrderForPlay = { id: orderId, type: orderType, tile: tileKey };
    renderSide();
    renderBoard();
  }
}

async function playOrderViaAPI(orderId) {
  if (G.phase !== 'execution') return;

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
      applyState(res.state);
      addLog(`${G.players[G.curP]?.name || 'Игрок'}: приказ "${orderName}" разыгран`, G.curP);
      // Check if dominate produced a joker choice
      if (res.state?.pending_joker_choice) {
        _showJokerChoiceUI(res.state.pending_joker_choice);
      } else if (res.state?.pending_deploy) {
        setPhase('execution');
        showDeployUI();
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось разыграть приказ');
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
  if (G.phase !== 'execution') return;
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
      showMsg('Ошибка', res.error || 'Не удалось сбросить приказ');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function passOrderPlayTurnViaAPI() {
  if (G.phase !== 'execution') return;

  try {
    const res = await apiCall('/api/game/pass-turn-order-play', {
      player_id: G.curP
    });
    if (res.success) {
      _lastCleanState = JSON.parse(JSON.stringify(res.state));
      _selectedOrderForPlay = null;
      applyState(res.state);

      if (G.phase === 'end-round') {
        addLog('✅ Все приказы разыграны! Конец раунда.', -1);
        setPhase('end-round');
      } else if (G.phase === 'execution') {
        const nextPlayer = G.players[G.curP];
        addLog(`${nextPlayer.name} ходит в фазе розыгрыша`, -1);
        showHP(nextPlayer.name, 'Розыгрыш приказов', () => setPhase('execution'));
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось передать ход');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function nextRoundViaAPI() {
  if (G.phase !== 'end-round') return;

  try {
    const res = await apiCall('/api/game/next-round', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      addLog(`Раунд ${G.round}. Первый ход: ${G.players[G.curP].name}`, -1);
      showHP(G.players[G.curP].name, 'Расстановка приказов', () => setPhase('order-placement'));
    } else {
      showMsg('Ошибка', res.error || 'Не удалось перейти к следующему раунду');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}
