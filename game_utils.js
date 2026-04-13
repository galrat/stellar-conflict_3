'use strict';
// ══════════════════════════════════════════════
//  UTILITIES  (pure helpers, no DOM/state)
// ══════════════════════════════════════════════

// Название юнита берётся из fac.unitNames['{ground|space}_{tier}'].
// Fallback: 'T{tier}' если фракция не определена или названия нет.
function getUnitName(factionId, unitType, tier) {
  const fac = FACTIONS.find(f => f.id === factionId);
  return (fac && fac.unitNames && fac.unitNames[`${unitType}_${tier}`]) || `T${tier}`;
}

// ── Color helpers ────────────────────────────────────────────────
// Возвращает '#ffffff' или '#000000' в зависимости от яркости фона
function getTextColor(hex) {
  const r = parseInt(hex.slice(1,3),16)/255;
  const g = parseInt(hex.slice(3,5),16)/255;
  const b = parseInt(hex.slice(5,7),16)/255;
  const lum = 0.2126*r + 0.7152*g + 0.0722*b;
  return lum > 0.35 ? '#000000' : '#ffffff';
}

// hex + alpha → rgba(...)
function hexAlpha(hex, a) {
  const r=parseInt(hex.slice(1,3),16), g=parseInt(hex.slice(3,5),16), b=parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${a})`;
}

// ── Rotation helpers ─────────────────────────────────────────────
function getRotatedAreas(tile) {
  const rot = (tile.rotation || 0);
  const rmap = RMAP[rot / 90];
  const out = new Array(4);
  for (let i = 0; i < 4; i++) out[rmap[i]] = tile.areas[i];
  return out;
}

function getAreaByDisplay(tile, displayIdx) {
  return getRotatedAreas(tile)[displayIdx];
}

function getRealIdx(tile, displayIdx) {
  const area = getAreaByDisplay(tile, displayIdx);
  return tile.areas.indexOf(area);
}
