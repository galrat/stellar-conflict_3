"""
api/utils.py — вспомогательные функции для игры (snapshots, state fields, etc.)
"""
import json
import glob
from pathlib import Path
from typing import List
from api.state import get_active_game, STATE_DEFAULTS

# Папка для временных snapshots (для undo)
TEMP_DIR = Path.home() / "Downloads" / "Stellar_Conflict_Temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MAX_TEMP_SNAPSHOTS = 10

# Папка проекта
PROJECT_DIR = Path(__file__).parent.parent
CURRENT_STATE_FILE = PROJECT_DIR / "current_state.txt"


def ensure_state_fields(state: dict):
    """Гарантировать наличие всех обязательных полей в state."""
    import copy
    for key, default in STATE_DEFAULTS.items():
        if key not in state:
            state[key] = copy.deepcopy(default)


def get_temp_snapshots() -> List[str]:
    """Получить список временных snapshots, отсортированные по времени"""
    files = glob.glob(str(TEMP_DIR / "state_temp_*.json"))
    return sorted(files)


def save_temp_snapshot() -> str:
    """Сохранить текущий state во временный файл. Возвращает путь файла."""
    active_game = get_active_game()
    if active_game is None:
        return ""

    snapshots = get_temp_snapshots()

    # Если уже есть 10 — удалить самый старый
    if len(snapshots) >= MAX_TEMP_SNAPSHOTS:
        Path(snapshots[0]).unlink()
        snapshots = snapshots[1:]

    # Номер нового файла
    next_num = len(snapshots)
    filepath = TEMP_DIR / f"state_temp_{next_num}.json"

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(active_game, f, indent=2, ensure_ascii=False)

    return str(filepath)


def load_temp_snapshot(idx: int) -> bool:
    """Загрузить временный snapshot с индексом. Возвращает True если успех."""
    from api.state import set_active_game
    try:
        snapshots = get_temp_snapshots()
        if idx < 0 or idx >= len(snapshots):
            return False

        with open(snapshots[idx], 'r', encoding='utf-8') as f:
            state = json.load(f)

        set_active_game(state)
        ensure_state_fields(state)
        return True
    except Exception:
        return False


def clear_temp_snapshots():
    """Очистить все временные snapshots"""
    snapshots = get_temp_snapshots()
    for f in snapshots:
        Path(f).unlink()


def save_current_state():
    """Сохранить текущий state в current_state.txt в папке проекта"""
    active_game = get_active_game()
    if active_game is None:
        return
    try:
        with open(CURRENT_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(active_game, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  Ошибка при сохранении current_state.txt: {e}")


def prepare_response_state(active_game: dict, compute_ui_hints_fn) -> dict:
    """Подготовить state для отправки клиенту: добавить ui hints."""
    state = active_game.copy()
    state['ui'] = compute_ui_hints_fn(active_game)
    return state
