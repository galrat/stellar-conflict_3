'use strict';
// ══════════════════════════════════════════════
//  ORDER PLACEMENT — расстановка приказов
//  Globals: ORDER_TYPES_DATA, ORDER_ICONS, makeOrderTokens(),
//           selectOrderType(), placeOrderOnTile(), cancelCurrentOrder(),
//           renderOrderPanel(), getValidOrderTiles()
//  Depends on globals (resolved at call time):
//    G, historySave, showHP, setPhase, addLog, showMsg,
//    renderSide, renderBoard, getNeighborKeys, show
// ══════════════════════════════════════════════

// ── Определение типов приказов ───────────────────────────────────────────────
const ORDER_TYPES_DATA = [
  { id: 'move',     label: 'Advance',    icon: '➤' },
  { id: 'build',    label: 'Deploy',     icon: '⚙' },
  { id: 'dominate', label: 'Dominate',   icon: '★' },
  { id: 'plan',     label: 'Strategize', icon: '◎' },
];

// Быстрый поиск иконки по id типа (используется в renderBoard)
const ORDER_ICONS = Object.fromEntries(ORDER_TYPES_DATA.map(o => [o.id, o.icon]));

// ── Жетоны приказов ──────────────────────────────────────────────────────────

/**
 * Создать стартовый набор из 8 жетонов (по 2 каждого типа).
 * Возвращает массив объектов {type}.
 */
function makeOrderTokens() {
  return ORDER_TYPES_DATA.flatMap(ot => [{ type: ot.id }, { type: ot.id }]);
}

// ── Подсчёт использованных жетонов по типу ───────────────────────────────────

/**
 * Возвращает объект {type: usedCount} для текущего игрока.
 * Вычисляется из cp.orders — источник истины.
 */
function _getUsedCounts(playerIdx) {
  const usedCounts = {};
  ORDER_TYPES_DATA.forEach(ot => { usedCounts[ot.id] = 0; });
  const orders = G.players[playerIdx].orders || [];
  orders.forEach(o => { if (o && o.type) usedCounts[o.type]++; });
  return usedCounts;
}

// ── Допустимые тайлы для размещения приказа ──────────────────────────────────

/**
 * Возвращает Set ключей тайлов, на которые playerIdx может поставить приказ:
 * — тайл, где у игрока есть войска ИЛИ постройки,
 * — ЛИБО тайл, соседний (по горизонтали/вертикали) с таким тайлом.
 * Стекование на одном тайле разрешено — ограничений по повторному размещению нет.
 */
function getValidOrderTiles(playerIdx) {
  const tiles = Object.values(G.map);

  // Тайлы с присутствием игрока
  const ownedKeys = new Set();
  tiles.forEach(tile => {
    const hasOwn = tile.areas.some(a =>
      a.troops.some(t => t.player === playerIdx) ||
      (a.structures || []).some(s => s.player === playerIdx)
    );
    if (hasOwn) ownedKeys.add(tile.key);
  });

  // Добавить соседей
  const valid = new Set(ownedKeys);
  ownedKeys.forEach(k =>
    getNeighborKeys(k).forEach(nk => { if (G.map[nk]) valid.add(nk); })
  );

  return valid;
}

// ── Выбор типа приказа (клик по жетону в панели) ─────────────────────────────

function selectOrderType(type) {
  if (G.phase !== 'order-placement') return;
  if (G.currentStepOrderPlaced) return;   // текущий шаг уже выполнен

  const usedCounts = _getUsedCounts(G.curP);
  const available = 2 - (usedCounts[type] || 0);
  if (available <= 0) {
    showMsg('Нет жетона', 'Жетон этого типа уже использован.'); return;
  }

  G.selectedOrderType = type;
  renderSide();
  renderBoard(null, false, true);   // true = показать допустимые тайлы

  const ot = ORDER_TYPES_DATA.find(o => o.id === type);
  document.getElementById('pinstr').innerHTML =
    `<strong>${ot.icon} ${ot.label}</strong><br>` +
    `Кликните на допустимую систему для размещения приказа.`;
}

// ── Размещение приказа на тайл ───────────────────────────────────────────────

/**
 * Вызывается при клике на тайл key в фазе order-placement.
 * Приказ размещается на весь тайл; aIdx=0 — запасное значение для совместимости с execNext.
 */
