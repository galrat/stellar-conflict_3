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

# ── Stage 2 — активная игра ──────────────────────────────────────────────────
_active_game: Optional[dict] = None
_game_lock = asyncio.Lock()

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
        return True
    except Exception:
        return False

def _clear_temp_snapshots():
    """Очистить все временные snapshots"""
    snapshots = _get_temp_snapshots()
    for f in snapshots:
        Path(f).unlink()


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


class CancelOrderRequest(BaseModel):
    """Отмена приказа"""
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
            print(f"✅ Stage 2 инициализирована. Игроки: {[p.get('name') for p in _active_game.get('players', [])]}")
        return GameStateResponse(success=True, state=_active_game)
    except Exception as e:
        print(f"❌ Ошибка инициализации Stage 2: {e}")
        return GameStateResponse(success=False, error=str(e))


@app.get('/api/game/state')
async def get_game_state() -> GameStateResponse:
    """Получить текущее состояние игры"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        return GameStateResponse(success=True, state=_active_game.copy())


@app.post('/api/game/place-order')
async def place_order_endpoint(request: PlaceOrderRequest) -> GameStateResponse:
    """Разместить приказ на поле"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        try:
            # СОХРАНИТЬ SNAPSHOT перед изменениями
            _save_temp_snapshot()

            # Проверка: есть ли такой приказ в руке игрока
            player = _active_game['players'][request.player_id]
            order_idx = -1
            for i, o in enumerate(player.get('hand_orders', [])):
                if o.get('id') == request.order_id:
                    order_idx = i
                    break

            if order_idx < 0:
                return GameStateResponse(success=False, error="Приказ не найден в руке")

            # Удалить из руки
            order = player['hand_orders'].pop(order_idx)

            # Добавить на поле
            if 'orders' not in _active_game:
                _active_game['orders'] = []

            position = len([o for o in _active_game['orders'] if o.get('tile') == request.tile_key])
            _active_game['orders'].append({
                'id': order['id'],
                'type': order['type'],
                'owner': request.player_id,
                'tile': request.tile_key,
                'position': position,
                'revealed': False
            })

            # Обновить счётчик
            _active_game['ordersPlaced'][request.player_id] += 1

            print(f"📝 Приказ {request.order_id} размещён на [{request.tile_key}]")
            return GameStateResponse(success=True, state=_active_game.copy())

        except Exception as e:
            print(f"❌ Ошибка размещения приказа: {e}")
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/cancel-order')
async def cancel_order_endpoint(request: CancelOrderRequest) -> GameStateResponse:
    """Отменить приказ (заглушка на текущем этапе)"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        print(f"↩️ Отмена приказа {request.order_id} (заглушка)")
        return GameStateResponse(success=True, state=_active_game.copy())


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
            return GameStateResponse(success=True, state=_active_game.copy())
        else:
            return GameStateResponse(success=False, error="Ошибка загрузки snapshot")


@app.post('/api/game/pass-turn')
async def pass_turn_endpoint(request: PassTurnRequest) -> GameStateResponse:
    """Передать ход"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        # Переход на следующего игрока
        current = _active_game.get('curP', 0)
        next_p = 1 - current
        _active_game['curP'] = next_p
        print(f"➜ Ход передан игроку {next_p}")
        return GameStateResponse(success=True, state=_active_game.copy())


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
                'place-order': 'POST /api/game/place-order',
                'cancel-order': 'POST /api/game/cancel-order',
                'pass-turn': 'POST /api/game/pass-turn',
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
