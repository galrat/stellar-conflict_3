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
import copy

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
        # Все приказы на плитке (оба игрока) — глобальный стек
        all_tile_orders = [o for o in current_state.get('orders', [])
                           if o.get('tile') == tile_key]
        if not all_tile_orders:
            continue

        # Глобальный топ = приказ с наибольшей позицией среди всех на плитке
        all_tile_orders.sort(key=lambda o: o.get('position', 0), reverse=True)
        top_order = all_tile_orders[0]

        # Доступен только если верхний приказ принадлежит игроку
        if top_order.get('owner') == player_id:
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

    # Проверить что это глобально верхний приказ на плитке (среди всех игроков)
    all_tile_orders = [o for o in current_state.get('orders', [])
                       if o.get('tile') == order.get('tile')]
    if all_tile_orders:
        all_tile_orders.sort(key=lambda o: o.get('position', 0), reverse=True)
        if all_tile_orders[0].get('id') != order_id:
            return False, "Приказ перекрыт другим приказом в стопке", None

    # Разыграть приказ
    order_name = get_order_name(order.get('type'))
    message = f"Приказ '{order_name}' разыгран"

    # Удалить приказ с поля
    new_state = copy.deepcopy(current_state)
    new_state['orders'] = [o for o in new_state.get('orders', [])
                           if o.get('id') != order_id]

    # Вернуть приказ в руку игрока
    hand_order = {
        'id': order.get('id'),
        'type': order.get('type'),
        'owner': player_id,
    }
    new_state['players'] = [dict(p) for p in new_state.get('players', [])]
    new_state['players'][player_id]['hand_orders'] = list(
        new_state['players'][player_id].get('hand_orders', [])
    )
    new_state['players'][player_id]['hand_orders'].append(hand_order)

    return True, message, new_state


def discard_order(current_state, player_id, order_id):
    """
    Сбросить приказ в колоду сброса (без розыгрыша).

    Только верхний приказ в стопке на плитке может быть сброшен.
    Сброшенный приказ возвращается в руку на фазе конца раунда.

    Args:
        current_state: состояние игры
        player_id: ID игрока
        order_id: ID приказа

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

    # Проверить что это глобально верхний приказ на плитке (среди всех игроков)
    all_tile_orders = [o for o in current_state.get('orders', [])
                       if o.get('tile') == order.get('tile')]
    if all_tile_orders:
        all_tile_orders.sort(key=lambda o: o.get('position', 0), reverse=True)
        if all_tile_orders[0].get('id') != order_id:
            return False, "Приказ перекрыт приказом соперника в стопке", None

    order_name = get_order_name(order.get('type'))

    # Удалить приказ с поля
    new_state = copy.deepcopy(current_state)
    new_state['orders'] = [o for o in new_state.get('orders', [])
                           if o.get('id') != order_id]

    # Добавить в dropped_orders
    if 'dropped_orders' not in new_state:
        new_state['dropped_orders'] = []
    new_state['dropped_orders'] = list(new_state['dropped_orders'])
    new_state['dropped_orders'].append({
        'id': order.get('id'),
        'type': order.get('type'),
        'owner': player_id,
    })

    message = f"Приказ '{order_name}' сброшен"
    return True, message, new_state


def return_dropped_orders(current_state):
    """
    Вернуть все сброшенные приказы в руки игроков (вызывается на фазе конца раунда).

    Returns:
        dict: обновлённое состояние
    """
    dropped = current_state.get('dropped_orders', [])
    if not dropped:
        return current_state

    new_state = copy.deepcopy(current_state)
    new_state['players'] = [dict(p) for p in new_state.get('players', [])]
    for p in new_state['players']:
        p['hand_orders'] = list(p.get('hand_orders', []))

    for order in dropped:
        pid = order.get('owner')
        if pid in (0, 1):
            new_state['players'][pid]['hand_orders'].append({
                'id': order.get('id'),
                'type': order.get('type'),
                'owner': pid,
            })

    new_state['dropped_orders'] = []
    return new_state


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

    Логика (ход всегда чередуется):
    - Сначала пробуем передать ход сопернику
    - Если у соперника нет приказов — текущий игрок продолжает
    - Если приказов нет ни у кого → КОНЕЦ РАУНДА

    Returns:
        dict: { 'next_player': int или None, 'can_play': bool, 'message': str }
    """
    current_player = current_state.get('curP', 0)
    other_player = 1 - current_player
    orders_info = check_orders_remain(current_state)

    if orders_info['total'] == 0:
        return {
            'next_player': None,
            'can_play': False,
            'message': 'Все приказы разыграны. Начало КОНЕЦ РАУНДА.',
            'phase_next': 'end-round',
        }

    p_other = 'p1' if current_player == 0 else 'p0'
    p_curr  = 'p0' if current_player == 0 else 'p1'

    # Всегда сначала передаём ход сопернику (чередование)
    if orders_info[p_other] > 0:
        return {
            'next_player': other_player,
            'can_play': True,
            'message': f'Ход передан игроку {other_player}.',
        }
    elif orders_info[p_curr] > 0:
        # У соперника приказов нет — текущий продолжает
        return {
            'next_player': current_player,
            'can_play': True,
            'message': f'У соперника приказов нет. Игрок {current_player} продолжает.',
        }
    else:
        return {
            'next_player': None,
            'can_play': False,
            'message': 'Все приказы разыграны. Начало КОНЕЦ РАУНДА.',
            'phase_next': 'end-round',
        }