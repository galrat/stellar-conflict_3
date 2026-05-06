'use strict';
// ══════════════════════════════════════════════
//  API BRIDGE  (Python handles game logic)
// ══════════════════════════════════════════════

async function apiCall(endpoint, body = {}) {
  const r = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text();
    console.error(`API ${endpoint} → ${r.status}:`, text);
    return { success: false, error: `Сервер вернул ошибку ${r.status}` };
  }
  return r.json();
}

function applyState(newState) {
  // Сохраняем UI-only поля которые Python не знает
  const uiFields = ['selHandIdx', 'selUnitIdx', 'selUnitType', 'selStructIdx'];
  const saved = {};
  uiFields.forEach(k => { saved[k] = G[k]; });
  const prevPlayer = G.curP;
  const prevPhase = G.phase;
  Object.assign(G, newState);
  // Явно очищаем pending-поля если сервер их удалил
  if (!('pending_deploy' in newState)) G.pending_deploy = null;
  if (!('pending_joker_choice' in newState)) G.pending_joker_choice = null;
  if (!('pending_advance' in newState)) G.pending_advance = null;
  if (!('pending_strategize' in newState)) G.pending_strategize = null;
  if (!('pending_chaos_dominate' in newState)) G.pending_chaos_dominate = null;
  if (!('pending_eldar_dominate' in newState)) G.pending_eldar_dominate = null;
  if (!('pending_marine_dominate' in newState)) G.pending_marine_dominate = null;
  if (!('pending_orks_dominate' in newState)) G.pending_orks_dominate = null;
  uiFields.forEach(k => { G[k] = saved[k]; });
  // Сбросить выбранный приказ при смене игрока
  if (G.curP !== prevPlayer) _selectedOrderForPlay = null;

  syncLog();
  renderBoard();
  renderSide();
  updateHeader();

  // Если фаза изменилась (Stage 2), вызвать setPhase для полного обновления UI
  // Для Stage 1 фаз setPhase не нужен, они управляют своим UI сами
  const stage2Phases = ['order-placement', 'orders_placed', 'execution', 'end-round'];
  if (G.phase !== prevPhase && stage2Phases.includes(G.phase)) {
    setPhase(G.phase);
  }
}

async function _restoreGame(phase) {
  try {
    await apiCall('/api/game/clear-temp', {});
    const data = await apiCall('/api/game/restore', { state: G });
    if (data.success) {
      applyState(data.state);
      syncLog();
      // Если при загрузке был незавершён выбор джокера — показать диалог сразу
      if (data.state?.pending_joker_choice) {
        _showJokerChoiceUI(data.state.pending_joker_choice);
      } else if (phase === 'execution') {
        const player = G.players[G.curP];
        showHP(player.name, 'Розыгрыш приказов', () => setPhase('execution'));
      } else if (phase === 'end-round') {
        setPhase('end-round');
      } else if (phase === 'order-placement' || phase === 'orders_placed') {
        setPhase(phase);
      }
    } else {
      showMsg('Ошибка восстановления', data.error || 'Не удалось восстановить игру');
    }
  } catch(e) {
    showMsg('Сервер недоступен', 'Запустите: uvicorn game_server:app --reload --port 8000');
  }
}

async function startStage2() {
  clearLog();
  addLog('Карта готова. Инициализация Stage 2...', -1);
  try {
    G.phase = 'order-placement';  // Установить фазу ДО отправки на сервер
    // Очистить старые snapshots перед новой игрой
    await apiCall('/api/game/clear-temp', {});
    const data = await apiCall('/api/game/init', { state: G });
    if (data.success) {
      applyState(data.state);
      addLog(`Stage 2 начат. Ход: ${G.players[G.curP].name}`, -1);
      setPhase('order-placement');

      // Автосохранение карты после инициализации (state уже обогащён Python)
      fetch(`${API_URL}/api/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: 'map_autosave', state: G })
      }).catch(() => {});
    } else {
      showMsg('Ошибка Stage 2', data.error || 'Неизвестная ошибка');
    }
  } catch(e) {
    showMsg('Сервер недоступен', 'Запустите: uvicorn game_server:app --reload --port 8000');
  }
}
