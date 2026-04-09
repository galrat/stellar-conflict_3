"""
game_server.py — FastAPI сервер для Stellar Conflict

Запуск: uvicorn game_server:app --reload --port 8000
Сервер слушает на http://localhost:8000

Stage 1 (карта) — JS управляет, сервер только сохраняет/загружает.
Stage 2 (приказы) — Python управляет state, JS только отображает.
"""
import asyncio
import json
import glob
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Optional, List
from faction_defs import FACTIONS
from python_engine.orders_placement import (
    get_available_tiles,
    validate_order_placement,
    place_order_impl,
    next_phase_or_player,
)
from python_engine.order_play import (
    get_available_orders,
    play_order,
    discard_order,
    return_dropped_orders,
    determine_next_player_order_play,
    check_orders_remain,
    ORDER_TYPES,
)

app = FastAPI(title="Stellar Conflict Game Server")

# Добавить CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"  # для разработки
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Лимит размера контента (10 МБ макс)
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

# Папка Загрузки (работает на Windows, Mac, Linux)
SAVES_DIR = Path.home() / "Downloads" / "Stellar_Conflict_Saves"
SAVES_DIR.mkdir(parents=True, exist_ok=True)

# Папка проекта
PROJECT_DIR = Path(__file__).parent
CURRENT_STATE_FILE = PROJECT_DIR / "current_state.txt"

# ── Stage 2 — активная игра ──────────────────────────────────────────────────
_active_game: Optional[dict] = None
_game_lock = asyncio.Lock()

# Поля с дефолтами, которые должны быть в state
_STATE_DEFAULTS = {
    'dropped_orders': [],
    'ordersPlaced': [0, 0],
    'orders': [],
    'order_placed_this_turn': [False, False],
    'execution_order_played': [False, False],
    'round': 1,
}

def _ensure_state_fields(state: dict):
    """Гарантировать наличие всех обязательных полей в state."""
    import copy
    for key, default in _STATE_DEFAULTS.items():
        if key not in state:
            state[key] = copy.deepcopy(default)


def compute_ui_hints(state: dict) -> dict:
    """
    Вычислить UI-подсказки на основе текущего состояния игры.
    JS использует эти данные вместо локальной логики.
    """
    phase = state.get('phase', 'setup')
    cur_p = state.get('curP', 0)
    players = state.get('players', [{}, {}])
    cp_name = players[cur_p].get('name', f'Игрок {cur_p}') if cur_p < len(players) else f'Игрок {cur_p}'

    ui = {
        'instruction': '',
        'buttons': [],
        'playable_order_ids': [],
        'blocked_tiles': [],
        'can_place_order': False,
        'order_placed_this_turn': False,
    }

    if phase == 'order-placement':
        orders_placed = state.get('ordersPlaced', [0, 0])
        placed_count = orders_placed[cur_p] if cur_p < len(orders_placed) else 0
        order_placed_flag = state.get('order_placed_this_turn', [False, False])
        placed_this_turn = order_placed_flag[cur_p] if cur_p < len(order_placed_flag) else False

        ui['instruction'] = f'<strong>РАССТАНОВКА ПРИКАЗОВ</strong><br>{cp_name}: выберите приказ, кликните центр системы. Выставлено: {placed_count}/4'
        ui['can_place_order'] = placed_count < 4 and not placed_this_turn
        ui['order_placed_this_turn'] = placed_this_turn
        ui['buttons'] = ['btn-pass']
        if placed_this_turn:
            ui['buttons'].append('btn-undo-order')

    elif phase == 'orders_placed':
        ui['instruction'] = f'<strong>ОЖИДАНИЕ РОЗЫГРЫША</strong><br>{cp_name}: приказы выставлены. Нажмите ПЕРЕДАТЬ ХОД чтобы начать розыгрыш.'
        ui['buttons'] = ['btn-pass']

    elif phase == 'execution':
        # Вычислить playable_order_ids и blocked_tiles
        available = get_available_orders(state, cur_p)
        ui['playable_order_ids'] = [o['id'] for o in available]

        # Заблокированные тайлы: тайлы где у игрока есть приказы, но верхний - чужой
        player_orders = [o for o in state.get('orders', []) if o.get('owner') == cur_p]
        player_tiles = set(o.get('tile') for o in player_orders)
        for tile_key in player_tiles:
            all_on_tile = [o for o in state.get('orders', []) if o.get('tile') == tile_key]
            all_on_tile.sort(key=lambda o: o.get('position', 0), reverse=True)
            if all_on_tile and all_on_tile[0].get('owner') != cur_p:
                ui['blocked_tiles'].append(tile_key)

        played_flag = state.get('execution_order_played', [False, False])
        played = played_flag[cur_p] if cur_p < len(played_flag) else False

        total_orders = len([o for o in state.get('orders', []) if o.get('owner') == cur_p])
        ui['instruction'] = f'<strong>РОЗЫГРЫШ ПРИКАЗОВ</strong><br>{cp_name}: кликните на приказ (панель или поле). Первый клик — выбор, второй — розыгрыш. Осталось: {total_orders}'

        # Кнопка ПЕРЕДАТЬ ХОД: если уже сыграл или нет доступных приказов
        can_pass = played or len(ui['playable_order_ids']) == 0
        if can_pass:
            ui['buttons'].append('btn-pass')

        ui['order_played_this_turn'] = played

    elif phase == 'end-round':
        round_num = state.get('round', 1)
        total_rounds = state.get('totalRounds', 8)
        ui['instruction'] = f'<strong>КОНЕЦ РАУНДА {round_num}/{total_rounds}</strong><br>Все приказы разыграны. Нажмите "Следующий раунд" для продолжения.'
        ui['buttons'] = ['btn-next-round']

    return ui


