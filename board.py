"""
board.py — игровое поле: размещение тайлов, соседство, валидация
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from tiles import SystemTile, TileType, Area, AreaType


@dataclass
class Board:
    """
    Игровое поле — словарь тайлов по ключу "col,row".
    Ограничение формы: занятые клетки должны вписываться в прямоугольник
    3×2 или 2×3 (любая ориентация).
    """
    tiles: Dict[str, SystemTile] = field(default_factory=dict)

    # ── Размещение ─────────────────────────────────────────────────────────

    def key(self, col: int, row: int) -> str:
        return f"{col},{row}"

    def get(self, col: int, row: int) -> Optional[SystemTile]:
        return self.tiles.get(self.key(col, row))

    def place(self, tile: SystemTile) -> bool:
        """
        Размещает тайл на поле.
        Возвращает True при успехе, False если позиция недопустима.
        """
        if not self.is_valid_position(tile.col, tile.row):
            return False
        self.tiles[tile.key] = tile
        return True

    def remove(self, col: int, row: int) -> Optional[SystemTile]:
        """Убирает тайл с поля и возвращает его (для отмены)."""
        k = self.key(col, row)
        return self.tiles.pop(k, None)

    # ── Валидация позиции ──────────────────────────────────────────────────

    def is_valid_position(self, col: int, row: int) -> bool:
        """
        Проверяет: можно ли поставить тайл в (col, row)?
        Условия:
          1. Клетка свободна.
          2. Если поле не пустое — тайл должен примыкать к уже стоящему боком.
          3. Итоговый прямоугольник не выходит за 3×2 или 2×3.
        """
        k = self.key(col, row)
        if k in self.tiles:
            return False
        if not self.tiles:
            return True            # первый тайл — куда угодно
        if not self._is_adjacent(col, row):
            return False
        return self._fits_shape(col, row)

    def _is_adjacent(self, col: int, row: int) -> bool:
        for dc, dr in [(0,1),(0,-1),(1,0),(-1,0)]:
            if self.key(col+dc, row+dr) in self.tiles:
                return True
        return False

    def _fits_shape(self, col: int, row: int) -> bool:
        """Проверяет, что bounding box с новым тайлом ≤ 3×2 или ≤ 2×3."""
        all_cols = [t.col for t in self.tiles.values()] + [col]
        all_rows = [t.row for t in self.tiles.values()] + [row]
        w = max(all_cols) - min(all_cols) + 1
        h = max(all_rows) - min(all_rows) + 1
        return (w <= 3 and h <= 2) or (w <= 2 and h <= 3)

    def valid_positions(self) -> List[Tuple[int, int]]:
        """Возвращает все допустимые клетки для следующего тайла."""
        if not self.tiles:
            return [(0, 0)]
        candidates = set()
        for t in self.tiles.values():
            for dc, dr in [(0,1),(0,-1),(1,0),(-1,0)]:
                nc, nr = t.col+dc, t.row+dr
                k = self.key(nc, nr)
                if k not in self.tiles:
                    candidates.add((nc, nr))
        return [(c, r) for c, r in candidates if self._fits_shape(c, r)]

    # ── Соседство ──────────────────────────────────────────────────────────

    def neighbors(self, col: int, row: int) -> List[SystemTile]:
        """Возвращает список соседних тайлов (по стороне)."""
        result = []
        for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            t = self.get(col+dc, row+dr)
            if t:
                result.append(t)
        return result

    def neighbor_keys(self, key: str) -> List[str]:
        col, row = map(int, key.split(","))
        return [t.key for t in self.neighbors(col, row)]

    # ── Поворот ─────────────────────────────────────────────────────────────

    def rotate_tile_cw(self, col: int, row: int) -> bool:
        """Повернуть тайл по часовой стрелке. True если успешно."""
        t = self.get(col, row)
        if t is None:
            return False
        t.rotate_cw()
        return True

    def rotate_tile_ccw(self, col: int, row: int) -> bool:
        """Повернуть тайл против часовой стрелки. True если успешно."""
        t = self.get(col, row)
        if t is None:
            return False
        t.rotate_ccw()
        return True

    # ── Статистика ──────────────────────────────────────────────────────────

    def count_units(self, player_id: int) -> int:
        return sum(
            len(area.units_of_player(player_id))
            for t in self.tiles.values()
            for area in t.areas
        )

    def bounding_box(self) -> dict:
        if not self.tiles:
            return {"min_col":0,"max_col":0,"min_row":0,"max_row":0,"width":1,"height":1}
        cols = [t.col for t in self.tiles.values()]
        rows = [t.row for t in self.tiles.values()]
        w = max(cols)-min(cols)+1
        h = max(rows)-min(rows)+1
        return {"min_col":min(cols),"max_col":max(cols),
                "min_row":min(rows),"max_row":max(rows),
                "width":w,"height":h}

    def to_dict(self) -> dict:
        return {
            "tiles": {k: t.to_dict() for k, t in self.tiles.items()},
            "tile_count": len(self.tiles),
            "bounding_box": self.bounding_box(),
            "valid_positions": self.valid_positions(),
        }