function placeOrderOnTile(key) {
  if (G.phase !== 'order-placement') return;

  if (G.currentStepOrderPlaced) {
    showMsg('Приказ уже размещён',
      'Нажмите «Готово →» для передачи хода или «✕ Отменить приказ» для отмены.');
    return;
  }

  if (!G.selectedOrderType) {
    showMsg('Выберите жетон', 'Нажмите на жетон приказа в панели, чтобы выбрать тип.');
    return;
  }

  const cp = G.players[G.curP];
  const valid = getValidOrderTiles(G.curP);

  if (!valid.has(key)) {
    showMsg('Недопустимая система',
      'Приказ можно размещать только на системе с вашими войсками/постройками или соседней с ней.');
    return;
  }

  // Проверить доступность жетона через placed orders
  const usedCounts = _getUsedCounts(G.curP);
  const available = 2 - (usedCounts[G.selectedOrderType] || 0);
  if (available <= 0) { showMsg('Нет жетона', 'Жетон этого типа уже использован.'); return; }

  const slotIdx = (cp.orders || []).findIndex(o => o === null);
  if (slotIdx === -1) { showMsg('Все 4 приказа размещены', ''); return; }

  // Записать приказ; placedAt = шаг расстановки (определяет место в стеке и порядок исполнения)
  cp.orders[slotIdx] = { key, aIdx: 0, type: G.selectedOrderType, slot: slotIdx, placedAt: G.orderStep };

  G.currentStepOrderPlaced = true;
  G._thisStepOrderSlot = slotIdx;
  G.selectedOrderType = null;

  const ot = ORDER_TYPES_DATA.find(o => o.id === cp.orders[slotIdx].type);
  const ordCount = cp.orders.filter(o => o !== null).length;

  addLog(`${cp.name}: приказ ${ot.icon} размещён на [${key}] ▼`, G.curP);

  renderSide();
  renderBoard();

  document.getElementById('pinstr').innerHTML =
    `<strong>ПРИКАЗ РАЗМЕЩЁН (${ordCount}/4)</strong><br>` +
    `${cp.name}: нажмите «Готово →» для передачи хода или «✕» для отмены.`;

  show('btn-co');
}

// ── Отмена текущего приказа ──────────────────────────────────────────────────

function cancelCurrentOrder() {
  if (!G.currentStepOrderPlaced) return;
  if (G._thisStepOrderSlot === null || G._thisStepOrderSlot === undefined) return;

  const cp = G.players[G.curP];
  const ord = cp.orders[G._thisStepOrderSlot];
  if (!ord) return;

  // Убрать приказ из слота (доступность жетона автоматически восстанавливается)
  cp.orders[G._thisStepOrderSlot] = null;

  G.currentStepOrderPlaced = false;
  G._thisStepOrderSlot = null;

  addLog(`${cp.name} отменил размещение приказа`, G.curP);

  const ordCount = cp.orders.filter(o => o !== null).length;

  document.getElementById('btn-co').style.display = 'none';
  renderSide();
  renderBoard();

  document.getElementById('pinstr').innerHTML =
    `<strong>РАССТАНОВКА ПРИКАЗОВ</strong><br>` +
    `${cp.name}: выберите жетон приказа (${ordCount}/4 размещено).`;
}

// ── Рендер панели приказов (renderSide) ──────────────────────────────────────

/**
 * Отрисовывает жетоны и размещённые приказы в контейнере container.
 * Вызывается из renderSide() вместо старого блока с os0/os1.
 */
function renderOrderPanel(container) {
  container.innerHTML = '';
  const cp = G.players[G.curP];

  if (G.phase !== 'order-placement') {
    // Вне фазы приказов — заглушка
    for (let i = 0; i < 4; i++) {
      const slot = document.createElement('div');
      slot.className = 'oslot';
      slot.textContent = `— приказ ${i + 1}`;
      container.appendChild(slot);
    }
    return;
  }

  // ── Заголовок: сколько размещено ──
  const ordCount = (cp.orders || []).filter(o => o !== null).length;
  const hdr = document.createElement('div');
  hdr.className = 'pool-type-lbl';
  hdr.textContent = `Жетоны приказов (${ordCount}/4):`;
  container.appendChild(hdr);

  // ── Доступные жетоны по типам (вычисляем из placed orders) ──
  const grid = document.createElement('div');
  grid.className = 'otok-grid';

  const usedCounts = _getUsedCounts(G.curP);

  ORDER_TYPES_DATA.forEach(ot => {
    const available = 2 - (usedCounts[ot.id] || 0);

    // Рендерим только доступные жетоны — использованные просто не отображаются
    for (let c = 0; c < available; c++) {
      const isSel = G.selectedOrderType === ot.id;
      const tok = document.createElement('div');
      tok.className = `ttok otok otok-${ot.id}${isSel ? ' sel' : ''}`;
      tok.title = ot.label;
      tok.innerHTML = `${ot.icon}<span class="olabel">${ot.label}</span>`;
      tok.onclick = () => selectOrderType(ot.id);
      grid.appendChild(tok);
    }
    // Использованные жетоны не добавляются — они просто исчезают из панели
  });

  container.appendChild(grid);

  // ── Уже размещённые приказы ──
  const placed = (cp.orders || []).filter(o => o !== null);
  if (placed.length > 0) {
    const pHdr = document.createElement('div');
    pHdr.className = 'pool-type-lbl';
    pHdr.style.marginTop = '6px';
    pHdr.textContent = 'Размещено:';
    container.appendChild(pHdr);

    placed.forEach(o => {
      const ot = ORDER_TYPES_DATA.find(x => x.id === o.type);
      const slot = document.createElement('div');
      slot.className = `oslot otok-${ot?.id || ''}`;
      slot.style.cssText = 'font-size:.72rem;padding:4px 7px;border-style:solid;';
      slot.textContent = `${ot?.icon || '?'} ${ot?.label || o.type} → [${o.key}]`;
      container.appendChild(slot);
    });
  }
}
