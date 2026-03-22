"""
order_deploy.py — Приказ DEPLOY (Build / Развёртывание)
========================================================
Этот файл описывает механику приказа Deploy в игре Stellar Conflict.
Используется как справочник при реализации логики в game_engine.html.

ПОРЯДОК ИСПОЛНЕНИЯ
------------------
1. Открывается модальное окно покупки (deploy modal).
2. Игрок выбирает юниты и/или постройку для покупки.
3. Подтверждает покупку — юниты/постройки надо разместить на карте.
4. Игрок кликает планетарные области для размещения купленного.
5. Завершает ход.

УСЛОВИЯ ПОКУПКИ ЮНИТОВ
-----------------------
- Нужна ФАБРИКА в системе приказа.
- Лимит покупки за один Deploy = вместимость планеты с фабрикой.
- Нельзя превысить максимальный резерв фракции (max_qty).
- Стоимость:
  * T0 (пехота/истребители): 2₡
  * T1 (морские пехотинцы): 3₡
  * T2 (механизированные/разрушители): 4₡ + зачастую 1⚒ молоток
  * T3 (элита): 5₡ + 1⚒ молоток
- Уровень юнита ограничен количеством городов в системе:
  * 0 городов → T0 и T1 (T1 требует 0 разрыва т.е. свободно)
  * На 1 уровень выше базового = +1⚒ молоток (tier gap)

ЖЕТОНЫ СКИДКИ (⊖)
------------------
- Каждый жетон ⊖ снижает стоимость одного юнита на 2₡ (минимум 0₡).
- Один жетон — одна скидка на один юнит.
- При отмене покупки юнита: возвращается net-стоимость (со скидкой) И жетон скидки.
- НЕ возвращается 2₡ «за скидку» — только то что было реально потрачено.
- Логика хранения: item.credCost = РЕАЛЬНО УПЛАЧЕННАЯ сумма (уже с учётом скидки).

ПОКУПКА ПОСТРОЕК
----------------
- Нужна дружественная планета в системе с вашими войсками и без постройки.
- Стоимость: Фабрика 2₡, Город 3₡, Бастион 2₡.
- Одна постройка за Deploy (нельзя купить и юнитов и постройку в одном Deploy).
  Уточнение: можно, если фракция имеет соответствующий апгрейд.
- После покупки постройку нужно разместить интерактивно (клик по планете).

ПРОПУСК / ОТМЕНА
----------------
- Нажать "✕ Отмена" в модальном окне:
  → Сессия закрывается, ход НЕ передаётся автоматически.
  → Показывается "Завершить ход" (в стек событий) и "Отменить ход" (возврат к снапшоту).
- Нажать "Подтвердить" с пустой корзиной:
  → Засчитывается как пропуск → приказ в стек событий.
- "Отменить ход" всегда возвращает к состоянию начала хода (_turnSnap).

СПЕЦИФИКА ФРАКЦИЙ
-----------------
- Орки (dominate): покупают 1 юнита без фабрики через способность доминации.
- Хаос: апгрейд Dread Ritual — покупка T0–T2 без фабрики, -1₡ за культиста.
- Space Marines: апгрейд Recruitment Worlds — бастионы считаются как фабрики.
- Элдары: апгрейд Wraithbone Singers — можно поставить постройку на планету
  где уже есть другая постройка.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CartItem:
    """Элемент корзины покупок в Deploy."""
    unit_type: str        # 'ground' или 'space'
    tier: int             # 0, 1, 2, 3
    cred_cost: int        # РЕАЛЬНО уплаченная сумма (после скидки)
    forge_cost: int       # молотки уплаченные
    discount_used: bool   # был ли использован жетон скидки
    unit_id: int          # уникальный id для последующего размещения


@dataclass
class StructPurchase:
    """Купленная постройка, ожидающая размещения."""
    struct_type: str      # 'factory', 'city', 'bastion'
    cred_cost: int        # РЕАЛЬНО уплаченная сумма
    discount_used: bool   # был ли использован жетон скидки


@dataclass
class DeploySession:
    """
    Сессия покупки (Deploy modal).
    Создаётся при открытии приказа Deploy, уничтожается при подтверждении/отмене.
    """
    pi: int                               # индекс игрока
    oi: int                               # индекс слота приказа (-1 для способностей)
    tile_key: str                         # ключ тайла системы приказа
    credits: int                          # кредиты (рабочая копия, не игрок!)
    tokens: dict                          # жетоны (рабочая копия)
    cart: list[CartItem] = field(default_factory=list)
    struct_purchase: Optional[StructPurchase] = None
    has_factory: bool = False
    factory_capacity: int = 0            # сколько юнитов можно купить
    cities_in_tile: int = 0              # количество городов (влияет на тир)
    on_board: dict = field(default_factory=dict)  # {type_tier: count} — уже на поле
    max_cart_size: int = 99


def calc_unit_cost(base_cost: int, tier: int, cities: int,
                   forge_tokens: int, discount_tokens: int,
                   use_discount: bool = False) -> dict:
    """
    Рассчитывает реальную стоимость покупки юнита.

    Возвращает {'ok': bool, 'cred': int, 'forge': int, 'reason': str}
    """
    tier_gap = max(0, tier - cities)    # превышение тира над городами
    extra_forge = 1 if tier_gap == 1 else 0
    total_forge = (1 if tier >= 2 else 0) + extra_forge  # базовая стоимость молотков

    if tier_gap > 1:
        return {'ok': False, 'cred': 0, 'forge': 0, 'reason': f'Нужно {tier - 1}+ городов'}
    if forge_tokens < total_forge:
        return {'ok': False, 'cred': 0, 'forge': 0, 'reason': 'Мало молотков'}

    effective_cred = base_cost
    if use_discount and discount_tokens > 0:
        effective_cred = max(0, base_cost - 2)

    return {'ok': True, 'cred': effective_cred, 'forge': total_forge, 'reason': ''}


def remove_from_cart(sess: DeploySession, cart_idx: int) -> None:
    """
    Убирает юнита из корзины и корректно возвращает ресурсы.

    Важно: item.cred_cost уже хранит РЕАЛЬНО уплаченную сумму (с учётом скидки).
    Возвращаем именно её, плюс жетон скидки если был использован.
    """
    item = sess.cart[cart_idx]
    sess.credits += item.cred_cost       # возвращаем то что реально потратили
    sess.tokens['forge'] = sess.tokens.get('forge', 0) + item.forge_cost
    if item.discount_used:
        sess.tokens['discount'] = sess.tokens.get('discount', 0) + 1
        # НЕ добавляем дополнительные 2₡ — скидка уже учтена в cred_cost
    sess.cart.pop(cart_idx)


def apply_post_purchase_discount(sess: DeploySession, cart_idx: int) -> bool:
    """
    Применяет жетон скидки к уже купленному юниту в корзине.

    Уменьшает item.cred_cost и возвращает часть кредитов.
    Возвращает True при успехе.
    """
    item = sess.cart[cart_idx]
    if item.discount_used:
        return False
    if sess.tokens.get('discount', 0) <= 0:
        return False
    refund = min(2, item.cred_cost)    # возвращаем не больше чем заплатили
    item.cred_cost -= refund
    item.discount_used = True
    sess.tokens['discount'] -= 1
    sess.credits += refund
    return True
