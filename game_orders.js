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
      _resetStrategizeUI();
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
      // Check if dominate produced a joker or chaos ability
      if (res.state?.pending_joker_choice) {
        console.log('→ Joker choice');
        _showJokerChoiceUI(res.state.pending_joker_choice);
      } else if (res.state?.pending_chaos_dominate) {
        console.log('→ Chaos dominate ability');
        setPhase('execution');
      } else if (res.state?.pending_eldar_dominate) {
        console.log('→ Eldar dominate ability');
        setPhase('execution');
      } else if (res.state?.pending_orks_dominate) {
        console.log('→ Orks dominate ability');
        setPhase('execution');
        showOrksDominateUI();
      } else if (res.state?.pending_deploy) {
        console.log('→ Deploy UI (pending_deploy есть)');
        setPhase('execution');
        showDeployUI();
      } else if (res.state?.pending_advance) {
        console.log('→ Advance UI');
        showAdvanceUI();
      } else if (res.state?.pending_strategize) {
        console.log('→ Strategize UI');
        renderStrategize();
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

async function chooseGreenTideOrder(orderType) {
  try {
    const res = await apiCall('/api/game/choose-green-tide-order', {
      player_id:    G.curP,
      order_choice: orderType,
    });
    if (res.success) {
      applyState(res.state);
      if (res.state?.pending_joker_choice) {
        _showJokerChoiceUI(res.state.pending_joker_choice);
      } else if (res.state?.pending_chaos_dominate) {
        setPhase('execution');
      } else if (res.state?.pending_eldar_dominate) {
        setPhase('execution');
      } else if (res.state?.pending_marine_dominate) {
        setPhase('execution');
      } else if (res.state?.pending_orks_dominate) {
        setPhase('execution');
        showOrksDominateUI();
      } else if (res.state?.pending_deploy) {
        showDeployUI();
      } else if (res.state?.pending_advance) {
        showAdvanceUI();
      } else if (res.state?.pending_strategize) {
        renderStrategize();
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function playOrderUpgradeViaAPI(orderId, upgradeIds) {
  try {
    const res = await apiCall('/api/game/play-order-upgrade', {
      player_id:   G.curP,
      order_id:    orderId,
      upgrade_ids: upgradeIds,
    });
    if (res.success) {
      _selectedOrderForPlay = null;
      applyState(res.state);
      if (res.state?.pending_green_tide) {
        renderSide();
      } else if (res.state?.pending_deploy) {
        showDeployUI();
      } else if (res.state?.pending_advance) {
        showAdvanceUI();
      } else if (res.state?.pending_strategize && !res.state?.pending_direct_the_faithful) {
        renderStrategize();
      } else {
        setPhase('execution');
      }
    } else {
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
      if (res.state?.pending_chaos_dominate) {
        setPhase('execution');
      } else if (res.state?.pending_eldar_dominate) {
        setPhase('execution');
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось разрешить джокер');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function _showChaosDominateUI(pending) {
  const pid     = pending.player_id;
  const targets = pending.valid_targets || [];

  const targetBtns = targets.map(t =>
    `<button class="abtn bp" onclick="_chaosDominateChoose(${pid},'${t.tile_key}',${t.area_idx})"
       style="margin:4px 2px;">
       Система ${t.tile_key} · Планета ${t.area_idx}
     </button>`
  ).join('');

  const html = `
    <div style="margin-bottom:10px;color:#aaa;">
      Переместите культиста в нейтральную или дружественную планету соседней системы:
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-bottom:14px;">
      ${targetBtns}
    </div>
    <div style="text-align:center;">
      <button class="abtn" onclick="_chaosDominateSkip(${pid})"
        style="padding:8px 24px;">Пропустить</button>
    </div>`;
  showMsg('⬡ Хаос: особое свойство доминации', html);
}

async function _chaosDominateChoose(playerId, tileKey, areaIdx) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-chaos-choose', {
      player_id: playerId,
      tile_key:  tileKey,
      area_idx:  areaIdx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Хаос: культист → система ${tileKey}, область ${areaIdx}`, playerId);
      if (res.state?.pending_chaos_retreat) {
        _showChaosRetreatUI(res.state.pending_chaos_retreat);
      } else {
        setPhase('execution');
      }
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function _showChaosRetreatUI(pending) {
  const pid      = pending.player_id;
  const tileKey  = pending.tile_key;
  const areaIdx  = pending.area_idx;
  const capacity = pending.capacity;
  const units    = pending.units || [];

  const unitBtns = units.map(u => {
    const label = u.player === pid ? `Ваш: ${u.unitType} tier${u.tier}` : `Соперник: ${u.unitType} tier${u.tier}`;
    return `<button class="abtn bp" onclick="_chaosRetreatChoose(${pid},'${tileKey}',${areaIdx},${u.troop_idx})"
      style="margin:4px 2px;display:block;width:100%;">${label}</button>`;
  }).join('');

  const html = `
    <div style="margin-bottom:10px;color:#aaa;">
      Область переполнена (capacity=${capacity}). Выберите юнита для удаления:
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;">${unitBtns}</div>`;
  showMsg('⬡ Хаос: выберите юнита для удаления', html);
}

async function _chaosRetreatChoose(playerId, tileKey, areaIdx, troopIdx) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-chaos-retreat', {
      player_id: playerId,
      tile_key:  tileKey,
      area_idx:  areaIdx,
      troop_idx: troopIdx,
    });
    if (res.success) {
      applyState(res.state);
      addLog(`Хаос: юнит удалён из ${tileKey}/${areaIdx}`, playerId);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function _chaosDominateSkip(playerId) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/dominate-chaos-skip', { player_id: playerId });
    if (res.success) {
      applyState(res.state);
      addLog('Хаос: особое свойство пропущено', playerId);
      setPhase('execution');
    } else {
      showMsg('Ошибка', res.error || '');
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
