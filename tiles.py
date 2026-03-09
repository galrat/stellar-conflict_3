"""
tiles.py — тайлы систем и области (зоны) внутри тайла
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
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
    id:        str       = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tile_type: TileType  = TileType.NORMAL
    owner:     int       = 0          # player_id владельца
    col:       int       = 0          # колонка на поле (может быть < 0)
    row:       int       = 0          # строка на поле
    rotation:  int       = 0          # 0 | 90 | 180 | 270
    areas:     List[Area] = field(default_factory=list)

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
            "id":        self.id,
            "tile_type": self.tile_type.value,
            "owner":     self.owner,
            "col":       self.col,
            "row":       self.row,
            "rotation":  self.rotation,
            "key":       self.key,
            "is_home":   self.is_home,
            "areas":     [a.to_dict() for a in self.areas],
            "rotated_areas": [a.to_dict() for a in self.rotated_areas()],
        }
