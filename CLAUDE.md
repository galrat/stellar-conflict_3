# 🎮 Stellar Conflict — Архитектура проекта

## Обзор

**Stellar Conflict** — пошаговая тактическая стратегия для двух игроков на основе Forbidden Stars.

### Текущий статус
- ✅ **Stage 1** (карта): размещение систем, войск, построек, варп-штормов — **РАБОТАЕТ**
- 🟡 **Stage 2** (приказы): расстановка и открытие приказов — **В РАЗРАБОТКЕ**
  - Размещение приказов: ✅ работает
  - Отмена приказов: ✅ работает через snapshots
  - Открытие приказов: 🟡 будет дальше
- 🟡 **Stage 3** (реализация всех приказов)
  - реализация dominate
  - реализация deploy
  - реализация strategize
  - реализация advance
- 🟡 **Stage 4** (реализация особенностей фракции)

---

## Архитектура: Python + JavaScript

### 🎨 JavaScript (game_engine.html) — только UI

**Что делает:**
- Рендеринг доски, боковых панелей, кнопок
- Принимает клики пользователя
- Отправляет команды на сервер через REST API
- Отображает state из Python

**Не делает:**
- ❌ Не проверяет валидность ходов
- ❌ Не хранит логику игры
- ❌ Не обновляет счетчики
- ❌ Не управляет приказами

### 🐍 Python (game_server.py + game_state.py) — всё остальное

**Что делает:**
- ✅ Хранит глобальное состояние игры (`_active_game`)
- ✅ Обрабатывает все действия игроков (размещение приказов, передача хода и т.д.)
- ✅ Валидирует ходы
- ✅ Управляет snapshots для отмены
- ✅ Отправляет обновленный state в JS

**Endpoints (Stage 2):**
```
POST /api/game/init                    — инициализация Stage 2
GET  /api/game/state                   — получить текущий state
GET  /api/game/available-tiles/{id}    — получить доступные плитки для игрока
POST /api/game/place-order             — разместить приказ
POST /api/game/cancel-order            — отмена приказа (заглушка)
POST /api/game/pass-turn               — передать ход
POST /api/game/undo                    — отмена последнего действия
POST /api/game/clear-temp              — очистить все snapshots
```

---

## State — единый источник истины

### Что такое State

State (G) — словарь со всем состоянием игры. Хранится на Python сервере.

Ключевые поля:
```javascript
{
  phase: "order-placement",      // текущая фаза
  curP: 0,                        // чей ход (0 или 1)
  firstPlayer: 0,                 // кто ходит первым
  ordersPlaced: [0, 4],          // сколько приказов выставлено
  
  players: [
    { 
      name, faction, pool, hand_orders, 
      hand_order_upgrades: [{ name, order_upgrade_status, ... }],  // order_upgrade_status: "active" или "used"
      ... 
    },
    { ... }
  ],
  
  map: {
    "0,0": { tileDefId, rotation, side, areas, ... },
    ...
  },
  
  orders: [
    { id, type, owner, tile, position, revealed },
    ...
  ],
  
  dropped_orders: [
    { id, type, owner },
    ...
  ],
  
  ordersPlaced: [orders_p0, orders_p1],  // количество размещенных приказов
  
  order_placed_this_turn: [p0_placed, p1_placed],  // флаг для проверки размещения приказа в этом ходу
  
  warpStorms: [
    { tileKey, side, owner, status },  // status: "active" или "used"
    ...
  ],
  
  log: [{ message, player_id }]
}
```

### Как он обновляется

1. **JS отправляет команду** → `POST /api/game/place-order`
2. **Python обрабатывает**:
   - Сохраняет snapshot (для undo)
   - Проверяет валидность
   - Обновляет `_active_game`
3. **Python отправляет обновленный state** → JSON ответ
4. **JS загружает state** → `applyState(newState)`
5. **JS перерисовывает** → `renderBoard(), renderSide()`

### Snapshot система (для отмены)

