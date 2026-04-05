"""
game_server.py — FastAPI сервер для сохранения и загрузки игр

Запуск: uvicorn game_server:app --reload --port 8000
Сервер слушает на http://localhost:8000
"""
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

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
# FastAPI имеет встроенный лимит через max_upload_size
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

# Папка Загрузки (работает на Windows, Mac, Linux)
SAVES_DIR = Path.home() / "Downloads" / "Stellar_Conflict_Saves"
SAVES_DIR.mkdir(parents=True, exist_ok=True)


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


@app.get('/')
async def root():
    """Корневой эндпоинт"""
    return {
        'status': 'ok',
        'name': '🎮 Stellar Conflict Game Server',
        'endpoints': {
            'save': 'POST /api/save',
            'load': 'GET /api/load/{filename}',
            'list': 'GET /api/list',
            'delete': 'DELETE /api/delete/{filename}',
            'download': 'GET /api/download/{filename}',
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
