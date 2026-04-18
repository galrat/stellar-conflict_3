"""
game_server.py — FastAPI сервер для Stellar Conflict

Запуск: uvicorn game_server:app --reload --port 8000
Сервер слушает на http://localhost:8000

Stage 1 (карта) — JS управляет, сервер только сохраняет/загружает.
Stage 2 (приказы) — Python управляет state, JS только отображает.
"""
from api import app

if __name__ == '__main__':
    print('=' * 60)
    print('🎮 Stellar Conflict Game Server')
    print('=' * 60)
    print('Запуск: uvicorn game_server:app --reload --port 8000')
    print('Server: http://localhost:8000')
    from pathlib import Path
    SAVES_DIR = Path.home() / "Downloads" / "Stellar_Conflict_Saves"
    print(f'Saves: {SAVES_DIR.absolute()}')
    print('=' * 60)
    print('⚠️  Используйте uvicorn для запуска, не python!')
