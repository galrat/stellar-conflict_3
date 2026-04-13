'use strict';
// ══════════════════════════════════════════════
//  EVENT CARD PICKER
// ══════════════════════════════════════════════

function showEventCardPicker() {
  if (G.phase !== 'end-round') return;
  const selectionDone = G.event_selection_done || [false, false];
  if (selectionDone[G.curP]) return;

  const offered    = (G.event_cards_offered || [[], []])[G.curP] || [];
  const playerName = G.players[G.curP].name;

  if (!offered.length) {
    return;
  }

  let cardsHtml = offered.map(card => `
    <div class="event-card-choice" onclick="selectEventCard('${card.name.replace(/'/g, "\\'")}')"
         style="padding:10px;background:rgba(0,200,255,.1);margin-bottom:8px;border-radius:6px;cursor:pointer;border:1px solid rgba(0,200,255,.2);">
      <div style="font-weight:bold;margin-bottom:4px;">${card.name}</div>
      <div style="font-size:.75rem;color:#aaa;margin-bottom:4px;">${card.card_type || ''}</div>
      <div style="font-size:.8rem;">${card.effect || ''}</div>
    </div>
  `).join('');

  const html = `
    <div style="margin-bottom:10px;color:#aaa;">Выберите одну карту для руки:</div>
    <div style="max-height:400px;overflow-y:auto;">${cardsHtml}</div>
  `;
  showMsg(`🃏 Карты событий — ${playerName}`, html);
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
      addLog(`${G.players[prevPlayer].name} взял карту событий`, prevPlayer);

      const selectionDone = G.event_selection_done || [false, false];
      if (!selectionDone.every(Boolean)) {
        // Второй игрок ещё не выбирал — hotpass, setPhase внутри колбека покажет пикер
        showHP(G.players[G.curP].name, 'Выбор карты события', () => setPhase('end-round'));
      } else {
        setPhase('end-round');  // Оба выбрали — покажет кнопку "Следующий раунд"
      }
    } else {
      showMsg('Ошибка', res.error || 'Не удалось выбрать карту');
    }
  } catch(e) {
    showMsg('Ошибка сервера', e.message);
  }
}
