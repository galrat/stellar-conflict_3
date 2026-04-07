# Фазы игры Stellar Conflict

## Определение фаз

Фазы определены в двух местах:

### 1. game_state.py (Stage 1 — размещение на карте)
Файл: `game_state.py`, строки 91-98

Enum `Phase`:
```python
class Phase(Enum):
    SETUP           = "setup"
    TILE_PLACEMENT  = "tile_placement"
    TROOP_ON_TILE   = "troop_on_tile"
    TROOP_PLACEMENT = "troop_placement"
    ORDER_PLACEMENT = "order_placement"
    ORDERS_PLACED   = "orders_placed"
    EXECUTION       = "execution"
    ROUND_END       = "round_end"
    GAME_END        = "game_end"
```

**Статус**: Эти фазы определены для старой архитектуры с GameState движком на Python.
В новой архитектуре (game_engine.html как основной клиент) используются другие имена фаз.

---

### 2. game_engine.html (Stage 1 & Stage 2 — основной UI)
Файл: `game_engine.html`, используются в `setPhase()` (строка 935)

**Все фазы в порядке прохождения**:

#### Stage 1 (Размещение на карте)
| Фаза | Константа | Где используется | Описание |
|------|-----------|------------------|---------|
| `'game-start'` | - | game_engine.html строка 649 | Начало игры, выбор фракций |
| `'tile-placement'` | - | setPhase() строка 949 | Размещение системы (тайла) на доску |
| `'troop-on-tile'` | - | setPhase() строка 956 | Размещение войск на только что поставленный тайл |
| `'troop-placement'` | - | (не найдена в UI) | Общее размещение войск (UNUSED) |
| `'warp-storm'` | - | setPhase() строка 966 | Размещение варп-штормов |

#### Stage 2 (Розыгрыш приказов)
| Фаза | Где определяется | Описание |
|------|-----------------|---------|
| `'order-placement'` | orders_placement.py:225 | Расстановка приказов (по 8 каждому) |
| `'orders_placed'` | orders_placement.py:229, 235 | Ожидание: оба выставили, ждём розыгрыша |
| `'execution'` | game_server.py:604, order_play.py | Розыгрыш размещенных приказов |
| `'end-round'` | game_server.py:706, 710 | Конец раунда (основная логика) |

---

## Переходы между фазами

```
Stage 1 (Tile Placement):
┌──────────────┐
│ 'game-start' │ (выбор фракций)
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│ 'tile-placement'        │ (размещение системы)
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ 'troop-on-tile'         │ (войска на новый тайл)
└──────┬──────────────────┘
       │ Когда 6 тайлов: перейти в warp-storm
       ▼
┌─────────────────────────┐
│ 'warp-storm'            │ (варп-штормы, по 2 шт)
└──────┬──────────────────┘
       │ После обоих игроков
       ▼
       
Stage 2 (Order Play):
┌──────────────────────────────┐
│ 'order-placement'            │ (расстановка, по 1 за ход)
└──────┬───────────────────────┘
       │ После 8 приказов каждым
       ▼
┌──────────────────────────────┐
│ 'orders_placed'              │ (ожидание, только ПЕРЕДАТЬ ХОД)
└──────┬───────────────────────┘
       │ После передачи хода обоими
       ▼
┌──────────────────────────────┐
│ 'execution'                  │ (розыгрыш по одному)
└──────┬───────────────────────┘
       │ После всех приказов
       ▼
┌──────────────────────────────┐
│ 'end-round'                  │ (конец раунда)
└──────────────────────────────┘
```

---

## Где искать фазы в коде

### Python Backend
- **game_state.py** (строки 91-98): Старый enum Phase (больше не используется в Stage 2)
- **python_engine/orders_placement.py** (строка 229): Переход в `'orders_placed'`
- **python_engine/orders_placement.py** (строка 238): Переход в `'execution'`
- **game_server.py** (строки 604-606): Обработка фазы `'execution'`
- **game_server.py** (строки 706, 710): Установка фазы `'end-round'`

### JavaScript Frontend
- **game_engine.html** (строка 935): Функция `setPhase(phase)` — главная обработка фаз
- **game_engine.html** (строка 987): Обработка `'orders_placed'` в setPhase()
- **game_engine.html** (строка 992): Обработка `'execution'` в setPhase()
- **game_engine.html** (строка 1002): Обработка `'end-round'` в setPhase()
- **game_engine.html** (строка 1957): Отрисовка UI для `'orders_placed'` в renderSide()
- **game_engine.html** (строка 1976): Отрисовка UI для `'execution'` в renderSide()
- **game_engine.html** (строка 2037): Отрисовка UI для `'end-round'` в renderSide()`

### Глобальный state
- **game_engine.html** (строка 487-519): Объект `G` содержит `G.phase`
- **current_state.txt**: Текущая фаза сохраняется с соответствующим значением (order-placement, orders_placed, execution, end-round)

---

## Актуальный список фаз для Stage 2

На текущей стадии разработки используются эти фазы:

```
Stage 2 фазы:
- order-placement      ✅ РЕАЛИЗОВАНА (расстановка приказов)
- play-orders          ✅ РЕАЛИЗОВАНА (розыгрыш приказов)
- end-round            🟡 TODO (конец раунда)
```

---

## Примечания

### Несоответствие между game_state.py и game_engine.html

`game_state.py` содержит старый enum Phase с подчеркиваниями:
- `ORDER_PLACEMENT = "order_placement"`
- `EXECUTION = "execution"`

Но `game_engine.html` использует дефисы:
- `'order-placement'`
- `'play-orders'`

**Статус**: game_state.py больше не используется в Stage 2. Все фазы контролируются через `game_engine.html` и Python endpoints.

### Как добавить новую фазу

1. **На сервере** (game_server.py):
   - Добавить endpoint для новой фазы
   - Обновить логику переходов в existing endpoints

2. **На клиенте** (game_engine.html):
   - Добавить условие в `setPhase()` (строка 935+)
   - Добавить обработку UI для новой фазы в `renderSide()` и `renderBoard()`
   - Добавить условие в `applyState()` если нужна особая логика при загрузке state

3. **В документации**:
   - Обновить этот файл PHASES.md
   - Обновить CLAUDE.md если это критично
