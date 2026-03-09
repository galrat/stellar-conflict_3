"""
demo.py — демонстрация Python-движка Stellar Conflict
Запуск: python demo.py
"""
import sys
sys.path.insert(0, ".")

from game_state import GameState, GameConfig
from factions import UnitConfig


def separator(title: str):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print('═'*55)


def show_log(game: GameState, last_n: int = 5):
    for entry in game.log[-last_n:]:
        prefix = "  [SYS]" if entry.player_id == -1 else f"  [P{entry.player_id+1}]"
        print(f"{prefix} {entry.message}")


def show_board(game: GameState):
    bb = game.board.bounding_box()
    print(f"  Поле: {bb['width']}×{bb['height']}, тайлов: {len(game.board.tiles)}")
    for key, tile in game.board.tiles.items():
        rot_areas = tile.rotated_areas()
        area_info = " | ".join(
            f"{a.area_type.value[:3].upper()}({len(a.units)}u)" for a in rot_areas
        )
        flag = "🏠" if tile.is_home else "  "
        print(f"  {flag} [{key}] rot={tile.rotation}° owner=P{tile.owner+1}  {area_info}")


def show_pool(game: GameState, player_id: int):
    p = game.players[player_id]
    by_type: dict = {}
    for u in p.pool:
        k = u.label
        by_type[k] = by_type.get(k, 0) + 1
    print(f"  {p.name} резерв ({len(p.pool)}): " +
          ", ".join(f"{v}×{k}" for k, v in by_type.items()))


# ══════════════════════════════════════════════════════════════
#  СЦЕНАРИЙ 1: дефолтная конфигурация, базовый геймплей
# ══════════════════════════════════════════════════════════════
separator("СЦЕНАРИЙ 1 — дефолтная конфигурация")

game = GameState(GameConfig(
    p1_name="Alpha", p1_faction="federation",
    p2_name="Omega",  p2_faction="empire",
))
show_log(game, 3)
show_pool(game, 0)
show_pool(game, 1)

# P1 кладёт домашнюю систему
ok, msg = game.place_tile(player_id=0, hand_index=0, col=0, row=0)
print(f"\nP1 place_tile(home) → {ok}: {msg}")

# Поворот по часовой
ok, msg = game.rotate_tile(0, 0, clockwise=True)
print(f"P1 rotate_tile CW  → {ok}: {msg}")

# Проверить поворот
tile = game.board.get(0, 0)
print(f"  Тайл [0,0] rotation={tile.rotation}°  areas: {[a.area_type.value for a in tile.rotated_areas()]}")

# Поворот ещё раз
game.rotate_tile(0, 0, clockwise=True)
print(f"  После 2-го поворота: {[a.area_type.value for a in game.board.get(0,0).rotated_areas()]}")

# P1 размещает наземный юнит в зону планеты (с учётом поворота)
tile00 = game.board.get(0, 0)
planet_disp = next(i for i, a in enumerate(tile00.rotated_areas()) if a.area_type.value == "planet")
space_disp  = next(i for i, a in enumerate(tile00.rotated_areas()) if a.area_type.value == "space")
ok, msg = game.place_unit(player_id=0, unit_index=0, tile_key="0,0", area_display_index=planet_disp)
print(f"P1 place_unit(ground→planet) → {ok}: {msg}")

# P1 пробует наземный юнит в зону космоса — должна быть ошибка
ok, msg = game.place_unit(player_id=0, unit_index=0, tile_key="0,0", area_display_index=space_disp)
print(f"P1 place_unit(ground→space)  → {ok}: {msg}  (ожидается ошибка)")

# P1 размещает космический юнит в космос
space_unit_idx = next(i for i, u in enumerate(game.players[0].pool) if u.category.value == "space")
ok, msg = game.place_unit(player_id=0, unit_index=space_unit_idx, tile_key="0,0", area_display_index=space_disp)
print(f"P1 place_unit(space→space)  → {ok}: {msg}")

show_board(game)

# ── Отмена последнего юнита
ok, msg = game.undo_last_unit(player_id=0)
print(f"\nP1 undo_last_unit → {ok}: {msg}")
show_board(game)

# ── Отмена всего тайла
ok, msg = game.undo_tile(player_id=0)
print(f"P1 undo_tile      → {ok}: {msg}")
print(f"  Тайлов на поле: {len(game.board.tiles)}  (ожидается 0)")
show_pool(game, 0)

# ══════════════════════════════════════════════════════════════
#  СЦЕНАРИЙ 2: кастомная конфигурация юнитов
# ══════════════════════════════════════════════════════════════
separator("СЦЕНАРИЙ 2 — кастомная конфигурация юнитов")

custom_config = GameConfig(
    p1_name="Rex", p1_faction="collective",
    p2_name="Zar", p2_faction="syndicate",
    total_rounds=3,
    tiles_per_player=3,
    p1_unit_config=UnitConfig(infantry=4, marines=0, mechanized=0, elite=2,
                               fighters=0, destroyers=3),
    p2_unit_config=UnitConfig(infantry=1, marines=3, mechanized=1, elite=0,
                               fighters=4, destroyers=0),
)

game2 = GameState(custom_config)
show_pool(game2, 0)
show_pool(game2, 1)

# Быстро расставим все 6 тайлов (3×2 вертикальная форма)
#   X
#   X
#   X   <- P2 продолжает...
positions_p0 = [(0,0),(1,0),(0,1)]
positions_p1 = [(1,1),(0,2),(1,2)]

all_positions = []
for i in range(3):
    all_positions.append((0, i, positions_p0[i]))
    all_positions.append((1, i, positions_p1[i]))

pi_cur = 0
for player_id, hand_idx, (c, r) in all_positions:
    ok, msg = game2.place_tile(player_id=pi_cur, hand_index=hand_idx, col=c, row=r)
    print(f"  P{pi_cur+1} place_tile({c},{r}) → {ok}")
    if ok:
        # Разместить по 1 юниту
        p = game2.players[pi_cur]
        if p.pool:
            game2.place_unit(pi_cur, 0, f"{c},{r}", 0)
        game2.end_troop_on_tile(pi_cur)
    pi_cur = game2.current_player_id

separator("Итоговое поле")
show_board(game2)
print(f"\n  Счёт: {game2.score()}")

# ══════════════════════════════════════════════════════════════
#  СЦЕНАРИЙ 3: проверка ограничения 3×2
# ══════════════════════════════════════════════════════════════
separator("СЦЕНАРИЙ 3 — проверка ограничений формы поля")

game3 = GameState(GameConfig())
game3.place_tile(0, 0, 0, 0)
game3.end_troop_on_tile(0)
game3.place_tile(1, 0, 1, 0)
game3.end_troop_on_tile(1)
game3.place_tile(0, 1, 2, 0)
game3.end_troop_on_tile(0)

# Допустимые позиции сейчас
valid = game3.board.valid_positions()
print(f"  Допустимые позиции: {valid}")

# Попробуем недопустимую (вышло бы за 3×2 И за 2×3)
bad_ok, bad_msg = game3.place_tile(1, 1, 3, 0)
print(f"  place_tile(3,0) → {bad_ok}: {bad_msg}  (ожидается ошибка)")

# Вертикальная форма 2×3 — допустима
ok4, _ = game3.place_tile(1, 1, 0, 1)
print(f"  place_tile(0,1) → вертикаль → {ok4}  (ожидается True)")

print("\n  Финальное поле:")
show_board(game3)

separator("Демонстрация завершена")
print()