Каждое действие сохраняется в файл `state_temp_N.json`:
```
C:\Users\[User]\Downloads\Stellar_Conflict_Temp\
  state_temp_0.json
  state_temp_1.json
  ... (максимум 10)
```

Логика:
- **Перед** любым изменением state сохраняется snapshot
- Максимум 10 файлов; при достижении лимита удаляется самый старый
- При undo: Python загружает последний snapshot и восстанавливает state
- Используемый snapshot удаляется

---

## Поток данных

```
┌──────────────────────────────────────────┐
│ GAME_ENGINE.HTML (рендеринг + UI)        │
│ → apiCall() отправляет команду           │
└──────────────┬───────────────────────────┘
               │ POST /api/game/place-order
               ▼
┌──────────────────────────────────────────┐
│ GAME_SERVER.PY (логика игры)             │
│ → _active_game хранит state              │
│ → snapshots для отмены                   │
│ → возвращает обновленный state           │
└──────────────┬───────────────────────────┘
               │ { success: true, state }
               ▼
┌──────────────────────────────────────────┐
│ GAME_ENGINE.HTML                         │
│ → applyState() обновляет G               │
│ → renderBoard() перерисовывает           │
└──────────────────────────────────────────┘
```

---

## Ключевые компоненты

### JavaScript (game_engine.html)
- `apiCall(endpoint, body)` — отправляет запрос
- `applyState(newState)` — загружает state из Python
- `placeOrderViaAPI(tileKey)` — размещает приказ
- `undoLastOrderViaAPI()` — отменяет приказ
- `passOrderTurnViaAPI()` — передает ход
- `renderBoard()`, `renderSide()` — отображение

### Python (game_server.py)
- `init_game()` — инициализирует Stage 2
- `place_order_endpoint()` — обрабатывает приказ (использует orders_placement.py)
- `undo_endpoint()` — восстанавливает snapshot
- `pass_turn_endpoint()` — передает ход (использует orders_placement.py)
- `get_available_tiles_endpoint()` — возвращает доступные плитки
- `_save_temp_snapshot()` — сохраняет state (макс 10 файлов)
- `_load_temp_snapshot()` — загружает state

### Python (python_engine/orders_placement.py)
- `get_available_tiles()` — получить дружественные и соседние плитки
- `validate_order_placement()` — валидировать размещение приказа
- `place_order_impl()` — реализовать размещение приказа
- `check_orders_complete()` — проверить все ли 8 приказов разместены
- `next_phase_or_player()` — переход на следующего игрока или фазу

---

## Запуск

**Terminal 1** (HTTP сервер):
```bash
python -m http.server 3000
```

**Terminal 2** (API сервер):
```bash
uvicorn game_server:app --reload --port 8000
```

**Browser:**
```
http://localhost:3000/game_engine.html
```

---

## Файлы

- `game_engine.html` — UI, рендеринг, клиентская логика
- `game_server.py` — REST API сервер, обработка ходов
- `game_state.py` — полный игровой движок на Python
- `tiles.js`, `tiles.py` — каталог плиток
- `faction_defs/` — описание фракций

---

## Важно запомнить

### Единственный источник истины — Python

Все игровое состояние хранится в `_active_game` на Python сервере.

JS — это только "тонкий клиент" который:
1. Отправляет клики пользователя
2. Получает обновленный state
3. Отображает state на экране

### Отмена работает через файлы

Не нужно синхронизировать state между JS и Python:
1. JS отправляет команду
2. Python сохраняет snapshot ПЕРЕД изменениями
3. Если нужно отменить — Python загружает snapshot
4. JS получает восстановленный state

### Масштабируемость

Для добавления новой команды:
1. Добавить endpoint в `game_server.py`
2. Сохранить snapshot
3. Обновить `_active_game`
4. Вернуть новый state
5. В JS: `apiCall()` → `applyState()` → `renderBoard()`

---

## Сделано ✅

- Stage 1: полное размещение карты
- Snapshots и отмена
- API для приказов
- Передача хода
- Фракционные цвета

## Дальше 🟡

- Открытие приказов (reveal)
- Розыгрыш приказов (execute)
- Боевая система
