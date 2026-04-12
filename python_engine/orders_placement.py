"""
Stage 2.1: Order Placement (Расстановка приказов)
Этап после выставления последнего варп-шторма

ЛОГИКА РАЗМЕЩЕНИЯ ПРИКАЗА:
1. Показать доступные приказы из hand_orders текущего игрока
2. Показать доступные плитки:
   - Дружественные плитки (содержат юниты или постройки игрока)
   - Соседние плитки (рядом с дружественными)
3. Игрок выбирает приказ и плитку
4. Валидация: плитка должна быть в доступных
5. Если валидна → размещение (приказ в центр плитки)
6. Показать кнопки Cancel и Pass Turn

ОТМЕНА (Cancel):
- Восстановить snapshot (системой snapshots)
- Вернуть state к предыдущему состоянию

ПЕРЕДАЧА ХОДА (Pass Turn):
- Проверить: если оба игрока разместили по 4 приказа → phase = "orders_placed"
- Иначе: смена текущего игрока, остаемся в "order-placement"
- Когда оба игрока передали ход в "orders_placed" → phase = "execution"

Примечание:
- Один приказ за раз, потом отмена или передача хода
- Приказ охватывает всю плитку (позиция посередине)
- Варп-штормы не блокируют размещение
- Всегда можно разместить приказ (нет случаев отказа)
"""


def get_available_tiles(current_state, player_id):
    """
    Получить доступные плитки для размещения приказа.

    Доступные плитки:
    - Дружественные (содержат юниты/постройки игрока)
    - Соседние (рядом с дружественными по горизонтали/вертикали)

    Args:
        current_state: текущее состояние игры
        player_id: ID игрока (0 или 1)

    Returns:
        list: список доступных tile_key
    """
    friendly_tiles = set()
    available_tiles = set()

    map_data = current_state.get('map', {})

    # 1. Найти дружественные плитки
    # Плитка дружественная если она содержит юниты/постройки игрока
    for tile_key, tile_info in map_data.items():
        areas = tile_info.get('areas', [])  # Список объектов областей

        has_player_content = False

        # Проверить каждую область этой плитки
        for area in areas:
            # Проверить войска (troops) в области
            troops = area.get('troops', [])
            for troop in troops:
                if troop.get('player') == player_id:
                    has_player_content = True
                    break

            # Проверить постройки (structures) в области
            structures = area.get('structures', [])
            for structure in structures:
                if structure.get('player') == player_id:
                    has_player_content = True
                    break

            if has_player_content:
                break

        if has_player_content:
            friendly_tiles.add(tile_key)
            available_tiles.add(tile_key)

    # 2. Добавить соседние плитки (квадратная сетка, 4 соседа — как в board.py)
    for tile_key in friendly_tiles.copy():
        col, row = map(int, tile_key.split(','))

        neighbors = [
            (col + 1, row),      # вправо
            (col - 1, row),      # влево
            (col, row + 1),      # вниз
            (col, row - 1),      # вверх
        ]

        for nc, nr in neighbors:
            neighbor_key = f"{nc},{nr}"
            if neighbor_key in map_data:
                available_tiles.add(neighbor_key)

    return sorted(list(available_tiles))


def validate_order_placement(current_state, player_id, order_id, tile_key):
    """
    Валидировать размещение приказа.

    Args:
        current_state: текущее состояние игры
        player_id: ID игрока
        order_id: ID приказа
        tile_key: ключ плитки

    Returns:
        tuple: (success: bool, message: str)
    """
    # 0. Проверить границы player_id
    if player_id not in (0, 1):
        return False, "Некорректный ID игрока"

    # 0b. Проверить что это ход текущего игрока
    if player_id != current_state.get('curP', -1):
        return False, "Сейчас не ваш ход"

    # 1. Проверить лимит приказов (максимум 4)
    orders_placed = current_state.get('ordersPlaced', [0, 0])[player_id]
    if orders_placed >= 4:
        return False, "Все приказы уже размещены"

    # 2. Проверить приказ в руке
    player = current_state['players'][player_id]
    order_found = False

    for order in player.get('hand_orders', []):
        if order.get('id') == order_id:
            order_found = True
            break

    if not order_found:
        return False, "Приказ не найден в руке"

    # 3. Проверить плитку на карте
    if tile_key not in current_state.get('map', {}):
        return False, "Плитка не найдена на карте"

    # 4. Проверить, доступна ли плитка
    available_tiles = get_available_tiles(current_state, player_id)

    if tile_key not in available_tiles:
        return False, "Вы не можете разместить приказ в этой системе"

    return True, "OK"


def place_order_impl(current_state, player_id, order_id, tile_key):
    """
    Реализовать размещение приказа (без валидации).

    Args:
        current_state: текущее состояние игры
        player_id: ID игрока
        order_id: ID приказа
        tile_key: ключ плитки

    Returns:
        dict: обновленное состояние
    """
    player = current_state['players'][player_id]

    # 1. Удалить приказ из руки
    order_data = None
    order_idx = -1

    for i, order in enumerate(player.get('hand_orders', [])):
        if order.get('id') == order_id:
            order_data = order
            order_idx = i
            break

    if order_idx >= 0:
        player['hand_orders'].pop(order_idx)

    # 2. Разместить приказ на плитке (в центр, охватывает всю плитку)
    if 'orders' not in current_state:
        current_state['orders'] = []

    # Позиция для множественных приказов на одной плитке
    position = len([o for o in current_state['orders'] if o.get('tile') == tile_key])

    current_state['orders'].append({
        'id': order_data.get('id'),
        'type': order_data.get('type'),
        'owner': player_id,
        'tile': tile_key,
        'position': position,
        'revealed': False
    })

    # 3. Обновить счётчик
    current_state['ordersPlaced'][player_id] += 1

    return current_state


def check_orders_complete(current_state):
    """
    Оба игрока разместили по 4 приказа?

    Returns:
        bool: True если этап размещения завершен
    """
    orders_placed = current_state.get('ordersPlaced', [0, 0])
    return orders_placed[0] >= 4 and orders_placed[1] >= 4


def next_phase_or_player(current_state):
    """
    После Pass Turn: переход на следующую фазу или игрока.

    Логика:
    - order-placement: если оба выставили по 4 → orders_placed
    - orders_placed: если оба нажали ход → execution (розыгрыш)

    Returns:
        dict: обновленное состояние
    """
    current_phase = current_state.get('phase', 'unknown')

    if current_phase == 'order-placement':
        # На этапе расстановки
        if check_orders_complete(current_state):
            # Оба выставили по 4 приказа → переход в orders_placed
            current_state['phase'] = 'orders_placed'
            # curP не меняем — остаётся последний выставлявший
        else:
            # Еще не все выставили → смена игрока
            current_state['curP'] = 1 - current_state['curP']

    elif current_phase == 'orders_placed':
        # На этапе ожидания (оба игрока выставили)
        # Переход в execution, первым ходит firstPlayer
        current_state['phase'] = 'execution'
        current_state['curP'] = current_state.get('firstPlayer', 0)

    return current_state