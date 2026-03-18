'use strict';
// ══════════════════════════════════════════════
//  GAME HISTORY — сохранение / отмена / возврат хода
//  Globals: historySave(), historyUndo(), historyRedo(), historySetFloor()
//  Depends on globals (resolved at call time):
//    G, setPhase, updateHeader, renderSide, renderBoard
// ══════════════════════════════════════════════

const _HIST_LS_KEY = 'stellar_conflict_saves';

// Массив снимков состояния (in-memory)
let _histSnaps = [];
let _histPos   = -1;
let _histFloor = 0;  // нижняя граница undo — не откатываться раньше этого снимка

/**
 * Сохранить текущее состояние G с меткой label.
 * Вызывается: после создания карты и после каждой передачи хода.
 */
function historySave(label) {
  label = label || ('Состояние ' + new Date().toLocaleTimeString('ru'));

  // Deep-clone G, исключая функции-колбэки
  const snap = JSON.parse(JSON.stringify(G, (k, v) => {
    if (k === '_battleCb') return null;
    return v;
  }));

  // Обрезаем «будущее» если undo уже был
  _histSnaps = _histSnaps.slice(0, _histPos + 1);
  _histSnaps.push({ snap, label, ts: Date.now() });
  // Ограничим глубину истории 30 состояниями
  if (_histSnaps.length > 30) { _histSnaps.shift(); if (_histFloor > 0) _histFloor--; }
  _histPos = _histSnaps.length - 1;

  // Сохраняем индекс в localStorage (отдельная «папка сохранений»)
  try {
    const index = _histSnaps.map(h => ({ label: h.label, ts: h.ts }));
    localStorage.setItem(_HIST_LS_KEY, JSON.stringify(index));
  } catch (e) { /* переполнение quota — игнорируем */ }

  _histUpdateBtns();
}

/**
 * Зафиксировать текущую позицию как минимальную точку откатa.
 * Вызывается при старте фазы приказов — нельзя откатиться в фазу расстановки.
 */
function historySetFloor() {
  _histFloor = _histPos;
  _histUpdateBtns();
}

/** Отменить ход: вернуться к предыдущему снимку (но не дальше _histFloor). */
function historyUndo() {
  if (_histPos <= _histFloor) return;
  _histPos--;
  _histRestoreAt(_histPos);
}

/** Вернуть ход: перейти к следующему снимку. */
function historyRedo() {
  if (_histPos >= _histSnaps.length - 1) return;
  _histPos++;
  _histRestoreAt(_histPos);
}

function _histRestoreAt(pos) {
  const entry = _histSnaps[pos];
  if (!entry) return;

  // Восстановить G: стереть все поля и присвоить из снимка
  Object.keys(G).forEach(k => delete G[k]);
  Object.assign(G, entry.snap);

  // Переинициализировать UI для текущей фазы
  setPhase(G.phase);
  _histUpdateBtns();
}

/** Обновить видимость кнопок «отменить/вернуть». */
function _histUpdateBtns() {
  const u = document.getElementById('btn-undo');
  const r = document.getElementById('btn-redo');
  if (u) u.style.display = _histPos > _histFloor                ? 'block' : 'none';
  if (r) r.style.display = _histPos < _histSnaps.length - 1     ? 'block' : 'none';
}