def _prepare_response_state() -> dict:
    """Подготовить state для отправки клиенту: добавить ui hints."""
    state = _active_game.copy()
    state['ui'] = compute_ui_hints(_active_game)
    return state


# ── Временные snapshots (для undo) ────────────────────────────────────────────
TEMP_DIR = Path.home() / "Downloads" / "Stellar_Conflict_Temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MAX_TEMP_SNAPSHOTS = 10

def _get_temp_snapshots() -> List[str]:
    """Получить список временных snapshots, отсортированные по времени"""
    import glob
    files = glob.glob(str(TEMP_DIR / "state_temp_*.json"))
    return sorted(files)

def _save_temp_snapshot() -> str:
    """Сохранить текущий state во временный файл. Возвращает путь файла."""
    if _active_game is None:
        return ""

    snapshots = _get_temp_snapshots()

    # Если уже есть 10 — удалить самый старый
    if len(snapshots) >= MAX_TEMP_SNAPSHOTS:
        Path(snapshots[0]).unlink()
        snapshots = snapshots[1:]

    # Номер нового файла
    next_num = len(snapshots)
    filepath = TEMP_DIR / f"state_temp_{next_num}.json"

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(_active_game, f, indent=2, ensure_ascii=False)

    return str(filepath)

def _load_temp_snapshot(idx: int) -> bool:
    """Загрузить временный snapshot с индексом. Возвращает True если успех."""
    global _active_game
    try:
        snapshots = _get_temp_snapshots()
        if idx < 0 or idx >= len(snapshots):
            return False

        with open(snapshots[idx], 'r', encoding='utf-8') as f:
            _active_game = json.load(f)
        _ensure_state_fields(_active_game)
        return True
    except Exception:
        return False

def _clear_temp_snapshots():
    """Очистить все временные snapshots"""
    snapshots = _get_temp_snapshots()
    for f in snapshots:
        Path(f).unlink()

