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
from fastapi import FastAPI, HTTPException, Request
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
from python_engine.round_end import (
    run_end_of_round,
    init_unit_statuses,
)
from python_engine.deploy import (
    get_deploy_info,
    validate_basket_for_state,
    validate_place_unit_for_state,
    validate_and_remove_overflow,
    validate_buy_building_for_state,
    apply_deploy_to_state,
)
from python_engine.advance import (
    advance_play,
    advance_choose_source,
    advance_move_ship,
    advance_move_ground,
    advance_commit,
    advance_fight,
    advance_orbital,
    advance_orbital_remove,
    advance_skip_orbital,
    advance_next_step,
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
    'event_cards_offered': [[], []],
    'event_selection_done': [False, False],
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
        # Если идёт выполнение приказа Deploy
        pd = state.get('pending_deploy')
        if pd:
            step = pd.get('step', '')
            tile_key = pd.get('tile_key', '')
            step_labels = {
                'buy_units':        'покупка юнитов',
                'place_units':      'размещение юнитов',
                'resolve_overflow': 'разрешение переполнения',
                'buy_building':     'покупка здания',
            }
            ui['instruction'] = (
                f'<strong>DEPLOY</strong> — тайл [{tile_key}]<br>'
                f'{cp_name}: {step_labels.get(step, step)}'
            )
            # Кнопки зависят от шага
            if step == 'place_units':
                ui['buttons'] = ['btn-uu', 'btn-undo-order']
            else:
                ui['buttons'] = ['btn-undo-order']
            ui['deploy_step']        = step
            ui['deploy_info']        = pd.get('deploy_info', {})
            ui['deploy_hand']        = pd.get('hand', [])
            ui['deploy_placed']      = pd.get('placed', [])
            ui['deploy_removed_map'] = pd.get('removed_from_map', [])
            return ui

        # Если идёт выполнение приказа Advance
        pa = state.get('pending_advance')
        if pa:
            step = pa.get('step', '')
            tile_key = pa.get('tile_key', '')
            step_labels = {
                'choose_source':   'выбор источника',
                'ships':           'перемещение кораблей',
                'ground':          'перемещение наземных юнитов',
                'combat':          'бой',
                'orbital':         'орбитальный удар',
                'orbital_defend':  'защита от орбитального удара',
            }
            ui['instruction'] = (
                f'<strong>ADVANCE</strong> — тайл [{tile_key}]<br>'
                f'{cp_name}: {step_labels.get(step, step)}'
            )
            ui['buttons'] = ['btn-undo-order']
            ui['advance_step'] = step
            ui['advance_tile_key'] = tile_key
            ui['advance_adjacent_tiles'] = pa.get('adjacent_tiles', [])
            ui['advance_available_ships'] = pa.get('available_ships', [])
            ui['advance_available_ground'] = pa.get('available_ground_units', [])
            ui['advance_committed_moves'] = pa.get('committed_moves', [])
            ui['advance_contest_area'] = pa.get('contest_area_idx')
            ui['advance_source_tile'] = pa.get('source_tile')
            return ui

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

        # Кнопка ОТМЕНА: появляется после розыгрыша/сброса, до передачи хода
        if played:
            ui['buttons'].append('btn-undo-order')

        ui['order_played_this_turn'] = played

    elif phase == 'end-round':
        round_num = state.get('round', 1)
        total_rounds = state.get('totalRounds', 8)
        selection_done = state.get('event_selection_done', [False, False])
        cp_name = state.get('players', [{}, {}])[cur_p].get('name', f'P{cur_p}')

        if not all(selection_done):
            # Ожидаем выбор карты событий
            offered = state.get('event_cards_offered', [[], []])
            cards = offered[cur_p] if cur_p < len(offered) else []
            ui['instruction'] = (
                f'<strong>КОНЕЦ РАУНДА {round_num}/{total_rounds}</strong><br>'
                f'{cp_name}: выберите карту события'
            )
            ui['event_cards_to_pick'] = cards
            ui['buttons'] = ['btn-pick-event']
        else:
            # Оба выбрали — готовы к следующему раунду
            ui['instruction'] = (
                f'<strong>КОНЕЦ РАУНДА {round_num}/{total_rounds}</strong><br>'
                f'Все приказы разыграны. Нажмите "Следующий раунд" для продолжения.'
            )
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


class DominateJokerRequest(BaseModel):
    """Выбор типа токена для джокера при розыгрыше Dominate"""
    player_id: int
    choice: str  # 'support' | 'discount' | 'forge'


class DeployConfirmBasketRequest(BaseModel):
    """Подтверждение корзины юнитов при Deploy"""
    player_id: int
    basket: List[dict]  # [{'unit_key': str, 'use_cash': bool}]


class DeployPlaceUnitRequest(BaseModel):
    """Размещение одного юнита при Deploy"""
    player_id: int
    unit_key: str
    area_idx: int


class DeployResolveOverflowRequest(BaseModel):
    """Убрать юнита из overflow области при Deploy"""
    player_id: int
    remove_area_idx: int
    remove_unit_key: str


class DeployBuyBuildingRequest(BaseModel):
    """Купить и разместить здание при Deploy"""
    player_id: int
    building_type: str
    area_idx: int
    use_cash: bool = False


class DeploySkipRequest(BaseModel):
    """Пропустить шаг (здание или юниты) при Deploy"""
    player_id: int


class AdvanceChooseSourceRequest(BaseModel):
    """Выбрать source тайл для Advance (или None чтобы пропустить)"""
    player_id: int
    source_tile_key: Optional[str] = None


class AdvanceMoveUnitRequest(BaseModel):
    """Переместить юнита при Advance"""
    player_id: int
    from_area_idx: int
    to_area_idx: int


class AdvanceOrbitalRequest(BaseModel):
    """Выбрать корабль и цель для орбитального удара"""
    player_id: int
    ship_area_idx: int
    target_area_idx: int


class AdvanceOrbitalRemoveRequest(BaseModel):
    """Защищающийся удаляет юнита после орбитального удара"""
    player_id: int
    area_idx: int
    unit_idx: int


class AdvanceGenericRequest(BaseModel):
    """Общий запрос для Advance (commit, fight, skip, next_step)"""
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

            # Инициализировать unit_status='active' для всех войск на карте
            init_unit_statuses(_active_game)

            # Инициализировать collected_objectives для каждого игрока
            for p in _active_game.get('players', []):
                if 'collected_objectives' not in p:
                    p['collected_objectives'] = 0

            # Нормализовать токены: reinforcement → support, cash → discount
            for p in _active_game.get('players', []):
                tok = p.setdefault('tokens', {})
                # Переименовать старые ключи если присутствуют
                if 'reinforcement' in tok and 'support' not in tok:
                    tok['support'] = tok.pop('reinforcement')
                if 'cash' in tok and 'discount' not in tok:
                    tok['discount'] = tok.pop('cash')
                # Установить дефолты
                tok.setdefault('support', 0)
                tok.setdefault('discount', 0)
                tok.setdefault('forge', 0)
                p['tokens'] = tok

            print(f"✅ Stage 2 инициализирована. Игроки: {[p.get('name') for p in _active_game.get('players', [])]}")
            _save_current_state()
        return GameStateResponse(success=True, state=_prepare_response_state())
    except Exception as e:
        print(f"❌ Ошибка инициализации Stage 2: {e}")
        return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/restore')
async def restore_game(request: InitGameRequest) -> GameStateResponse:
    """
    Восстановить сохранённое состояние игры на сервере без сброса фазы.
    Используется при загрузке сохранения в фазах execution/end-round.
    Делает то же что /api/game/init, но не меняет фазу.
    """
    global _active_game
    try:
        async with _game_lock:
            _active_game = request.state.copy()

            # Обогатить данными фракций (карты, апгрейды, события)
            for p in _active_game.get('players', []):
                fid = p.get('faction')
                if fid and fid in FACTIONS:
                    fac = FACTIONS[fid]
                    faction_color = fac.color
                    if faction_color and not faction_color.startswith('#'):
                        faction_color = f'#{faction_color}'
                    p['faction_color'] = faction_color
                    # Карты восстанавливаем только если их нет в сохранении
                    if 'hand_battle_cards' not in p:
                        p['hand_battle_cards'] = [c.to_dict() for c in fac.battle_cards if c.level.value == -1]
                    if 'available_battle_cards' not in p:
                        p['available_battle_cards'] = [c.to_dict() for c in fac.battle_cards if c.level.value != -1]
                    if 'available_order_upgrades' not in p:
                        p['available_order_upgrades'] = [u.to_dict() for u in fac.order_upgrades]
                    if 'available_event_cards' not in p:
                        p['available_event_cards'] = [e.to_dict() for e in fac.event_cards]
                    if 'hand_order_upgrades' not in p:
                        p['hand_order_upgrades'] = []
                    if 'hand_event_cards' not in p:
                        p['hand_event_cards'] = []

            for p in _active_game.get('players', []):
                p.pop('color', None)

            _ensure_state_fields(_active_game)
            init_unit_statuses(_active_game)

            # Нормализовать токены
            for p in _active_game.get('players', []):
                tok = p.setdefault('tokens', {})
                if 'reinforcement' in tok and 'support' not in tok:
                    tok['support'] = tok.pop('reinforcement')
                if 'cash' in tok and 'discount' not in tok:
                    tok['discount'] = tok.pop('cash')
                tok.setdefault('support', 0)
                tok.setdefault('discount', 0)
                tok.setdefault('forge', 0)

            phase = _active_game.get('phase', 'unknown')
            print(f"✅ Игра восстановлена. Фаза: {phase}. Игроки: {[p.get('name') for p in _active_game.get('players', [])]}")
            _save_current_state()
        return GameStateResponse(success=True, state=_prepare_response_state())
    except Exception as e:
        print(f"❌ Ошибка восстановления игры: {e}")
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
            # В фазе execution snapshot — это «точка возврата» хода игрока.
            # Его НЕ удаляем: повторный undo должен вернуть к тому же состоянию.
            if _active_game.get('phase') != 'execution':
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

            # Для order-placement сохраняем snapshot ДО изменений (чтобы отменить размещение)
            if phase == 'order-placement':
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
                # Начало хода в фазе розыгрыша: сбрасываем все старые snapshots
                # и сохраняем ОДИН snapshot текущего состояния — к нему и будем возвращаться
                _clear_temp_snapshots()
                _save_temp_snapshot()
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

            # Нельзя играть если не разрешён выбор джокера
            if _active_game.get('pending_joker_choice'):
                return GameStateResponse(success=False, error="Сначала разрешите выбор джокера (Dominate)")

            # Нельзя играть если уже совершено действие в этом ходу (сброс или розыгрыш)
            played_flag = _active_game.get('execution_order_played', [False, False])
            if played_flag[current_player]:
                return GameStateResponse(success=False, error="Вы уже совершили действие в этом ходу. Передайте ход.")

            # Найти приказ до разыгрыша чтобы знать тип и плитку
            played_order = next(
                (o for o in _active_game.get('orders', [])
                 if o.get('id') == request.order_id and o.get('owner') == request.player_id),
                None
            )
            order_type = played_order.get('type') if played_order else None
            order_tile = played_order.get('tile') if played_order else None

            # Разыграть приказ (убрать с поля, вернуть в руку)
            success, message, new_state = play_order(_active_game, request.player_id, request.order_id)

            if not success:
                return GameStateResponse(success=False, error=message)

            # Обновить state (приказ убран с поля, возвращён в руку)
            _active_game['orders'] = new_state['orders']
            _active_game['players'] = new_state['players']

            # Для deploy и advance — execution_order_played ставится только после завершения
            if order_type not in ('deploy', 'advance'):
                _active_game['execution_order_played'][request.player_id] = True

            # Добавить в лог
            if 'log' not in _active_game:
                _active_game['log'] = []
            _active_game['log'].append({'message': message, 'player_id': request.player_id})

            # Выполнить эффект приказа
            if order_type == 'deploy' and order_tile:
                info = get_deploy_info(_active_game, request.player_id, order_tile)
                _active_game['pending_deploy'] = {
                    'player_id':        request.player_id,
                    'tile_key':         order_tile,
                    'step':             'buy_units' if info['has_factory'] else 'buy_building',
                    'has_factory':      info['has_factory'],
                    'deploy_info':      info,
                    'basket':           [],
                    'unit_costs':       {'credits': 0, 'forge': 0, 'cash': 0},
                    'hand':             [],
                    'placed':           [],
                    'removed_from_map': [],
                }
                print(f"🏗 Deploy на тайле {order_tile}, шаг: {_active_game['pending_deploy']['step']}")

            elif order_type == 'dominate' and order_tile:
                from python_engine.dominate import dominate_order
                dom_success, dom_msg, dom_state = dominate_order(_active_game, request.player_id, order_tile)
                if dom_success and dom_state:
                    _active_game.clear()
                    _active_game.update(dom_state)
                    print(f"🏆 {dom_msg}")
                elif not dom_success:
                    print(f"⚠ Dominate effect failed: {dom_msg}")

            elif order_type == 'advance' and order_tile:
                adv_state = advance_play(_active_game, request.player_id, order_tile)
                _active_game.clear()
                _active_game.update(adv_state)
                print(f"⚔️ Advance на тайле {order_tile}, шаг: {_active_game['pending_advance']['step']}")

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

            # Нельзя сбрасывать если не разрешён выбор джокера
            if _active_game.get('pending_joker_choice'):
                return GameStateResponse(success=False, error="Сначала разрешите выбор джокера (Dominate)")

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


@app.post('/api/game/dominate-joker')
async def dominate_joker_endpoint(request: DominateJokerRequest) -> GameStateResponse:
    """Разрешить выбор джокера при розыгрыше приказа Dominate"""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            from python_engine.dominate import dominate_resolve_joker

            # Проверить что есть pending_joker_choice
            pending = _active_game.get('pending_joker_choice', {})
            if not pending:
                return GameStateResponse(success=False, error="Нет ожидающего выбора джокера")

            if pending.get('player_id') != request.player_id:
                return GameStateResponse(success=False, error="Это не ваш выбор джокера")

            joker_count = pending.get('joker_count', 1)
            # Упрощение: все джокеры одного типа
            joker_choices = [request.choice] * joker_count

            success, message, new_state = dominate_resolve_joker(
                _active_game, request.player_id, joker_choices
            )

            if not success:
                return GameStateResponse(success=False, error=message)

            # Обновить state
            _active_game.clear()
            _active_game.update(new_state)

            print(f"🎲 {message}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            import traceback
            traceback.print_exc()
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

            # Блокировать передачу хода если идёт deploy или advance
            if _active_game.get('pending_deploy'):
                return GameStateResponse(success=False, error="Сначала завершите приказ Deploy")
            if _active_game.get('pending_advance'):
                return GameStateResponse(success=False, error="Сначала завершите приказ Advance")

            # Проверить: если у игрока есть разыгрываемые приказы — обязан сыграть
            playable = get_available_orders(_active_game, current_player)
            played_flag = _active_game.get('execution_order_played', [False, False])
            if playable and not played_flag[current_player]:
                return GameStateResponse(
                    success=False,
                    error="Вы должны разыграть доступный приказ перед передачей хода"
                )

            # Определить следующий ход
            next_info = determine_next_player_order_play(_active_game)

            if next_info.get('next_player') is not None:
                _active_game['curP'] = next_info['next_player']
                _active_game['execution_order_played'][next_info['next_player']] = False
                # Начало хода нового игрока: сбросить старые snapshots, сохранить новый checkpoint
                _clear_temp_snapshots()
                _save_temp_snapshot()
                print(f"➜ {next_info['message']}")
            else:
                # Считаем сброшенные приказы ДО очистки (нужно для draw_event_cards)
                dropped_before = _active_game.get('dropped_orders', [])
                dropped_counts = [
                    len([o for o in dropped_before if o.get('owner') == pid])
                    for pid in range(len(_active_game.get('players', [])))
                ]

                # Конец раунда — вернуть сброшенные приказы в руки
                updated = return_dropped_orders(_active_game)
                _active_game['players'] = updated['players']
                _active_game['dropped_orders'] = updated['dropped_orders']

                # Авто-шаги конца раунда: цели, доход, восстановление, карты событий
                run_end_of_round(_active_game, dropped_counts)

                _active_game['phase'] = 'end-round'
                print(f"✅ {next_info['message']}")

            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            print(f"❌ Ошибка при передаче хода: {e}")
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/select-event-card')
async def select_event_card_endpoint(request: Request) -> GameStateResponse:
    """Игрок выбирает карту события из предложенных."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")

        try:
            body = await request.json()
            player_id = body.get('player_id')
            card_name = body.get('card_name')

            if player_id is None or card_name is None:
                return GameStateResponse(success=False, error="Требуется player_id и card_name")

            phase = _active_game.get('phase', '')
            if phase != 'end-round':
                return GameStateResponse(success=False, error="Выбор карт доступен только в фазе end-round")

            selection_done = _active_game.get('event_selection_done', [False, False])
            if selection_done[player_id]:
                return GameStateResponse(success=False, error="Игрок уже выбрал карту")

            # Найти карту в предложенных
            offered = _active_game.get('event_cards_offered', [[], []])
            player_offered = offered[player_id] if player_id < len(offered) else []
            card = next((c for c in player_offered if c.get('name') == card_name), None)

            if not card:
                return GameStateResponse(success=False, error=f"Карта '{card_name}' не найдена в предложенных")

            _save_temp_snapshot()

            # Добавить карту в руку и убрать из доступных
            players = _active_game.get('players', [])
            if player_id < len(players):
                if 'hand_event_cards' not in players[player_id]:
                    players[player_id]['hand_event_cards'] = []
                players[player_id]['hand_event_cards'].append(card)

                # Убрать одну копию карты из available_event_cards
                available = players[player_id].get('available_event_cards', [])
                for i, c in enumerate(available):
                    if c.get('name') == card_name:
                        available.pop(i)
                        break

                p_name = players[player_id].get('name', f'P{player_id}')
                _active_game.get('log', []).append({
                    'message': f'{p_name} взял карту события: {card_name}',
                    'player_id': player_id
                })

            # Отметить выбор
            _active_game['event_selection_done'][player_id] = True

            # Если второй игрок ещё не выбирал — передать ход ему
            other = 1 - player_id
            if not _active_game['event_selection_done'][other]:
                _active_game['curP'] = other

            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())

        except Exception as e:
            print(f"❌ Ошибка при выборе карты события: {e}")
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
            _active_game['event_cards_offered'] = [[], []]
            _active_game['event_selection_done'] = [False, False]

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


# ── DEPLOY ENDPOINTS ──────────────────────────────────────────────────────────

def _get_pending_deploy(player_id: int):
    """Вернуть pending_deploy если он активен и принадлежит игроку."""
    pd = _active_game.get('pending_deploy')
    if not pd:
        return None, "Нет активного приказа Deploy"
    if pd.get('player_id') != player_id:
        return None, "Это не ваш приказ Deploy"
    return pd, None


def _finish_deploy(player_id: int, building=None):
    """Применить deploy к state и очистить pending_deploy."""
    pd = _active_game['pending_deploy']
    apply_deploy_to_state(
        _active_game,
        player_id,
        pd['tile_key'],
        pd['placed'],
        pd['unit_costs'],
        building=building,
        removed_from_map=pd.get('removed_from_map'),
    )
    del _active_game['pending_deploy']
    _active_game['execution_order_played'][player_id] = True


@app.post('/api/game/deploy-confirm-basket')
async def deploy_confirm_basket_endpoint(request: DeployConfirmBasketRequest) -> GameStateResponse:
    """Подтвердить корзину юнитов для покупки."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            pd, err = _get_pending_deploy(request.player_id)
            if err:
                return GameStateResponse(success=False, error=err)
            if pd['step'] != 'buy_units':
                return GameStateResponse(success=False, error=f"Шаг buy_units недоступен (текущий: {pd['step']})")

            success, errors, costs = validate_basket_for_state(
                _active_game, request.player_id, pd['tile_key'], request.basket
            )
            if not success:
                return GameStateResponse(success=False, error='; '.join(errors))

            hand = [item['unit_key'] for item in request.basket]
            pd['basket']     = request.basket
            pd['unit_costs'] = costs
            pd['hand']       = hand
            # Если корзина пуста — сразу к зданию
            pd['step']       = 'place_units' if hand else 'buy_building'

            print(f"✅ Deploy basket confirmed: {hand}, costs={costs}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/deploy-place-unit')
async def deploy_place_unit_endpoint(request: DeployPlaceUnitRequest) -> GameStateResponse:
    """Разместить одного купленного юнита в области тайла."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            pd, err = _get_pending_deploy(request.player_id)
            if err:
                return GameStateResponse(success=False, error=err)
            if pd['step'] != 'place_units':
                return GameStateResponse(success=False, error=f"Шаг place_units недоступен (текущий: {pd['step']})")

            success, error, overflow = validate_place_unit_for_state(
                _active_game, request.player_id, pd['tile_key'],
                pd['hand'], pd['placed'], request.unit_key, request.area_idx
            )
            if not success:
                return GameStateResponse(success=False, error=error)

            pd['placed'].append({'unit_key': request.unit_key, 'area_idx': request.area_idx})

            # Вычислить остаток в руке
            hand_remaining = list(pd['hand'])
            for p in pd['placed']:
                if p['unit_key'] in hand_remaining:
                    hand_remaining.remove(p['unit_key'])

            if hand_remaining:
                pd['step'] = 'place_units'  # ещё есть что размещать
            elif overflow:
                pd['step'] = 'resolve_overflow'
            else:
                pd['step'] = 'buy_building'

            print(f"📍 Deploy placed {request.unit_key} -> area {request.area_idx}, overflow={overflow}, next={pd['step']}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/deploy-resolve-overflow')
async def deploy_resolve_overflow_endpoint(request: DeployResolveOverflowRequest) -> GameStateResponse:
    """Убрать юнита из переполненной области."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            pd, err = _get_pending_deploy(request.player_id)
            if err:
                return GameStateResponse(success=False, error=err)
            if pd['step'] != 'resolve_overflow':
                return GameStateResponse(success=False, error=f"Шаг resolve_overflow недоступен (текущий: {pd['step']})")

            success, error, new_placed, removed_from_map, remaining_overflow = validate_and_remove_overflow(
                _active_game, request.player_id, pd['tile_key'],
                pd['placed'], request.remove_area_idx, request.remove_unit_key
            )
            if not success:
                return GameStateResponse(success=False, error=error)

            pd['placed'] = new_placed
            if removed_from_map:
                pd['removed_from_map'].append({
                    'unit_key': request.remove_unit_key,
                    'area_idx': request.remove_area_idx,
                })

            pd['step'] = 'resolve_overflow' if remaining_overflow else 'buy_building'

            src = 'с карты' if removed_from_map else 'из размещённых'
            print(f"↩ Deploy removed {request.remove_unit_key} from area {request.remove_area_idx} ({src}), next={pd['step']}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/deploy-buy-building')
async def deploy_buy_building_endpoint(request: DeployBuyBuildingRequest) -> GameStateResponse:
    """Купить и разместить здание, завершить Deploy."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            pd, err = _get_pending_deploy(request.player_id)
            if err:
                return GameStateResponse(success=False, error=err)
            if pd['step'] != 'buy_building':
                return GameStateResponse(success=False, error=f"Шаг buy_building недоступен (текущий: {pd['step']})")

            success, errors, final_cost = validate_buy_building_for_state(
                _active_game, request.player_id, pd['tile_key'],
                request.building_type, request.area_idx, request.use_cash
            )
            if not success:
                return GameStateResponse(success=False, error='; '.join(errors))

            building = {
                'type':       request.building_type,
                'area_idx':   request.area_idx,
                'final_cost': final_cost,
                'use_cash':   request.use_cash,
            }
            _finish_deploy(request.player_id, building=building)

            print(f"🏗 Deploy finished: {request.building_type} placed in area {request.area_idx}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/deploy-undo-place')
async def deploy_undo_place_endpoint(request: DeploySkipRequest) -> GameStateResponse:
    """Вернуть последнего размещённого юнита в руку (во время deploy place_units)."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            pd, err = _get_pending_deploy(request.player_id)
            if err:
                return GameStateResponse(success=False, error=err)
            if pd['step'] not in ('place_units', 'resolve_overflow'):
                return GameStateResponse(success=False, error="Нет размещённых юнитов для отмены")
            if not pd['placed']:
                return GameStateResponse(success=False, error="Нет размещённых юнитов для отмены")

            pd['placed'].pop()

            # Пересчитать шаг
            hand_remaining = list(pd['hand'])
            for p in pd['placed']:
                if p['unit_key'] in hand_remaining:
                    hand_remaining.remove(p['unit_key'])
            # После отмены всегда возвращаемся в place_units
            pd['step'] = 'place_units'

            print(f"↩ Deploy undo place: осталось разместить {len(hand_remaining)}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/deploy-skip-building')
async def deploy_skip_building_endpoint(request: DeploySkipRequest) -> GameStateResponse:
    """Пропустить покупку здания и завершить Deploy."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            pd, err = _get_pending_deploy(request.player_id)
            if err:
                return GameStateResponse(success=False, error=err)
            if pd['step'] != 'buy_building':
                return GameStateResponse(success=False, error=f"Шаг buy_building недоступен (текущий: {pd['step']})")

            _finish_deploy(request.player_id, building=None)

            print(f"🏗 Deploy finished (no building)")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


# ── ADVANCE ENDPOINTS ─────────────────────────────────────────────────────────

@app.post('/api/game/advance-choose-source')
async def advance_choose_source_endpoint(request: AdvanceChooseSourceRequest) -> GameStateResponse:
    """Выбрать source тайл для Advance."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_choose_source(_active_game, request.player_id, request.source_tile_key)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: выбран source тайл {request.source_tile_key}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/advance-move-ship')
async def advance_move_ship_endpoint(request: AdvanceMoveUnitRequest) -> GameStateResponse:
    """Переместить корабль."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_move_ship(_active_game, request.player_id, request.from_area_idx, request.to_area_idx)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: корабль {request.from_area_idx} → {request.to_area_idx}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/advance-move-ground')
async def advance_move_ground_endpoint(request: AdvanceMoveUnitRequest) -> GameStateResponse:
    """Переместить наземного юнита."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_move_ground(_active_game, request.player_id, request.from_area_idx, request.to_area_idx)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: наземный юнит {request.from_area_idx} → {request.to_area_idx}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))




@app.post('/api/game/advance-commit')
async def advance_commit_endpoint(request: AdvanceGenericRequest) -> GameStateResponse:
    """Зафиксировать все перемещения."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_commit(_active_game, request.player_id)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: перемещения зафиксированы")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/advance-fight')
async def advance_fight_endpoint(request: AdvanceGenericRequest) -> GameStateResponse:
    """Провести бой."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_fight(_active_game, request.player_id)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: бой завершён")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/advance-orbital')
async def advance_orbital_endpoint(request: AdvanceOrbitalRequest) -> GameStateResponse:
    """Выбрать корабль и цель для орбитального удара."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_orbital(_active_game, request.player_id, request.ship_area_idx, request.target_area_idx)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: орбитальный удар {request.ship_area_idx} → {request.target_area_idx}")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/advance-orbital-remove')
async def advance_orbital_remove_endpoint(request: AdvanceOrbitalRemoveRequest) -> GameStateResponse:
    """Защищающийся удаляет юнита после орбитального удара."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_orbital_remove(_active_game, request.player_id, request.area_idx, request.unit_idx)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: орбитальный удар — юнит удалён")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/advance-skip-orbital')
async def advance_skip_orbital_endpoint(request: AdvanceGenericRequest) -> GameStateResponse:
    """Пропустить орбитальный удар."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_skip_orbital(_active_game, request.player_id)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: орбитальный удар пропущен")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
            return GameStateResponse(success=False, error=str(e))


@app.post('/api/game/advance-next-step')
async def advance_next_step_endpoint(request: AdvanceGenericRequest) -> GameStateResponse:
    """Перейти от ships к ground."""
    async with _game_lock:
        if _active_game is None:
            return GameStateResponse(success=False, error="Игра не инициализирована")
        try:
            new_state = advance_next_step(_active_game, request.player_id)
            _active_game.clear()
            _active_game.update(new_state)
            print(f"⚔️ Advance: переход к наземным юнитам")
            _save_current_state()
            return GameStateResponse(success=True, state=_prepare_response_state())
        except Exception as e:
            import traceback; traceback.print_exc()
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
