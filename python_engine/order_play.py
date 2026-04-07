"""
Stage 2.2: Order play (Розыгрыш приказов)
Этап после выставления последнего приказа каждым игроком

ЛОГИКА РОЗЫГРЫША ПРИКАЗА:
0. сохранить state как current_state
1. Определить текущего игрока
2. Определить все его доступные приказы, показать их в левой панели. Доступный приказ - это тот который лежит наверху стопки,
разыграть можно только свой верхний приказ стопки
3. Дать выбрать приказ, но выбор это еще не розыгрыш, игрок нажимает на приказ, он показывается в панели слева, далее
игрок нажимает кнопку Разыграть приказ
4. Розыгрыш каждого приказа будет реализован отдельно пока вместо этого выходит сообщение приказ НАЗВАНИЕ разыгран
при этом обновляется state который становится new_state
5. Игрок нажимает либо кнопку ОТМЕНА, которая возвращает  состояние current_state, либо кнопку ПЕРЕДАТЬ ХОД и происходит передача хода
6. Нельзя разыграть два приказа подряд, всегда надо передать ход.
7. Если у игрока нет доступных приказов, то только тогда он может нажать на ПЕРЕДАТЬ ХОД не разыгрывая приказ
8. Если только у одного игрока остались приказы на поле он все равно разыгрвает их по одному передавая ход.
9. Когда все приказы разыграны, то есть игрок с последним приказом нажал ПЕРЕДАТЬ ХОД начинается стадия КОНЕЦ РАУНДА
она будет описана позже.
"""

ORDER_TYPES = {
    'dominate': 'Dominate',
    'deploy': 'Deploy',
    'advance': 'Advance',
    'strategize': 'Strategize',
}


def get_available_orders(current_state, player_id):
    """
    Получить все доступные приказы текущего игрока.
    Доступный приказ = верхний приказ в стопке на каждой плитке.

    Args:
        current_state: состояние игры
        player_id: ID игрока (0 или 1)

    Returns:
        list: список доступных приказов [{ id, type, tile, position }, ...]
    """
    available = []
    map_data = current_state.get('map', {})

    # Для каждой плитки найти все приказы
    for tile_key in map_data.keys():
        # Получить приказы на этой плитке, отсортировать по позиции
        tile_orders = [o for o in current_state.get('orders', [])
                       if o.get('tile') == tile_key and o.get('owner') == player_id]

        # Сортировка: верхний приказ имеет наименьшую позицию
        # (позиция = индекс в стопке, где 0 = нижний, наибольший = верхний)
        if tile_orders:
            tile_orders.sort(key=lambda o: o.get('position', 0), reverse=True)
            # Верхний приказ = с наибольшей позицией
            top_order = tile_orders[0]
            available.append({
                'id': top_order.get('id'),
                'type': top_order.get('type'),
                'tile': tile_key,
                'position': top_order.get('position'),
                'revealed': top_order.get('revealed', False),
            })

    return available


def get_order_name(order_type):
    """
    Получить человеческое название приказа по типу.

    Args:
        order_type: тип приказа (dominate, deploy, advance, strategize)

    Returns:
        str: название приказа
    """
    return ORDER_TYPES.get(order_type, order_type)


def play_order(current_state, player_id, order_id):
    """
    Разыграть приказ.

    Текущая реализация:
    - Проверяет что приказ существует и принадлежит игроку
    - Генерирует сообщение о разыгрыше
    - Помечает приказ как revealed

    Args:
        current_state: состояние игры
        player_id: ID игрока
        order_id: ID разыгрываемого приказа

    Returns:
        tuple: (success: bool, message: str, new_state: dict или None)
    """
    # Найти приказ
    order = None
    for o in current_state.get('orders', []):
        if o.get('id') == order_id and o.get('owner') == player_id:
            order = o
            break

    if not order:
        return False, "Приказ не найден или не ваш", None

    # Проверить что это верхний приказ (наибольшая позиция на плитке)
    tile_orders = [o for o in current_state.get('orders', [])
                   if o.get('tile') == order.get('tile') and o.get('owner') == player_id]

    if tile_orders:
        tile_orders.sort(key=lambda o: o.get('position', 0), reverse=True)
        if tile_orders[0].get('id') != order_id:
            return False, "Можно разыграть только верхний приказ в стопке", None

    # Разыграть приказ
    order_name = get_order_name(order.get('type'))
    message = f"Приказ '{order_name}' разыгран"

    # Пометить как разыгранный
    order['revealed'] = True

    # Удалить разыгранный приказ из state
    new_state = {**current_state}
    new_state['orders'] = [o for o in new_state.get('orders', [])
                           if o.get('id') != order_id]

    return True, message, new_state


def check_orders_remain(current_state):
    """
    Проверить остались ли приказы на поле.

    Returns:
        tuple: (orders_remain: bool, orders_by_player: dict)
    """
    orders_p0 = len([o for o in current_state.get('orders', []) if o.get('owner') == 0])
    orders_p1 = len([o for o in current_state.get('orders', []) if o.get('owner') == 1])

    return {
        'p0': orders_p0,
        'p1': orders_p1,
        'total': orders_p0 + orders_p1,
        'any_remain': orders_p0 > 0 or orders_p1 > 0,
    }


def determine_next_player_order_play(current_state):
    """
    Определить следующего игрока для розыгрыша приказа.

    Логика:
    - Если у текущего игрока есть приказы → он ходит
    - Если только у другого игрока есть приказы → тот ходит
    - Если приказов нет → начало КОНЕЦ РАУНДА

    Returns:
        dict: { 'next_player': int или None, 'can_play': bool, 'message': str }
    """
    current_player = current_state.get('curP', 0)
    orders_info = check_orders_remain(current_state)

    if orders_info['total'] == 0:
        return {
            'next_player': None,
            'can_play': False,
            'message': 'Все приказы разыграны. Начало КОНЕЦ РАУНДА.',
            'phase_next': 'end-round',
        }

    # Есть ли приказы у текущего игрока?
    p_curr = 'p0' if current_player == 0 else 'p1'
    p_other = 'p1' if current_player == 0 else 'p0'

    if orders_info[p_curr] > 0:
        return {
            'next_player': current_player,
            'can_play': True,
            'message': f'Приказы остались. Ход игрока {current_player}.',
        }
    elif orders_info[p_other] > 0:
        other_player = 1 - current_player
        return {
            'next_player': other_player,
            'can_play': True,
            'message': f'У игрока {current_player} приказов нет. Ход игрока {other_player}.',
        }
    else:
        return {
            'next_player': None,
            'can_play': False,
            'message': 'Все приказы разыграны. Начало КОНЕЦ РАУНДА.',
            'phase_next': 'end-round',
        }