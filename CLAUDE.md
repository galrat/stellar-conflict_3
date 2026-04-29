# Stellar Conflict

Пошаговая тактическая стратегия 2 игрока (Forbidden Stars). Hotseat. Python сервер + JS тонкий клиент.

## Архитектура

**JS — только UI.** Рисует, принимает клики, вызывает API, вызывает applyState(). Никакой игровой логики.
**Python — всё остальное.** Логика, валидация, state, snapshots.

Поток: JS клик → apiCall() → Python обрабатывает → возвращает state → applyState() → render()

## Запрещено
- Не рефакторить существующий код, если задача этого не требует
- Не добавлять зависимости без обсуждения


## Файлы — что трогать при каких задачах

### JS (только UI)
- `game_render_board.js` — отрисовка доски и тайлов
- `game_render_side.js` — боковая панель (фазы, юниты, здания)
- `game_render_header.js` — шапка (ресурсы, раунд)
- `game_orders.js` — обработка кликов по приказам
- `game_deploy.js` — UI фазы deploy
- `game_events.js` — UI карт событий
- `game_advance.js` — UI фазы advance
- `game_save.js` — сохранение/загрузка через API
- `game_api.js` — apiCall(), единая точка fetch
- `game_constants.js` — константы (FACTIONS, CELL, RMAP)
- `game_utils.js` — вспомогательные функции
- `game_ui.js` — модалки, лог, showMsg, showHP
- `tiles.js` — каталог тайлов
- `stage1.js` — фаза построения карты (одноразовая)
- `styles.css` — все стили

### Python
- `game_server.py` — FastAPI endpoints, compute_ui_hints
- `game_state.py` — игровой движок, полный state
- `python_engine/orders_placement.py` — логика расстановки приказов
- `python_engine/order_play.py` — логика розыгрыша приказов
- `faction_base.py` — базовые классы фракций
- `faction_defs/` — данные фракций
- `game_serializer.py` — сериализация state
- `tiles.py` — каталог тайлов (Python)

### НЕ читать без явного запроса
- `factions_data.json` (74 КБ)
- `current_state.txt` (41 КБ)
- `state_example.txt`
- `game.js` (устарел, не подключён)
- `PHASES.md`, `instructions.txt`, `recommendations.txt`
- `stage1.js`
- Используй game_constants.js исключительно для инициализации графического интерфейса и начальной структуры объекта G. Все игровые правила, лимиты войск и характеристики юнитов игнорируй — их нужно брать динамически из Python-файлов фракций через серверные запросы

## Запуск

```
Terminal 1: python -m http.server 3000
Terminal 2: uvicorn game_server:app --reload --port 8000
Browser:    http://localhost:3000/game_engine.html
```

## Статус фаз

- ✅ stage_map_building — размещение карты, войск, построек, варп-штормов
- ✅ stage_orders_placement — расстановка 4 приказов каждым игроком
- 🟡 stage_orders_play — розыгрыш/сброс работает, эффекты приказов в разработке
- ✅ dominate, 
- ✅ deploy, 
- ❌ strategize, 
- ❌ advance — заглушки
- ❌ Особенности фракций

## Правила работы

- Be concise. Do not explain what you are about to do without request — just do it
- Read only files listed for the specific task. Do not explore the project broadly.
- Game logic always goes in Python. JS only renders and calls API.
- Snapshots save to `C:\Users\[User]\Downloads\Stellar_Conflict_Temp\` (max 10 files).
- Tell me which files you will study and change before doing this.