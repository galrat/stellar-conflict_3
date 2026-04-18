'use strict';
// ══════════════════════════════════════════════
//  HEADER
// ══════════════════════════════════════════════
function updateHeader() {
  const cp=G.players[G.curP];
  // Если идёт deploy — вычитаем зарезервированные ресурсы за юнитов из отображения
  const pd = G.pending_deploy;
  const unitCosts = (pd && pd.unit_costs) ? pd.unit_costs : null;
  const deployPlayer = pd ? pd.player_id : null;

  [0,1].forEach(pi=>{
    const p=G.players[pi], pfx=pi===0?'p1':'p2';
    document.getElementById(`h-${pfx}-name`).textContent=p.name;
    document.getElementById(`h-${pfx}-init`).textContent=p.name.substring(0,2).toUpperCase();
    const fac=FACTIONS.find(f=>f.id===p.faction);
    document.getElementById(`h-${pfx}-fac`).textContent=fac?`${fac.icon} ${fac.name}`:'—';
    const resEl = document.getElementById(`h-${pfx}-res`);
    if (resEl) {
      // Для игрока, выполняющего deploy, показываем скорректированные ресурсы
      const uc = (unitCosts && pi === deployPlayer) ? unitCosts : null;
      const credits  = (p.credits  ?? 0) - (uc?.credits ?? 0);
      const support  = (p.tokens?.support  ?? 0);
      const discount = (p.tokens?.discount ?? 0) - (uc?.cash    ?? 0);
      const forge    = (p.tokens?.forge    ?? 0) - (uc?.forge   ?? 0);
      const parts = [];
      if (p.credits != null) parts.push(`💰${credits}`);
      if (support)  parts.push(`⊕${support}`);
      if (discount) parts.push(`⊖${discount}`);
      if (forge)    parts.push(`⚒${forge}`);
      resEl.textContent = parts.join('  ') || '';
    }
  });
  const hRound = document.getElementById('h-round');
  if (hRound) hRound.textContent = G.round ? `Раунд ${G.round}` : 'Раунд —';

  const hObj0 = document.getElementById('h-obj-p1');
  const hObj1 = document.getElementById('h-obj-p2');
  if (hObj0) hObj0.textContent = `🎯 ${G.players[0]?.collected_objectives ?? 0}`;
  if (hObj1) hObj1.textContent = `🎯 ${G.players[1]?.collected_objectives ?? 0}`;

  const edsp = document.getElementById('event-stack-disp');
  if (edsp) edsp.style.display='none';
}
