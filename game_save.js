'use strict';
// ══════════════════════════════════════════════
//  SAVE / LOAD
// ══════════════════════════════════════════════
const SAVE_KEY = 'stellar_conflict_map';
// Чистое состояние — снимается сразу после передачи хода
let _lastCleanState = null;

function saveGame() {
  if (isSaving) return;

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const defaultName = `game_${timestamp}`;

  const html = `
    <div style="margin-bottom:8px;color:#aaa;">Название файла:</div>
    <input id="save-filename-input" type="text" value="${defaultName}"
      style="width:100%;box-sizing:border-box;padding:8px;background:rgba(0,200,255,.07);border:1px solid rgba(0,200,255,.3);color:#e0f0ff;border-radius:4px;font-size:.9rem;">
    <div style="margin-top:12px;display:flex;gap:8px;">
      <button class="abtn bp" style="flex:1" onclick="_doSaveGame()">💾 Сохранить</button>
      <button class="abtn bw" style="flex:0 0 auto" onclick="closeMsg()">Отмена</button>
    </div>`;
  showMsg('💾 Сохранить игру', html);
  setTimeout(() => {
    const inp = document.getElementById('save-filename-input');
    if (inp) { inp.focus(); inp.select(); }
  }, 50);
}

function _doSaveGame() {
  const inp = document.getElementById('save-filename-input');
  const filename = (inp ? inp.value.trim() : '') || `game_${Date.now()}`;
  closeMsg();

  const stateToSave = _lastCleanState || G;
  isSaving = true;
  fetch(`${API_URL}/api/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, state: stateToSave })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      showMsg('💾 Сохранено', `Файл: <strong>${data.filename}</strong><br><br>📁 Загрузки/Stellar_Conflict_Saves/`);
    } else {
      showMsg('Ошибка сохранения', data.error || 'Неизвестная ошибка');
    }
  })
  .catch(e => {
    localStorage.setItem('game_' + filename, JSON.stringify(G));
    showMsg('💾 Сохранено (локально)', `<strong>${filename}</strong><br><br>⚠ Сервер недоступен.`);
  })
  .finally(() => { isSaving = false; });
}

function _upgradeLoadedState(state) {
  // Ensure all areas have area_place property for objective marker rendering
  const map = state.map || {};
  Object.values(map).forEach(tile => {
    if (tile.areas && Array.isArray(tile.areas)) {
      tile.areas.forEach((area, idx) => {
        if (typeof area.area_place !== 'number') {
          area.area_place = idx;
        }
      });
    }
  });
}

function loadGame() {
  fetch(`${API_URL}/api/list`)
  .then(r => r.json())
  .then(data => {
    if (!data.success || data.games.length === 0) {
      console.warn('⚠️  Нет сохранённых игр на сервере');
      showMsg('Нет сохранений', 'Сохранённые игры находятся в:<br>Загрузки/Stellar_Conflict_Saves/<br><br>Запустите сервер: python game_server.py');
      return;
    }

    let html = '<div style="max-height:500px;overflow-y:auto;">';
    data.games.forEach(g => {
      const date = new Date(g.modified * 1000).toLocaleString();
      html += `<div style="padding:8px;background:rgba(0,200,255,.1);margin-bottom:6px;border-radius:4px;cursor:pointer;" onclick="loadGameFile('${g.filename}')">
        <div style="font-weight:bold;">${g.filename}</div>
        <div style="font-size:.75rem;color:#aaa;">${date} · ${g.size} B</div>
      </div>`;
    });
    html += '</div>';

    console.log(`✅ Получено ${data.games.length} сохранённых игр`);
    showMsg('📂 Загрузить игру', html);
  })
  .catch(e => {
    console.error('❌ Ошибка при загрузке списка игр:', e);
    showMsg('Ошибка', '⚠ Сервер недоступен.<br><br>Для загрузки из Загрузок запустите:<br><code>python game_server.py</code>');
  });
}

function validateGameState(state) {
  // Проверка обязательных полей
  const requiredFields = ['version', 'players', 'phase', 'map', 'curP'];
  for (const field of requiredFields) {
    if (!(field in state)) {
      return { valid: false, error: `Отсутствует поле: ${field}` };
    }
  }

  // Проверка версии
  if (state.version !== 1) {
    console.warn(`⚠️  Версия сохранения: ${state.version}. Текущая версия: 1. Попытаемся загрузить...`);
  }

  // Проверка типов
  if (!Array.isArray(state.players) || state.players.length !== 2) {
    return { valid: false, error: 'Некорректное количество игроков' };
  }

  if (typeof state.phase !== 'string') {
    return { valid: false, error: 'Некорректная фаза игры' };
  }

  return { valid: true };
}

function loadGameFile(filename) {
  fetch(`${API_URL}/api/load/${filename}`)
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      const validation = validateGameState(data.state);
      if (!validation.valid) {
        console.error('❌ Ошибка валидации:', validation.error);
        showMsg('Ошибка загрузки', `Файл повреждён или устарел:<br><strong>${validation.error}</strong>`);
        return;
      }

      // Upgrade state to ensure all areas have area_place
      _upgradeLoadedState(data.state);

      Object.keys(G).forEach(k => delete G[k]);
      Object.assign(G, data.state);
      console.log(`✅ Игра загружена: ${filename}`);
      clearLog();  // очистить DOM-лог перед загрузкой новой игры
      showScreen('game-screen');

      const phase = G.phase;
      if (['execution', 'end-round', 'order-placement', 'orders_placed'].includes(phase)) {
        // Восстановить state на сервере без сброса карт и прочих данных
        console.log(`🔄 Восстанавливаю игру в фазе ${phase}...`);
        _restoreGame(phase);
      } else {
        // Stage 1 фазы: tile-placement, troop-on-tile, warp-storm и т.д.
        setPhase(phase);
        updateHeader();
        renderBoard();
        renderSide();
        syncLog();
      }

      addLog('Игра загружена', -1);
      closeMsg();
    } else {
      console.error('❌ Ошибка загрузки файла:', data.error);
      showMsg('Ошибка загрузки', data.error);
    }
  })
  .catch(e => {
    console.error('❌ Ошибка при загрузке:', e);
    showMsg('Ошибка', 'Не удалось загрузить: ' + e.message);
  });
}
