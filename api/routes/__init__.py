"""
api/routes — роутеры приложения
"""
# Импортируем всё из routes в порядке зависимостей
from api.routes.common import app
# storage и game_logic регистрируют свои маршруты через app
from api.routes import storage
from api.routes import game_logic

__all__ = ['app']
