"""
tiles.py — тайлы систем и области (зоны) внутри тайла
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import uuid

from units import Unit, UnitCategory, Structure


class AreaType(Enum):
    """Тип области внутри тайла системы."""
    PLANET = "planet"   # планета — наземные юниты
    SPACE  = "space"    # космос  — космические юниты


class TileType(Enum):
    """Тип тайла системы."""
    HOME   = "home"    # домашняя: 3 планеты + 1 космос
    NORMAL = "normal"  # обычная:  2 планеты + 2 космоса


# Порядок областей в сетке 2×2 (индексы 0-3, чтение слева-направо, сверху-вниз):
#  0 | 1
#  -----
#  2 | 3
AREA_LAYOUTS: dict[TileType, List[AreaType]] = {
    TileType.HOME:   [AreaType.PLANET, AreaType.PLANET, AreaType.PLANET, AreaType.SPACE],
    TileType.NORMAL: [AreaType.PLANET, AreaType.PLANET, AreaType.SPACE,  AreaType.SPACE],
}


# ── Каталог тайлов ──────────────────────────────────────────────────────────

@dataclass
class TileSideDef:
    """Описание одной стороны тайла из каталога.

    Все матрицы 2×2 развёрнуты в плоский список длиной 4 в порядке
    row-major: [0][0]=TL, [0][1]=TR, [1][0]=BL, [1][1]=BR → индексы 0..3.
    """
    side:     str        # 'a' или 'b'
    layout:   List[int]  # 1 = планета, 0 = космос
    capacity: List[int]  # вместимость области (для планет = кол-во черепов)
    valuable: List[int]  = field(default_factory=lambda: [0, 0, 0, 0])  # ценные ресурсы — красный кружок
    joker:    List[int]  = field(default_factory=lambda: [0, 0, 0, 0])  # жетон джокера


@dataclass
class TileDef:
    """Запись в каталоге системных тайлов."""
    id:      str
    is_home: bool
    sides:   List[TileSideDef]

    def make_areas(self, side_idx: int = 0) -> List["Area"]:
        """Создать список из 4 объектов Area по определению стороны."""
        s = self.sides[side_idx]
        areas = []
        for i in range(4):
            atype = AreaType.PLANET if s.layout[i] == 1 else AreaType.SPACE
            areas.append(Area(index=i, area_type=atype, skulls=s.capacity[i]))
        return areas


def _td(tid: str, is_home: bool, *sides_data) -> TileDef:
    """Вспомогательная фабрика: принимает пары (layout_flat, capacity_flat)."""
    sides = []
    labels = ("a", "b")
    for k, (layout, capacity) in enumerate(sides_data):
        sides.append(TileSideDef(side=labels[k], layout=list(layout), capacity=list(capacity)))
    return TileDef(id=tid, is_home=is_home, sides=sides)


# Ключ — tile_def_id, совпадает с faction.home_tile_id для домашних тайлов.
# layout/capacity хранятся как плоские 4-элементные списки: TL, TR, BL, BR.
TILE_CATALOG: Dict[str, TileDef] = {t.id: t for t in [
    # ── Домашние тайлы фракций (HOME: 3 планеты + 1 космос) ───────────────
    _td("home_chaos",     True,
        ([1,1,1,0], [2,1,2,3]),
        ([1,1,1,0], [1,2,2,3])),
    _td("home_empire",    True,
        ([1,1,1,0], [3,2,1,3]),
        ([1,1,0,1], [2,3,3,1])),
    _td("home_orks",      True,
        ([1,1,1,0], [3,3,2,3]),
        ([1,1,1,0], [2,3,3,3])),
    _td("home_syndicate", True,
        ([1,0,1,1], [1,3,1,2]),
        ([1,1,0,1], [2,1,3,1])),
    _td("home_nomads",    True,
        ([1,0,1,1], [1,3,2,1]),
        ([1,1,1,0], [1,2,1,3])),
    _td("home_theocracy", True,
        ([1,1,1,0], [2,1,1,3]),
        ([1,1,0,1], [1,2,3,1])),
    _td("home_machines",  True,
        ([1,1,1,0], [2,2,2,3]),
        ([1,1,1,0], [3,2,1,3])),
    _td("home_pirates",   True,
        ([1,1,0,1], [1,2,3,1]),
        ([1,0,1,1], [2,3,1,1])),
    _td("home_elders",    True,
        ([1,1,1,0], [1,1,1,3]),
        ([1,0,1,1], [1,3,1,1])),
    _td("home_traders",   True,
        ([1,1,1,0], [1,2,1,3]),
        ([1,1,0,1], [2,1,3,1])),
    _td("home_mutants",   True,
        ([1,1,1,0], [3,1,2,3]),
        ([1,0,1,1], [2,3,3,1])),
    _td("home_crusaders", True,
        ([1,1,1,0], [3,2,3,3]),
        ([1,1,1,0], [2,3,2,3])),
    _td("home_marine",    True,
        ([1,1,1,0], [3,2,2,3]),
        ([1,1,1,0], [2,3,3,3])),
    _td("home_eldar",     True,
        ([1,0,1,1], [2,3,1,2]),
        ([1,1,0,1], [1,2,3,1])),
    # ── Обычные тайлы (NORMAL: 2 планеты + 2 космоса) ─────────────────────
    _td("normal_01", False,
        ([1,1,0,0], [2,1,3,3]),
        ([1,0,1,0], [1,3,2,3])),
    _td("normal_02", False,
        ([1,0,1,0], [1,3,1,3]),
        ([0,1,0,1], [3,2,3,1])),
    _td("normal_03", False,
        ([1,0,0,0], [3,3,3,3]),
        ([1,1,0,0], [2,1,3,3])),
    _td("normal_04", False,
        ([1,0,0,1], [2,3,3,1]),
        ([1,0,1,0], [3,3,1,3])),
    _td("normal_05", False,
        ([1,1,0,0], [1,1,3,3]),
        ([1,0,1,0], [2,3,1,3])),
    _td("normal_06", False,
        ([1,1,0,0], [2,2,3,3]),
        ([1,1,0,0], [1,3,3,3])),
    _td("normal_07", False,
        ([0,1,0,1], [3,1,3,2]),
        ([1,1,0,0], [1,1,3,3])),
    _td("normal_08", False,
        ([1,0,0,1], [1,3,3,2]),
        ([1,1,0,0], [2,2,3,3])),
]}


@dataclass
class Area:
    """Одна зона (квадрат) внутри тайла."""
    index:      int             = 0
    area_type:  AreaType        = AreaType.PLANET
    # skulls — количество черепов на планете; определяет вместимость.
    # Для SPACE не используется — вместимость всегда 3.
    skulls:     int             = 1
    units:      List[Unit]      = field(default_factory=list)
    structures: List[Structure] = field(default_factory=list)

    @property
    def capacity(self) -> int:
        """Максимум боевых юнитов в зоне."""
        return max(1, self.skulls) if self.area_type == AreaType.PLANET else 3

    @property
    def is_full(self) -> bool:
        return len(self.units) >= self.capacity

    def accepts(self, unit: Unit) -> bool:
        """Проверяет совместимость юнита с зоной по типу."""
        if unit.category == UnitCategory.GROUND:
            return self.area_type == AreaType.PLANET
        if unit.category == UnitCategory.SPACE:
            return self.area_type == AreaType.SPACE
        return False

    def can_place_unit(self, unit: Unit) -> tuple[bool, str]:
        """Проверяет и тип, и вместимость. Возвращает (ok, сообщение)."""
        if not self.accepts(unit):
            return False, "Тип юнита не подходит для этой зоны"
        if self.is_full:
            return False, f"Зона заполнена (макс. {self.capacity})"
        return True, ""

    def units_of_player(self, player_id: int) -> List[Unit]:
        return [u for u in self.units if u.player_id == player_id]

    def to_dict(self) -> dict:
        return {
            "index":      self.index,
            "area_type":  self.area_type.value,
            "skulls":     self.skulls,
            "capacity":   self.capacity,
            "units":      [u.to_dict() for u in self.units],
            "structures": [s.to_dict() for s in self.structures],
        }


@dataclass
class SystemTile:
    """
    Тайл системы — содержит 4 зоны в сетке 2×2.

    Поворот (rotation): 0, 90, 180, 270 градусов по часовой стрелке.
    При повороте сами объекты Area не меняются — меняется их визуальное
    расположение. Метод rotated_areas() возвращает список областей
    в «повёрнутом» порядке для отрисовки.

    Карта поворота индексов (2×2 сетка):
        0 1      0°   →   0 1      90°  →   2 0     180° →   3 2     270° →   1 3
        2 3               2 3               3 1               1 0               0 2
    """
    id:          str       = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tile_type:   TileType  = TileType.NORMAL
    tile_def_id: str       = ""        # ID из TILE_CATALOG; если задан — области берутся из каталога
    owner:       int       = 0         # player_id владельца
    col:         int       = 0         # колонка на поле (может быть < 0)
    row:         int       = 0         # строка на поле
    rotation:    int       = 0         # 0 | 90 | 180 | 270
    areas:       List[Area] = field(default_factory=list)

    # Таблица переупорядочивания индексов при повороте
    # _ROTATION_MAP[r//90] = [new_pos_for_original_0, ...1, ...2, ...3]
    _ROTATION_MAP = [
        [0, 1, 2, 3],   # 0°   (без изменений)
        [2, 0, 3, 1],   # 90°  по часовой
        [3, 2, 1, 0],   # 180°
        [1, 3, 0, 2],   # 270° (= 90° против часовой)
    ]

    def __post_init__(self):
        if not self.areas:
            if self.tile_def_id and self.tile_def_id in TILE_CATALOG:
                self.areas = TILE_CATALOG[self.tile_def_id].make_areas(side_idx=0)
            else:
                layout = AREA_LAYOUTS[self.tile_type]
                self.areas = [Area(index=i, area_type=t) for i, t in enumerate(layout)]

    @property
    def key(self) -> str:
        return f"{self.col},{self.row}"

    @property
    def is_home(self) -> bool:
        return self.tile_type == TileType.HOME

    def rotate_cw(self):
        """Повернуть на 90° по часовой стрелке."""
        self.rotation = (self.rotation + 90) % 360

    def rotate_ccw(self):
        """Повернуть на 90° против часовой стрелки."""
        self.rotation = (self.rotation - 90) % 360

    def rotated_areas(self) -> List[Area]:
        """
        Возвращает список из 4 областей в порядке отображения
        с учётом текущего поворота.
        Индекс в возвращаемом списке — позиция в отрисовке (0=TL, 1=TR, 2=BL, 3=BR).
        """
        rmap = self._ROTATION_MAP[self.rotation // 90]
        result = [None] * 4
        for original_idx, display_pos in enumerate(rmap):
            result[display_pos] = self.areas[original_idx]
        return result

    def area_at_display(self, display_pos: int) -> Area:
        """Зона по визуальной позиции (с учётом поворота)."""
        return self.rotated_areas()[display_pos]

    def all_units(self) -> List[Unit]:
        return [u for area in self.areas for u in area.units]

    def units_of_player(self, player_id: int) -> List[Unit]:
        return [u for u in self.all_units() if u.player_id == player_id]

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "tile_type":   self.tile_type.value,
            "tile_def_id": self.tile_def_id,
            "owner":       self.owner,
            "col":         self.col,
            "row":         self.row,
            "rotation":    self.rotation,
            "key":         self.key,
            "is_home":     self.is_home,
            "areas":       [a.to_dict() for a in self.areas],
            "rotated_areas": [a.to_dict() for a in self.rotated_areas()],
        }
