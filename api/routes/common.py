"""
api/routes/common.py — инфраструктура (FastAPI, CORS, тайлы)
"""
import re
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


# ── Загрузка каталога тайлов с диска (пока tiles.js — источник истины) ──
def _load_tile_catalog_from_js():
    """Загружает каталог тайлов из tiles.js файла."""
    try:
        js_file = Path(__file__).parent.parent.parent / "tiles.js"
        content = js_file.read_text(encoding='utf-8')
        # Извлекаем TILE_CATALOG из JS кода — ищем "const TILE_CATALOG = ["
        start = content.find('const TILE_CATALOG = [')
        if start == -1:
            return []
        start += len('const TILE_CATALOG = ')
        # Ищем закрывающий ];
        end = content.find('];', start)
        if end == -1:
            return []
        json_str = content[start:end+1]
        # Конвертируем JS объекты в JSON (замена одинарных кавычек на двойные)
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        json_str = re.sub(r": '([^']*)'", r': "\1"', json_str)
        tiles = json.loads(json_str)
        return tiles
    except Exception as e:
        print(f"Error loading tiles from JS: {e}")
        return []


TILE_CATALOG_FRONTEND = _load_tile_catalog_from_js()


@app.get('/api/tiles')
async def get_tiles():
    """Получить каталог тайлов для фронтенда (тонкий клиент)."""
    return {'tiles': TILE_CATALOG_FRONTEND}


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
