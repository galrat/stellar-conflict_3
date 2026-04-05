"""
export_factions.py — синхронизирует данные фракций из Python в game_engine.html.

Запуск:  python export_factions.py

Что делает:
  1. Читает все фракции из faction_defs (Python)
  2. Формирует блок FACTIONS для JavaScript
  3. Заменяет блок const FACTIONS = [...] в game_engine.html

После этого просто обнови страницу в браузере — изменения подхватятся.
"""
import re
import sys
sys.path.insert(0, ".")

from faction_defs import FACTIONS


def escape_js_string(s: str) -> str:
    """Безопасно экранирует строку для JS."""
    if not s:
        return ""
    s = str(s)
    s = s.replace("\\", "\\\\")  # обратные слэши сначала
    s = s.replace("'", "\\'")    # одиночные кавычки
    s = s.replace('"', '\\"')    # двойные кавычки
    s = s.replace("\n", " ")     # переносы строк
    s = re.sub(r"\s+", " ", s)  # множественные пробелы
    return s.strip()

def build_js_factions(factions: dict) -> str:
    """Генерирует JS-массив FACTIONS из Python-данных фракций."""
    lines = ["const FACTIONS = ["]
    for f in factions.values():
        uc = f.unit_config

        # Генерируем unitTiers на основе unit_config
        ground_tiers = []
        if uc.infantry > 0:
            ground_tiers.extend([0] * uc.infantry)     # tier 0
        if uc.marines > 0:
            ground_tiers.extend([1] * uc.marines)      # tier 1
        if uc.mechanized > 0:
            ground_tiers.extend([2] * uc.mechanized)   # tier 2
        if uc.elite > 0:
            ground_tiers.extend([3] * uc.elite)        # tier 3

        space_tiers = []
        if uc.fighters > 0:
            space_tiers.extend([0] * uc.fighters)      # tier 0
        if uc.destroyers > 0:
            space_tiers.extend([2] * uc.destroyers)    # tier 2

        ground = uc.infantry + uc.marines + uc.mechanized + uc.elite
        space  = uc.fighters + uc.destroyers

        # Генерируем структуры на основе unit_config
        structures = []
        if uc.factories > 0:
            structures.extend(['factory'] * uc.factories)
        if uc.cities > 0:
            structures.extend(['city'] * uc.cities)
        if uc.bastions > 0:
            structures.extend(['bastion'] * uc.bastions)

        # Если flavor случайно стал кортежем — склеиваем в строку
        raw_flavor = " ".join(f.flavor) if isinstance(f.flavor, tuple) else f.flavor
        # Убеждаемся что цвет содержит #
        color = f.color if '#' in f.color else f"#{f.color}"

        # Экранируем все строки
        flavor = escape_js_string(raw_flavor)
        name = escape_js_string(f.name)

        lines.append(
            f"  {{ id:'{f.id}', name:'{name}', icon:'{f.icon}', color:'{color}', "
            f"homeTileId:'{f.home_tile_id}', "
            f"flavor:'{flavor}', "
            f"troops:{{ground:{ground},space:{space}}}, "
            f"unitTiers:{{ground:{ground_tiers},space:{space_tiers}}}, "
            f"structures:{structures} }},"
        )
    lines.append("];")
    return "\n".join(lines)


def update_html(html_path: str, js_factions: str) -> None:
    """Заменяет блок const FACTIONS = [...] в HTML-файле."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем блок от "const FACTIONS = [" до первого "];" на отдельной строке
    pattern = r"const FACTIONS = \[.*?\];"
    if not re.search(pattern, content, flags=re.DOTALL):
        print("ОШИБКА: блок 'const FACTIONS = [...]' не найден в HTML.")
        sys.exit(1)

    new_content = re.sub(pattern, js_factions, content, flags=re.DOTALL)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_content)


if __name__ == "__main__":
    html_path = "game_engine.html"

    js_block = build_js_factions(FACTIONS)
    update_html(html_path, js_block)

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"OK — {len(FACTIONS)} фракций записано в {html_path}:")
    for fid, f in FACTIONS.items():
        uc = f.unit_config
        ground = uc.infantry + uc.marines + uc.mechanized + uc.elite
        space  = uc.fighters + uc.destroyers
        print(f"  {f.icon} {f.name:20s} ground={ground}  space={space}")
    print("\nОбнови страницу в браузере.")