def _save_current_state():
    """Сохранить текущий state в current_state.txt в папке проекта"""
    if _active_game is None:
        return
    try:
        with open(CURRENT_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_active_game, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  Ошибка при сохранении current_state.txt: {e}")


# ── Models ──────────────────────────────────────────────────────────────────

class SaveRequest(BaseModel):
    """Запрос на сохранение игры"""
    filename: str = 'game_auto.json'
    state: dict[str, Any]


class SaveResponse(BaseModel):
    """Ответ при сохранении"""
    success: bool
    filename: str = None
    path: str = None
    error: str = None


class LoadResponse(BaseModel):
    """Ответ при загрузке"""
    success: bool
    state: dict[str, Any] = None
    error: str = None


class GameInfo(BaseModel):
    """Информация об одной сохранённой игре"""
    filename: str
    size: int
    modified: float


class ListResponse(BaseModel):
    """Ответ со списком игр"""
    success: bool
    games: list[GameInfo] = []
    error: str = None


class SuccessResponse(BaseModel):
    """Простой ответ успеха/ошибки"""
    success: bool
    error: str = None


# ── Stage 2 Models ──────────────────────────────────────────────────────────

class GameStateResponse(BaseModel):
    """Ответ с состоянием игры (для /api/game/*)"""
    success: bool
    state: dict[str, Any] = None
    error: str = None


class InitGameRequest(BaseModel):
    """Инициализация Stage 2 — передача начального state из JS"""
    state: dict[str, Any]


class PlaceOrderRequest(BaseModel):
    """Размещение приказа"""
    player_id: int
    order_id: str
    tile_key: str


class PlayOrderRequest(BaseModel):
    """Розыгрыш приказа (без tile_key)"""
    player_id: int
    order_id: str


class CancelOrderRequest(BaseModel):
    """Отмена / сброс приказа"""
    player_id: int
    order_id: str


class PassTurnRequest(BaseModel):
    """Передача хода"""
    player_id: int


class UndoRequest(BaseModel):
    """Отмена последнего действия"""
    player_id: int


# ── Routes ──────────────────────────────────────────────────────────────────

@app.post('/api/save')
async def save_game(request: SaveRequest) -> SaveResponse:
    """Сохранить состояние игры"""
    try:
        filename = request.filename or 'game_auto.json'

        if not filename.endswith('.json'):
            filename += '.json'

        filepath = SAVES_DIR / filename

        # Проверка размера перед сохранением
        json_str = json.dumps(request.state, ensure_ascii=False)
        if len(json_str.encode('utf-8')) > MAX_CONTENT_LENGTH:
            raise ValueError(f'Файл слишком большой: {len(json_str)} байт > {MAX_CONTENT_LENGTH}')

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(request.state, f, indent=2, ensure_ascii=False)

        file_size = filepath.stat().st_size
        print(f"✅ Сохранено: {filename} ({file_size} B)")

        return SaveResponse(
            success=True,
            filename=filename,
            path=str(filepath)
        )
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return SaveResponse(
            success=False,
            error=str(e)
        )


@app.get('/api/load/{filename}')
async def load_game(filename: str) -> LoadResponse:
    """Загрузить состояние игры"""
    try:
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = SAVES_DIR / filename

        if not filepath.exists():
            print(f"⚠️  Файл не найден: {filename}")
            raise HTTPException(
                status_code=404,
                detail='File not found'
            )

        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)

        print(f"✅ Загружено: {filename}")
        return LoadResponse(
            success=True,
            state=state
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return LoadResponse(
            success=False,
            error=str(e)
        )


@app.get('/api/list')
async def list_games() -> ListResponse:
    """Список сохранённых игр"""
    try:
        games = []
        for filepath in sorted(SAVES_DIR.glob('*.json')):
            games.append(GameInfo(
                filename=filepath.name,
                size=filepath.stat().st_size,
                modified=filepath.stat().st_mtime
            ))

        print(f"📂 Список игр: найдено {len(games)} файлов")
        return ListResponse(success=True, games=games)
    except Exception as e:
        print(f"❌ Ошибка при получении списка: {e}")
        return ListResponse(
            success=False,
            error=str(e)
        )


@app.delete('/api/delete/{filename}')
async def delete_game(filename: str) -> SuccessResponse:
    """Удалить сохранённую игру"""
    try:
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = SAVES_DIR / filename

        if not filepath.exists():
            print(f"⚠️  Файл не найден для удаления: {filename}")
            raise HTTPException(
                status_code=404,
                detail='File not found'
            )

        filepath.unlink()
        print(f"🗑️  Удалено: {filename}")
        return SuccessResponse(success=True)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        return SuccessResponse(
            success=False,
            error=str(e)
        )


@app.get('/api/download/{filename}')
async def download_game(filename: str):
    """Скачать сохранённую игру как JSON файл"""
    try:
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = SAVES_DIR / filename

        if not filepath.exists():
            print(f"⚠️  Файл не найден для скачивания: {filename}")
            raise HTTPException(
                status_code=404,
                detail='File not found'
            )

        print(f"⬇️  Скачивание: {filename}")
        return FileResponse(
            filepath,
            media_type='application/json',
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ── STAGE 2 ENDPOINTS ──────────────────────────────────────────────────────

@app.post('/api/game/init')
async def init_game(request: InitGameRequest) -> GameStateResponse:
    """
    Инициализация Stage 2: JS передаёт состояние после Stage 1, Python берёт управление.
    Пока просто сохраняет state и возвращает его — логика приказов будет позже.
    """
    global _active_game
    try:
        async with _game_lock:
            _active_game = request.state.copy()

            # Обогатить state данными о картах и цветом фракции
            for p in _active_game.get('players', []):
                fid = p.get('faction')
                if fid and fid in FACTIONS:
                    fac = FACTIONS[fid]
                    # Добавить цвет фракции
                    faction_color = fac.color
                    if faction_color and not faction_color.startswith('#'):
                        faction_color = f'#{faction_color}'
                    p['faction_color'] = faction_color

                    p['hand_battle_cards'] = [c.to_dict() for c in fac.battle_cards if c.level.value == -1]
                    p['available_battle_cards'] = [c.to_dict() for c in fac.battle_cards if c.level.value != -1]
                    p['available_order_upgrades'] = [u.to_dict() for u in fac.order_upgrades]
                    p['available_event_cards'] = [e.to_dict() for e in fac.event_cards]
                    if 'hand_order_upgrades' not in p:
                        p['hand_order_upgrades'] = []
                    else:
                        # Если уже есть hand_order_upgrades, добавить status если его нет
                        for upgrade in p['hand_order_upgrades']:
                            if 'order_upgrade_status' not in upgrade:
                                upgrade['order_upgrade_status'] = 'active'
                    if 'hand_event_cards' not in p:
                        p['hand_event_cards'] = []

            # Удалить старое поле color, заменено на faction_color
            for p in _active_game.get('players', []):
                p.pop('color', None)

            # Инициализация обязательных полей
            _ensure_state_fields(_active_game)

            # Удалить из hand_orders приказы которые уже размещены на поле
            orders_on_field = set(o.get('id') for o in _active_game.get('orders', []))
            for p in _active_game.get('players', []):
                if 'hand_orders' in p:
                    p['hand_orders'] = [o for o in p['hand_orders']
                                       if o.get('id') not in orders_on_field]

            # Добавить status для варп-штормов если нет
            if 'warpStorms' in _active_game:
                for storm in _active_game['warpStorms']:
                    if 'status' not in storm:
                        storm['status'] = 'active'

            print(f"✅ Stage 2 инициализирована. Игроки: {[p.get('name') for p in _active_game.get('players', [])]}")
            _save_current_state()
        return GameStateResponse(success=True, state=_prepare_response_state())
    except Exception as e:
        print(f"❌ Ошибка инициализации Stage 2: {e}")
        return GameStateResponse(success=False, error=str(e))


@app.get('/api/game/state')
async def get_game_state() -> GameStateResponse:
    """Получить текущее состояние игры"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        return GameStateResponse(success=True, state=_prepare_response_state())


@app.post('/api/game/place-order')
async def place_order_endpoint(request: PlaceOrderRequest) -> GameStateResponse:
    """Разместить приказ на поле"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        try:
            # 1. Валидировать размещение
            success, message = validate_order_placement(
                _active_game, request.player_id, request.order_id, request.tile_key
            )

            if not success:
                return GameStateResponse(success=False, error=message)

            # 2. СОХРАНИТЬ SNAPSHOT перед изменениями
            _save_temp_snapshot()

            # 3. Разместить приказ
            place_order_impl(_active_game, request.player_id, request.order_id, request.tile_key)

            # 4. Установить флаг что приказ размещен в этом ходу
            _active_game['order_placed_this_turn'][request.player_id] = True

            print(f"📝 Приказ {request.order_id} размещён на [{request.tile_key}]")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            import traceback
            print(f"❌ Ошибка размещения приказа: {e}")
            print(f"Полный traceback:")
            traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.get('/api/game/available-tiles/{player_id}')
async def get_available_tiles_endpoint(player_id: int):
    """Получить доступные плитки для размещения приказа"""
    async with _game_lock:
        if _active_game is None:
            return {"success": False, "error": "Игра не инициализирована"}

        try:
            tiles = get_available_tiles(_active_game, player_id)
            return {
                "success": True,
                "available_tiles": tiles,
                "player_id": player_id,
            }
        except Exception as e:
            print(f"❌ Ошибка получения доступных плиток: {e}")
            return {"success": False, "error": str(e)}


@app.post('/api/game/cancel-order')
async def cancel_order_endpoint(request: CancelOrderRequest) -> GameStateResponse:
    """Отменить приказ (заглушка на текущем этапе)"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        print(f"↩️ Отмена приказа {request.order_id} (заглушка)")
        _save_current_state()
        return GameStateResponse(success=True, state=_prepare_response_state())


@app.post('/api/game/clear-temp')
async def clear_temp_endpoint() -> SuccessResponse:
    """Очистить все временные snapshots"""
    try:
        _clear_temp_snapshots()
        print("🧹 Очищены временные snapshots")
        return SuccessResponse(success=True)
    except Exception as e:
        return SuccessResponse(success=False, error=str(e))


@app.post('/api/game/undo')
async def undo_endpoint(request: UndoRequest) -> GameStateResponse:
    """Отмена последнего действия (загрузить предыдущий snapshot)"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        snapshots = _get_temp_snapshots()
        if not snapshots:
            return GameStateResponse(success=False, error="Нечего отменять")

        # Загрузить последний snapshot (самый новый)
        if _load_temp_snapshot(len(snapshots) - 1):
            # Удалить использованный snapshot
            Path(snapshots[-1]).unlink()
            print(f"↩️  Отмена выполнена")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        else:
            return GameStateResponse(success=False, error="Ошибка загрузки snapshot")


@app.get('/api/faction-cards/{faction_id}')
async def get_faction_cards(faction_id: str):
    """Получить все карты фракции по ID"""
    if faction_id not in FACTIONS:
        return {"success": False, "error": f"Фракция '{faction_id}' не найдена"}
    fac = FACTIONS[faction_id]
    return {
        "success": True,
        "hand_battle_cards": [c.to_dict() for c in fac.battle_cards if c.level.value == -1],
        "available_battle_cards": [c.to_dict() for c in fac.battle_cards if c.level.value != -1],
        "hand_order_upgrades": [],
        "available_order_upgrades": [u.to_dict() for u in fac.order_upgrades],
        "hand_event_cards": [],
        "available_event_cards": [e.to_dict() for e in fac.event_cards],
    }


@app.post('/api/game/pass-turn')
async def pass_turn_endpoint(request: PassTurnRequest) -> GameStateResponse:
    """Передать ход (переход на следующего игрока или фазу)"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        try:
            current_player = _active_game.get('curP', 0)
            phase = _active_game.get('phase', 'unknown')

            # На этапе order-placement требуется проверка что приказ был размещен
            if phase == 'order-placement':
                order_placed_list = _active_game.get('order_placed_this_turn', [False, False])
                order_placed = order_placed_list[current_player] if len(order_placed_list) > current_player else False

                if not order_placed:
                    print(f"❌ Ход отклонен: player={current_player} не разместил приказ")
                    return GameStateResponse(
                        success=False,
                        error="Вы должны разместить приказ перед передачей хода"
                    )

            # На этапе orders_placed просто передать ход
            elif phase == 'orders_placed':
                pass  # Просто переход к next_phase_or_player

            # СОХРАНИТЬ SNAPSHOT перед изменениями
            _save_temp_snapshot()

            # Применить логику следующей фазы или игрока
            next_phase_or_player(_active_game)

            # Сбросить флаг для нового игрока если остаемся в order-placement
            current_phase = _active_game.get('phase', 'unknown')
            next_player = _active_game.get('curP', 0)

            if current_phase == 'order-placement':
                _active_game['order_placed_this_turn'][next_player] = False
                print(f"➜ Ход передан игроку {next_player}")
            elif current_phase == 'orders_placed':
                print(f"✅ Оба игрока выставили приказы. Фаза: orders_placed")
            elif current_phase == 'execution':
                print(f"✅ Переход в фазу execution (розыгрыш приказов). Начинаем с игрока {next_player}")
            else:
                print(f"➜ Ход передан игроку {next_player}")

            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            print(f"❌ Ошибка при передаче хода: {e}")
            return GameStateResponse(success=False, error=str(e))


@app.get('/api/game/available-orders/{player_id}')
async def get_available_orders_endpoint(player_id: int):
    """Получить доступные приказы для розыгрыша"""
    async with _game_lock:
        if _active_game is None:
            return {"success": False, "error": "Игра не инициализирована"}

        try:
            orders = get_available_orders(_active_game, player_id)
            return {
                "success": True,
                "available_orders": orders,
                "player_id": player_id,
            }
        except Exception as e:
            print(f"❌ Ошибка получения доступных приказов: {e}")
            return {"success": False, "error": str(e)}


@app.post('/api/game/play-order')
async def play_order_endpoint(request: PlayOrderRequest) -> GameStateResponse:
    """Разыграть приказ"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        try:
            phase = _active_game.get('phase', 'unknown')

            if phase != 'execution':
                return GameStateResponse(success=False, error="Не время розыгрыша приказов")

            current_player = _active_game.get('curP', 0)
            if request.player_id != current_player:
                return GameStateResponse(success=False, error="Сейчас не ваш ход")

            # Нельзя играть если уже совершено действие в этом ходу (сброс или розыгрыш)
            played_flag = _active_game.get('execution_order_played', [False, False])
            if played_flag[current_player]:
                return GameStateResponse(success=False, error="Вы уже совершили действие в этом ходу. Передайте ход.")

            # СОХРАНИТЬ SNAPSHOT перед разыгрышем
            _save_temp_snapshot()

            # Разыграть приказ
            success, message, new_state = play_order(_active_game, request.player_id, request.order_id)

            if not success:
                return GameStateResponse(success=False, error=message)

            # Обновить state (приказ убран с поля, возвращён в руку)
            _active_game['orders'] = new_state['orders']
            _active_game['players'] = new_state['players']

            # Отметить что игрок разыграл приказ в этом ходу
            _active_game['execution_order_played'][request.player_id] = True

            # Добавить в лог
            if 'log' not in _active_game:
                _active_game['log'] = []
            _active_game['log'].append({'message': message, 'player_id': request.player_id})

            print(f"🎯 {message}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            import traceback
            print(f"❌ Ошибка розыгрыша приказа: {e}")
            traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/discard-order')
async def discard_order_endpoint(request: CancelOrderRequest) -> GameStateResponse:
    """Сбросить приказ в колоду сброса (без розыгрыша)"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        try:
            phase = _active_game.get('phase', 'unknown')
            if phase != 'execution':
                return GameStateResponse(success=False, error="Сброс доступен только на этапе розыгрыша")

            current_player = _active_game.get('curP', 0)
            if request.player_id != current_player:
                return GameStateResponse(success=False, error="Сейчас не ваш ход")

            # Нельзя сбрасывать если уже совершено действие в этом ходу
            played_flag = _active_game.get('execution_order_played', [False, False])
            if played_flag[current_player]:
                return GameStateResponse(success=False, error="Вы уже совершили действие в этом ходу. Передайте ход.")

            _save_temp_snapshot()

            success, message, new_state = discard_order(_active_game, request.player_id, request.order_id)
            if not success:
                return GameStateResponse(success=False, error=message)

            _active_game['orders'] = new_state['orders']
            _active_game['dropped_orders'] = new_state['dropped_orders']

            # Сброс тоже считается ходом — нельзя играть другой приказ после
            _active_game['execution_order_played'][request.player_id] = True

            if 'log' not in _active_game:
                _active_game['log'] = []
            _active_game['log'].append({'message': message, 'player_id': request.player_id})

            print(f"🗑 {message}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            print(f"❌ Ошибка сброса приказа: {e}")
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/pass-turn-order-play')
async def pass_turn_order_play_endpoint(request: PassTurnRequest) -> GameStateResponse:
    """Передать ход на этапе розыгрыша приказов"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        try:
            phase = _active_game.get('phase', 'unknown')

            if phase != 'execution':
                return GameStateResponse(success=False, error="Не время розыгрыша приказов")

            current_player = _active_game.get('curP', 0)

            # Проверить: если у игрока есть разыгрываемые приказы — обязан сыграть
            playable = get_available_orders(_active_game, current_player)
            played_flag = _active_game.get('execution_order_played', [False, False])
            if playable and not played_flag[current_player]:
                return GameStateResponse(
                    success=False,
                    error="Вы должны разыграть доступный приказ перед передачей хода"
                )

            # СОХРАНИТЬ SNAPSHOT перед изменениями
            _save_temp_snapshot()

            # Определить следующий ход
            next_info = determine_next_player_order_play(_active_game)

            if next_info.get('next_player') is not None:
                _active_game['curP'] = next_info['next_player']
                _active_game['execution_order_played'][next_info['next_player']] = False
                print(f"➜ {next_info['message']}")
            else:
                # Конец раунда — вернуть сброшенные приказы в руки
                updated = return_dropped_orders(_active_game)
                _active_game['players'] = updated['players']
                _active_game['dropped_orders'] = updated['dropped_orders']
                _active_game['phase'] = 'end-round'
                print(f"✅ {next_info['message']}")

            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            print(f"❌ Ошибка при передаче хода: {e}")
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/next-round')
async def next_round_endpoint(request: PassTurnRequest) -> GameStateResponse:
    """Перейти к следующему раунду (сброс приказов, смена первого игрока)"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        try:
            phase = _active_game.get('phase', 'unknown')
            if phase != 'end-round':
                return GameStateResponse(success=False, error="Переход к следующему раунду доступен только в фазе end-round")

            _save_temp_snapshot()

            # Сбросить приказы и флаги
            _active_game['orders'] = []
            _active_game['ordersPlaced'] = [0, 0]
            _active_game['order_placed_this_turn'] = [False, False]
            _active_game['execution_order_played'] = [False, False]
            _active_game['dropped_orders'] = []

            # Следующий раунд
            current_round = _active_game.get('round', 1)
            _active_game['round'] = current_round + 1

            # Смена первого игрока
            _active_game['firstPlayer'] = 1 - _active_game.get('firstPlayer', 0)
            _active_game['curP'] = _active_game['firstPlayer']

            # Генерировать hand_orders для нового раунда (8 приказов: 2 каждого типа)
            order_types = ['dominate', 'deploy', 'advance', 'strategize']
            for pid in range(2):
                hand_orders = []
                for ot in order_types:
                    for copy_num in range(2):
                        hand_orders.append({
                            'id': f'{ot}_{pid}_{copy_num}_r{_active_game["round"]}',
                            'type': ot,
                            'owner': pid,
                        })
                _active_game['players'][pid]['hand_orders'] = hand_orders

            _active_game['phase'] = 'order-placement'

            print(f"🔄 Раунд {_active_game['round']}. Первый ход: игрок {_active_game['curP']}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            import traceback
            print(f"❌ Ошибка при переходе к следующему раунду: {e}")
            traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.get('/')
async def root():
    """Корневой эндпоинт"""
    return {
        'status': 'ok',
        'name': '🎮 Stellar Conflict Game Server',
        'endpoints': {
            'stage1': {
                'save': 'POST /api/save',
                'load': 'GET /api/load/{filename}',
                'list': 'GET /api/list',
                'delete': 'DELETE /api/delete/{filename}',
                'download': 'GET /api/download/{filename}',
            },
            'stage2': {
                'init': 'POST /api/game/init',
                'state': 'GET /api/game/state',
                'order-placement': {
                    'available-tiles': 'GET /api/game/available-tiles/{player_id}',
                    'place-order': 'POST /api/game/place-order',
                    'pass-turn': 'POST /api/game/pass-turn',
                },
                'order-play': {
                    'available-orders': 'GET /api/game/available-orders/{player_id}',
                    'play-order': 'POST /api/game/play-order',
                    'pass-turn-order-play': 'POST /api/game/pass-turn-order-play',
                },
                'shared': {
                    'cancel-order': 'POST /api/game/cancel-order',
                    'discard-order': 'POST /api/game/discard-order',
                    'next-round': 'POST /api/game/next-round',
                    'undo': 'POST /api/game/undo',
                    'clear-temp': 'POST /api/game/clear-temp',
                }
            }
        }
    }


if __name__ == '__main__':
    print('=' * 60)
    print('🎮 Stellar Conflict Game Server')
    print('=' * 60)
    print('Запуск: uvicorn game_server:app --reload --port 8000')
    print('Server: http://localhost:8000')
    print(f'Saves: {SAVES_DIR.absolute()}')
    print('=' * 60)
    print('⚠️  Используйте uvicorn для запуска, не python!')
