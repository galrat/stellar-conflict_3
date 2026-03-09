"""
combat.py — боевая система
"""
import random
from dataclasses import dataclass, field
from typing import List, Tuple
from units import Unit


@dataclass
class BattleResult:
    """Результат одного сражения в зоне."""
    tile_key:    str
    area_index:  int
    area_type:   str

    # Участники
    p1_units:    List[Unit]
    p2_units:    List[Unit]

    # Броски кубика
    dice_p1:     int = 0
    dice_p2:     int = 0

    # Итоговые очки (кубик + количество юнитов + бонусы)
    score_p1:    int = 0
    score_p2:    int = 0

    winner:      int = -1   # player_id победителя, -1 = ничья → победа защитника
    loser:       int = -1
    loser_units: List[Unit] = field(default_factory=list)


def resolve_battle(tile_key: str, area_index: int, area_type: str,
                   p1_units: List[Unit], p2_units: List[Unit]) -> BattleResult:
    """
    Разыгрывает бой в одной зоне.

    Правила:
      • Бросается один d6 за каждую сторону.
      • К броску прибавляется количество юнитов стороны.
      • К броску прибавляется максимальный attack_bonus среди юнитов стороны.
      • Проигравший теряет ВСЕ юниты в зоне.
      • При равном счёте побеждает защитник (p1, кто стоял раньше).
    """
    result = BattleResult(
        tile_key=tile_key, area_index=area_index, area_type=area_type,
        p1_units=list(p1_units), p2_units=list(p2_units),
    )

    bonus_p1 = max((u.attack_bonus for u in p1_units), default=0)
    bonus_p2 = max((u.attack_bonus for u in p2_units), default=0)

    result.dice_p1 = random.randint(1, 6)
    result.dice_p2 = random.randint(1, 6)

    result.score_p1 = result.dice_p1 + len(p1_units) + bonus_p1
    result.score_p2 = result.dice_p2 + len(p2_units) + bonus_p2

    p1_id = p1_units[0].player_id if p1_units else 0
    p2_id = p2_units[0].player_id if p2_units else 1

    if result.score_p1 >= result.score_p2:
        result.winner = p1_id
        result.loser  = p2_id
        result.loser_units = list(p2_units)
    else:
        result.winner = p2_id
        result.loser  = p1_id
        result.loser_units = list(p1_units)

    return result


def apply_battle(area, battle: BattleResult):
    """
    Применяет результат боя к объекту Area — удаляет юниты проигравшего.
    """
    loser_ids = {u.id for u in battle.loser_units}
    area.units = [u for u in area.units if u.id not in loser_ids]


def format_battle(battle: BattleResult,
                  p1_name: str = "P1", p2_name: str = "P2") -> str:
    """Текстовое описание результата боя для лога."""
    b1 = max((u.attack_bonus for u in battle.p1_units), default=0)
    b2 = max((u.attack_bonus for u in battle.p2_units), default=0)
    lines = [
        f"⚔ БИТВА [{battle.tile_key}] зона {battle.area_index+1} ({battle.area_type})",
        f"  {p1_name}: {len(battle.p1_units)} юн. + 🎲{battle.dice_p1} + бонус{b1} = {battle.score_p1}",
        f"  {p2_name}: {len(battle.p2_units)} юн. + 🎲{battle.dice_p2} + бонус{b2} = {battle.score_p2}",
        f"  → Победил: {p1_name if battle.winner == (battle.p1_units[0].player_id if battle.p1_units else 0) else p2_name}",
    ]
    return "\n".join(lines)
