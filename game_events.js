'use strict';
// ══════════════════════════════════════════════
//  EVENT CARD PICKER
// ══════════════════════════════════════════════

let _warpMoveState = null; // null | {step:'select_storm'|'select_dest', direction, moves, storm_idx, validDests}

function showEventCardPicker() {
  if (G.phase !== 'end-round') return;
  const selectionDone = G.event_selection_done || [false, false];
  if (selectionDone[G.curP]) return;

  // Если карта уже выбрана — сразу к перемещению шторма
  if (G.pending_warp_move && G.pending_warp_move.player_id === G.curP) {
    showWarpStormMover(G.pending_warp_move.direction);
    return;
  }

  const offered    = (G.event_cards_offered || [[], []])[G.curP] || [];
  const playerName = G.players[G.curP].name;

  if (!offered.length) return;

  let cardsHtml = offered.map(card => {
    const safeName = card.name.replace(/'/g, "\\'");
    const safeImg  = (card.image || '').replace(/'/g, "\\'");
    const nameHtml = card.image
      ? `<span onclick="event.stopPropagation();previewEventCardImage('${safeImg}','${safeName}')"
               style="cursor:pointer;text-decoration:underline dotted;text-underline-offset:3px;"
               title="Нажмите для просмотра">${card.name}</span>`
      : card.name;
    return `
    <div class="event-card-choice" onclick="selectEventCard('${safeName}')"
         style="padding:10px;background:rgba(0,200,255,.1);margin-bottom:8px;border-radius:6px;cursor:pointer;border:1px solid rgba(0,200,255,.2);">
      <div style="font-weight:bold;margin-bottom:4px;">${nameHtml}</div>
      <div style="font-size:.75rem;color:#aaa;margin-bottom:4px;">${card.card_type || ''}</div>
      <div style="font-size:.8rem;">${card.effect || ''}</div>
    </div>`;
  }).join('');

  const html = `
    <div style="margin-bottom:10px;color:#aaa;">Выберите одну карту для руки:</div>
    <div style="max-height:400px;overflow-y:auto;">${cardsHtml}</div>
  `;
  showMsg(`Карты событий — ${playerName}`, html);
}

async function selectEventCard(cardName) {
  closeMsg();
  try {
    const res = await apiCall('/api/game/select-event-card', {
      player_id: G.curP,
      card_name: cardName
    });
    if (res.success) {
      const prevPlayer = G.curP;
      applyState(res.state);
      addLog(`${G.players[prevPlayer].name} взял карту событий: ${cardName}`, prevPlayer);

      if (G.pending_warp_move && G.pending_warp_move.player_id === G.curP) {
        showWarpStormMover(G.pending_warp_move.direction);
      } else {
        // Направление пустое — шторм был пропущен автоматически
        _afterWarpMoveUi();
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось выбрать карту');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function previewEventCardImage(imgUrl, cardName) {
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.88);z-index:9999;display:flex;align-items:center;justify-content:center;cursor:pointer;';
  overlay.innerHTML = `
    <div style="max-width:380px;text-align:center;padding:16px;">
      <div style="color:#888;margin-bottom:8px;font-size:.8rem;">${cardName} — нажмите чтобы закрыть</div>
      <img src="${imgUrl}" style="max-width:100%;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,.7);">
    </div>`;
  overlay.onclick = () => overlay.remove();
  document.body.appendChild(overlay);
}

async function showWarpStormMover(direction) {
  try {
    const res = await apiCall('/api/game/warp-storm-all-moves', { direction });
    if (!res.success) {
      showMsg('Ошибка', res.error || 'Не удалось получить ходы варп-шторма');
      return;
    }
    const moves = res.moves || [];
    if (!moves.length) {
      showMsg(
        'Варп-шторм',
        `<div style="padding:8px 0;">Ни один варп-шторм не может двигаться в направлении «${direction}».</div>` +
        `<button onclick="skipWarpMove()" style="margin-top:10px;padding:6px 18px;background:#555;border:none;color:#fff;border-radius:4px;cursor:pointer;font-size:.9rem;">OK</button>`
      );
      return;
    }
    _warpMoveState = { step: 'select_storm', direction, moves };
    renderBoard();
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function _warpSelectStorm(stormIdx) {
  const { direction, moves } = _warpMoveState;
  const validDests = moves
    .filter(m => m.storm_idx === stormIdx)
    .map(m => ({ tileKey: m.tileKey, side: m.side }));
  _warpMoveState = { step: 'select_dest', storm_idx: stormIdx, direction, validDests };
  renderBoard();
}

async function skipWarpMove() {
  closeMsg();
  _warpMoveState = null;
  try {
    const res = await apiCall('/api/game/skip-warp-move', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      _showWarpMoveConfirm(false);
    } else {
      showMsg('Ошибка', res.error || 'Не удалось пропустить перемещение');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

async function doMoveWarpStorm(stormIdx, tileKey, side) {
  const direction = _warpMoveState?.direction || '';
  _warpMoveState = null;
  try {
    const res = await apiCall('/api/game/move-warp-storm', {
      player_id: G.curP,
      storm_idx:  stormIdx,
      direction,
      tile_key:  tileKey,
      side,
    });
    if (res.success) {
      applyState(res.state);
      renderBoard();
      _showWarpMoveConfirm(true);
    } else {
      showMsg('Ошибка', res.error || 'Не удалось переместить варп-шторм');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function _showWarpMoveConfirm(hasMoved) {
  const detail = hasMoved
    ? 'Варп-шторм перемещён.'
    : 'Ход завершён (нет допустимых перемещений).';
  showMsg('Подтвердите выбор',
    `<div style="padding:6px 0 14px;">${detail}<br>
     <span style="color:#888;font-size:.82rem;">Подтвердите или отмените выбор карты события.</span></div>
     <div style="display:flex;gap:10px;justify-content:center;">
       <button onclick="closeMsg();_afterWarpMoveUi();"
               style="padding:7px 22px;background:rgba(0,160,80,.85);border:none;color:#fff;border-radius:4px;cursor:pointer;">Передать ход</button>
       <button onclick="_undoWarpMove();"
               style="padding:7px 22px;background:#444;border:none;color:#fff;border-radius:4px;cursor:pointer;">Отменить</button>
     </div>`
  );
}

async function _undoWarpMove() {
  closeMsg();
  _warpMoveState = null;
  try {
    const res = await apiCall('/api/game/undo', { player_id: G.curP });
    if (res.success) {
      applyState(res.state);
      renderBoard();
      setPhase('end-round');
    } else {
      showMsg('Ошибка', res.error || 'Нечего отменять');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}

function _afterWarpMoveUi() {
  const selectionDone = G.event_selection_done || [false, false];
  if (!selectionDone.every(Boolean)) {
    showHP(G.players[G.curP].name, 'Выбор карты события', () => setPhase('end-round'));
  } else {
    setPhase('end-round');
  }
}
