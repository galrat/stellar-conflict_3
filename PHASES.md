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
    EXECUTION       = "execution"
    ENDED           = "ended"
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
| `'order-placement'` | orders_placement.py:225 | Расстановка приказов (по 1 за ход) |
| `'orders_placed'` | orders_placement.py:229, 235 | Ожидание: оба игрока выставили, ждем розыгрыша |
| `'execution'` | orders_placement.py:238 | Розыгрыш размещенных приказов (по одному) |
| `'end-round'` | order_play.py (TODO) | Конец раунда |

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
┌─────────────────────────┐
│ 'order-placement'       │ (по 8 приказов на игрока)
└──────┬──────────────────┘
       │ После 8 приказов каждым игроком
       ▼
┌─────────────────────────┐
│ 'orders_placed'         │ (ожидание: только ПЕРЕДАТЬ ХОД)
└──────┬──────────────────┘
       │ После передачи хода обоими игроками
       ▼
┌─────────────────────────┐
│ 'execution'             │ (розыгрыш по одному)
└──────┬──────────────────┘
       │ После всех приказов
       ▼
┌─────────────────────────┐
│ 'end-round'             │ (конец раунда, TODO)
└─────────────────────────┘
```

---

## Где искать фазы в коде

### Python Backend
- **game_state.py** (строки 91-98): Старый enum Phase
- **python_engine/orders_placement.py** (строка 221): Переход в `'play-orders'`
- **python_engine/order_play.py**: Переход в `'end-round'`
- **game_server.py** (строки 585, 592): Проверка фаз

### JavaScript Frontend
- **game_engine.html** (строка 935): Функция `setPhase(phase)` — главная обработка фаз
- **game_engine.html** (строка 649): Условие `G.phase === 'order-placement' || G.phase === 'game-start'`
- **game_engine.html** (строка 1847): Отрисовка UI для `'order-placement'`
- **game_engine.html** (строка 1930): Отрисовка UI для `'play-orders'`

### Глобальный state
- **game_engine.html** (строка 487-519): Объект `G` содержит `G.phase`
- **current_state.txt** (строка 585): Текущая фаза сохраняется как `"phase": "order-placement"`

---

## Актуальный список фаз для Stage 2

На текущей стадии разработки используются эти фазы:

```
Stage 2 фазы:
- order-placement      ✅ РЕАЛИЗОВАНА (расстановка приказов, по 8 каждому)
- orders_placed        ✅ РЕАЛИЗОВАНА (ожидание начала розыгрыша)
- execution            ✅ РЕАЛИЗОВАНА (розыгрыш приказов по одному)
- end-round            🟡 TODO (конец раунда)
```

---

## Примечания

### Фазы в game_state.py vs game_engine.html

`game_state.py` содержит старый enum Phase с подчеркиваниями (для Stage 1):
- `SETUP = "setup"`
- `TILE_PLACEMENT = "tile_placement"`
- и т.д.

`game_engine.html` использует дефисы (Stage 1 и Stage 2):
- `'game-start'`
- `'tile-placement'`
- `'order-placement'`
- `'orders_placed'` (новая фаза)
- `'execution'` (вместо старого 'play-orders')

**Статус**: game_state.py Phase enum больше не используется в Stage 2. Все фазы контролируются через `game_engine.html` и Python endpoints. Phase enum в game_state.py может быть удален в будущем или обновлен для соответствия.

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
