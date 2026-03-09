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


def build_js_factions(factions: dict) -> str:
    """Генерирует JS-массив FACTIONS из Python-данных фракций."""
    lines = ["const FACTIONS = ["]
    for f in factions.values():
        uc = f.unit_config
        ground = uc.infantry + uc.marines + uc.mechanized + uc.elite
        space  = uc.fighters + uc.destroyers

        # Экранируем одиночные кавычки во флаворе (безопасно для JS-строки)
        flavor = f.flavor.replace("'", "\\'").replace("\n", " ").strip()
        # Убираем лишние пробелы
        flavor = re.sub(r"\s+", " ", flavor)

        lines.append(
            f"  {{ id:'{f.id}', name:'{f.name}', icon:'{f.icon}', "
            f"flavor:'{flavor}', "
            f"troops:{{ground:{ground},space:{space}}} }},"
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
