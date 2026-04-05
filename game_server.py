"""
game_server.py — простой Flask сервер для сохранения и загрузки игр

Запуск: python game_server.py
Сервер слушает на http://localhost:5000
"""
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Лимит размера контента (10 МБ макс)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

# Папка Загрузки (работает на Windows, Mac, Linux)
SAVES_DIR = Path.home() / "Downloads" / "Stellar_Conflict_Saves"
SAVES_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/api/save', methods=['POST'])
def save_game():
    """Сохранить состояние игры"""
    try:
        data = request.get_json()
        filename = data.get('filename', 'game_auto.json')
        state = data.get('state')

        if not filename.endswith('.json'):
            filename += '.json'

        filepath = SAVES_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        file_size = filepath.stat().st_size
        print(f"✅ Сохранено: {filename} ({file_size} B)")

        return jsonify({'success': True, 'filename': filename, 'path': str(filepath)})
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/load/<filename>', methods=['GET'])
def load_game(filename):
    """Загрузить состояние игры"""
    try:
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = SAVES_DIR / filename

        if not filepath.exists():
            print(f"⚠️  Файл не найден: {filename}")
            return jsonify({'success': False, 'error': 'File not found'}), 404

        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)

        print(f"✅ Загружено: {filename}")
        return jsonify({'success': True, 'state': state})
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/list', methods=['GET'])
def list_games():
    """Список сохранённых игр"""
    try:
        games = []
        for filepath in sorted(SAVES_DIR.glob('*.json')):
            games.append({
                'filename': filepath.name,
                'size': filepath.stat().st_size,
                'modified': filepath.stat().st_mtime
            })

        print(f"📂 Список игр: найдено {len(games)} файлов")
        return jsonify({'success': True, 'games': games})
    except Exception as e:
        print(f"❌ Ошибка при получении списка: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_game(filename):
    """Удалить сохранённую игру"""
    try:
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = SAVES_DIR / filename

        if not filepath.exists():
            print(f"⚠️  Файл не найден для удаления: {filename}")
            return jsonify({'success': False, 'error': 'File not found'}), 404

        filepath.unlink()
        print(f"🗑️  Удалено: {filename}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/download/<filename>', methods=['GET'])
def download_game(filename):
    """Скачать сохранённую игру как JSON файл"""
    try:
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = SAVES_DIR / filename

        if not filepath.exists():
            print(f"⚠️  Файл не найден для скачивания: {filename}")
            return jsonify({'success': False, 'error': 'File not found'}), 404

        print(f"⬇️  Скачивание: {filename}")
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    print('=' * 60)
    print('🎮 Stellar Conflict Game Server')
    print('=' * 60)
    print(f'Server: http://localhost:5000')
    print(f'Saves: {SAVES_DIR.absolute()}')
    print('=' * 60)
    app.run(debug=True, port=5000)
