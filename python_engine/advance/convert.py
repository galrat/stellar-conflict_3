"""
Конвертация state['map'] в плоский список областей и обратно.

Формат области: [[col, row], [area_row, area_col], unique_number, area_type, area_owner, capacity, rotation]
  [col, row]            — координаты тайла
  [area_row, area_col]  — визуальная позиция области в сетке 2×2 (с учётом поворота тайла)
  unique_number         — сквозной номер области по всем тайлам
  area_type             — "planet" или "space"
  area_owner            — 1, 2 или None (нейтральная / спорная)
  capacity              — вместимость области
  rotation              — поворот тайла (0, 90, 180, 270) — нужен для обратного преобразования
"""

# Визуальные позиции [row, col] для канонических индексов 0..3 при данном повороте тайла.
# Канонический порядок: 0=TL(0,0), 1=TR(0,1), 2=BL(1,0), 3=BR(1,1)
#
# Rotation 90° CW:  TL→TR, TR→BR, BL→TL, BR→BL
# Rotation 180°:    TL→BR, TR→BL, BL→TR, BR→TL
# Rotation 270° CW: TL→BL, TR→TL, BL→BR, BR→TR
_ROTATE = {
    0:   [(0,0),(0,1),(1,0),(1,1)],
    90:  [(0,1),(1,1),(0,0),(1,0)],
    180: [(1,1),(1,0),(0,1),(0,0)],
    270: [(1,0),(0,0),(1,1),(0,1)],
}

# Обратное отображение: visual (row,col) → канонический индекс
_UNROTATE = {
    rot: {v: i for i, v in enumerate(positions)}
    for rot, positions in _ROTATE.items()
}


def state_to_areas(state: dict) -> list:
    """Преобразует state['map'] в плоский список областей."""
    result = []
    unique_num = 0
    for tile_key in sorted(state.get('map', {}).keys()):
        tile = state['map'][tile_key]
        col, row = map(int, tile_key.split(','))
        rotation = tile.get('rotation', 0)
        rotate = _ROTATE.get(rotation, _ROTATE[0])
        for area_idx, area in enumerate(tile.get('areas', [])):
            area_row, area_col = rotate[area_idx]
            area_type = area.get('type', 'space')
            capacity = area.get('capacity', 3)
            troops = area.get('troops', [])
            has_p0 = any(t.get('player') == 0 for t in troops)
            has_p1 = any(t.get('player') == 1 for t in troops)
            if has_p0 and not has_p1:
                owner = 1
            elif has_p1 and not has_p0:
                owner = 2
            else:
                owner = None
            result.append([[col, row], [area_row, area_col], unique_num, area_type, owner, capacity, rotation])
            unique_num += 1
    return result


def areas_to_map(areas: list) -> dict:
    """Преобразует плоский список областей обратно в структуру state['map'].

    Войска и постройки не сохраняются в плоском формате — в возвращаемом словаре
    поля 'troops' и 'structures' будут пустыми списками.
    """
    map_dict: dict = {}
    for entry in areas:
        if len(entry) == 7:
            tile_coords, area_coords, unique_num, area_type, owner, capacity, rotation = entry
        else:
            tile_coords, area_coords, unique_num, area_type, owner, capacity = entry
            rotation = 0
        col, row = tile_coords
        tile_key = f"{col},{row}"
        if tile_key not in map_dict:
            map_dict[tile_key] = {'areas': [None, None, None, None]}
        unrotate = _UNROTATE.get(rotation, _UNROTATE[0])
        area_idx = unrotate[tuple(area_coords)]
        map_dict[tile_key]['areas'][area_idx] = {
            'unique_number': unique_num,
            'type': area_type,
            'area_owner': owner,
            'capacity': capacity,
            'troops': [],
            'structures': [],
        }
    for tile in map_dict.values():
        tile['areas'] = [a for a in tile['areas'] if a is not None]
    return map_dict
