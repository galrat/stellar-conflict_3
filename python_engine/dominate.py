"""
python_engine/dominate.py — логика приказа Dominate

Механика:
  1. Найти все дружественные планеты в системе (тайл с приказом)
  2. Собрать ценные ресурсы: support, discount, forge, joker
  3. Если есть joker — выбор игрока (через pending_joker_choice)
  4. Применить к токенам игрока (cap: не более 3 каждого, Tyranids — 4)
  5. Факционное особое свойство: Chaos — переместить культиста в соседнюю систему

Токены (единый стандарт):
  area.support  → player.tokens.support  (жетон поддержки)
  area.discount → player.tokens.discount (жетон скидки)
  area.forge    → player.tokens.forge    (жетон молотка)
  area.joker    → игрок выбирает один из трёх типов
"""
import copy

from faction_defs.chaos_data.dominate import (
    maybe_start_chaos_dominate,
    chaos_dominate_move,
    chaos_retreat_unit,
)

TOKEN_CAP_DEFAULT  = 3
TOKEN_CAP_TYRANIDS = 4  # Tyranids: "up to 4 of each"
TOKEN_TYPES        = ('support', 'discount', 'forge')


def _is_friendly_planet(area, player_id):
    """Планета с хотя бы одним юнитом или постройкой игрока."""
    if area.get('type') != 'planet':
        return False
    has_unit      = any(t.get('player') == player_id for t in area.get('troops', []))
    has_structure = any(s.get('player') == player_id for s in area.get('structures', []))
    return has_unit or has_structure


def _get_token_cap(state, player_id):
    faction = state['players'][player_id].get('faction', '')
    return TOKEN_CAP_TYRANIDS if faction == 'tyranids' else TOKEN_CAP_DEFAULT


def dominate_order(state, player_id, tile_key):
    """
    Выполнить приказ Dominate.

    Returns: (success, message, new_state)
    If joker found: new_state has pending_joker_choice, caller should stop
    and wait for /api/game/dominate-joker endpoint.
    """
    new_state = copy.deepcopy(state)
    tile = new_state.get('map', {}).get(tile_key)
    if not tile:
        return False, f"Тайл {tile_key} не найден", None

    # 1. Собрать ресурсы с дружественных планет
    collected = {t: 0 for t in TOKEN_TYPES}
    joker_count = 0

    for area in tile.get('areas', []):
        if not _is_friendly_planet(area, player_id):
            continue
        for tok in TOKEN_TYPES:
            collected[tok] += area.get(tok, 0)
        joker_count += area.get('joker', 0)

    # 2. Если есть joker — сохранить pending и вернуть для выбора игрока
    if joker_count > 0:
        new_state['pending_joker_choice'] = {
            'player_id':  player_id,
            'tile_key':   tile_key,
            'collected':  collected,
            'joker_count': joker_count,
        }
        msg = f"Dominate: выберите тип токена для {joker_count} джокера(-ов)"
        return True, msg, new_state

    # 3. Применить собранные ресурсы
    _apply_tokens(new_state, player_id, collected)

    # 4. Faction special: Chaos
    maybe_start_chaos_dominate(new_state, player_id, tile_key)

    msg = _build_log(player_id, collected, joker_resolved=None)
    new_state.setdefault('log', []).append({'message': msg, 'player_id': player_id})
    return True, msg, new_state


def dominate_resolve_joker(state, player_id, joker_choices):
    """
    Завершить Dominate после выбора типа для joker.
    joker_choices: list of token types, len == joker_count
    e.g. ['support', 'forge']
    """
    new_state = copy.deepcopy(state)
    pending   = new_state.pop('pending_joker_choice', None)
    if not pending or pending.get('player_id') != player_id:
        return False, "Нет ожидающего выбора джокера", None

    collected    = dict(pending['collected'])
    joker_count  = pending['joker_count']

    if len(joker_choices) != joker_count:
        return False, f"Нужно выбрать {joker_count} тип(ов) для джокера", None
    for ch in joker_choices:
        if ch not in TOKEN_TYPES:
            return False, f"Неверный тип токена: {ch}", None
        collected[ch] += 1

    _apply_tokens(new_state, player_id, collected)

    # Faction special: Chaos (after joker resolved)
    maybe_start_chaos_dominate(new_state, player_id, pending['tile_key'])

    msg = _build_log(player_id, collected, joker_resolved=joker_choices)
    new_state.setdefault('log', []).append({'message': msg, 'player_id': player_id})
    return True, msg, new_state


def _apply_tokens(state, player_id, collected):
    """Добавить собранные токены к игроку с учётом капа."""
    player  = state['players'][player_id]
    tokens  = player.setdefault('tokens', {t: 0 for t in TOKEN_TYPES})
    cap     = _get_token_cap(state, player_id)

    for tok in TOKEN_TYPES:
        current = tokens.get(tok, 0)
        tokens[tok] = min(cap, current + collected.get(tok, 0))


def _build_log(player_id, collected, joker_resolved):
    parts = [f"{v} {k}" for k, v in collected.items() if v > 0]
    if joker_resolved:
        parts.append(f"joker→{','.join(joker_resolved)}")
    gained = ', '.join(parts) if parts else 'ничего'
    return f"Игрок {player_id}: Dominate — получено: {gained}"
