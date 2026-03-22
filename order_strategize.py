"""
order_strategize.py — Приказ STRATEGIZE (Plan / Планирование)
=============================================================
Этот файл описывает механику приказа Strategize в игре Stellar Conflict.
Используется как справочник при реализации логики в game_engine.html.

ПОРЯДОК ИСПОЛНЕНИЯ
------------------
1. Открывается модальное окно Strategize.
2. Игрок может КУПИТЬ боевые карты (battle cards) из своей фракции.
3. Игрок может КУПИТЬ улучшение приказа (order upgrade) для своей фракции.
4. Подтвердить или отменить.

ПОКУПКА БОЕВЫХ КАРТ (Battle Cards)
-----------------------------------
- Карты уровня 'initial' — начальные, выдаются бесплатно при старте игры (уже в руке).
- Карты уровня 'zero' (tier 0) — покупаются за 0₡ + особые условия (напр. молотки).
- Карты уровня 'two' (tier 2) — покупаются за 2₡.
- Карты уровня 'three' (tier 3) — покупаются за 3₡.
- Карта добавляется в руку игрока (hand).
- Можно купить несколько карт за один Strategize (если хватает ресурсов).
- Уже купленные карты нельзя купить повторно.

ПОКУПКА УЛУЧШЕНИЙ ПРИКАЗОВ (Order Upgrades)
--------------------------------------------
- Каждая фракция имеет несколько улучшений, привязанных к типу приказа.
- Уровни улучшений:
  * tier 0 — бесплатно (0₡)
  * tier 1 — стоит 2₡ (Command Level 1)
  * tier 2 — стоит 3₡ (Command Level 2)
- Покупается через Strategize и применяется немедленно.
- Хранится в player.purchasedOrderUpgrades.
- Уже купленное улучшение нельзя купить повторно.

ОГРАНИЧЕНИЯ
-----------
- Нельзя купить больше карт/улучшений чем позволяют ресурсы.
- Жетоны скидки (⊖) применяются к покупке карт: -2₡ за жетон.
- Молотки (⚒) могут требоваться для некоторых карт tier 0.

ПРОПУСК
-------
Если игрок ничего не купил → приказ уходит в стек событий.
Если купил хотя бы одну карту или улучшение → ход засчитан.

ОТМЕНА
------
"✕ Отмена" → всегда добавляет в стек событий и показывает кнопки
"Завершить ход" и "Отменить ход".

ОТКРЫТАЯ ИНФОРМАЦИЯ
-------------------
Факт наличия карт в руке — открытая информация (показывается в правой панели).
Конкретные карты — закрытая информация (показываются только владельцу).

АПГРЕЙДЫ И ИХ ЭФФЕКТЫ (по фракциям)
------------------------------------

Хаос:
  - Fear from Above (move): орбитальный удар + [?] раз в раунд
  - Dread Ritual (build): покупка T0–T2 без фабрики, -1₡ за культиста
  - Favour of the Dark Gods (plan): 2 жетона из игры → верх колоды событий
  - From the Warp (move): корабли могут двигаться сквозь варп-штормы
  - Complete Destruction (move): орбитальный удар + бастионы не защищают

Space Marines:
  - Reign of Fire (move): орбитальный удар + [M]→[G]
  - Crusade (move): +1 (R) если нет дружественных миров; Command Level 1
  - Direct the Faithful (plan): можно поменять одну постройку; Command Level 1
  - Recruitment Worlds (build): бастионы = фабрики; Command Level 1
  - Drop Pods (move): орбитальный удар + поставить бесплатного Марина; Level 2

Орки:
  - Lootin' (move): орбитальный удар + обмен материалами с врагом
  - Werk Fasta! (build): купить постройку до юнитов; Command Level 1
  - The Green Tide (plan): можно разыграть как другой приказ; Command Level 1
  - Ork Roks (move): 2 юнита через 1 пустой войд; Command Level 1
  - Stealin'! (move): орбитальный удар + украсть жетон; Command Level 2

Элдары:
  - Tactical Strikes (move): орбитальный удар + выбор цели для урона
  - Wraithbone Singers (build): постройка на планету с другой постройкой; Level 1
  - Farseer (plan): Strategize без юнитов в системе; Command Level 1
  - Corsair Raid (move): орбитальный удар после боя; Command Level 1
  - Strafing Run (move): орбитальный удар + [S]→переместить корабли; Level 2
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


CARD_LEVEL_COST = {
    'initial': 0,   # начальные карты (уже в руке)
    'zero': 0,      # tier 0 карты (бесплатно или спец. условие)
    'two': 2,       # tier 2 — 2₡
    'three': 3,     # tier 3 — 3₡
}

UPGRADE_TIER_COST = {
    0: 0,   # бесплатный апгрейд
    1: 2,   # Command Level 1 — 2₡
    2: 3,   # Command Level 2 — 3₡
}


@dataclass
class StrategizeSession:
    """Сессия выполнения приказа Strategize."""
    pi: int                               # индекс игрока
    oi: int                               # индекс слота приказа
    credits: int                          # рабочая копия кредитов
    tokens: dict                          # рабочая копия жетонов
    cards_bought: list = field(default_factory=list)    # купленные карты
    upgrade_bought: Optional[dict] = None               # купленное улучшение
    did_something: bool = False           # сделал ли игрок хоть что-то


def can_buy_card(sess: StrategizeSession, card: dict,
                 already_owned: list) -> dict:
    """
    Проверяет, может ли игрок купить боевую карту.

    Возвращает {'ok': bool, 'cost': int, 'reason': str}.
    """
    if card.get('name') in already_owned:
        return {'ok': False, 'cost': 0, 'reason': 'Уже куплена'}
    if card.get('level') == 'initial':
        return {'ok': False, 'cost': 0, 'reason': 'Начальная карта'}

    cost = CARD_LEVEL_COST.get(card.get('level', 'two'), 2)
    if sess.credits < cost:
        return {'ok': False, 'cost': cost, 'reason': 'Мало кредитов'}
    return {'ok': True, 'cost': cost, 'reason': ''}


def buy_card(sess: StrategizeSession, card: dict,
             already_owned: list) -> bool:
    """Купить боевую карту. Возвращает True при успехе."""
    check = can_buy_card(sess, card, already_owned)
    if not check['ok']:
        return False
    sess.credits -= check['cost']
    sess.cards_bought.append(card.get('name'))
    sess.did_something = True
    return True


def can_buy_upgrade(sess: StrategizeSession, upgrade: dict,
                    already_owned: list) -> dict:
    """
    Проверяет, может ли игрок купить улучшение приказа.
    """
    if upgrade.get('name') in already_owned:
        return {'ok': False, 'cost': 0, 'reason': 'Уже куплено'}

    tier = upgrade.get('tier', 0)
    cost = UPGRADE_TIER_COST.get(tier, 2)
    if sess.credits < cost:
        return {'ok': False, 'cost': cost, 'reason': 'Мало кредитов'}
    return {'ok': True, 'cost': cost, 'reason': ''}


def buy_upgrade(sess: StrategizeSession, upgrade: dict,
                already_owned: list) -> bool:
    """Купить улучшение приказа. Возвращает True при успехе."""
    check = can_buy_upgrade(sess, upgrade, already_owned)
    if not check['ok']:
        return False
    if sess.upgrade_bought:
        return False  # уже куплено одно улучшение за этот ход
    cost = check['cost']
    sess.credits -= cost
    sess.upgrade_bought = upgrade
    sess.did_something = True
    return True


def confirm_strategize(game_state, sess: StrategizeSession) -> bool:
    """
    Применяет результаты Strategize к игроку.
    Возвращает True если что-то было куплено (not skipped).
    """
    p = game_state.players[sess.pi]
    p.credits = sess.credits
    p.tokens = sess.tokens

    for card_name in sess.cards_bought:
        if card_name not in p.hand:
            p.hand.append(card_name)

    if sess.upgrade_bought:
        if not hasattr(p, 'purchased_order_upgrades'):
            p.purchased_order_upgrades = []
        p.purchased_order_upgrades.append(sess.upgrade_bought)

    return sess.did_something
